# Duchamp Darwin graphics and input bringup

2026-11-17. Scope: the preserved source-built XNU in isolated QEMU. The native 32+4 MiB boot candidate is frozen. Physical UFS and phone operations remain disabled.

## Audit of the implementation actually linked

The kernel is SHA-256 `e7b51ecb16fe9ad21a78455714b2bf26c1dee1fbc3a6a7f0cb3971a9cd569457`. The original 1126-entry compile manifest is `../../outputs/duchamp-patched-clang-20261117/source-build-compile-commands.json`. `../../outputs/duchamp-darwin-next-stage-20261117/graphics-source-inputs.json` records exact compiled source paths, object paths and source digests. No archived kernel was substituted and no kernel bytes were patched.

The actual staged XNU root is `/var/tmp/duchamp-clang.zZKCR0J4/kernel-workspace/dxb/xnu/`. The following paths are relative to that root:

| Component | Source and behavior | Limit |
| --- | --- | --- |
| Platform matching | `iokit/Kernel/arm/SweetPlatformExpert.cpp`, `SweetPlatformExpert::start()` and `processTopLevel()`; existing device-tree platform expert | Registration alone is not proof of every user client or matching request. |
| Surface allocation | `iokit/Kernel/arm/SweetSurface.cpp`; `IOCoreSurfaceRoot` publishes `IOSurfaceRootUserClient`, which allocates/maps CPU-accessible BGRA storage and returns its surface ID and task mapping | Match the actual provider class, not the user-client name. This is the project's surface shim, not evidence of full proprietary IOSurface compatibility. |
| Framebuffer | `iokit/Kernel/arm/SweetFramebuffer.cpp`, `AppleCLCD::start()` lines 153–207 and `IOMobileFramebufferUserClient::externalMethod()`; selector 4 SwapBegin and 5 SwapEnd | CPU copy to the RAM framebuffer. Several other selectors are success/no-op shims. No Mali GPU or Metal submission is tested. |
| Input providers | `iokit/Kernel/arm/hid/SweetHID.cpp`, `SweetHIDButtons::start()` and `SweetHIDTouch::start()` | Virtual providers already exist. A matched touch service is not evidence that real touch packets or BackBoard input work. |
| HID userspace queue | `iokit/Kernel/arm/hid/IOHIDEventServiceUserClient.cpp`; shared queue mapping, open/close, notification port | Test keyboard events through the real queue and Mach notification path before digitizer/contact testing. |
| Matching RPC | `iokit/Kernel/IOUserClient.cpp`, `is_io_service_get_matching_service()` and `_bin()` | Legacy string entry explicitly returns `kIOReturnUnsupported`; the binary/inband entry accepts serialized XML through `OSUnserializeXML`. |
| Mach transport | `osfmk/mach/message.h` lines 1326–1373, `libsyscall/mach/mach_msg.c`, `osfmk/ipc/ipc_kmsg.c::ipc_kmsg_option_check()` | Kernel-object RPC must use `MACH64_SEND_KOBJECT_CALL`. Ordinary `mach_msg` in this runtime selects message-queue semantics and is rejected. No kernel check was relaxed. |

Wire IDs and the generated server hash are preserved in `iokit-abi-source.json`. The exercised IDs are 2880 (matching-service-bin), 2862 (open extended), 2863 (map), 2865 (method), and 2818 (notification port). These describe this kernel's generated ABI, not a generic cross-version contract.

## Initial virtual environment

Reuse the compiled providers rather than create a second framebuffer or input driver. The new 0BSD `tools/duchamp-darwin-graphics.c` is a real dynamic ARM64 Mach-O, linked to the existing libSystem runtime, loaded by the original launchd as a separate root/System service. It does not require adding private UI frameworks to the 32 MiB root.

1. Obtain the IOKit main port; match AppleCLCD, IOCoreSurfaceRoot and the two HID providers. A deliberately absent class must not match.
2. Open framebuffer, surface and button user clients. Read actual framebuffer geometry and map the shared input queue into the process.
3. Enable the existing `sweethidtest=5` virtual Menu-button source only in an explicitly selected QEMU profile. Consume press/release records and a real Mach notification; validate queue bounds, sender, usage, timestamps and ordering.
4. Allocate a 64x32 BGRA surface, fill a deterministic pattern in the mapped userspace buffer, and submit its actual ID through SwapBegin/SwapEnd at `(160,1600)`.
5. Save the process/surface/swap witness on writable md1. Independently sample QEMU framebuffer RAM, crop that rectangle, and compare every pixel byte with the expected pattern. The host observer never writes guest framebuffer memory.

`tools/qemu_frame_witness.py` validates bounded crop requests and captures the first matching RAM sample. The rectangle excludes stride padding. `tools/qemu-sweet.py` saves both the raw crop and a PNG, with the sample number and elapsed host time. A host-generated reference pattern alone is not accepted as a guest frame.

The test controller bootstraps `/sbin/duchamp-graphics.plist` using actual launchctl. Existing system job files stay unchanged. The service verifier's explicit `--graphics` mode requires the additional bootstrap command and its zero status as well as the original 74 checks; its default profile is unchanged.

The existing HID user client requires `com.apple.hid.system.user-access-service`. The test supplies only that entitlement in its own ad-hoc-signed QEMU program, verifies it with the pinned offline signer, and leaves the kernel entitlement check unchanged. The preceding unentitled program was actually rejected (`0xe00002c2`); the entitled program received the two events. This is not firmware authorization or a signature from Apple/Xiaomi.

## Dependencies for larger graphical userspace

| Area | Established baseline / next validation |
| --- | --- |
| Dynamic execution and IPC | Real dyld/libSystem execution and Mach send/receive are covered by the separate 17-check regression. Continue using real client/server processes and captured replies. |
| launchd lifecycle | Original PID 1, xpcproxy, syslogd, notifyd and service shutdown remain checked. The graphics service has no KeepAlive loop hiding failures. |
| Filesystems | Read-only md0 and writable 4 MiB md1 at `/private/var`, `/var` alias and devfs console remain required. No UFS-backed root is introduced. |
| Interactive input | Next exercise digitizer/contact coordinates and cancellation, then drive an open-source interactive rendering program from virtual input. The initial Menu-button test does not establish mouse-to-touch or BackBoard delivery. |
| Display services | Audit the exact user-client selectors, notifications, surface sharing and lifecycle each proposed compositor needs. No new BackBoard/QuartzCore/SpringBoard component is executed by this probe. |
| UI framework closure | Establish a permitted, matching runtime and dependencies, execute the real required components, and trace actual submitted surface IDs before making UI compatibility claims. This phase does not establish SpringBoard support. |
| Physical portability | MT6897 input, panel, cache, memory ownership and recovery must have their own hardware evidence. QEMU CPU copies and synthetic buttons do not establish these. |

The next independent milestone is a small open-source Darwin UI loop that changes a presented frame in response to a virtual input event, including resize/close and user-client cleanup. Physical work remains blocked by the separate firmware/memory evidence decision.

Commands, actual results and failure history are in `DUCHAMP_DARWIN_NEXT_STAGE.md` and its linked artifact manifest.
