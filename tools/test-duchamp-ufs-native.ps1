[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$Kernel,
    [Parameter(Mandatory)][ValidatePattern('^[0-9a-f]{64}$')][string]$KernelSha256,
    [Parameter(Mandatory)][string]$Fixture,
    [Parameter(Mandatory)][ValidatePattern('^[0-9a-f]{40}$')][string]$Head,
    [Parameter(Mandatory)][ValidatePattern('^[0-9]+$')][string]$Run,
    [Parameter(Mandatory)][string]$Output,
    [ValidateRange(1,900)][int]$Seconds=180,
    [switch]$Backends
)
$ErrorActionPreference='Stop'
$taskOutput=[IO.Path]::GetFullPath($Output)
if(Test-Path -LiteralPath $taskOutput){throw 'Preserve existing output'}
$taskKernel=(Resolve-Path -LiteralPath $Kernel).Path
$taskFixture=(Resolve-Path -LiteralPath $Fixture).Path
if((Get-FileHash -LiteralPath $taskKernel -Algorithm SHA256).Hash.ToLowerInvariant() -ne $KernelSha256){throw 'Kernel pin differs'}
$taskFixtureNames=@('root.hfs','launchd','ufs-expected.bin','qemu-ufs.adt')
$taskManifest=Get-Content -LiteralPath (Join-Path $taskFixture 'fixture.json') -Raw | ConvertFrom-Json
$taskKeys=@($taskManifest.sha256.PSObject.Properties.Name)
if(@(Compare-Object $taskKeys $taskFixtureNames).Count -ne 0){throw 'Unexpected fixture manifest files'}
$taskFixtureHashes=[ordered]@{}
foreach($taskName in ($taskFixtureNames+@('fixture.json'))){
    $taskHash=(Get-FileHash -LiteralPath (Join-Path $taskFixture $taskName) -Algorithm SHA256).Hash.ToLowerInvariant()
    if($taskName -ne 'fixture.json' -and $taskHash -ne $taskManifest.sha256.$taskName){throw ('Fixture pin differs: '+$taskName)}
    $taskFixtureHashes[$taskName]=$taskHash
}
$taskNative=(& wsl.exe -d Ubuntu --cd /tmp -e mktemp -d /tmp/duchamp-ufs-XXXXXXXXXX).Trim()
if($LASTEXITCODE -ne 0 -or $taskNative -notmatch '^/tmp/duchamp-ufs-[A-Za-z0-9]+$'){throw 'Cannot create Linux workspace'}
$taskUnc='\\wsl.localhost\Ubuntu'+$taskNative.Replace('/','\')
New-Item -ItemType Directory -Path (Join-Path $taskUnc 'tools'),(Join-Path $taskUnc 'fixture') | Out-Null
$taskSources=[ordered]@{}
foreach($taskName in @('qemu-sweet.py','qemu_ufs.py','duchamp-ufs-init.S','duchamp-backend-init.S','test-duchamp-ufs-xnu.py','build-duchamp-ufs-fixture.py','mkpayload.py','adt.py')){
    $taskSource=Join-Path $PSScriptRoot $taskName
    $taskSources[$taskName]=(Get-FileHash -LiteralPath $taskSource -Algorithm SHA256).Hash.ToLowerInvariant()
    Copy-Item -LiteralPath $taskSource -Destination (Join-Path $taskUnc ('tools/'+$taskName))
}
Copy-Item -LiteralPath $taskKernel -Destination (Join-Path $taskUnc 'kernel')
foreach($taskName in $taskFixtureHashes.Keys){Copy-Item -LiteralPath (Join-Path $taskFixture $taskName) -Destination (Join-Path $taskUnc ('fixture/'+$taskName))}
$taskArgs=@('-d','Ubuntu','--cd',$taskNative,'-e','python3','tools/test-duchamp-ufs-xnu.py',
    '--kernel','kernel','--kernel-sha256',$KernelSha256,'--fixture','fixture','--output','result',
    '--ci-run',$Run,'--ci-head',$Head,'--seconds',[string]$Seconds)
if($Backends){$taskArgs+='--backends'}
Write-Output ('Linux workspace: '+$taskNative)
& wsl.exe @taskArgs
$taskExit=$LASTEXITCODE
New-Item -ItemType Directory -Path $taskOutput | Out-Null
if(Test-Path -LiteralPath (Join-Path $taskUnc 'result')){
    Get-ChildItem -LiteralPath (Join-Path $taskUnc 'result') -Force | ForEach-Object {Copy-Item -LiteralPath $_.FullName -Destination $taskOutput -Recurse}
}
$taskUnchanged=$true
foreach($taskName in $taskSources.Keys){
    if((Get-FileHash -LiteralPath (Join-Path $PSScriptRoot $taskName) -Algorithm SHA256).Hash.ToLowerInvariant() -ne $taskSources[$taskName]){$taskUnchanged=$false}
}
$taskInputsPreserved=((Get-FileHash -LiteralPath $taskKernel -Algorithm SHA256).Hash.ToLowerInvariant() -eq $KernelSha256)
foreach($taskName in $taskFixtureHashes.Keys){
    if((Get-FileHash -LiteralPath (Join-Path $taskFixture $taskName) -Algorithm SHA256).Hash.ToLowerInvariant() -ne $taskFixtureHashes[$taskName]){$taskInputsPreserved=$false}
}
[ordered]@{child_exit=$taskExit;source_sha256=$taskSources;fixture_sha256=$taskFixtureHashes;
    original_sources_unchanged=$taskUnchanged;original_inputs_unchanged=$taskInputsPreserved;
    linux_workspace=$taskNative;physical_device_access=$false} | ConvertTo-Json -Depth 5 |
    Set-Content -LiteralPath (Join-Path $taskOutput 'native-workspace.json') -Encoding utf8
if($taskExit -ne 0){exit $taskExit}
if(-not $taskUnchanged -or -not $taskInputsPreserved){throw 'Source/input preservation check failed'}
