# Original SpringBoard: current source-XNU QEMU runtime status

2026-11-18/19; `BLOCKED_BY_MEMORY_EVIDENCE` is unchanged for physical boot.

The original 20F66 SpringBoard process starts through launchd and remains
alive through the bounded health checks. **An operational SpringBoard UI has
not been established.** No custom Darwin GUI is substituted for its output.

## Binary and dependency identity

Path: `/System/Library/CoreServices/SpringBoard.app/SpringBoard`.
Bytes: 112,048. SHA-256:
`7926a1ba0b115cf45102b2c3d8e4eb7bc9c84bcf70b573d2a798690d9148059c`.
UUID: `40EC75F0-76C1-3DEB-85F1-39369B09E9D5`.
ARM64 subtype 0, iOS minimum/SDK16.5, `/usr/lib/dyld`, LC_MAIN offset16296,
LC_RPATH `@executable_path/Frameworks`, no LC_ID_DYLIB.

Direct strong imports:

1. `/System/Library/PrivateFrameworks/SpringBoard.framework/SpringBoard`
2. `/System/Library/Frameworks/Foundation.framework/Foundation`
3. `/usr/lib/libobjc.A.dylib`
4. `/usr/lib/libSystem.B.dylib`

All are in the intact 20F66 cache, UUID
`E5420DB3-30D0-33AA-8B7E-05B5038BB46D`. The recursive strong graph contains
1,005 nodes and 16,150 recorded import edges including weak edges; no strong
library path is missing. This is metadata closure, not universal API/ABI
compatibility. Original bundle resources, Objective-C trampoline module and
the pinned matching icon/font support set are installed separately. Exact
294-file installation hashes and resource receipts are in the native-job inputs.
The executable is unchanged and was not re-signed in this work. Signature
metadata and provenance limitations are in the [cache report](DUCHAMP_IOS_20F66_SHARED_CACHE.md).

## Native-job test

Primary evidence: `../../outputs/duchamp-ios20f66-integration-20261118/native-primary/`.

- `ui-registry.txt`: native LaunchServices status256, rebuild callback returned
  success, installed non-placeholder `com.apple.springboard` record points to
  `/System/Library/CoreServices/SpringBoard.app`.
- `ui-display.txt`: two actual BackBoard display replies succeeded before
  SpringBoard was loaded.
- `controller.log`: bootstrap returned0; original SpringBoard PID34, UID/GID
  501/501, PPID1 and executable path checked. Six five-second health samples
  retained this identity. The guest completed without observed kernel panic.
- `6-print-0.txt`: actual domain `user/501`, original executable/arguments,
  mobile user, one exec, never exited at that observation. Some endpoints,
  including `com.apple.frontboard.systemappservices`, were active. The launchd
  `initialized=1` field is a launchd lifecycle observation, not proof that all
  SpringBoard UI initialization finished.
- `com.apple.SpringBoard.log` is empty. Platform dyld print variables did not
  yield a per-image child mapping trace in the earlier direct-exec trial.
  Cache mappings are independently recorded, but a full per-process image list
  and a traced main PC were not captured. Absence of stderr is not success.

The original job declares 33 Mach services. Program/arguments, mobile user,
EmbeddedHomeScreen semantics and MachServices are retained. KeepAlive and
RunAtLoad are disabled for bounded diagnostics; stdout/stderr go to writable
RAM paths. The job is kept outside automatic LaunchDaemons scanning until the
native registry/display checks pass, then bootstrapped through original launchctl.
No third-party process supplies fake success replies.

Earlier direct-exec PID9 ended in SIGTRAP5 without timeout; this remains a
separate failed runtime trial. The subsequent provider/resource/native-domain
batch changed multiple prerequisites, so it does not isolate that trap's cause.

## Milestones and limits

| Milestone | Current evidence |
|---|---|
| Accepted by XNU | Verified original exec/native process |
| Initial dyld dependencies resolved | Execution proceeds beyond the earlier missing SpringBoard.framework failure |
| Program entry/runtime code | Runtime activity and active endpoints observed; exact main PC not traced |
| Complete runtime initialization | **Unknown**; launchd's initialized flag is insufficient |
| Mach services | Original job endpoints observed, including active ones; no SpringBoard RPC response test yet |
| Process survives | Verified same original PID/path/credentials during six five-second samples |
| Graphical work | **Not verified**: no attributed IOSurface, SwapEnd or pixel capture |

Observed missing runtime services include `com.apple.mobilegestalt.xpc`,
`com.apple.iconservices`, `com.apple.sessionservices`,
`com.apple.commcenter.xpc`, notification, timer, search and other providers.
These are recorded failures, not a proven minimal set of mandatory dependencies.
No empty frameworks or fabricated exported symbols are installed to bypass them.

The initial library blockers are resolved in this QEMU profile. The next
acceptance milestone is to trace original SpringBoard/CoreAnimation output,
identify any concrete first-frame failure and match surface/swap IDs to actual
framebuffer bytes. No Hello/Setup screen, real touch, Metal/Mali acceleration,
physical UFS or native-phone compatibility is claimed here.
