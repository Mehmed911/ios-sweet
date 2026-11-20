# Duchamp Darwin continuation: actual QEMU results

2026-11-17. `duchamp-bootstrap`, HEAD `d91562d9c2bd3bc33d52550c101de1009bb41dc0`; all work remains uncommitted. No phone transport, reboot, flash, slot change, physical MMIO/DMA, firmware modification or partition operation was performed.

**Achieved: a real dynamic Darwin process under original launchd matched the four existing IOKit services, consumed virtual input through the shared HID queue and Mach notifications, and presented a verified framebuffer pattern through a mapped surface and SwapEnd.** Native readiness remains `BLOCKED_BY_MEMORY_EVIDENCE`; historical export remains `EXPORT_INTERFACE_UNAVAILABLE`.

## Preserved kernel and test scope

The exact source-built kernel used is `../../outputs/duchamp-patched-clang-20261117/new-xnu-qemu-final/kernel.development.sweet`, SHA-256 `e7b51ecb16fe9ad21a78455714b2bf26c1dee1fbc3a6a7f0cb3971a9cd569457`. It was not rebuilt, patched or replaced in this phase. Existing framebuffer/HID source objects were already part of this kernel. The current test program and its runner are 0BSD; the already installed dyld/libSystem and service fixtures were reused without adding UI framework binaries.

The new program ran as **PID 10, PPID 1**, identified its parent as `/sbin/launchd`, and loaded **37 images** through dyld. It matched `AppleCLCD`, `IOCoreSurfaceRoot`, `SweetHIDButtons` and `SweetHIDTouch`; a nonexistent provider returned `0xe00002f0`. It read display size **1220x2712** from the framebuffer user client.

Actual guest trace:

```text
IDENTITY pid=10 ppid=1 uid=0 parent=/sbin/launchd
DYNAMIC images=37
DISPLAY width=1220 height=2712
INPUT event=1 down=1 sender=4294967578 timestamp=2242199187
INPUT event=2 down=0 sender=4294967578 timestamp=2248623599
INPUT PASS events=2 notifications=2
FRAME swap=1 surface=2 rect=160,1600,64,32
PASS Darwin IOKit framebuffer and HID queue
```

The host independently captured the 64x32 BGRA rectangle from QEMU framebuffer RAM at sample 7, 40.744 host seconds. Its **8192 bytes** exactly match the deterministic userspace pattern, SHA-256 `1af2135a15afd0e0b13b696ce529cf84a0e17341fdfee3b6416a30317a683521`. Surface **2** and swap **1** are from this same process and guest run. The host observer only reads memory; it does not draw the reference into the guest.

The probe remains alive presenting the frame until the runner stops QEMU after the services' second heartbeat. It did not report a successful process exit. Total run: **71.424 host seconds**, `no_panic_observed`, zero unknown console glyphs. This is a diagnostic CPU-rendered pattern and synthetic Menu-button pair, not BackBoard, a touch gesture, SpringBoard, Mali acceleration or a phone display result.

## Implementation changes

| File | Change |
| --- | --- |
| `tools/duchamp-darwin-graphics.c` | Real ARM64 dynamic test process: IOKit matching, three user clients, shared HID queue, Mach notifications, mapped surface, SwapBegin/SwapEnd, md1 trace and witness. |
| `tools/duchamp-iokit-wire.h` | Minimal build-specific LP64 Mach/IOKit ABI, checked struct sizes/descriptor offsets, bounded single-consumer queue decoding. |
| `tools/test-duchamp-darwin-graphics.py` | Reproducible compile/link, pinned offline ad-hoc signer, exact HID entitlement verification, copied HFS fixtures, same-boot guest/framebuffer validation and command logs. |
| `tools/qemu_frame_witness.py` | Read-only bounded crop observer with stride/bounds/digest validation. |
| `tools/qemu-sweet.py` | Opt-in virtual HID profile and framebuffer witness capture; existing default launch behavior retained. |
| `tools/qemu_ramroot_var.py` | Exact explicit `sweethidtest=5` QEMU profile, retaining read-only root, reservation validation and storage-free ADT requirement. |
| `tools/test-duchamp-readonly-var.py` | Opt-in graphics program/job/controller installation into copied root, preserving the 32 MiB root and 4 MiB writable var. |
| `tools/sweet-launchctl-control.c` | Compile-time opt-in to bootstrap the graphics job using launchctl before original service checks. |
| `tools/verify-sweet-syslogd.py` | Explicit graphics scenario additionally requires the bootstrap command; original 74 assertions remain enforced. |
| `tools/test-duchamp-iokit-wire.c`, `tools/test-qemu-frame-witness.py`, `tools/test-qemu-diagnostic-profile.py` | Native parser/observer/profile rejection tests. |

Actual ABI fixes in the new probe were derived from the generated server and linked source: use the supported matching-service-bin RPC rather than the unsupported legacy string RPC; use `mach_msg2_internal` with kernel-object semantics; match the actual provider class `IOCoreSurfaceRoot`; lay out LP64 OOL descriptors with type at byte 11 and size at byte 12. Kernel validation was not relaxed.

The existing HID entitlement check rejected the unentitled test (`graphics-v10/graphics-trace.txt`, open result `0xe00002c2`). The successful program carries only `com.apple.hid.system.user-access-service` in its own ad-hoc signature, checked by the pinned local signer. This is a QEMU test capability, not a trusted firmware grant. Earlier failed build/protocol attempts remain under `graphics-v1` through `graphics-v10`; only **graphics-v11** is the accepted graphics result.

## Commands and results

All commands below run from the repository in Ubuntu/WSL. Output directory must not exist. Compiler: Ubuntu Clang **21.1.8**; userspace linker: LLD **21.1.8**; QEMU **10.2.1**; Python **3.14.4**. These build the userspace probe; the preserved kernel was previously source-built with its recorded patched toolchain.

```sh
python3 -B tools/test-duchamp-darwin-graphics.py \
  ../../outputs/duchamp-darwin-next-stage-20261117/graphics-v11 \
  --kernel ../../outputs/duchamp-patched-clang-20261117/new-xnu-qemu-final/kernel.development.sweet \
  --mkfs ../../outputs/duchamp-readonly-var-20261116/formatter/unpacked/usr/sbin/mkfs.hfsplus
```

This completed with **exit 0**. `graphics-v11/commands.json` records exact compiler, linker, signer, guest and HFS extraction arguments, individual exit codes and log digests. The nested `guest/commands.json` records packaging and the full QEMU command. No prebuilt-kernel modification is used.

| Validation actually run | Result | Evidence under `../../outputs/duchamp-darwin-next-stage-20261117/` |
| --- | --- | --- |
| Native HID queue parser, Clang ASan/UBSan | 10/10 | `graphics-v11/command-000.log`, `command-001.log` |
| Passive crop observer | 8/8 | `graphics-v11/command-002.log`, `frame-witness-final.log` |
| Default dual-RAMDisk packaging | 12/12 | `packaging-final.log`, `native-targeted-commands.json` |
| Explicit HID profile restrictions | 7/7 | `diagnostic-profile-final.log`: default rejection, root-write argument, arbitrary HID period, both UFS nodes and truncation |
| Real graphics/input integration | 10/10 | `graphics-v11/verification.json` |
| Dual filesystem/service integration | 11/11 | `graphics-v11/guest/verification.json` |
| Original launchd/syslogd/notifyd services | 74/74 | `graphics-v11/guest/service-verification.json` |
| Separate dynamic/static Mach-O regression | 17/17 | `macho-regression/run/verification.json`, exact argv/exit 0 in `macho-command.json` |
| Frozen native/bootshim/memory/recovery inputs | 25/25 hashes unchanged | `frozen-inputs-after.json`; nine recovery image checks are local, not new phone tests |

The Mach-O regression observed dynamic PID 2/exit 0, static PID 3/exit 42, 37 dyld images, real Mach messaging, filesystem/VM checks and a surviving diagnostic PID 1. The separate graphics/service boot uses the original launchd PID 1. These two PID 1 implementations are not conflated.

The accepted graphics run preserved read-only md0 (`EROFS=30`), denied raw root write opens (`13`), mounted md1 on `/private/var`, verified `/var` resolution and devfs console, exercised md1 exhaustion/recovery (`ENOSPC=28`) and kept md0 byte-identical. No physical UFS node is added. The new profile rejection tests continue to reject both UFS ADT backends. Unchanged firmware-authorization models were not rebuilt or used as new physical evidence.

## Output identities

| Accepted QEMU artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| Graphics program with test entitlement | 98,304 | `e4bd2d2924f40720399142a21b6ce64cfe8ff2747c4c13b5c786151331c0c38a` |
| md0 before and after execution | 33,554,432 | `c3e5999a7e564ee2c13491c763e642e7d2edfac372f97d79c453673171eeaa20` |
| md1 seed | 4,194,304 | `0a041f53019110ebcea639cec14fd869a4ccf0e5a67ede31be18a9cd86c7688b` |
| md1 after execution | 4,194,304 | `f625b005c8c800f308ef86a084956ad36bd39fb11f36e5035ca8aaa6a7687af9` |
| QEMU dual-volume payload | 57,296,096 | `e708942a23840e8ed17904687ce05f8cc51028b242e32660afc294b2fb324e4f` |

HFS formatting has time-dependent metadata: the generated image hash identifies this run, not a promise of cross-run filesystem-byte reproducibility. Repacking the same verified input images produced byte-identical payloads. The native candidate and its existing hashes remain separate and unchanged.

Captured crop: `graphics-v11/guest/run/framebuffer-witness.png`; raw pixels and metadata are alongside it. The complete final console screenshot is `graphics-v11/guest/run/fb.png`. See `DUCHAMP_GRAPHICS_BRINGUP_PLAN.md` for the linked-source audit and next interactive milestone, and `DUCHAMP_FIRMWARE_EVIDENCE_BLOCKER.md` for the unchanged physical blockers.

## Next achievable milestone

Extend the open-source test application to redraw in response to virtual input and validate digitizer coordinates, cancellation and user-client cleanup. Larger graphical services require their actual matching dependencies and execution evidence. Native progress still needs final-boot memory ownership and modem/peripheral DMA isolation evidence; no QEMU result supplies those missing facts.
