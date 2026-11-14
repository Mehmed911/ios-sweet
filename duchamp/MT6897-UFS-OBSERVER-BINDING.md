# MT6897 read-only UFS observer binding

This binds the passive register snapshot to an MT6897 provider and supplies an
XNU mapping/reading adapter. It does not implement a UFS transport. The physical
root selector and all DMA, cache-maintenance, power, clock, reset, PHY and command
paths remain unchanged and disabled by default.

## What the saved evidence establishes

| Evidence | Established | Not established |
| --- | --- | --- |
| Pinned final Duchamp FDT | HCI base `0x112b0000`, extent `0x3000`, eight MCQ IRQs | Accessibility or power at a later XNU entry |
| Pinned Xiaomi UFS source | MCQ runtime base `0x2800`, queue stride `0x30`; Linux initialization and resume have explicit clock/PHY/power dependencies | Firmware leaves those resources pinned for XNU |
| Saved Android A resource capture | Linux owns the HCI and PHY; both were active at that capture; XNU delegation is unproven | Same-boot XNU read permission, stable clocks/power or firewall permission |
| XNU mapping API | `ml_io_map_with_prot()` maps Device memory with the requested protection | Device power, firmware permission or fault recovery |

The FDT digest is
`9c49589f70044127be8941a9ea5537977f440ccd5ac15cfd24e120c8a1181d29`.
The tests verify this and all three Xiaomi source blobs at commit
`3c4ccd07d5624879555ec710c11bb8818e5cb5c6` before building.

Xiaomi's `ufs_mtk_init()` documents that the common clock setup precedes variant
initialization, and performs PHY/power and further clock setup. Its runtime
resume reacquires PHY runtime-PM state and resumes UFS. Thus a saved `active`
value under Linux is not a boot-lifetime power guarantee. This review found no
same-boot XNU read-grant producer in the saved evidence. It does not establish
that hardware denies access; it leaves access unverified.

Sources: [Xiaomi initialization and runtime-PM implementation](https://github.com/MiCode/MTK_kernel_device_modules/blob/3c4ccd07d5624879555ec710c11bb8818e5cb5c6/drivers/ufs/ufs-mediatek.c),
[Xiaomi register definitions](https://github.com/MiCode/MTK_kernel_device_modules/blob/3c4ccd07d5624879555ec710c11bb8818e5cb5c6/drivers/ufs/ufs-mediatek.h),
[Apple ARM64 mapping and nofault code](https://github.com/apple-oss-distributions/xnu/blob/xnu-8796.141.3/osfmk/arm64/machine_routines.c).

## Implemented interface

- `drivers/mt6897_ufs_observer.c/h` owns a one-shot read binding, with a distinct
  read-access grant. Observation does not require or create a storage/DMA/cache
  activation lease. It can capture an active inherited controller and report
  its refusal flags without altering that controller.
- `xnu/mt6897_ufs_observer_xnu.c/h` provides the actual XNU adapter. Its mapper
  calls `ml_io_map_with_prot(base, size, VM_PROT_READ)`. Its reader issues bounded
  volatile 32-bit loads followed by `dsb ld`. It has no device-write, SMC, DMA,
  interrupt-acknowledgement or UFS-command callback.
- The BSD staging list includes the four new files. The workflow compares the
  staged adapter source/header against the repository inputs.

Registration is an explicit internal C call to
`mt6897_ufs_xnu_observer_bind()`, followed by
`mt6897_ufs_observer_capture()`. There is no boot-argument or ADT parser that can
turn a file or a boolean into authority. No physical authority is registered or
automatically invoked by this change. A zero-initialized object returns
`MUO_DISABLED` before any mapping or read.

The trusted platform authority must independently validate the current Duchamp
identity/resource layout and return a versioned grant for that exact boot,
owner, grant ID, resource epoch and HCI aperture. All six assertions are required:
the complete register window is readable, its power is stable, bus clocks are
pinned, non-secure reads are allowed, those resource pins remain until reset,
and the selected register reads are non-destructive. These are **internal
provider requirements**, not a discovered Xiaomi/MediaTek firmware ABI and not
proof created by the observer. The authority callbacks must validate an already
established contract; they must not probe, power or reconfigure hardware.

The producer must obtain that contract from verified initialization or a
documented handoff valid at this XNU entry. The saved Android report is never
converted into such a grant. DMA translation, system-cache maintenance and
exclusive storage ownership are separate prerequisites for a future command.

## Capture and revocation

Binding performs no callbacks. Capture verifies the grant and rechecks it
before authorizing the first mapping. Each read is revalidated and has an
atomic dispatch point. Concurrent capture and rebinding are rejected.

Revocation that wins a dispatch point prevents the operation. An already
authorized mapping or read may finish, so resource pins must remain valid.
Revocation that wins the final publication CAS discards all collected data.
Mapping failures, access failures and invalid register layouts latch a fault;
there is no retry/reset API. Output stays unchanged on failure.

The mapping is permanent, including on capture failure. The adapter is intended
for one-shot bring-up diagnostics with power/access pins until reset, not for a
production power-management lifecycle. `io_map()` supports early mappings once
bootstrap virtual memory is ready. This code does not add a call at the first
CPU instruction or claim a firmware-boundary capture.

`ml_probe_read()`/`ml_probe_read_64()` in the reviewed XNU source panic. The
`ml_nofault_copy()` implementation validates physical RAM pages and does not
provide device-abort recovery. Neither is used here. A volatile load can still
abort or hang if the platform violates the access/power contract; creating a
read-only virtual mapping cannot fix that. Such access remains disabled.

BSD's exported machine header omits the private mapper prototype; the adapter's
explicit declaration matches its full ARM64 header/implementation. The symbol
also exists in the previously verified complete XNU kernel.

## Local results

`tools/test-duchamp-ufs-observer-binding.py` passes:

- 25 cases on host ASan/UBSan and standalone ARM64 QEMU, including cold and
  active inherited MCQ captures, missing/old/incomplete grants, wrong apertures,
  malformed mappings, missing authority and repeated/concurrent calls.
- Authority denial at each of 318 validation points and revocation at each of
  those 318 points. No later read occurs; failed output is unchanged.
- Four deterministic pthread races: before mapping, during an authorized map,
  during an authorized load, and after all 316 reads before publication. An
  in-flight load may finish once and its result is discarded.
- Both new source files compile as Apple ARM64 objects with the real XNU BSD
  command/header configuration. The adapter imports only
  `ml_io_map_with_prot` and the read-provider bind function. It imports no SMC,
  DMA/cache or storage executor.
- Ten backend staging tests, nine UFS staging tests and 29 profile checks pass.
  Pre-existing or modified observer files are refused without edits.

The executable tests supply **synthetic grants and a RAM-backed mapping shim**.
They exercise the adapter's real ARM64 loads/barriers and assert a
`VM_PROT_READ` mapping request; they do not test physical MMU protection or
MT6897 MMIO. A separate QEMU PCI UFS device remains completely untouched, with
an empty trace. No new complete kernel was rebuilt or booted for this binding;
the earlier complete-kernel snapshot milestone is recorded separately in
[UFS-PASSIVE-SNAPSHOT.md](UFS-PASSIVE-SNAPSHOT.md).

Reproduce from the repository in WSL:

```sh
python3 -B tools/test-duchamp-ufs-observer-binding.py \
  ../../outputs/duchamp-ufs-observer-binding-20261114 \
  --dtb ../phone-fdt.bin \
  --xiaomi-sources /home/mehmedamir/.cache/duchamp-xiaomi-ufs-A695BT \
  --resource-bindings ../../outputs/duchamp-physical-ufs-20261112-v2/resource-bindings.json \
  --xnu-buildtree /home/mehmedamir/.cache/ios-sweet-xnu-ufs/base104-o4phjpsj \
  --xnu-log work/ci-xnu-ufs-snapshot-20261112/baseline-ci.log
```

Evidence is in `outputs/duchamp-ufs-observer-binding-20261114` in the outer
workspace, including `verification.json`, native/QEMU/race logs, the empty UFS
trace and the two real-header object/import reports. The report explicitly
records `xnu_read_grant_proven=false` and `physical_capture_allowed=false`.

No phone commands, reboots, slot changes, flashing, partition modifications or
physical register reads were performed. Actual queue capture remains pending a
trusted, same-boot, access/power-pinned producer; success of a RAM model cannot
supply it.
