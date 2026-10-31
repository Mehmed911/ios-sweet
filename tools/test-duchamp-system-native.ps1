[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$Kernel,
    [Parameter(Mandatory)][ValidatePattern('^[0-9a-f]{64}$')][string]$KernelSha256,
    [Parameter(Mandatory)][ValidatePattern('^[0-9a-f]{64}$')][string]$RootSha256,
    [Parameter(Mandatory)][string]$Reference,
    [Parameter(Mandatory)][string]$Adt,
    [Parameter(Mandatory)][string]$Hfsplus,
    [Parameter(Mandatory)][string]$Output,
    [ValidatePattern('^[A-Za-z0-9._-]+$')][string]$Distro='Ubuntu',
    [ValidateRange(1,3600)][int]$Seconds=900,
    [ValidateRange(0,10)][Nullable[int]]$IcountShift
)
$ErrorActionPreference='Stop'
$taskOutput=[IO.Path]::GetFullPath($Output)
if(Test-Path -LiteralPath $taskOutput){throw 'Preserve existing output'}
$taskKernel=(Resolve-Path -LiteralPath $Kernel).Path
$taskReference=(Resolve-Path -LiteralPath $Reference).Path
$taskAdt=(Resolve-Path -LiteralPath $Adt).Path
$taskHfs=(Resolve-Path -LiteralPath $Hfsplus).Path
if((Get-FileHash -LiteralPath $taskKernel -Algorithm SHA256).Hash.ToLowerInvariant() -ne $KernelSha256){throw 'Kernel pin differs'}
$taskRoot=Join-Path $taskReference 'root.hfs'
if((Get-FileHash -LiteralPath $taskRoot -Algorithm SHA256).Hash.ToLowerInvariant() -ne $RootSha256){throw 'Root pin differs'}
# Windows->WSL copy avoids the Linux /mnt/c 9P mount, including a stalled mount.
$taskNative=(& wsl.exe -d $Distro --cd /tmp -e mktemp -d /tmp/duchamp-system-XXXXXXXXXX).Trim()
if($LASTEXITCODE -ne 0 -or $taskNative -notmatch '^/tmp/duchamp-system-[A-Za-z0-9]+$'){throw 'Cannot create owned Linux workspace'}
$taskUnc='\\wsl.localhost\'+$Distro+$taskNative.Replace('/','\')
New-Item -ItemType Directory -Path (Join-Path $taskUnc 'tools'),(Join-Path $taskUnc 'reference'),(Join-Path $taskUnc 'reference/run') | Out-Null
$taskSources=@('test-duchamp-system-boot.py','verify-sweet-cfprefs-batch.py','qemu-sweet.py','mkpayload.py','adt.py','qemu_ufs.py')
$taskHashes=[ordered]@{}
foreach($taskName in $taskSources){
    $taskSource=Join-Path $PSScriptRoot $taskName
    $taskHashes[$taskName]=(Get-FileHash -LiteralPath $taskSource -Algorithm SHA256).Hash.ToLowerInvariant()
    Copy-Item -LiteralPath $taskSource -Destination (Join-Path $taskUnc ('tools/'+$taskName))
}
foreach($taskName in @('root.hfs','inputs.json','runtime-audit.json','launchctl-root-manifest.json','sweet-launchd-service','sweet-ipc-client','sweet-launchctl-control','run/verification.json')){
    Copy-Item -LiteralPath (Join-Path $taskReference $taskName) -Destination (Join-Path $taskUnc ('reference/'+$taskName))
}
Copy-Item -LiteralPath (Join-Path $taskReference 'test-sources') -Destination (Join-Path $taskUnc 'reference/test-sources') -Recurse
Copy-Item -LiteralPath $taskKernel -Destination (Join-Path $taskUnc 'kernel')
Copy-Item -LiteralPath $taskAdt -Destination (Join-Path $taskUnc 'tree.adt')
Copy-Item -LiteralPath $taskHfs -Destination (Join-Path $taskUnc 'hfsplus')
& wsl.exe -d $Distro --cd $taskNative -e chmod 755 ($taskNative+'/hfsplus')
if($LASTEXITCODE -ne 0){throw 'Cannot prepare copied HFS tool'}
$taskArguments=@('-d',$Distro,'--cd',$taskNative,'-e','python3',($taskNative+'/tools/test-duchamp-system-boot.py'),
    '--kernel',($taskNative+'/kernel'),'--kernel-sha256',$KernelSha256,'--root-sha256',$RootSha256,
    '--reference',($taskNative+'/reference'),'--adt',($taskNative+'/tree.adt'),'--hfsplus',($taskNative+'/hfsplus'),
    '--output',($taskNative+'/result'),'--seconds',[string]$Seconds)
if($null -ne $IcountShift){$taskArguments+=@('--icount-shift',[string]$IcountShift)}
Write-Output ('Linux workspace: '+$taskNative)
& wsl.exe @taskArguments
$taskExit=$LASTEXITCODE
New-Item -ItemType Directory -Path $taskOutput | Out-Null
$taskResult=Join-Path $taskUnc 'result'
if(Test-Path -LiteralPath $taskResult){
    Get-ChildItem -LiteralPath $taskResult -Force | ForEach-Object {Copy-Item -LiteralPath $_.FullName -Destination $taskOutput -Recurse}
}
$taskUnchanged=$true
foreach($taskName in $taskSources){
    if((Get-FileHash -LiteralPath (Join-Path $PSScriptRoot $taskName) -Algorithm SHA256).Hash.ToLowerInvariant() -ne $taskHashes[$taskName]){$taskUnchanged=$false}
}
$taskInputsPreserved=((Get-FileHash -LiteralPath $taskKernel -Algorithm SHA256).Hash.ToLowerInvariant() -eq $KernelSha256 -and
    (Get-FileHash -LiteralPath $taskRoot -Algorithm SHA256).Hash.ToLowerInvariant() -eq $RootSha256)
$taskMetadata=[ordered]@{child_exit=$taskExit;linux_workspace=$taskNative;source_sha256=$taskHashes;
    original_sources_unchanged=$taskUnchanged;original_kernel_root_unchanged=$taskInputsPreserved;
    transport='Windows UNC copy; all VM trace/snapshot/HFS operations on Linux filesystem';physical_device_access=$false}
$taskMetadata | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $taskOutput 'native-workspace.json') -Encoding utf8
if($taskExit -ne 0){exit $taskExit}
if(-not $taskUnchanged -or -not $taskInputsPreserved){throw 'Source/input preservation check failed'}
