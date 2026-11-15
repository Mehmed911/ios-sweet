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
turn a file or a boolean into physical authority. No physical authority is registered or
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
an empty trace. That initial standalone milestone did not rebuild a full kernel;
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

## Complete-XNU integration fixture

`xnu/qemu_ufs_observer.c` is a separate, opt-in emulator test. It calls the
production adapter without `MT6897_UFS_OBSERVER_XNU_TEST` or a mapper shim. The
ordinary `duchamp_qemu_backends_prepare()` path checks this test before opening
the virtual root device. With its option absent, it returns without mapping.

Before touching even virtual PCI configuration, the test requires Cortex-A76,
the existing QEMU firmware tag, a dedicated `qemu,mt6897-register-bank-v1` ADT
node, and the current ID of an accepted **synthetic** handoff. Scenario arguments
select only this emulator test; they cannot enable a physical authority.

The fixture attaches QEMU `ivshmem-plain` at PCI 05.0. It checks its device ID,
initial disabled state and 16 KiB BAR2 size, then places the RAM bank at
`0x112b0000` with PCI command 2 (memory decode, bus mastering disabled). Those
are virtual PCI configuration writes, not UFS controller writes. The bank
contains pinned MT6897-shaped offsets, including runtime `0x2800` and eight
queues. It does **not** emulate power, firmware, DMA, cache visibility or UFS
register side effects. See [QEMU ivshmem documentation](https://www.qemu.org/docs/master/system/devices/ivshmem.html).

Capture uses the real `ml_io_map_with_prot(..., VM_PROT_READ)`. EL1 `AT S1E1R`
and `AT S1E1W` queries check the resulting mapping without issuing a store.
The short permission-check section saves/restores DAIF and PAR_EL1. Successful
read translation must resolve to the bank; write translation must fault.
Every bank file is hashed before/after the run.

`tools/test-duchamp-ufs-observer-xnu.py` requires a complete-kernel checksum
and CI provenance; it never inserts replay hooks. It exercises cold capture,
disabled/wrong-boot/incomplete authority, revocation before map/during reads/
before publication, inherited pending queue 7, a wrong emulator device profile,
and the default-off root regression. Only the cold and default-off fixtures may
continue to the **separate** virtual UFS controller and its read-only GPT root.
Other cases must leave that controller's entire trace empty. The diagnostic
stop after an expected rejection is intentional, not a successful root boot.

This test proves software integration and virtual page protection only. An
internal read-access/power-pinned authority valid at the real XNU entry is still
required before physical register capture; a snapshot alone additionally
cannot grant exclusive storage/DMA/cache ownership.

### Verified complete build and execution (2026-11-14)

macOS Actions [43631086106](https://github.com/Mehmed911/ios-sweet/actions/runs/43631086106)
succeeded from isolated source `7726168b844c7e00e24039cd93b8d0f4ed9a5e2d`
on `codex/xnu-ufs-observer-full-20261114`, with 324 verified inputs. This is the
previous successful snapshot baseline plus the binding/test sources; unrelated
working-tree edits were not copied into CI. The complete 16781120-byte kernel is
SHA-256 `c6ebb7330ad393f19637f759b2ee35b0e4b2e66ae4f22b7cfde90c3f64ade4f3`.
Artifact source/manifest/checksums and native caller-to-adapter-to-mapper edges
were verified. No replay hooks or locally patched kernel were used.

All eleven guest executions pass:

| Case | Maps / observer loads | Outcome before the separate virtual UFS |
| --- | --- | --- |
| Cold | 1 / 316 | Eight empty queues; continue to read-only GPT/HFS+ and diagnostic PID 1 in 34.122 host seconds |
| Observer disabled, wrong boot, missing power, missing bus clocks | 0 / 0 | Unchanged output; stop |
| Revoked before map | 0 / 0 | Unchanged output; stop |
| Revoked during reads | 1 / 98 | Unchanged output; stop |
| Revoked before publication | 1 / 316 | Unchanged output; stop |
| Inherited pending queue 7 | 1 / 316 | SQ head/tail 0/32, refusal flags `0x39`; stop |
| Wrong emulator device profile | No observer invocation | Stop before virtual PCI setup |
| Default option absent | No observer invocation | Read-only GPT/HFS+ diagnostic PID 1 in 34.161 host seconds |

All nine stopped cases have an entirely empty virtual-UFS trace. All register
banks and the GPT disk stay byte-identical. The four cases that create a mapping
pass real EL1 translation checks: read PAR `0x112b0b00` resolves to `0x112b0000`,
while write PAR `0x81f` reports a permission fault. This did not attempt a store.
Both root boots verify file bytes and `EROFS` on write-open.

The initial host checker required an early framebuffer-only handoff mark that
had scrolled away in the denial cases. Its assertion failed while XNU's own
observer tests reported success. The checker now validates each observer's
kernel-log boot ID against the exact synthetic mailbox. That ID comes from the
handoff getter, which returns nonzero only for an accepted matching record.
The old paired-ID mark is also checked when present. Saved-execution checking
reconstructs and compares payload bytes, ADT, mailbox and register bank, rather
than changing or restarting the guest. The wrong-profile case proves refusal,
and does not claim an accepted observer grant. No kernel change was needed.
Fresh end-to-end cold and disabled reruns also passed after the host correction;
the new positive run reached PID 1 in 34.084 seconds. Both the original checker
failure and the successful rechecks/reruns are retained.

Evidence, native disassembly, all guest logs/traces and source/CI receipts are in
the outer workspace's `outputs/duchamp-ufs-observer-xnu-full-20261114`.
`verification.json` identifies the actual complete kernel and synthetic
authority; `archive.json` hashes the evidence. Private preparation/download/
reproduction helpers and the selected artifact are under
`work/ci-xnu-ufs-observer-full-20261114`.

This adds no physical grant producer, phone action, reboot, slot change, flashing
or partition write. The next physical step still requires a verified same-boot
read-access and stable-resource contract at XNU entry. Cold QEMU bytes do not
prove that the real controller is idle, powered, accessible or delegated.

## Live Slot A check and Slot B decision (2026-11-15)

ADB identified Duchamp / MT6897 on Android Slot A. The slot and hashed Android
boot ID matched before and after capture. Linux reported the UFS host
(`ufshcd-mtk`) and PHY (`ufs_mtk_phy`) as runtime-active.

ATF's 128 KiB runtime snapshot and bounded 2 MiB raw export identified BL31
`lts-v2.8.6(release):2fbca47`. The PL/LK export had 142 UFS mentions. Both
pstore entries (`console-ramoops-0`, `pmsg-ramoops-0`) were readable. The
scanned ASCII and UTF-16LE bytes contained no correlated Slot B / XNU entry,
read grant, or resource pin record. The published ATF readers copy existing
debug RAM. They do not take a live UFS register sample.
[MiCode ATF reader](https://github.com/MiCode/MTK_kernel_device_modules/blob/3c4ccd07d5624879555ec710c11bb8818e5cb5c6/drivers/misc/mediatek/atf/tfa_debug.c#L175-L227)

The archived LK analysis shows an attempted UFS shutdown in the final cleanup
path, with no HCE readback on that path. It supplies no hardware observation
at XNU entry. The saved FDT fixes the physical aperture at `0x112b0000` /
`0x3000`. The Android driver manages UFS and PHY power during its own runtime
PM lifecycle. Physical read permission and the duration of power and bus-clock
availability at a Slot B XNU entry remain unproven.
[LK handoff audit](MT6897-LK-HANDOFF-CONTRACT.md),
[MiCode UFS driver](https://github.com/MiCode/MTK_kernel_device_modules/blob/3c4ccd07d5624879555ec710c11bb8818e5cb5c6/drivers/ufs/ufs-mediatek.c)

Before connecting the observer to the phone path, obtain a supported record
or verified platform initialization tied to the same Slot B XNU entry. It
must cover safe non-secure reads of the selected aperture and power/bus-clock
pins through reset for the current permanent mapping. The observer can then
measure queue state. Any future UFS command additionally requires separate
ownership, DMA and cache evidence.

The live report, source hashes, host capture helper and local recheck are in
the outer workspace's `outputs/duchamp-slot-b-ufs-read-authority-20261115`.
ADB accessed existing log and status files only. There was no reboot, slot
change, partition write, or physical UFS register access.
