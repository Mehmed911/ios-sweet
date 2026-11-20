# Duchamp Darwin compositor, stage 2

2026-11-17. Branch `duchamp-bootstrap`, HEAD `d91562d9c2bd3bc33d52550c101de1009bb41dc0`. Changes remain uncommitted. Native readiness remains **BLOCKED_BY_MEMORY_EVIDENCE**. No phone operation, physical UFS, firmware change, reboot, slot change, commit or push.

## Architecture and actual source paths

This is a bounded CPU compositor in a separate, real ARM64 Darwin Mach-O process managed by the original launchd. It uses the existing XNU port's IOKit providers; it does not introduce an Apple private class or emulate an Apple display-service protocol. Its custom Mach service is **`org.duchamp.qemu.compositor`**, protocol version 1.

```text
launchd PID 1
  compositor daemon <-- Mach RPC + surface/send rights --> independent clients
       |  kernel-appended audit PID + PID version             |
       |  private per-layer snapshots                  shared IOSurface pixels
       |  Z-order + straight-alpha blend + damage tracking     |
       |  two CPU frames / two output surface mappings  <-----+
       v
  existing AppleCLCD SwapBegin / SwapEnd -> QEMU framebuffer RAM
       ^
  existing SweetHIDButtons shared queue -> focused-client event port
```

The exact source-built kernel remains SHA-256 `e7b51ecb16fe9ad21a78455714b2bf26c1dee1fbc3a6a7f0cb3971a9cd569457`. No kernel bytes or prebuilt objects were patched. Only userspace and QEMU test infrastructure changed. The prior native 32 MiB md0 + 4 MiB md1 candidate, bootshim and recovery images remain separate from copied QEMU test images.

The successful stage-1 code path was audited before reuse:

- `tools/duchamp-darwin-graphics.c`: matching, framebuffer geometry, shared HID mapping/notifications, surface creation, SwapBegin/SwapEnd and the existing 10-check test.
- Its unchanged IOKit operations were extracted to `tools/duchamp-darwin-iokit.h` so both the original probe and new service use the same wire implementation. `tools/duchamp-iokit-wire.h` retains the verified LP64 descriptor layout and bounded HID queue reader.
- Actual kernel sources are under `/var/tmp/duchamp-clang.zZKCR0J4/kernel-workspace/dxb/xnu/`: `iokit/Kernel/arm/SweetSurface.cpp`, `SweetFramebuffer.cpp`, `arm/hid/SweetHID.cpp` and `IOHIDEventServiceUserClient.cpp`. Exact compiled paths/digests are retained in the previous stage's `graphics-source-inputs.json`.
- `SweetSurface.cpp::externalMethod()` selectors 34/35 import/export surface port rights. `returnSurface()` supplies the task mapping, ID, dimensions, stride, allocation size and pixel format. `trapRelease()`/`clientClose()` drop references/mappings.
- `SweetFramebuffer.cpp::AppleCLCD::present()` copies submitted surface pixels into the framebuffer. This is not a GPU submission or a hardware page flip.
- `osfmk/mach/message.h` defines the audit trailer and `MACH_RCV_TRAILER_AUDIT=3`. `bsd/kern/kern_proc.c:3177` checks audit token words 5/7 as PID/PID version. `osfmk/ipc/mach_port.c::mach_port_request_notification()` implements the real dead-name notification mechanism used here.

## New implementation

| Source | Responsibility |
| --- | --- |
| `tools/duchamp-compositor-core.h`, `.c` | Bounded scene, ownership, Z-order, alpha blend, dirty-region union, front/back CPU buffers, focus/press capture and owner removal. Same engine runs natively under ASan/UBSan and in Darwin. |
| `tools/duchamp-compositor-wire.h` | Fixed-width versioned custom requests/replies, port descriptors and receive-side audit-trailer bounds checks. |
| `tools/duchamp-compositor-iokit.h` | Create/import surface mappings, validate actual kernel metadata, close clients and submit output surfaces using the existing framebuffer path. |
| `tools/duchamp-darwin-compositor.c` | launchd Mach check-in, client capability import, authenticated owner lookup, RPC dispatch, shared-memory snapshots, HID routing, process death cleanup and presentation. Also contains separately launched diagnostic client entry points. |
| `tools/duchamp-compositor-control.h` | Test-only launchctl bootstrap/print/bootout and process-survival checks. Included only for the explicit compositor test build. |
| `tools/duchamp_compositor_expectations.py` | Independent host pixel oracle, with no writes to the guest. |
| `tools/test-duchamp-darwin-compositor.py` | Full XNU QEMU execution, original baseline checks, log extraction, byte-level frame and lifecycle validation. |
| `tools/test-duchamp-compositor-core.c` | Native rendering, bounds, ownership, focus, cleanup and malformed audit-trailer tests. |

`tools/test-duchamp-readonly-var.py`, `test-duchamp-darwin-graphics.py`, `sweet-launchctl-control.c`, `sweet-syslogd-control.h` and `verify-sweet-syslogd.py` add an explicit compositor scenario. Default behavior is retained. Additional job files live under `/sbin`, loaded with launchctl; the original five `/System/Library/LaunchDaemons` jobs and their pinned Apple executables remain unchanged.

## Mach interface and ownership

Normal requests have a 24-byte Mach header plus a 48-byte body. Registration is 100 bytes and carries **two port descriptors**, a surface send right and the client's receive-port send right. Replies are 48 bytes. Protocol fields are fixed-width and requests require the exact version, size and descriptor layout; an ordinary client PID field is never used as authority.

| Operation | Contract |
| --- | --- |
| REGISTER | Import the supplied surface capability using a dedicated IOKit connection. Compare claimed dimensions/ID with actual kernel-returned metadata; reject mismatches, duplicate owners/slots, invalid destination bounds or capacity exhaustion. Register a dead-name notification on the event endpoint. |
| QUERY | Return the caller's surface ID, current frame epoch and diagnostic phase/command when self-test mode is enabled. |
| DIRTY | Require the sender's `(PID, PID version)` to own the handle, strictly increasing commit sequence and a valid rectangle. Copy only that region into compositor-owned storage. |
| SET_Z | Change only the sender's own surface, with Z restricted to `[-8,8]`; invalidate its covered rectangle. Equal Z is resolved deterministically by surface ID. |
| FOCUS | Request focus only for the sender's own surface. Foreign-handle requests are denied. |
| EVENT / ACK | Service sends an ordered Menu-button event to the focused client's endpoint. Client ACK must belong to that owner/handle and advance the expected event sequence. |

The service receives with audit trailers. Kernel-appended PID and PID version bind the registering peer and all subsequent operations. The receive-side parser is not an authentication system by itself; native synthetic trailer tests verify bounds/format only. Trust comes from obtaining that trailer through the actual XNU Mach receive path. Surface access is capability-based: registration assigns the submitting capability holder as the compositor owner, not a claim about the original creator of a transferable surface.

On process exit, the kernel sends `MACH_NOTIFY_DEAD_NAME` for the event endpoint. The service requires a kernel audit sender (PID 0), matches the retained endpoint, removes all scene layers for that owner, clears focus/capture as necessary, closes its per-client IOKit connection and drops port references. A fresh lookup must reject the released surface ID. This is separate from merely polling a user-supplied PID.

## Buffers and memory safety

- Canvas: **64x32 BGRA pixels**, opaque output; at most four scene layers in the engine. The version-1 service exposes two client slots, one imported surface per client. Larger surfaces, resize and arbitrary transformations are not supported.
- Kernel metadata, not client sizes, establishes the mapped geometry/stride/allocation. The logical canvas is 8192 bytes, but this kernel rounds each allocation to **16 KiB**. Mapped allocations are capped at 64 KiB; logical reads still obey independently checked width/height/stride bounds.
- Bounds use subtraction/division to avoid multiplication/interval overflow. Zero sizes, out-of-range rectangles, undersized/unaligned strides, duplicate IDs, foreign owners and replayed sequences are rejected before copying.
- Clients retain their own shared surface. On accepted commits, the service takes a private snapshot of the declared region. A client changing pixels outside that rectangle cannot alter the prior private snapshot. Shared backing memory remains mapped into the service until its own IOKit reference closes, even if the client exits.
- Clients should wait for a commit ACK before reusing submitted pixels. A malicious concurrent writer can cause inconsistent pixel content within a snapshot; the prototype does not provide a transactional seal against such writes. The immutable bounds still constrain the read. This is not a production sandbox/security audit.
- Two compositor-owned CPU frames preserve unmodified pixels. Dirty rectangles coalesce to a bounded union; only that region is recomputed. The next buffer begins with the prior front buffer, then swaps indices.
- Two output surface mappings alternate with those frame indices. Presentation uses the existing SwapBegin/SwapEnd path into QEMU rectangle `(320,1664,64,32)`. The kernel CPU-copies the surface to its RAM framebuffer; this is not scanout double buffering.
- Straight-alpha source-over blends 8-bit channels with integer rounding `(source*a + destination*(255-a) + 127)/255`. Output is opaque over background `0xff102030`. There is no gamma correction, premultiplied-input support, GPU acceleration or color-management claim.

## Input and lifecycle

The service uses the existing mapped `SweetHIDButtons` queue. The initial interface is a single Menu-button press/release stream, not a touchscreen, pointer or multi-key protocol. A press captures its original target; changing focus while held does not split its release across clients. Owner removal clears a captured target, and focus falls back to the highest remaining layer.

The daemon's default entry is an ongoing service. An explicit **`--selftest`** argument enables the scripted scene transitions, finite deadline and test-client SIGKILL; these actions do not run in ordinary mode. Clients and test jobs are independent launchd-managed processes. Only the service and original stage-1 HID probe are given the specific HID test entitlement in their own ad-hoc signatures; the new clients run without it. Kernel entitlement checks are unchanged.

The QEMU scenario validates overlapping red/half-transparent blue surfaces, a committed 8x8 green patch, red raised above the overlay, restoration, focus capture, abrupt overlay death after release ACK, fallback input to red, and complete cleanup. A second daemon launch without `--selftest` tests early client exit and survival without requiring the diagnostic event sequence. The controller then removes that service through launchctl and verifies its PID is gone.

The prototype is deliberately bounded: one output rectangle, two client slots, single-threaded dispatch, keyboard test input and basic malformed-request fail-stop diagnostics. It is not a replacement for WindowServer, BackBoard, QuartzCore or SpringBoard. Remaining dependencies include digitizer/pointer routing, resize/format negotiation, fences/frame pacing, broader fault containment and a real open-source interactive client. Physical MT6897 memory/DMA evidence and drivers remain a separate blocked path.

## Actual QEMU results and reproduction

Accepted run: **`../../outputs/duchamp-darwin-compositor-20261117/attempt-4/`**, command exit **0**. It booted the pinned source-built XNU, executed the self-test service as **PID 12**, red client **PID 14** and overlay client **PID 16**, all parented by original launchd PID 1. Audit PID versions were **35** and **40** for those two clients. Logical client surfaces were IDs **4** and **5**; output front/back surfaces were IDs **2** and **3**. IDs are observed values for this run, not interface constants.

The explicit self-test mode received both down/up events at overlay ID 5 even after focus changed to red during the press. The overlay was then killed with SIGKILL after its release ACK; a genuine kernel dead-name notification triggered cleanup and a new surface lookup returned `0xe00002f0`. Red subsequently received both events, exited normally, and its surface was likewise reclaimed. Foreign surface writes/focus, invalid shared geometry/rectangles and a replayed commit were actually rejected.

The controller booted the ordinary, non-self-test daemon as **PID 28**, followed by early-exit clients **30** and **32**. Both exited with **zero input events/ACKs**; the service closed their IOKit mappings, rejected lookup of their old IDs and remained running with `runs = 1`. launchctl bootout then succeeded and the PID disappeared. The self-test daemon had independently passed the same lifecycle check.

```text
COMPOSITOR LIFECYCLE PASS pid=12 bootout=0 gone=1
COMPOSITOR NORMAL PASS pid=28 early_cleanup=2 survived=1 gone=1
```

The full accepted guest ran for **117.177 host seconds**, with `no_panic_observed`, zero unknown console glyphs and all six ordered framebuffer witnesses matched. Each witness is **8192 actual guest bytes**, read from QEMU RAM without host drawing. Every byte matched the independent Python oracle:

| Phase | Host sample | Output surface / first phase swap | SHA-256 of captured pixels |
| --- | ---: | --- | --- |
| Blend: visible red and half-alpha blue | 7 | 2 / 1 | `2a7d6be05ec0dba983e922ed0b7a9ebaaba63509ea444ca3d9340bdb06651976` |
| Dirty: only 8x8 changed, despite larger client write | 8 | 3 / 168 | `2055d70f07bfc4c5c816e542f9874aafe87d9cdce75f34f2de5ed459d944f5ca` |
| Z-order: opaque red raised | 10 | 2 / 356 | `cbab5a1f08bae3da182319ded4e1982af506c918d9103314f9cb59a54eb8219c` |
| Restore: overlay visible again | 12 | 3 / 579 | `2055d70f07bfc4c5c816e542f9874aafe87d9cdce75f34f2de5ed459d944f5ca` |
| Overlay cleanup: red survives | 13 | 2 / 727 | `cbab5a1f08bae3da182319ded4e1982af506c918d9103314f9cb59a54eb8219c` |
| All clients removed: background | 15 | 3 / 918 | `78d27a942ec1960e456dbb5b2b275b60e35041629b83195b334b94795be26c7b` |

The two 16 KiB output surfaces alternated with the CPU front/back indices, with scene epochs **2 through 7**. Host samples occur after presentation; the table records the service's first submission of each phase, not a fabricated atomic scanout timestamp. Raw crops, PNGs and sample times are in `attempt-4/execution/guest/run/sequence-*.raw`, `.png` and `frame-sequence.json`. Source changes to `qemu-sweet.py` add only an opt-in ordered observer; it never writes the reference into guest RAM.

| Test actually run | Result | Evidence under the stage-2 output directory |
| --- | --- | --- |
| Compositor, authentic Mach ownership/input, cleanup and lifecycle | **25/25** | `attempt-4/verification.json` |
| Native core/trailer bounds, ownership and rendering under ASan/UBSan | **48 assertions passed** | `native-commands.json`, `native-1.log`; also compiled/run in the accepted pipeline |
| Passive framebuffer observer including sequence bounds/path validation | **12/12** | `native-2.log`, accepted pipeline command log |
| Original graphics/input integration | **10/10** | `attempt-4/execution/verification.json` |
| Read-only md0 + writable md1 filesystem integration | **11/11** | `attempt-4/execution/guest/verification.json` |
| Original launchd/syslogd/notifyd service checks | **74/74** | `attempt-4/execution/guest/service-verification.json` |
| Separate full-XNU dynamic/static Mach-O regression | **17/17** | `macho-regression/run/verification.json`, `macho-command.json` |
| Default dual-volume packaging | **12/12** | `packaging-0.log`, `packaging-commands.json` |
| Accepted payload's explicit HID/storage denial profile | **7/7** | `accepted-profile.log`, `accepted-profile-command.json` |
| Native image, bootshim, FDT, memory validators and saved recovery hashes | **25/25 unchanged** | `frozen-inputs.json`; local preservation checks, not device validation |

The separate Mach-O run observed dynamic PID 2/exit 0, static PID 3/exit 42, 37 dyld images and real Mach messaging. The service boot uses original launchd PID 1; the Mach-O regression's diagnostic PID 1 is a different test. Neither result substitutes an archived CI kernel.

Filesystem evidence still reports `EROFS=30` for root writes, raw-root open denied (`13`), `ENOSPC=28` plus recovery on md1, correct `/var` resolution and `/dev/console`. md0 before/after SHA-256 is identical: `a4dd47519657fc6cfedcaa29895d52bbb52c2c9b53b8e1e856652c23d0564de5`. The accepted QEMU payload is **57,296,096 bytes**, SHA-256 `fc1aae8dcc7ef05295bde320a6b4a8e50d6fc739870bf0ff0a87e1407450d63d`. The native phone candidate was not replaced with this QEMU payload.

The entitled service binary is **114,688 bytes**, SHA-256 `88d3f922c40b0da99da0103450ca8b5a2116ead532f7a5aea6983d7f505b1284`; the unentitled client binary is **86,368 bytes**, SHA-256 `83daac783374774125977b95cee5fb5c3f4b717ec122fc1595b0b365052ecf0f`. HFS formatting includes time metadata, so image hashes identify this run. Repacking the same input images is tested byte-identical; cross-run HFS-byte identity is not promised.

Reproduce from Ubuntu/WSL in the repository, with a new output directory:

```sh
python3 -B tools/test-duchamp-darwin-compositor.py \
  ../../outputs/duchamp-darwin-compositor-20261117/attempt-4 \
  --kernel ../../outputs/duchamp-patched-clang-20261117/new-xnu-qemu-final/kernel.development.sweet \
  --mkfs ../../outputs/duchamp-readonly-var-20261116/formatter/unpacked/usr/sbin/mkfs.hfsplus
```

The complete compiler/linker/signer/QEMU/HFS command arguments and exit codes are in `attempt-4/commands.json`, `attempt-4/execution/commands.json` and its nested `guest/commands.json`. Userspace compiler/linker are Clang/LLD 21.1.8 and QEMU is 10.2.1; the preserved kernel's patched toolchain provenance stays in its original source-build manifest.

Failure history is retained, not counted as success. Attempt 1 rejected valid page-rounded surface allocations because the new logical-size cap was too small; inspection of actual `SweetSurface.cpp::sweet_surface_layout()` justified the corrected bounded allocation check. Attempt 2 passed the initial 22-check implementation. Attempt 3 was superseded while the test harness was being extended; its mismatched expected command list is not an accepted regression result. Attempt 4 compiled and tested the final consistent sources and ordinary-mode lifecycle together.

No new Blackbox investigation, firmware authorization model or native boot layout was introduced. The next independent milestone is an open-source input-driven interactive client with pointer/digitizer events and resize/lifetime stress. SpringBoard and physical Mali/MT6897 graphics compatibility remain unproven.
