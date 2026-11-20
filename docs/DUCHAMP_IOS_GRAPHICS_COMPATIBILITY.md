# Authentic iOS graphical userland compatibility audit

2026-11-18. Branch `duchamp-bootstrap`, HEAD `d91562d9c2bd3bc33d52550c101de1009bb41dc0` plus preserved uncommitted changes. Physical boot remains **BLOCKED_BY_MEMORY_EVIDENCE**. No phone, firmware, partition, slot, physical UFS, commit or push operation is part of this audit.

## Finding

The working Darwin shell does not establish backboardd or SpringBoard compatibility. The current 32 MiB root contains standalone restore dyld/libSystem and the project's test services, not a complete iOS graphical runtime. The exact original 20F66 SpringBoard executable needs `SpringBoard.framework` and Foundation, both absent from this guest. The original backboardd has 42 missing strong dependencies; its first direct missing dependency in load-command order is `StudyLog.framework`.

These are measured **guest-file closure** gaps. They do not mean the files are unavailable elsewhere: the local 20F66 cache inventory lists all those paths. A host cache entry does not satisfy a dependency in this guest, and a custom two-window compositor does not implement Apple's rendering or input protocols.

The native rerun confirms both barriers: original backboardd PID 9 and SpringBoard PID 10 were accepted by exec (`exec_errno=0`), then dyld reported the paths above and both terminated with **SIGABRT (6)** before graphical service initialization. The probe itself is a real launchd child, PID 4, and reports 37 loaded images with **no shared cache**. These are unsuccessful authentic-service admission attempts, not working daemons.

The first justified next stage is a separate QEMU fixture containing the intact matching cache and required resources, followed by native dyld admission, user/session-domain checks and bounded daemon health tests. Replacing more private selectors with success stubs would not resolve the verified blocker.

## Evidence and scope

The exact source-linked kernel is:

```text
SHA256 97adb3971c14e1c8f1fd42b18623b183d32edf9d882dc99a2c216b5dc229d001
bytes  19543912
inputs 1127 source-link objects
```

Its build receipt is `../../outputs/duchamp-app-multitouch-20261118/kernel-2/build-manifest.json`. The audit artifacts are under `../../outputs/duchamp-ios-graphics-audit-20261118/`. `kernel-interface-sources.json` verifies that the ten inspected kernel source files match the source hashes recorded for their actual linked objects. This distinguishes linked implementation from a patch or header merely present in the repository.

Original Apple inputs remain local private test files. Their extraction receipts identify the Apple-hosted iPhone10,3/iPhone10,6 iOS 16.5 build 20F66 restore image. This stage does not redistribute Apple binaries, change their bytes or manufacture signing credentials. Hash and signature-load-command presence are not certificate-chain authentication. New tooling is original 0BSD code.

`admission-*/dependency-audit/dependency-report.json` contains every missing path, dependency edge, weak import, source digest, original launchd job and host-cache inventory reference. It distinguishes static metadata from actual execution. Direct-exec admission observations do not prove the original launchd jobs or their Mach services have started.

## Compatibility matrix

The classifications concern the stated interface, not an entire framework. IMPLEMENTED means the named subset is executed by the current regression; PARTIALLY_IMPLEMENTED means important semantics remain absent or unverified. REQUIRES_APPLE_COMPONENT is not a claim that this component cannot exist locally.

| Dependency / interface | Classification | Current evidence and limit |
| --- | --- | --- |
| ARM64 Mach-O exec, fork/spawn, process identity, exit | IMPLEMENTED | Real dynamic/static programs and independent application processes on the exact kernel. Static and dyld-based paths are separate tests. |
| Mach messages, rights transfer, audited senders, dead-name cleanup | IMPLEMENTED | Existing native compositor/WM/application and launchd tests. This establishes general transport, not private service protocols. |
| Original launchd PID 1, System-domain test jobs | IMPLEMENTED | Real launchctl lifecycle, syslogd, notifyd, application restart and cleanup. |
| Full mobile user/501 launchd environment and Apple service policy | PARTIALLY_IMPLEMENTED | Original daemon plists request mobile credentials and additional policy; the root test catalog is not that environment. A direct exec as UID/GID 501 is only admission testing. |
| Restore dyld/libSystem standalone runtime | IMPLEMENTED | Actual C entry, 37-image baseline, filesystem/VM and Mach IPC tests. |
| Intact original shared cache on this exact current profile | PARTIALLY_IMPLEMENTED | Kernel shared-region code is linked. Current root has no complete cache; earlier large-root results used different inputs. A fresh mapping/UUID/slide test remains required. |
| IOKit matching/open/method/map/notification subset | PARTIALLY_IMPLEMENTED | Generated-kernel ABI used by native probes; legacy string matching returns unsupported while binary/XML matching is implemented. Not every IOKit framework call is covered. |
| IOSurface kernel CPU allocation, ID/port lookup and mapping | PARTIALLY_IMPLEMENTED | Existing compositor exercises the project subset. Use-count traps, several value/notification/accelerator/shared-event paths are no-ops. Public framework compatibility is broader. |
| Original IOSurface.framework in the current 32 MiB guest | REQUIRES_APPLE_COMPONENT | Absent from the tested graphical-admission guest. A prior 80-file standalone closure totals 100,274,720 bytes before broader UI resources. |
| IOMobileFramebuffer project CPU scanout | PARTIALLY_IMPLEMENTED | Actual surface/swap IDs, pixel comparisons and geometry work. Unknown selectors return success in the existing shim; GPU synchronization and full display semantics are not thereby implemented. |
| GraphicsServices | REQUIRES_APPLE_COMPONENT | Original cache entry exists on the host; absent from the current guest. No new private API is invented. |
| CoreGraphics | REQUIRES_APPLE_COMPONENT | Original 2D rendering framework is a missing required dependency. Test primitives are not a substitute. |
| CoreAnimation / QuartzCore | REQUIRES_APPLE_COMPONENT | QuartzCore is absent from this guest. The native compositor speaks its own protocol, not CARenderServer. |
| UIKitCore / SpringBoard.framework | REQUIRES_APPLE_COMPONENT | Cache inventory contains them; current guest does not. SpringBoard executable availability alone is insufficient. |
| Virtual keyboard HID shared queue | IMPLEMENTED | Existing graphics test consumes actual queued Menu press/release and Mach notifications. Scope is that tested provider. |
| VirtIO multitouch to custom Darwin shell | IMPLEMENTED | Two simultaneous contacts, capture, cancellation, geometry and restart tests through the actual virtual device. |
| VirtIO multitouch to BackBoard's HID event-system path | MISSING | The current DT/GW Mach path terminates at the custom shell/WM. No adapter to the original BackBoard protocol has been implemented or executed. |
| Full Apple HID service/filter/digitizer semantics | UNKNOWN | A provider match or two custom contacts does not prove them. Public IOHID source is a reference, not proof of the closed daemon's exact demands. |
| IOGPU/IOAccelerator/Mali hardware rendering | MISSING | Current output is CPU rendering. Absence of acceleration does not itself prove that every software-rendering startup path is impossible. |
| CARenderServer / BackBoard display and event service protocols | UNKNOWN | Names are declared by the original backboardd plist. Wire/semantic compatibility has not been established in the current fixture. |
| SpringBoard application registry, container/preference/policy resources | UNKNOWN | Earlier larger fixtures are not a current complete registry or user-session proof. Test catalog IDs are unrelated. |

## Source audit

The linked XNU source root is `/var/tmp/duchamp-clang.zZKCR0J4/kernel-workspace/dxb/xnu/`. Exact files and useful locations:

| Source | Relevant implementation |
| --- | --- |
| `bsd/kern/mach_loader.c:442`, `:760`, `:3012` | `load_machfile`, `parse_machfile`, `load_dylinker`: segment/address-space setup and dyld entry |
| `bsd/kern/kern_exec.c:1161`, `:6878` | Mach exec and loading PID 1 |
| `bsd/vm/vm_unix.c:2086`, `:2882`; `osfmk/vm/vm_shared_region.c` | Shared-region check and map/slide implementation |
| `iokit/Kernel/IOUserClient.cpp:2798`, `:2836` | Unsupported legacy matching entry versus implemented binary/XML matching |
| `iokit/Kernel/arm/SweetPlatformExpert.cpp` | Built-in platform/provider registration |
| `iokit/Kernel/arm/SweetSurface.cpp:567`, `:732`, `:776`, `:789` | Result ABI, implemented selectors, success/no-op fallback and no-op use-count trap |
| `iokit/Kernel/arm/SweetFramebuffer.cpp` | CPU presentation, existing notification timer and limited selector switch |
| `iokit/Kernel/arm/hid/SweetHID.cpp:382`, `:443`, `:466` | Button/touch providers and digitizer-event construction |
| `iokit/Kernel/arm/hid/IOHIDEventServiceUserClient.cpp` | Existing user-client open, queue/map and notification handling |

The userspace paths are `tools/duchamp-darwin-iokit.h`, `duchamp-iokit-wire.h`, `duchamp-darwin-compositor.c`, `duchamp-darwin-gui.c`, `duchamp-window-core.[ch]`, `duchamp-app-service.inc`, `duchamp-darwin-touch.c` and `duchamp-touch-wire.h`. Their custom DC/GW/DT/AP interfaces are original test interfaces and must not be presented as Apple private API implementations.

Public references: [XNU Mach-O loader](https://github.com/apple-oss-distributions/xnu/blob/xnu-8796.121.2/bsd/kern/mach_loader.c), [Mach-O format](https://github.com/apple-oss-distributions/xnu/blob/xnu-8796.121.2/EXTERNAL_HEADERS/mach-o/loader.h), [IOUserClient](https://github.com/apple-oss-distributions/xnu/blob/xnu-8796.121.2/iokit/Kernel/IOUserClient.cpp), [IOHIDFamily](https://github.com/apple-oss-distributions/IOHIDFamily), [IOSurface Mach-port sharing](https://developer.apple.com/documentation/iosurface/iosurfacecreatemachport(_:)), [CoreGraphics](https://developer.apple.com/documentation/coregraphics), [Core Animation architecture](https://developer.apple.com/library/archive/documentation/Cocoa/Conceptual/CoreAnimation_guide/Introduction/Introduction.html), [launchd job semantics](https://github.com/apple-oss-distributions/launchd/blob/main/man/launchd.plist.5). These references describe public formats/general facilities; the closed services' complete private protocol requirements are not publicly specified by them.

## Safe implementation in this stage

- `tools/duchamp_macho_preflight.py` adds bounded load-command, string, segment and fixup-metadata inspection before reusing the existing Mach-O auditor. It rejects malformed/truncated images, overflow, arm64e passed as plain ARM64, unknown required dyld commands and cache-only dylibs passed off as standalone files. It preserves strong/weak distinctions. Runpath resolution, including inheritance, is deliberately unsupported and unresolved strong rpaths stay unknown. Structural closure never implies execution or signature authentication.
- `tools/audit-duchamp-ios-graphics.py` inspects an actual copied guest HFS image through the existing read-only extraction interface. It records failed extractions, exact dependencies and original job declarations. A host cache listing cannot satisfy an absent guest file.
- `tools/duchamp-ios-graphics-admission.c` is an original native probe: it observes actual cache/provider/query results and makes one bounded direct-exec attempt per unchanged Apple executable with UID/GID 501. It records exec acceptance/errors, PID, wait status, signal, timeout and loader output. It supplies no fake Apple service replies.
- `tools/test-duchamp-ios-graphics-admission.py` packages a separate 32+4 MiB RAM fixture, verifies every original binary readback, uses the exact source-built kernel and preserves root immutability. It records unknown startup rather than declaring failure/success when no observation exists.
- `tools/test-duchamp-macho-preflight.py` covers malformed images and closure semantics. The existing service validator now accepts additional **contiguous healthy** heartbeats if console sampling misses the intended stop; it still requires the original first two and rejects gaps, replay, wrong process and unhealthy samples. `tools/test-syslogd-heartbeat-validation.py` tests those cases. No production compositor/WM/input/kernel interface was replaced.
- `tools/test-duchamp-ios-admission-status.py` checks terminal wait-status decoding. A raw log's `exit=0` is the high-byte bit field, **not** a normal exit when `signal=6`. `verification-normalized.json` preserves the raw bits and reports `exit_status=null` for these SIGABRT outcomes. The original raw report is retained.

## Execution and regression evidence

The final audit manifest records exact commands, exit codes, log digests, source/kernel identities, native observations and accepted test runs. Initial incomplete or failed attempts remain separate. The first admission attempt exhausted 180 host seconds without producing a native probe trace; its results are **unknown**, not an Apple-service startup result. The 360-second-budget rerun produced the actual probe and dyld records.

| Fresh suite | Result | Receipt under the audit output directory |
| --- | --- | --- |
| Native API/exec admission diagnostic | 15/15; **both Apple services loader-blocked** | `admission-2/verification-normalized.json` |
| Bounded Mach-O preflight | 21/21 | `final-targeted-0.log` |
| Heartbeat validation | 9/9 | `final-targeted-1.log` |
| Terminal wait-status validation | 7/7 | `final-targeted-2.log` |
| Application lifecycle and actual multitouch | 35/35; twelve full frame comparisons | `regression-applications-2/verification.json` |
| Real virtual-device input | 14/14 in that application run | `regression-applications-2/host-input/verification.json` |
| Normal browser application/touch session | 18/18 | `browser-regression/verification.json` |
| Browser native lifecycle/log postflight | 15/15 | `browser-regression/native-postflight/verification.json` |
| GUI / mouse | 22/22 / 18/18 | `regression-gui/verification.json`, `regression-mouse/verification.json` |
| Compositor / graphics | 25/25 / 10/10 | `regression-compositor/verification.json`, `execution/verification.json` |
| Filesystem / original Darwin services | 11/11 / 74/74 | nested accepted regression guest reports |
| Real dynamic / static Mach-O | 17/17; dynamic exit 0, static exit 42 | `regression-macho-2/run/verification.json` |

These suites overlap and must not be summed as independent tests. All use the exact kernel above. They preserve read-only md0, writable md1, launchd PID 1, real guest processes and UFS-disabled profiles. Diagnostic success means the observations and safeguards passed; it does **not** mean Apple graphical services started.

The initial application regression failed only the old exact-two-heartbeat criterion despite eighteen healthy saved samples. Its failed report remains intact; the fresh corrected-validator run passed. An initial Mach-O orchestration command placed the output path in the wrong argument and stopped at an existing-directory check; the corrected new-output run passed. Neither failed attempt is relabelled as success.

Reproduce the separate admission fixture:

```sh
python3 -B tools/test-duchamp-ios-graphics-admission.py ../../outputs/duchamp-ios-graphics-audit-repeat \
  --kernel-manifest ../../outputs/duchamp-app-multitouch-20261118/kernel-2/build-manifest.json \
  --mkfs ../../outputs/duchamp-readonly-var-20261116/formatter/unpacked/usr/sbin/mkfs.hfsplus
```

Use a new output directory. This command copies the existing local runtime, stages the two byte-pinned original executables and boots QEMU; it has no phone transport. Host-only dependency reinspection uses `tools/audit-duchamp-ios-graphics.py NEW_OUTPUT --guest-image EXISTING_COPIED_ROOT` and never executes an Apple binary.

## Recommended next implementation

1. Build a separate QEMU-only large runtime fixture from the already held, matching intact cache, preserving the frozen native candidate. Verify component hashes, UUID, mapping/slide and original dyld execution on this exact kernel.
2. Stage original job/resource files with explicit System versus user/501 domains and writable runtime paths. Track each actual service endpoint and bounded health response; bootstrap lookup alone is insufficient.
3. Trace real IOSurface, display notifications, QuartzCore render submission and HID input. Implement only an observed, bounded missing operation, with negative cases and pixel/input witnesses.
4. Require actual backboardd health and SpringBoard frame provenance before making a compatibility claim. No simulated service name or custom window is accepted as proof.

The native memory-ownership, DMA/cache, panel, physical touch and Mali requirements remain independent. This audit establishes no new physical-device readiness.
