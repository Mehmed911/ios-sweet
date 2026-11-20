# backboardd dependency audit — 20F66

2026-11-18. QEMU-only; physical status remains **BLOCKED_BY_MEMORY_EVIDENCE**. Main matrix and source references: [iOS graphics compatibility](DUCHAMP_IOS_GRAPHICS_COMPATIBILITY.md).

## Exact original input

```text
host: work/ui-daemon-scan-v1/apple-extracted/usr/libexec/backboardd
guest: /usr/libexec/backboardd
bytes: 1182960
SHA256: 686f26a6a7b749fd0ae30acca704022da8cb6f85b5c39a0e0e09e25ffd00d273
```

The locally held extraction receipt is `work/ui-daemon-scan-v1/extraction-receipt.json`. It identifies the 20F66 Apple restore input and source image digest. No executable bytes, imports, signature or entitlements are patched in this trial. File presence and signature metadata do not authenticate a signing chain.

## First barrier in the current guest

The current 32 MiB guest is a standalone Darwin runtime. Static inspection finds **42 missing strong dependencies**, with no malformed present dependency in the inspected closure. The first direct missing path in load-command order is:

```text
/System/Library/PrivateFrameworks/StudyLog.framework/StudyLog
```

The original cache inventory contains this path, but the cache is not installed/mapped by the current RAM-root profile. The full missing set, importers, weak imports and hashes are in the accepted admission run's `dependency-audit/dependency-report.json`; this is a guest-specific result, not a claim of global unavailability.

Key required groups include BackBoardServices, BackBoardHIDEventFoundation, BackBoardHIDEventProcessors, BoardServices, BaseBoard, GraphicsServices, IOMobileFramebuffer, IOSurface, QuartzCore, CoreGraphics, Foundation/CoreFoundation, IOKit, RunningBoardServices, CoreBrightness, WatchdogClient, CoreText/ImageIO and other directly declared libraries. The machine-readable report lists every path; guessing an implementation from a framework name is explicitly excluded.

## Original launchd contract

`work/ui-daemon-scan-v1/apple-extracted/System/Library/LaunchDaemons/com.apple.backboardd.plist` declares:

- Label `com.apple.backboardd`, executable `/usr/libexec/backboardd`, user `mobile`.
- `RunAtLoad=true`, `KeepAlive=true`, interactive spawn type and high-priority I/O.
- Eighteen Mach service declarations, including `PurpleSystemEventPort`, `PurpleWorkspacePort`, `com.apple.iohideventsystem`, `com.apple.CARenderServer`, `com.apple.backboard.display.services`, `com.apple.backboard.hid.services` and watchdog/accessibility services.

Those are **declared provided endpoints**, not a discovered complete list of outbound dependencies, and not proof that this guest registered them. The direct-exec probe does not load the original KeepAlive job or create dummy endpoints; therefore it cannot accidentally hide a crash loop behind a service lookup.

## Kernel and protocol requirements

| Area | Status on current baseline | Remaining validation |
| --- | --- | --- |
| Mach execution and generic IPC | IMPLEMENTED | Map the exact daemon protocol only after loader admission |
| IOSurface CPU user client | PARTIALLY_IMPLEMENTED | Original framework calls, locking/use counts, notifications, values and ownership semantics; unknown selectors currently have no-op success paths |
| Display | PARTIALLY_IMPLEMENTED | CPU copy and selected queries are tested; original render-server use, notifications, waits/fences and power transitions need execution evidence |
| Input | PARTIALLY_IMPLEMENTED | Existing HID keyboard queue is tested; current multitouch feeds the custom shell, not BackBoard's event system |
| VirtIO-to-BackBoard adapter | MISSING | No bridge from current DT/GW packets to a verified BackBoard digitizer path |
| GraphicsServices / QuartzCore / CoreGraphics / BackBoard frameworks | REQUIRES_APPLE_COMPONENT | Matching cache/runtime and resource closure, followed by original library execution |
| User/session, preferences, power/watchdog and private service interactions | UNKNOWN | Preserve the actual mobile job/domain, observe calls and bounded real replies; do not fabricate private APIs |

`SweetHIDTouch::touch()` exists in linked `iokit/Kernel/arm/hid/SweetHID.cpp`, but the new QEMU cdev input does not call it. Matching `SweetHIDTouch` alone is not proof of digitizer delivery to backboardd. The public [IOHID implementation](https://github.com/apple-oss-distributions/IOHIDFamily) is a reference for facilities, not a complete specification of the closed daemon's requirements.

## Native trial and acceptance

The native probe is a real launchd child and makes one bounded original-executable attempt after setting UID/GID 501. It records a close-on-exec status pipe, PID, wait status and stderr. A loader rejection is a measured blocker, not a successful backboardd start. No output is counted as readiness merely because it contains a process or service name.

The initial 180-second run produced no native admission trace before its budget ended; startup state remains unknown for that run. The accepted `admission-2` rerun records **PID 9**, successful exec admission and **SIGABRT 6**, with no timeout. The original dyld message is:

```text
dyld[9]: Library not loaded: /System/Library/PrivateFrameworks/StudyLog.framework/StudyLog
```

Its reason includes no such file and no dyld cache. The executable UUID `E81FD7FD-034F-3195-A4F5-3C692536E5AA` in that message matches the inspected original file. The native capability probe confirms cache absence, the five existing display/surface/test-HID providers, surface-limit ABI version 1 and display query 1220×2712. It does not find the queried IOHIDSystem or IOAccelerator providers; that observation alone does not specify backboardd's required kernel-provider contract.

`admission-2/backboardd-loader.log` and `verification-normalized.json` retain these observations. A signalled process has no normal exit status; zero high-byte exit bits in the raw wait record are not exit success. The 15/15 diagnostic result means the admission observations were captured correctly, **not** that backboardd is working. Full original-job bootstrap, sustained daemon health, an actual display response and actual HID input remain acceptance requirements after the loader barrier is resolved.

Historical `work/platform-services-qemu-v6/evidence/verification.json` contains earlier backboardd identity observations with a larger runtime and a different kernel. Its UI section has two identity checks; it is not a fresh complete health/protocol test on the current kernel and is not substituted for this audit.
