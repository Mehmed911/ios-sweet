# QEMU multitouch for the Darwin test shell

2026-11-18. QEMU-only implementation on `duchamp-bootstrap`, with no phone operation, commit or push. Physical status remains **BLOCKED_BY_MEMORY_EVIDENCE**. This is virtual-device input for the original Darwin test GUI; it establishes neither MT6897 touchscreen support nor BackBoard/SpringBoard compatibility.

## Verified device selection

The installed QEMU 10.2.1 lists `virtio-multitouch-device`. An isolated paused VM, generated machine configuration, QMP schema and `info qtree` establish the actual selected ARM `virt,gic-version=3` configuration. The first VirtIO tablet remains at `0x0a003e00`; the second multitouch transport is `0x0a003c00`, length `0x200`. Both are modern VirtIO input device ID 18. These are QEMU addresses, never physical MT6897 addresses.

```text
-global virtio-mmio.force-legacy=false
-device virtio-tablet-device,id=duchamp-pointer
-device virtio-multitouch-device,id=duchamp-touch
```

`qemu-sweet.py --virtio-multitouch` requires the existing pointer profile as well. `qemu_touch_profile.py` verifies the exact boot argument, compatible string, device node, address and length at both payload verification points. The ordinary pointer profile rejects an undeclared touch extension. Existing RAM-root bounds and UFS-disabled checks remain mandatory.

QEMU source defines slot and tracking-ID bounds 0 through `INPUT_EVENT_SLOTS_MAX=0xa`, inclusive: eleven bounded slots. The implementation supports those bounds, with native/host boundary tests; actual simultaneous end-to-end testing exercises **two contacts**, not eleven. Raw touch events are ABS_MT_SLOT, ABS_MT_TRACKING_ID, ABS_MT_POSITION_X/Y and SYN_REPORT.

Primary sources and locally verified artifacts:

- [QEMU 10.2.1 VirtIO HID input](https://github.com/qemu/qemu/blob/v10.2.1/hw/input/virtio-input-hid.c).
- [QEMU 10.2.1 input slot definitions](https://github.com/qemu/qemu/blob/v10.2.1/include/ui/input.h).
- [QEMU input-send-event and InputMultiTouchEvent](https://www.qemu.org/docs/master/interop/qemu-qmp-ref.html#command-input-send-event).
- [QEMU VirtIO input report delivery](https://github.com/qemu/qemu/blob/v10.2.1/hw/input/virtio-input.c).
- [QEMU VirtIO queue introspection schema](https://github.com/qemu/qemu/blob/v10.2.1/qapi/virtio.json).
- `../../outputs/duchamp-app-multitouch-20261118/touch-capability.json`, `touch-qtree.txt`, `touch-qapi.json`, `research-source.json`, `x-query-virtio-queue-status.json` and `x-query-virtio-queue-element.json` retain actual installed-device observations.

## Actual path

```text
Browser DOM pointer contacts / explicit QMP test contacts
 -> bounded localhost input bridge
 -> QMP input-send-event, mtt begin/update/data/end/cancel
 -> actual QEMU virtio-multitouch-device event queue
 -> XNU /dev/duchamp-touch
 -> launchd /sbin/duchamp-touch-input
 -> audited DT Mach reports to shell
 -> owner-checked GW touch messages to existing window manager
 -> per-contact capture, application delivery, geometry and existing compositor
```

Host input never calls the WM touch RPC directly and never writes framebuffer pixels. The viewer maps the QEMU RAM file read-only. Twelve native lifecycle states and twelve normal-session browser crops are compared against independently generated complete 160×96 framebuffer byte arrays. Browser automation uses an isolated Linux Chromium installation and real DOM event handlers; it is not evidence of a human or a physical touchscreen.

## Kernel ABI and queue

`tools/duchamp-qemu-pointer-kernel.c` now has separate per-device contexts. Existing `/dev/duchamp-pointer` minor 0 retains its 32-byte ABI. New `/dev/duchamp-touch` minor 1 exposes an exact 208-byte report: version 2, generation, sequence, flags, active/changed masks, rejection count, reserved word and eleven 16-byte contacts containing ID, X, Y and active state.

`tools/duchamp-virtio-touch.h` implements the portable parser and continuity validator. It rejects duplicate IDs, invalid slots, incomplete positions, impossible coordinates, malformed masks and stale or inconsistent sequences. Invalid frames and SYN_DROPPED cancel contacts rather than indexing unchecked arrays. Raw coordinates 0..32767 normalize with rounding into 160×96 canvas bounds.

The cdev is root-only, read-only and exclusive-open. Its registration checks exact opt-in ADT/boot arguments and QEMU CPU identity and performs no device MMIO. Opening verifies the virtual device, resets with a bounded wait, negotiates the modern feature and publishes a 64-entry split event queue in retained memory. Generation changes on reset/reopen. Invalid descriptor IDs, lengths, pending counts and addresses fail closed. The existing pointer service remains independent.

Polling is approximately 5 ms. This is not a new interrupt-driven input stack. Queue memory and barriers are verified only for coherent QEMU RAM, not physical MediaTek cache maintenance, DMA isolation or resource ownership. Device hot-unplug remains unsupported on this machine's VirtIO-MMIO bus; service restart/reset/reopen is supported and tested.

## Host backpressure and cancellation truthfulness

QEMU 10.2.1 drops an entire report if it cannot acquire enough writable queue descriptors. It does not generate SYN_DROPPED for this shortage. A successful QMP reply alone therefore does not prove that the input was delivered.

The bridge checks actual event-queue capacity through `x-query-virtio-queue-status` at the observed QOM path `/machine/peripheral/duchamp-touch`, queue 0. It validates the queue type/size, in-use count, available-ring address inside the mapped guest RAM and last-consumed index. The avail index is read from the **read-only** RAM mapping. Before submission it waits at most two seconds for enough slots for the complete raw report, including slot/tracking-ID events and SYN. Two contact downs need nine descriptors, not seven. It submits no partial report on timeout. Each accepted journal entry records `queue_available` and `queue_required`.

This uses a QEMU debug interface explicitly marked unstable; an unavailable or changed interface denies input rather than falling back to guessed addresses. Queue-address MMIO registers are write-only in modern VirtIO. An initial guard reading them failed in the real VM; that attempt was retained as a failure and replaced by the verified QMP query. See [the actual MMIO implementation](https://github.com/qemu/qemu/blob/v10.2.1/hw/virtio/virtio-mmio.c).

The host input source is serialized and is the only injector used by these tests. Other concurrent QMP input injectors are outside this guarantee. Guest consumption can replenish descriptors. Unexpected reset/service death is handled separately by generation/endpoint validation and cancellation; a failed cancel marks the source unsynchronized and requires a fresh guest input session. The viewer never reports `released=true` after an unconfirmed cancel.

The browser has a 64-entry queue, coalesces only consecutive movement of the same contact, and preserves begin/end edges. The localhost bridge checks token, Origin, body size, contact bounds, source handle, sequence and transaction validity before issuing QMP. Invalid multi-contact transactions emit zero device commands. No arbitrary QMP or guest-memory write endpoint is exposed.

**Cancellation distinction:** QEMU maps both QMP `end` and `cancel` to tracking ID -1. The guest cannot infer which host reason caused that raw release. Browser touchCancel is tested as ending the contacts. Separately, killing/restarting the actual native input process generates an authenticated Mach endpoint death; the shell explicitly cancels its previously captured contacts in the WM. This second path verifies genuine service-loss cancellation, rather than claiming the virtual hardware encodes a distinction it lacks.

## Ownership and focus

The touch service sends a bounded `DT_MSG` containing the report and its endpoint capability. The shell checks the audited PID/version and exact input executable path, retains the capability, validates generation and monotonic frame continuity, and accepts events only from that connection. It tracks partially delivered contacts so a failed forwarding operation can cancel what the WM already received.

The WM selects a target on contact down and captures it until release/cancel. Focus changes do not retarget held contacts. Separate contacts can move and resize distinct windows simultaneously; conflicting geometry captures on one window do not fight each other. Backgrounding cancels a window's captures. Client termination detaches captures without delivering a late release to a restarted process. Each application receives only its own targeted events. These controls augment the existing compositor ownership rules, not a fabricated Apple-private IOKit interface.

## Test commands and evidence

Use `DUCHAMP_DARWIN_APP_LIFECYCLE.md` for the source-linked kernel hash, build commands and normal application launcher. Exact command arrays, logs, exit codes and output digests live outside Git under `../../outputs/duchamp-app-multitouch-20261118/`.

```sh
python3 -B tools/test-duchamp-touch-host.py
python3 -B tools/test-duchamp-live-input-host.py
python3 -B tools/test-qemu-frame-witness.py
python3 -B tools/test-qemu-touch-profile.py <verified-pointer-payload>
python3 -B tools/test-qemu-pointer-profile.py <default-dual-RAMDisk-payload>
```

Targeted results: touch parser **71** ASan/UBSan assertions; application/capture core **42**; prior pointer **33** and WM **53**. Host touch **15/15**, prior host mouse **9/9**, strict touch profile **11/11**, pointer profile **10/10**, passive frame observer **13/13**, default dual-RAMDisk packaging **12/12**. Explicit touch mode allows sixteen observation slots for twelve phases; the ordinary eight-observation limit remains unchanged.

Final queue-guard results: `attempt-7/verification.json` **35/35**, twelve full observed frame crops and actual source-built-XNU processes; `attempt-7/host-input/verification.json` **14/14**. Normal `browser-5/verification.json` **18/18**, with twelve crops and `native-postflight/verification.json` **15/15**. Queue journal entries confirm at least the required capacity before every submitted report. The final manifest links all regressions; failure receipts are retained. Tests distinguish direct QMP-generated virtual-device input, browser-generated virtual-device input and the older explicitly synthetic Mach GUI test.

## Limits and next milestone

The display is a small original test shell. There is no gesture recognizer, palm rejection, pressure, orientation or physical touch controller driver in this path. End-to-end testing covers two simultaneous contacts; eleven is a validated protocol bound, not a measured eleven-finger result. Only one contact marker is painted even when multiple contacts are active. The next independent step is gesture recognition and per-contact feedback on top of this proven transport. Native boot, modem/DMA ownership and physical memory safety require separate evidence and remain blocked.
