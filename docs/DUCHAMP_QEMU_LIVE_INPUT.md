# Darwin QEMU live mouse input

2026-11-18. Branch `duchamp-bootstrap`, HEAD `d91562d9c2bd3bc33d52550c101de1009bb41dc0` plus preserved uncommitted changes. This stage is QEMU-only. Physical readiness remains **BLOCKED_BY_MEMORY_EVIDENCE**. No phone commands, firmware operations, commit or push were performed.

## Implemented path

```text
Browser pointer event
  -> localhost HTTP input bridge
  -> QMP input-send-event (absolute X/Y, BTN_LEFT)
  -> QEMU virtio-tablet-device
  -> modern VirtIO-MMIO event queue
  -> source-built XNU /dev/duchamp-pointer
  -> native /sbin/duchamp-pointer-input, managed by launchd
  -> audited Mach IPC to shell --live
  -> existing window-manager pointer/capture/focus logic
  -> existing compositor and framebuffer
```

The bridge does not call the window-manager RPC directly or write framebuffer pixels. The display view maps the QEMU RAM file read-only and copies the existing 160x96 canvas at framebuffer rectangle `(320,1664,160,96)`. The browser scales it to 800x480. The compositor, window ownership, blending and front/back presentation remain in the existing Darwin processes.

`--selftest` still explicitly uses synthetic Mach input for the old GUI regression. The new device suite uses QMP-generated input that traverses the real virtual device and XNU driver. The separate browser suite uses automated Linux Chromium pointer actions through the same DOM handlers a human mouse uses. Automation is **not** evidence of a human operating a physical mouse, a phone touchscreen, IOHIDSystem/BackBoard compatibility, or SpringBoard.

## Why this device

The actual machine is QEMU `virt,gic-version=3`, Cortex-A76, one CPU, `-nodefaults -nographic`; RAM is selected by the existing payload runner, currently 7 GiB for these high-address profiles. There was no input device in the original launch command. QEMU does not automatically deliver host mouse events to this XNU port.

| Option | Observed prerequisites | Decision |
| --- | --- | --- |
| USB HID | QEMU lists USB tablet/mouse and XHCI, but this XNU profile has no usable corresponding USB host/HID path | Would require another host-controller stack |
| PS/2 | Not a device on the selected ARM virt machine | Rejected |
| Serial mouse/tablet | QEMU source requires modem-control or baud-setting ioctls that its PL011 path does not forward as needed; the relevant VMAPPLE driver is also not present in this kernel | Rejected |
| VirtIO-MMIO tablet | Listed by this installed QEMU; generated FDT and `info qtree` locate the transport; device identity independently read in the virtual machine | Implemented |

The runner explicitly adds:

```text
-global virtio-mmio.force-legacy=false
-device virtio-tablet-device,id=duchamp-pointer
```

The observed transport is `0x0a003e00`, length `0x200`. Identity reads returned magic `0x74726976`, version `2`, device `18`, vendor `0x554d4551`. This is a deliberately restricted QEMU profile, not an address for MT6897. Profile checking rejects a changed address, compatible string, missing opt-in, duplicate node or UFS-enabled ADT.

Primary references: [QEMU virt board](https://www.qemu.org/docs/master/system/arm/virt.html), [QEMU 10.2.1 VirtIO-MMIO implementation](https://github.com/qemu/qemu/blob/v10.2.1/hw/virtio/virtio-mmio.c), [QMP input-send-event](https://www.qemu.org/docs/master/interop/qemu-qmp-ref.html#command-input-send-event), [serial mouse](https://github.com/qemu/qemu/blob/v10.2.1/chardev/msmouse.c), [serial tablet](https://github.com/qemu/qemu/blob/v10.2.1/chardev/wctablet.c), [PL011](https://github.com/qemu/qemu/blob/v10.2.1/hw/char/pl011.c). Installed QEMU evidence is retained with the run, rather than inferred from the documentation alone.

## Driver and isolation

`tools/duchamp-qemu-pointer-kernel.c` registers a root-only, exclusive-open, read-only character device. Registration checks the explicit boot argument, CPU identity and exact custom ADT node; it performs no MMIO. On open it verifies the virtual-device identity, resets the device with a bounded wait, negotiates `VIRTIO_F_VERSION_1` and creates a 64-entry split queue. All descriptors and events fit in one permanently allocated contiguous page. The page is retained across resets; an uncertain reset never frees memory still potentially visible to the virtual device.

Device event types are absolute X/Y, left button and SYN_REPORT. Every used-ring index, descriptor ID, event length, pending count and coordinate is checked before indexing. Queue publication/consumption uses acquire/release ordering and ARM barriers. This profile uses coherent QEMU guest RAM; those barriers are **not** proof of MT6897 system-cache, IOMMU or UFS DMA ownership. Device interrupts are suppressed and input is polled by the service approximately every 5 ms; this is not an IRQ-driven VirtIO implementation.

The read ABI is an exact 32-byte report: version, generation, sequence, flags, X, Y, left button and rejected count. Device reset/reopen changes generation; input reports are sequenced. The portable parser and coordinate transform are in `tools/duchamp-virtio-pointer.h`. Raw absolute coordinates `0..32767` map, with rounding, into `0..159` and `0..95`.

The shell accepts the input endpoint only from the kernel-audited PID and PID version of `/sbin/duchamp-pointer-input`. It retains the endpoint capability and death notification. Subsequent events must match that sender, generation and the next sequence. Existing window-manager checks continue to restrict pointer authority to the shell; application clients receive only their existing focused/captured input. Endpoint death while held forces a release before the connection is discarded.

The local bridge binds only `127.0.0.1`, uses a random per-session token and input-source handle, validates Origin, body size, exact JSON fields, integer bounds and monotonic sequences, and exposes no arbitrary QMP command API. Invalid requests do not issue `input-send-event`. Movement can coalesce under backpressure; button edges and their coordinates cannot. Pointer capture preserves release outside the canvas. Blur, source loss and a three-second heartbeat timeout release the button. Reconnection rejects old source handles. The bridge waits for actual virtual-device DRIVER_OK before accepting input.

The host `browser-pointer` label records the DOM path (`isTrusted`); it is not cryptographic provenance or proof of human input. Process isolation is established by the Mach audit/capability checks, not by that label.

## Source-built kernel and files

`tools/build-duchamp-qemu-pointer-kernel.py` verifies all 1126 original source-build object hashes, compiles a copied `IOKitBSDInit.cpp` containing the new registration hook, compiles the new C driver with the actual snapshot flags, and fully relinks 1127 source-built inputs. It does not patch a kernel binary or use archived CI objects. The generated source diff, exact compiler/linker commands and all object hashes are retained. The original source snapshot, objects and kernel remain unchanged.

| Artifact | SHA-256 |
| --- | --- |
| Preserved original source-built kernel | `e7b51ecb16fe9ad21a78455714b2bf26c1dee1fbc3a6a7f0cb3971a9cd569457` |
| New QEMU pointer kernel, 19,544,392 bytes | `cf0b0f80e83580bfe0b00529f148b8ad5705ea565ee3c1e683494948d9752e0d` |
| GUI Mach-O, 103,776 bytes | `f46774a2fd12024c67d6e89f0cd0c896eb5abdebb8d928c6f3d3458693471ed4` |
| Native input service, 67,952 bytes | `a51b1e644aa675876ffbb821d55fb805cb73155507167997215d0e65fe84abd6` |

Kernel compilation uses the isolated patched Clang 24 toolchain from the verified source build. Darwin clients use Clang/LLD 21.1.8. Tested QEMU is 10.2.1. Exact command lines and versions are in the output manifests.

Files added:

- `tools/duchamp-virtio-pointer.h`, `duchamp-qemu-pointer-kernel.c`, `build-duchamp-qemu-pointer-kernel.py`: parser, driver and complete source relink.
- `tools/duchamp-pointer-wire.h`, `duchamp-darwin-pointer.c`: custom Mach input service and audited endpoint protocol.
- `tools/qemu_pointer_profile.py`, `duchamp_source_kernel.py`: strict opt-in payload profile and source-build receipt checks.
- `tools/duchamp_live_input.py`, `run-duchamp-live-input.py`: local viewer and normal six-job interactive session, without the diagnostic observer.
- `tools/duchamp_live_input_oracle.py`, `duchamp_live_input_test.py`, `test-duchamp-live-browser.py`, `test-duchamp-live-input-host.py`, `test-duchamp-virtio-pointer.c`, `test-qemu-pointer-profile.py`: independent pixels, actual device/browser tests and negative tests.

Files extended: `tools/duchamp-darwin-gui.c`, `duchamp-gui-control.h`, `test-duchamp-readonly-var.py`, `qemu-sweet.py`, `test-duchamp-darwin-gui.py`, `test-duchamp-darwin-graphics.py`, `test-duchamp-darwin-compositor.py`, `verify-sweet-syslogd.py`, and `NOTES.md`. Existing default tests and input-disabled profiles remain available.

## Test evidence

All paths below are under workspace `outputs/duchamp-live-input-20261118`, outside the repository. Each runner records exact argv, exit codes and logs. The final manifest indexes hashes and test results.

| Test | Actual result | Evidence |
| --- | --- | --- |
| Native input parser, ASan/UBSan | 33 assertions, exit 0 | `attempt-1/command-002.log`, `command-003.log` |
| Native window manager, ASan/UBSan | 53 assertions, exit 0 | `attempt-1/command-000.log`, `command-001.log` |
| Real virtual-device live input | 18/18, seven byte-exact framebuffer crops | `attempt-1/verification.json`, `guest/run/frame-sequence.json` |
| Normal interactive browser path | 16/16, ten byte-exact crops, 28 actual browser pointer events | `browser-test-4/verification.json`, `session/viewer/input-events.jsonl` |
| Host malformed/replayed input, disconnect, readiness, read-only map | 9/9, exit 0 | `targeted/test-00.log` |
| Strict pointer payload negatives | 10/10, exit 0 | `targeted/test-01.log` |
| Passive frame observer | 12/12, exit 0 | `targeted/test-02.log` |
| Default dual-RAMDisk packaging negatives | 12/12, exit 0 | `targeted/packaging-corrected.log` |
| Existing GUI on the new kernel | 22/22 and seven exact crops | `gui-regression/verification.json` |
| Existing compositor on the new kernel | 25/25 and six exact crops; native assertions 48 | `compositor-regression/verification.json` |
| Existing graphics / filesystems / launchd services | 10/10, 11/11, 74/74 | nested regression reports and commands |
| Real dynamic/static Mach-O on the new kernel | 17/17; dynamic PID 2 exit 0, static PID 3 exit 42 | `macho-regression/run/verification.json` |
| Frozen native candidate / FDT / recovery host files | 25/25 hashes unchanged | `preserved-inputs.json` |

In the live-device run, compositor PID 18, manager PID 20, shell PID 24, input PID 26, observer PID 28, red PID 30 and blue PID 32 were launchd children. Restarting the actual input process produced PID 34 and device generation 2. The shell logged `forced_release=1`; the observer verified the button became released before subsequent focus changes. Input service logs and observer logs were extracted unchanged from md1 into `extracted-input/`.

The accepted device suite uses the observer only to query state and restart the input process, not to inject pointer events. The normal interactive browser run omits this observer entirely. Browser-test-4 independently verifies launch, focus, drag, resize, release outside the canvas, page-close release and reconnection. Its drag test deliberately stalls a pre-press HTTP request to prove that event coalescing preserves the press origin. Full browser results, DOM errors, input journal and pixel/screenshot hashes are in `browser-test-4/verification.json` and `browser-test-4/*.raw`; screenshots show the actual canvas, not a generated mockup. The 240-second normal session exited 0, with no panic observed; its md0 dump remained byte-identical, md1 changed as expected, and its saved preflight witness still records EROFS/ENOSPC and `/var` alias checks. `normal-session-evidence/` contains its extracted guest logs. `finalize.py` and `final-manifest.json` record the independent offline postflight, including source/object verification and all suite references.

Failure history is retained. Kernel attempt 1 needed the existing `kern/clock.h` declaration for `delay`; kernel 2 compiled and linked successfully. Browser attempt 1 exposed early clicks before driver readiness. Attempts 2/3 stopped at the browser's 30-second default startup wait; the guest desktop in the accepted device run appeared around 56 seconds. Readiness gating and an explicit startup timeout fixed this. A targeted packaging invocation initially referenced a nonexistent file (zero tests executed); the corrected command passed all 12. No assertion, expected pixel or test requirement was relaxed to classify a failed run as passed.

The original `attempt-1/guest/verification.json` retains the base package hash before adding the pointer ADT. `actual-run-payloads.json` separately validates and identifies the exact `guest/payload.bin` passed to QEMU: 57,298,732 bytes, SHA-256 `31fcf39de95c82892e6fdcaadb34303dca57b60aad3362e927e72245db9a9fdc`. The reporting code now records the transformed image hash, size and ADT hash plus the base hash separately; `metadata-preflight-command.json` proves those fields match actual bytes. HFS timestamps mean independently prepared root images need not have identical whole-image hashes; repackaging the same seed files is checked byte-for-byte.

## Reproduce and interact

Run from this repository under WSL Ubuntu. Output paths must be new. The normal launcher prints a local browser URL; after XNU starts, use the orange/blue launcher buttons, title strips to drag, and bottom-right corners to resize. Reconnect uses the button beneath the canvas. Closing the page releases input; stopping the launcher ends only its owned QEMU instance. Changes to md1 are temporary.

```sh
OUT=../../outputs/duchamp-live-input-20261118
MKFS=../../outputs/duchamp-readonly-var-20261116/formatter/unpacked/usr/sbin/mkfs.hfsplus

# Optional source relink into a NEW directory, using preserved verified inputs.
python3 -B tools/build-duchamp-qemu-pointer-kernel.py "$OUT/kernel-new" \
  --baseline-build ../../outputs/duchamp-patched-clang-20261117

# Actual-device regression profile.
python3 -B tools/test-duchamp-darwin-gui.py "$OUT/device-new" \
  --kernel "$OUT/kernel-2/kernel.development.sweet" \
  --kernel-manifest "$OUT/kernel-2/build-manifest.json" \
  --mkfs "$MKFS" --live-input

# Ordinary interactive session: six launchd jobs, no self-test/observer.
python3 -B tools/run-duchamp-live-input.py "$OUT/interactive-new" \
  --kernel-manifest "$OUT/kernel-2/build-manifest.json" \
  --artifacts "$OUT/attempt-1" --mkfs "$MKFS" --seconds 3600
```

The browser automation test requires the isolated Playwright installation recorded in `browser-environment.json`; it installs no system browser/compiler replacement. Windows desktop UI automation was unavailable in this session because its helper reported a missing kernel-assets path. Actual browser validation therefore used Linux Chromium in WSL, not Windows desktop mouse automation.

## Limitations and next touchscreen stage

- This VirtIO-MMIO bus rejects device hot-unplug: `Bus 'virtio-mmio-bus.31' does not support hotplugging`. `device-capability.json` records the actual response. Reconnect coverage is real driver close/reset/reopen plus browser-source reconnect, not physical bus removal/re-addition.
- The viewer and shared-memory backend currently require POSIX/WSL. They are not a tested native-Windows QEMU display backend. Canvas refresh is approximately 60 ms; no 120 Hz or measured physical latency claim is made.
- Single pointer, left button and absolute position are implemented. Wheel, right click, multi-touch, IOHID touch descriptors and Android FocalTech/SPI are not added by this stage.
- The native input service retries/reset/reinitializes its device connection. Existing GUI self-tests cover manager restart; seamless recovery of an interactive shell across manager failure is a separate test, not established here.
- The next independent input milestone is multiple pointer/contact IDs with explicit cancel semantics and an open-source touch test client using the same ownership checks. Integrating Apple's private display/input services requires their actual execution evidence. MT6897 SPI2, clocks, GPIO, PHY, IOMMU and memory ownership remain separate hardware work.
- Physical UFS and the native boot candidate remain unchanged and disabled/blocked. QEMU virtual DMA success supplies no missing phone handoff evidence.
