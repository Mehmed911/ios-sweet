# Original backboardd: current source-XNU QEMU runtime status

2026-11-18/19; physical status remains `BLOCKED_BY_MEMORY_EVIDENCE`.

The original 20F66 executable now starts through its native launchd job and
answers the native display-information RPC. It is **not classified as a fully
working graphics/input service**. No original frame or BackBoard HID stream
was verified in this batch.

## Identity and dependency resolution

Executable: `/usr/libexec/backboardd`, 1,182,960 bytes,
SHA-256 `686f26a6a7b749fd0ae30acca704022da8cb6f85b5c39a0e0e09e25ffd00d273`,
UUID `E81FD7FD-034F-3195-A4F5-3C692536E5AA`. ARM64 subtype 0, iOS16.5,
LC_MAIN offset 38500, `/usr/lib/dyld`, no LC_RPATH. The original 45 strong
imports include `/System/Library/PrivateFrameworks/StudyLog.framework/StudyLog`.
Its entire recursive strong closure is present in the intact 20F66 cache:
267 nodes, 2,381 recorded edges including weak imports. The optional
`/usr/appleinternal/lib/liblinkguard.dylib` is not treated as a strong failure.

Cache UUID `E5420DB3-30D0-33AA-8B7E-05B5038BB46D`; all 43 runtime component
hashes verified. See [cache report](DUCHAMP_IOS_20F66_SHARED_CACHE.md) for
provenance, architecture, signatures, mappings, commands and filesystem scope.

## Actual observations

Evidence root: `../../outputs/duchamp-ios20f66-integration-20261118/`.

- `runtime-1/observer.log`: direct-exec PID 8, successful exec, requested UID/GID
  501, SIGTRAP 5, no watchdog timeout. This trial alone is not service startup.
- `native-primary/controller.log`: the original launchd-managed PID 25 has
  actual UID/GID 501/501 and PPID 1, with its actual executable path checked.
  Six five-second health samples retain that process identity.
- `native-primary/ui-display.txt`: original BackBoardServices framework obtains
  server port 7683; two native `_BKSDisplayGetMainScreenInfo` calls return
  `kr=0`, values `1125,2436,1,0`, flags `0,0`. Sentinels were replaced only
  following valid native replies. No custom process implements that endpoint.
- `native-primary/4-print-0.txt`: original mobile job in `user/501`; the original
  MachServices dictionary is preserved. Job declarations alone are not reply proof.
- `native-primary/com.apple.backboardd.log`: duplicate Objective-C class warning
  for `_BKRuleResolutionTranscript` in the binary and BackBoardHIDEventFoundation.
  It did not prevent these observed replies; the warning is not silently removed.

The original job declares 18 Mach services. Diagnostic overrides are limited
to KeepAlive=false, RunAtLoad=false and writable stdout/stderr destinations.
Program/arguments, mobile credentials and MachServices remain original.
The native provider batch also includes matching logd, container manager,
installd, lsd, runningboardd, resources and application registry setup.
This differs from the failed direct-exec fixture in several ways; a unique
cause of the SIGTRAP has not been isolated.

## Milestones

| Milestone | Current evidence |
|---|---|
| Kernel accepts executable | Verified original exec and native launchd process |
| Initial dyld dependencies resolve | Verified past previous missing StudyLog failure to native RPC handling |
| Program executes | Verified original process handling display requests; no instrumented main PC |
| Runtime initialization completes | Display-service subset verified; complete HID/render/power initialization unknown |
| Mach service registration | Native server port and two actual display replies; other declared endpoints not all tested |
| Remains alive | Verified same PID/path/UID/PPID over six five-second health samples |
| Meaningful frame/input work | **Not verified** |

## Remaining runtime dependencies

Actual bootstrap failures include `com.apple.mobilegestalt.xpc`,
`com.apple.oscard`, `com.apple.ACCHWComponentAuthService`,
`com.apple.coremedia.virtualframebuffer.xpc` and analytics endpoints.
`runtime-missing-services.json` retains source frame locations and requestor
identities for observed failures. Some may be optional. No claim is made that
one listed failure uniquely explains the absence of a graphical frame.

BackBoard reports 1125x2436 while virtual scanout is 1220x2712. Both are actual
observations, not a verified physical panel configuration. Full IOSurface,
CoreAnimation render-server behavior and native digitizer delivery remain
separate requirements. The existing custom compositor is not used as evidence
that these original interfaces work.

Next: trace a real native graphics transaction to its IOSurface, SwapEnd and
framebuffer bytes, and exercise an original BackBoard input consumer. Keep
physical UFS, phone boot and the frozen native memory layout unchanged.
