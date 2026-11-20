# SpringBoard dependency audit — 20F66

2026-11-18. QEMU-only. Physical readiness remains **BLOCKED_BY_MEMORY_EVIDENCE**. See [the compatibility matrix](DUCHAMP_IOS_GRAPHICS_COMPATIBILITY.md) and [backboardd requirements](DUCHAMP_BACKBOARDD_DEPENDENCIES.md).

## Exact original executable

```text
host: work/springboard-bundle-v2/apple-extracted/System/Library/CoreServices/SpringBoard.app/SpringBoard
guest: /System/Library/CoreServices/SpringBoard.app/SpringBoard
bytes: 112048
SHA256: 7926a1ba0b115cf45102b2c3d8e4eb7bc9c84bcf70b573d2a798690d9148059c
```

`work/springboard-bundle-v2/receipt.json` records the local original bundle extraction. The executable is small because most implementation resides in its framework dependencies; its presence is not an installed graphical system. The tested copy remains byte-identical and is not re-signed or patched.

Its four strong direct imports are:

1. `/System/Library/PrivateFrameworks/SpringBoard.framework/SpringBoard`
2. `/System/Library/Frameworks/Foundation.framework/Foundation`
3. `/usr/lib/libobjc.A.dylib`
4. `/usr/lib/libSystem.B.dylib`

The last two exist in the standalone Darwin guest. The first two do not; the first loader barrier is **SpringBoard.framework**. Both missing paths appear in the separately held original 20F66 cache inventory. Their downstream dependency closure has not been satisfied merely by finding those cache names.

## Job, session and resources

The original `work/ui-daemon-scan-v1/apple-extracted/System/Library/LaunchDaemons/com.apple.SpringBoard.plist` declares label `com.apple.SpringBoard`, mobile user, app spawn type, embedded-home-screen behavior, KeepAlive, a five-second throttle and additional RunningBoard properties. It also contains `LimitLoadFromHardware` data. The exact original job and its 33 Mach service declarations are copied as metadata into the audit report, not silently normalized into the root test catalog.

Provided names include `PurpleSystemAppPort`, `com.apple.springboard.services`, `com.apple.frontboard.systemappservices`, status-bar, keyboard, notification, bulletin-board and other endpoints. These are job declarations, not proof of registration or a complete outbound dependency specification. Correct user/501 bootstrap context, job-selection policy, application registry, preferences, containers and bundle/resource files still need independent execution evidence.

Earlier Setup/QuartzCore fixtures and their images are preserved. They have different runtime/kernel/controller conditions and do not prove current-kernel compatibility. A historical screenshot or a local SpringBoard bundle does not replace a fresh native process and frame witness.

## Graphics dependencies after the loader barrier

| Layer | Classification | Meaning |
| --- | --- | --- |
| XNU Mach-O, dyld/libSystem, generic Mach IPC | IMPLEMENTED for tested subset | Real C/static applications and native test services execute |
| Intact cache and original SpringBoard/Foundation implementation in this guest | REQUIRES_APPLE_COMPONENT | Current 32 MiB profile does not contain the required runtime |
| CoreGraphics and UIKit/QuartzCore stack | REQUIRES_APPLE_COMPONENT | Original 2D/layer framework execution and resource closure are needed |
| Existing CPU IOSurface/framebuffer shims | PARTIALLY_IMPLEMENTED | Tested pixels and IDs are insufficient to prove all original framework methods |
| BackBoard display/render/input protocols | UNKNOWN | Require actual daemon replies, render submissions and input routing |
| Current two-app catalog / window manager | IMPLEMENTED for original test ABI | Does not replace LaunchServices, FrontBoard, RunningBoard or SpringBoard |
| Touch delivery to SpringBoard through BackBoard | MISSING for the new VirtIO path | Current contacts terminate in the custom shell/WM |
| GPU acceleration on MT6897/Mali | MISSING | No physical or virtual GPU-driver claim; investigate actual software-renderer requirements separately |

Apple documents CoreGraphics as a 2D drawing framework and Core Animation as the layer/compositing infrastructure underlying UIKit. Those public roles do not specify the private service IPC used by SpringBoard. See [CoreGraphics](https://developer.apple.com/documentation/coregraphics) and [Core Animation architecture](https://developer.apple.com/library/archive/documentation/Cocoa/Conceptual/CoreAnimation_guide/Introduction/Introduction.html).

## Trial and success criteria

The direct-exec probe uses the original executable and mobile UID/GID, captures dyld output and records real wait status. It does not bootstrap the original SpringBoard job, fake BackBoard/FrontBoard replies or claim that the custom shell is SpringBoard. An exec error, a dyld missing-library error, a timeout and a running service are distinct outcomes.

The first admission run ended without a probe trace, so that run's state is unknown. The accepted `admission-2` rerun records **PID 10**, exec admitted with no exec errno, then **SIGABRT 6** and no timeout. Its real dyld output is:

```text
dyld[10]: Library not loaded: /System/Library/PrivateFrameworks/SpringBoard.framework/SpringBoard
```

The reason includes no such file and no dyld cache. UUID `40EC75F0-76C1-3DEB-85F1-39369B09E9D5` matches the inspected original executable. See `admission-2/SpringBoard-loader.log`, `verification-normalized.json` and the final manifest. There is no normal exit status for the SIGABRT outcome and no successful SpringBoard initialization. To establish actual SpringBoard startup later, require all of:

- Verified original matching cache/runtime and resource closure on this exact kernel.
- Correct original launchd policy/session and a sustained original process identity.
- BackBoard and required peer services returning real bounded responses.
- A SpringBoard-owned IOSurface associated with the actual SwapEnd and matching observed framebuffer bytes.
- An input event traversing the real event-system path and producing a verified original UI response.

No such complete original-service execution chain is claimed by this audit.
