# Darwin GUI shell and window manager

2026-11-18. Branch `duchamp-bootstrap`, HEAD `d91562d9c2bd3bc33d52550c101de1009bb41dc0` plus preserved, uncommitted changes. Accepted execution: `../../outputs/duchamp-darwin-gui-20261118/attempt-4/`. **Physical readiness remains BLOCKED_BY_MEMORY_EVIDENCE.** No phone transport, flash, reboot, slot change, physical UFS, firmware modification, commit or push was used.

## Result and scope

A new, original 0BSD Darwin experiment runs as real dynamic ARM64 Mach-O processes under the existing launchd PID 1. It displays a desktop/status strip, two launcher buttons, two decorated application windows and pointer feedback in a bounded **160×96** canvas. Actual QEMU execution verified window creation, focus and Z-order, captured input, movement, resizing, client termination cleanup, and window-manager restart/reconnection. All **seven complete framebuffer crops** matched an independent Python oracle byte-for-byte.

This is a small software-rendered test shell. It neither implements SpringBoard nor proves compatibility with Apple's private graphics services or MT6897/Mali. Pointer coordinates in this test come from the explicit shell self-test over audited Mach IPC, **not a QEMU USB mouse, BackBoard, IOHID digitizer or physical touch device**. The separate existing IOHID Menu-button press/release regression still passes. Ordinary shell mode shows the desktop; host mouse/touch integration and an interactive launcher event loop remain a next milestone. There are no animations, fonts, arbitrary applications, production sandbox, or atomic multi-window display transactions.

## Audit and process boundaries

The existing working implementation was inspected before modification:

- `tools/duchamp-darwin-compositor.c`: launchd check-in, audited Mach receives, surface capability import, private snapshots, input capture, kernel dead-name notifications, and normal/self-test lifecycle.
- `tools/duchamp-compositor-core.c` and `.h`: ownership `(PID, PID version)`, fixed-size layer storage, Z-order/alpha blending, damage union, CPU front/back frames, focus and cleanup.
- `tools/duchamp-compositor-wire.h`: actual kernel-appended audit trailer parsing, 48-byte request bodies, 100-byte capability registrations and 48-byte replies.
- `tools/duchamp-compositor-iokit.h` and `duchamp-darwin-iokit.h`: existing IOCoreSurfaceRoot and AppleCLCD wire calls. Create/import use kernel-supplied mapping/geometry metadata; presentation uses SwapBegin/SwapEnd and the kernel's CPU copy to framebuffer RAM.
- Actual compiled XNU source under `/var/tmp/duchamp-clang.zZKCR0J4/kernel-workspace/dxb/xnu/`: `iokit/Kernel/arm/SweetSurface.cpp`, `SweetFramebuffer.cpp`, `arm/hid/SweetHID.cpp`, and `IOHIDEventServiceUserClient.cpp`. No new private Apple class was invented or kernel source patched in this stage.

```text
original launchd PID 1
  GUI compositor: org.duchamp.qemu.gui-compositor
       ^ existing DC registration/dirty/Z wire + bounded VIEW extension
  window manager: org.duchamp.qemu.window-manager
       ^ audited custom GW Mach requests, copied client pixels
  shell / red app / blue app: independent processes

WM-owned IOSurface capabilities -> compositor private snapshots
 -> compositor front/back CPU frames -> AppleCLCD -> QEMU framebuffer RAM
```

Each executable path is a copy of the same 87,152-byte multi-entry Mach-O, with distinct launchd program arguments. This is still separate address spaces/processes, not in-process simulated clients. The GUI jobs and plists are installed only in a copied read-only test root under `/sbin`; the five baseline `/System/Library/LaunchDaemons` jobs and original service executables remain pinned and unchanged. Apps have RunAtLoad false and are actually started by the shell through the existing pinned launchctl. WM has KeepAlive true; its restart is explicitly tested with launchctl kickstart.

Observed accepted identities: compositor **PID 18**, WM **20**, shell **24**, red app **26**, blue app **28**, restarted WM **31**. Every GUI process independently required PPID 1, root UID and `/sbin/launchd` as its parent. These are run observations, not protocol constants. The shell loaded **37 dyld images**.

## Source changes

| File | Implementation |
| --- | --- |
| `tools/duchamp-window-core.h`, `.c` | Three bounded window records including desktop, owner validation, create/destroy, focus/Z, geometry, title-bar drag, resize grip, input hit testing/capture and original primitive decorations/cursor. |
| `tools/duchamp-gui-wire.h` | Versioned GW request/result layout, exact message sizes, bounded inline pixel submissions and one endpoint capability on creation. |
| `tools/duchamp-darwin-gui.c` | Separate compositor, WM, shell and app modes; actual Mach/IOKit calls, private pixel copies, dead-name cleanup, ordered input messages, launcher test, crash/reconnect test. |
| `tools/duchamp-compositor-core.h`, `.c` | Optional compile-time canvas dimensions, distinct backing capacity and visible viewport, bounded atomic single-layer move/resize, owner-checked single-layer removal. Default 64×32 behavior remains. |
| `tools/duchamp-compositor-wire.h` | Adds DC_VIEW without renumbering existing operations. |
| `tools/duchamp-gui-control.h` | Test-only launchctl bootstrap, completion/lifecycle checks and bootout. |
| `tools/test-duchamp-window-core.c` | 53 native ASan/UBSan assertions for window/core/wire bounds, owner/PID reuse, capture, geometry, cleanup and private viewport rendering. |
| `tools/duchamp_gui_expectations.py` | Independent host pixel reference for all seven GUI states. No writes to guest display RAM. |
| `tools/test-duchamp-darwin-gui.py` | Isolated compilation/linking, copied-root QEMU execution, log extraction, lifecycle and full-crop comparisons; optional saved-run verification. |
| `tools/test-duchamp-readonly-var.py` | Opt-in GUI binaries/plists and ordered framebuffer observations; default baseline retained. |
| `tools/sweet-launchctl-control.c`, `sweet-syslogd-control.h` | Compile-time opt-in GUI lifecycle after the existing service tests. |
| `tools/verify-sweet-syslogd.py` | Explicit --gui command sequence; still checks all 74 baseline assertions and exact expected CLI commands. |
| `tools/duchamp-darwin-compositor.c` | Self-test only: hold restored scene eight seconds before accepting HID input, so the ordered observer can capture it before cleanup. Ordinary daemon behavior is unchanged. |

## Window, surface and IPC ownership

There are two distinct ownership boundaries. GW windows belong to the client authenticated by XNU's audit trailer PID and PID version. At the lower compositor interface, all four backing surface capabilities belong to the WM. Apps receive neither compositor-owned frame pointers nor the WM's IOKit mapping/capabilities.

- Window ID 1 is the full desktop; only the audited `/sbin/duchamp-gui-shell` process can claim it or submit virtual pointer input. IDs 2/3 are application windows. These are fixed test slots, not an unbounded global allocation service.
- Client create/paint submits exactly **61,440 inline pixel bytes**. The WM copies them into its own bounded backing array. No user-supplied memory address is dereferenced. Malformed sizes, descriptor layouts and versions are rejected.
- Each backing allocation is 160×96 BGRA, with a 640-byte stride. The kernel rounds the mapping to **65,536 bytes**, within the existing metadata cap. Visible window rectangles may be smaller; resize cannot grow beyond backing capacity or canvas bounds. Overflow-safe subtraction/division checks precede reads/copies.
- WM-controlled borders/titlebars and the resize grip are composed over copied client content. Raising/focusing a window changes only that window's owned compositor handle; foreign client geometry/focus/paint cannot change it.
- DC_VIEW changes one validated destination viewport while preserving full backing stride. Old and new visible bounds are damaged. Snapshots remain private, and pixels outside the visible viewport cannot enlarge the destination copy.
- Front/back CPU frames and output surfaces remain owned by the compositor. Presentation is periodically refreshed to preserve the canvas against the diagnostic console's own drawing. This is CPU copying into RAM, not physical scanout synchronization or GPU acceleration.
- GW_POINTER hit tests highest Z. A title-bar press captures a move; the lower-right grip captures resize; content press captures input. Moving outside the window or changing focus does not reassign the release.
- GW_EVENT messages carry sequence, coordinates and down/up state through the client's retained endpoint. The app validates the actual audit sender, expected WM PID/path, window ID, bounds-related wire fields and monotonic sequence. The accepted red client received **eight ordered messages**, including separate down/up and drag/resize motion messages, rather than only observing a counter after both events.
- Client process exit destroys its receive endpoint. A genuine PID-0 Mach dead-name notification removes its window, closes its WM IOKit connection and retires the WM-to-compositor endpoint. The compositor independently receives its dead-name notification, drops that snapshot and closes its mapping.
- Explicit owner-checked GW_DESTROY and its notification cancellation path are present. Core destruction is covered natively; the end-to-end QEMU cleanup scenario exercised **actual process termination**, not that explicit RPC. It is not claimed as a separately exercised RPC.
- The WM is deliberately killed/restarted. Its old surface endpoints die, the compositor reclaims their mappings while surviving, then the persistent shell/red app reconnect to the new WM. The new layout and framebuffer bytes are independently verified.

These root-owned test jobs are not a production multi-user security boundary. Immutable dimensions/copies protect buffer bounds, but this is not a complete security audit, arbitrary-client stress test, transactional frame protocol or resource-exhaustion defense.

## Actual validation

All accepted commands exited **0**. Complete arguments, exit codes and log SHA-256 values are saved outside Git in the named output directories.

| Test | Result | Evidence below `../../outputs/duchamp-darwin-gui-20261118/` |
| --- | --- | --- |
| GUI on exact source-built XNU | **22/22** | `attempt-4/verification.json`, `commands.json` |
| Seven full 160×96 framebuffer crops | **7/7 byte-identical** | `attempt-4/guest/run/sequence-*.raw`, `.png`, `frame-sequence.json` |
| Window/core/wire ASan/UBSan | **53 assertions** | `attempt-4/command-000.log`, `command-001.log` |
| Original compositor ASan/UBSan | **48 assertions** | `legacy-regression-2/execution/commands.json` and native logs |
| Existing compositor, alpha, dirty rectangles, capture, normal-mode cleanup | **25/25** | `legacy-regression-2/verification.json` |
| Existing real IOKit framebuffer / HID probe | **10/10** | `legacy-regression-2/execution/verification.json` |
| Read-only md0, writable md1/var, console, EROFS/ENOSPC | **11/11** | `attempt-4/guest/verification.json` |
| Original launchd/syslogd/notifyd | **74/74** | `attempt-4/guest/service-verification.json` |
| Separate dynamic/static Mach-O, dyld, filesystem, VM, Mach IPC | **17/17** | `macho-regression/run/verification.json`, `regression-0.json` |
| Memory placement / lifetimes | **16/16 + 19/19** | `regression-1.log`, `regression-2.log` |
| Framebuffer observer | **12/12** | `regression-4.log` |
| Default dual-RAMDisk packaging | **12/12** | `packaging-0.log`, `packaging-commands.json` |
| Accepted GUI payload HID/storage-denial profile | **7/7** | `packaging-1.log` |
| Preserved local native candidate, bootshim, FDT and baseline files | **25/25 hashes unchanged** | `frozen-inputs.json`; not fresh hardware/recovery evidence |
| Recompile/relink final GUI sources independently | **bit-identical binary** | `reproducible-rebuild/commands.json`, `build-manifest.json` |

Real shell trace:

```text
PASS focus_and_release id=2 events=2
PASS move rect=26,22,70,44
PASS resize rect=26,22,80,50
PASS ownership_replay_bounds
PASS process_cleanup id=3
PASS service_restart old=20 new=31 desktop_reconnected=1
PASS GUI_COMPLETE manager=31 dyld_images=37
```

Framebuffer observations are 61,440 bytes each, cropped from actual QEMU RAM at `(320,1664,160,96)` while the VM is sampled. Sample times follow completed presentation; they are not invented atomic hardware timestamps.

| Captured state | Pixel SHA-256 |
| --- | --- |
| desktop | `82baedf8d2650a3b2c618dd2b0a2ff8e12b7111e02603ba8807add5b7537cd76` |
| two windows | `09cb50ff5690957c79cd58af18e1505f6dce485dbaccaa92c2a4da9a722bd5e5` |
| focused red | `97e1d9e03b735877b824d6b86fc3d4f8b005059500b4a94af71a6d8b78dd8320` |
| moved red | `7822ed5012135ff1e6910d9dac0d5ac9e8bbd7b024bcc87dfcae15fcde860b7d` |
| resized red | `2bf8ac22f35c847e2d30e39e03376e4699ee9ed39166bf2d57580028c86a434f` |
| blue cleaned up | `d32cacdf5731fe719a4a18339736bcb435d44147622a74b3247e9b2e2af706f1` |
| WM restarted | `bd36a563f72749a659416fc5228132ac6bfba0a8c791977b245f6e4ec78c48ca` |

The accepted guest reported no panic. md0 remained byte-identical after execution; writes returned EROFS 30, raw root open was rejected, and md1 exhaustion returned ENOSPC 28 with recovery. The payload denies legacy/QEMU UFS nodes; no physical UFS operation occurred. The separate Mach-O regression ran dynamic PID 2/exit 0 and static PID 3/exit 42; its diagnostic PID 1 is a separate test from the original launchd service boot.

## Build, hashes and reproduction

The existing source-built kernel is unchanged: **19,541,944 bytes**, SHA-256 `e7b51ecb16fe9ad21a78455714b2bf26c1dee1fbc3a6a7f0cb3971a9cd569457`. No archived CI kernel or binary patch was substituted. Userspace compiler/linker: Clang/LLD **21.1.8**; QEMU **10.2.1**. Full tool versions, source digests, input/output sizes and commands are in `build-manifest.json`.

Accepted outputs:

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| GUI Mach-O | 87,152 | `e0bbf130cd42a76f6137d7ad73be20ec69b621b8e57e2aa347d823f86f0675e3` |
| md0 root | 33,554,432 | `148d18e356e46eb2a839fe57f2f8c02f974fa921145679422798e9ddeb081546` |
| md1 seed | 4,194,304 | `a6423c3c57ba4115cccf26e30165b58432efcb8e858c760fd35620fef5aafefa` |
| QEMU payload | 57,296,096 | `4880d43a759106c33aa5edf0c949ae0926472749fa7a60dfd2f56ba4ece0dee0` |

The native phone boot candidate was not replaced by this QEMU payload. Formatting HFS+ includes timestamps; image hashes identify this accepted run. The GUI source recompilation/relink is byte-identical; cross-run timestamped HFS image identity is not promised.

Run from Ubuntu/WSL in the repository, choosing a **new** output directory:

```sh
python3 -B tools/test-duchamp-darwin-gui.py \
  ../../outputs/duchamp-darwin-gui-20261118/NEW-RUN \
  --kernel ../../outputs/duchamp-patched-clang-20261117/new-xnu-qemu-final/kernel.development.sweet \
  --mkfs ../../outputs/duchamp-readonly-var-20261116/formatter/unpacked/usr/sbin/mkfs.hfsplus
```

The wrapper records compiler/linker/signing/HFS commands. Nested `guest/commands.json` records packaging, QEMU and service verification. `guest/run/execution.json` records the actual QEMU invocation. Only the baseline HID probe receives its existing HID entitlement; GUI processes do not require it.

## Failure history and remaining work

Attempt 1 completed the process/window scenario but did not preserve stable framebuffer samples: drawing only on damage allowed diagnostic console text to overwrite the canvas. The GUI compositor now re-presents the current frame periodically. Attempts 2/3 captured all seven states but their already-running service verifier invocation lacked the newly required explicit GUI command list, so they are **not accepted** suite passes. The verifier was extended with `--gui`; attempt 4 rebuilt/executed the consistent final sources and passed all 22/11/74 checks. An initial packaging invocation omitted its required payload argument and exited 2; the corrected explicit-payload run passed 12/12.

The first legacy compositor rerun missed its very short restored state when automated HID immediately triggered client cleanup. Its self-test now waits eight seconds in that state before input. The final legacy rerun captured all six states and passed 25/25; no assertion or expected pixel was relaxed.

Next independent milestone: a bounded host-pointer-to-native-shell input adapter and ordinary-mode launcher event loop, followed by arbitrary client rendering/resize stress, explicit destroy-RPC integration coverage, read-only query permission policy and transactional multi-window updates. Real iOS display services require their own execution/dependency evidence. Physical Duchamp boot remains gated by missing runtime memory ownership/DMA-isolation evidence; none of this QEMU GUI work changes that decision.
