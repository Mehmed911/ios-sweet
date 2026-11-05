[CmdletBinding()]
param(
    [string]$Kernel = 'work/github-xnu-run-41740480659/artifact/kernel.development.sweet',
    [string]$Adt = 'work/ci-41231550176-ufs-route/fixture-backends-gic-auth/qemu-ufs.adt',
    [string]$Reference = 'work/launchctl-cfprefs-batch-v2',
    [string]$Hfsplus = 'research/libdmg-hfsplus-build/hfsplus',
    [string]$Output,
    [ValidateRange(1, 3600)][int]$Seconds = 300,
    [ValidatePattern('^[A-Za-z0-9._-]+$')][string]$Distro = 'Ubuntu',
    [switch]$VerifyOnly
)

$ErrorActionPreference = 'Stop'
$taskRepo = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path

function Resolve-TaskPath([string]$Path) {
    if ([IO.Path]::IsPathRooted($Path)) {
        return [IO.Path]::GetFullPath($Path)
    }
    return [IO.Path]::GetFullPath((Join-Path $taskRepo $Path))
}

function Assert-PinnedFile([string]$Name, [string]$Path, [string]$Expected) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "$Name is missing: $Path"
    }
    $taskActual = (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($taskActual -ne $Expected) {
        throw "$Name pin differs: expected $Expected, got $taskActual"
    }
    return $taskActual
}

$taskPins = [ordered]@{
    kernel = 'cbaba0812c449d67e0e3e6c718e696b52b3f43228d9f020c145e8b5b28926b30'
    adt = 'a82c9cc6e2891bacd444d9feac56f00fe58491a9f719292739f08cb73aa7fac9'
    root = '89388d378c8d2fc66cf942d3c60647ad0579ebb29df629903a7bad0c44469a21'
    hfsplus = 'be041fa07ae8cbe040a2ec3811241af993eea597e8d46917f6c32359b2cd8b1b'
}

$taskKernel = Resolve-TaskPath $Kernel
$taskAdt = Resolve-TaskPath $Adt
$taskReference = Resolve-TaskPath $Reference
$taskHfsplus = Resolve-TaskPath $Hfsplus
$taskRoot = Join-Path $taskReference 'root.hfs'

$null = Assert-PinnedFile 'kernel' $taskKernel $taskPins.kernel
$null = Assert-PinnedFile 'ADT' $taskAdt $taskPins.adt
$null = Assert-PinnedFile 'RAM root' $taskRoot $taskPins.root
$null = Assert-PinnedFile 'hfsplus' $taskHfsplus $taskPins.hfsplus

$taskReady = [ordered]@{
    ready = $true
    mode = 'QEMU RAM-root fast boot'
    pins = $taskPins
    paths = [ordered]@{
        kernel = $taskKernel
        adt = $taskAdt
        reference = $taskReference
        hfsplus = $taskHfsplus
    }
    physical_device_access = $false
    physical_ufs_enabled = $false
    partition_write = $false
}

if ($VerifyOnly) {
    $taskReady | ConvertTo-Json -Depth 5
    exit 0
}

if ([string]::IsNullOrWhiteSpace($Output)) {
    $taskStamp = Get-Date -Format 'yyyyMMdd-HHmmss'
    $Output = "work/fast-ramboot-$taskStamp"
}
$taskOutput = Resolve-TaskPath $Output
if (Test-Path -LiteralPath $taskOutput) {
    throw "Preserve existing output: $taskOutput"
}

$taskRunner = Join-Path $PSScriptRoot 'test-duchamp-system-native.ps1'
& $taskRunner `
    -Kernel $taskKernel `
    -KernelSha256 $taskPins.kernel `
    -RootSha256 $taskPins.root `
    -Reference $taskReference `
    -Adt $taskAdt `
    -AdtSha256 $taskPins.adt `
    -Hfsplus $taskHfsplus `
    -Output $taskOutput `
    -Distro $Distro `
    -Seconds $Seconds

if ($LASTEXITCODE -ne 0) {
    throw "Fast RAM boot failed with exit code $LASTEXITCODE"
}

$taskVerificationPath = Join-Path $taskOutput 'verification.json'
if (-not (Test-Path -LiteralPath $taskVerificationPath -PathType Leaf)) {
    throw 'Fast RAM boot did not produce verification.json'
}
$taskVerification = Get-Content -LiteralPath $taskVerificationPath -Raw | ConvertFrom-Json
if ($taskVerification.passed -ne $true -or
    $taskVerification.service_checks -ne 72 -or
    $taskVerification.checks.virtual_timer_irq_witness -ne $true) {
    throw 'Fast RAM boot result did not satisfy the pinned success contract'
}

[ordered]@{
    passed = $true
    output = $taskOutput
    elapsed_host_seconds = $taskVerification.elapsed_host_seconds
    service_checks = $taskVerification.service_checks
    virtual_timer_irq_witness = $taskVerification.checks.virtual_timer_irq_witness
    kernel_sha256 = $taskVerification.kernel_sha256
    adt_sha256 = $taskVerification.adt_sha256
    scope = 'QEMU RAM root only; no phone, physical UFS, MMIO, SMC or partition access'
} | ConvertTo-Json -Depth 4
