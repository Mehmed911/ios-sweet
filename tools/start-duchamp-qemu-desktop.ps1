param([switch]$InstallShortcut, [switch]$WindowsNative)

$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
$distro = 'Ubuntu'
$port = if ($WindowsNative) { 18292 } else { 18291 }
$title = if ($WindowsNative) { 'Duchamp QEMU Windows' } else { 'Duchamp QEMU Fast' }
$url = "http://127.0.0.1:$port/"
$edge = Join-Path ${env:ProgramFiles(x86)} 'Microsoft\Edge\Application\msedge.exe'
$logs = Join-Path $repo 'work\qemu-desktop'

if ($InstallShortcut) {
    $desktop = [Environment]::GetFolderPath('DesktopDirectory')
    $destination = Join-Path $desktop "$(if ($WindowsNative) { 'Duchamp QEMU Windows' } else { 'Duchamp QEMU' }).lnk"
    if (Test-Path -LiteralPath $destination) {
        throw "A shortcut already exists at $destination"
    }
    $engine = (Get-Process -Id $PID).Path
    $shell = New-Object -ComObject WScript.Shell
    $shortcut = $shell.CreateShortcut($destination)
    $shortcut.TargetPath = $engine
    $shortcut.Arguments = '-NoProfile -NonInteractive -WindowStyle Hidden -File "' + $PSCommandPath + '"'
    if ($WindowsNative) { $shortcut.Arguments += ' -WindowsNative' }
    $shortcut.WorkingDirectory = $repo
    $shortcut.Description = 'Start or reopen the local Duchamp QEMU test'
    $shortcut.IconLocation = "$edge,0"
    $shortcut.Save()
    Write-Output $destination
    return
}

function Test-DuchampViewer {
    try {
        $reply = Invoke-WebRequest -UseBasicParsing -Uri $url -TimeoutSec 2
        return ($reply.StatusCode -eq 200 -and $reply.Content.Contains("<title>$title</title>"))
    } catch {
        return $false
    }
}

$mutex = [Threading.Mutex]::new($false, "Local\DuchampQemuDesktopLauncher$port")
$locked = $false
try {
    $locked = $mutex.WaitOne([TimeSpan]::FromSeconds(35))
    if (-not $locked) { throw 'The emulator launcher is already preparing a session.' }
    if (-not (Test-Path -LiteralPath $edge -PathType Leaf)) { throw 'Microsoft Edge was not found.' }

    if (-not (Test-DuchampViewer)) {
        $windowsRepo = $repo.Replace('\', '/')
        $linuxRepo = [string](& wsl.exe -d $distro -- wslpath -u $windowsRepo)
        if ($LASTEXITCODE -ne 0 -or -not $linuxRepo.StartsWith('/')) {
            throw 'Ubuntu could not resolve the project path.'
        }
        $linuxHome = [string](& wsl.exe -d $distro -- printenv HOME)
        if ($LASTEXITCODE -ne 0 -or -not $linuxHome.StartsWith('/')) {
            throw 'Ubuntu could not resolve its cache directory.'
        }
        $scratch = "$linuxHome/.cache/duchamp-qemu-tests/quartzcore-replay-v1/setup-session-tmpfs"
        $volume = [string](& wsl.exe -d $distro -- findmnt -n -o FSTYPE -T $scratch)
        if ($LASTEXITCODE -ne 0) { throw 'The local Duchamp replay fixture was not found.' }
        if ($volume -eq 'ext4') {
            & wsl.exe -d $distro -u root -- mount -t tmpfs -o size=5500m,uid=1000,gid=1000,mode=0700 setup-session $scratch
            if ($LASTEXITCODE -ne 0) { throw 'Ubuntu could not prepare the RAM-only test volume.' }
        } elseif ($volume -ne 'tmpfs') {
            throw 'The test volume must be a local Ubuntu tmpfs.'
        }

        New-Item -ItemType Directory -Path $logs -Force | Out-Null
        $stamp = [DateTime]::UtcNow.ToString('yyyyMMdd-HHmmss', [Globalization.CultureInfo]::InvariantCulture)
        $run = "setup-run-desktop-$stamp-$PID"
        $stdout = Join-Path $logs "$run.stdout.txt"
        $stderr = Join-Path $logs "$run.stderr.txt"
        $arguments = @('-d', $distro, '--cd', ('"' + $linuxRepo + '"'), '--', 'sh',
            'tools/run-duchamp-qemu-desktop.sh', $port, $run)
        if ($WindowsNative) {
            $python = [string](& py.exe -3 -c 'import sys; print(sys.executable)')
            if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $python -PathType Leaf)) {
                throw 'Windows Python is required to start native QEMU.'
            }
            $linuxPython = [string](& wsl.exe -d $distro -- wslpath -u ($python.Replace('\', '/')))
            $nativeLog = Join-Path $logs "$run.native.txt"
            $linuxLog = [string](& wsl.exe -d $distro -- wslpath -u ($nativeLog.Replace('\', '/')))
            $arguments += @(('"' + $linuxPython + '"'), ('"' + $linuxLog + '"'))
        }
        $worker = Start-Process -FilePath 'wsl.exe' -ArgumentList $arguments -WindowStyle Hidden -RedirectStandardOutput $stdout -RedirectStandardError $stderr -PassThru
        $limit = [DateTime]::UtcNow.AddSeconds(25)
        while (-not (Test-DuchampViewer)) {
            if ($worker.HasExited -or [DateTime]::UtcNow -ge $limit) {
                throw "The Duchamp viewer did not start. See $stderr"
            }
            Start-Sleep -Milliseconds 300
        }
        Write-Output $run
    }
    Start-Process -FilePath $edge -ArgumentList @("--app=$url", '--window-size=495,860')
} catch {
    Add-Type -AssemblyName System.Windows.Forms
    [void][Windows.Forms.MessageBox]::Show($_.Exception.Message, 'Duchamp QEMU')
    throw
} finally {
    if ($locked) { $mutex.ReleaseMutex() }
    $mutex.Dispose()
}
