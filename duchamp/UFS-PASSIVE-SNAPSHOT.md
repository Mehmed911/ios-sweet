# Passive MT6897 UFS register snapshot

`drivers/ufs_register_snapshot.c` implements a bounded read-only observer for
UFSHCI and all eight advertised MCQ queues. It can supply observations to a
future physical provider. It does not initialize the controller, grant resource
ownership, allocate DMA memory, follow inherited queue addresses, issue SMCs or
send storage commands. The physical root selector remains disabled.

## Source and layout

The saved Duchamp FDT has SHA-256
`9c49589f70044127be8941a9ea5537977f440ccd5ac15cfd24e120c8a1181d29`.
Its UFS register window is `0x112b0000..0x112b2fff`, with one host interrupt and
eight MCQ interrupts. `tools/mt6897_ufs_model.py` checks that FDT and the three
pinned Xiaomi source blobs before the snapshot tests run.

Xiaomi commit `3c4ccd07d5624879555ec710c11bb8818e5cb5c6` defines the runtime
register offsets as SQD `0x2800`, SQIS `0x2814`, CQD `0x281c`, CQIS `0x2824`,
with a `0x30` stride. Its `ufs_mtk_op_runtime_config()` installs those offsets.
Its `ufs_mtk_mcq_config_resource()` derives the queue configuration base from
MCQCAP QCFGPTR, using `((MCQCAP >> 16) & 255) * 0x200` and a `0x40` queue stride.
The observer uses that checked dynamic base, bounds it below the runtime window,
and refuses a queue count exceeding eight.

Sources: [Xiaomi register definitions](https://github.com/MiCode/MTK_kernel_device_modules/blob/3c4ccd07d5624879555ec710c11bb8818e5cb5c6/drivers/ufs/ufs-mediatek.h),
[Xiaomi MCQ configuration](https://github.com/MiCode/MTK_kernel_device_modules/blob/3c4ccd07d5624879555ec710c11bb8818e5cb5c6/drivers/ufs/ufs-mediatek.c),
[QEMU v10.2.1 UFS implementation](https://github.com/qemu/qemu/blob/v10.2.1/hw/ufs/ufs.c).

QEMU has a separate runtime register base of `0x1000`. The shared header now
supplies those same constants to the existing QEMU MCQ transport. Rebuilding the
pinned transport-only replay gives its previous byte-identical Mach-O SHA-256
`5ed792c0052a6d791eb24dda3d87fd33c37bde4b98d41a3c480678658eb57a42`.

## Capture contract

The caller supplies an already accessible register reader and a permission
callback that checks the current boot identifier, aperture accessibility and
powered resource state. Permission is checked immediately before **every**
register read. Missing or revoked permission stops capture. A read failure or
invalid layout leaves the caller's output unchanged. Callbacks must return;
the observer cannot recover from a physical bus hang.
The reader must use ordered, non-destructive 32-bit device accesses. The QEMU
XNU reader uses a volatile load followed by `dsb ld`; it never acknowledges or
clears an interrupt while observing.

Two passes capture CAP, MCQCAP, VER, HCE, HCS, legacy transfer/task list bases,
doorbells and run bits, MCQ configuration, and each SQ/CQ's configuration,
base, head/tail and interrupt status. There are at most 316 register reads.
Invalid ring offsets, pending requests/completions, configured or enabled lists,
an enabled HCE, or a difference between the passes set refusal flags. The API
has no write, DMA or command callback. A successful return only means capture
completed; it does not mean permission to initialize or read storage.

Two equal samples cannot prove exclusive ownership or exclude activity between
the samples. In particular, a firmware request can finish between observations.
No captured state grants DMA translation, cache-maintenance rights, power/clock
ownership or an IRQ. The supplied boot ID is a correlation value whose origin
must be established independently, not an authentication token.

## Local verification on November 12

Run from the repository in WSL with the saved FDT and pinned Xiaomi files:

```sh
python3 -B tools/test-duchamp-ufs-register-snapshot.py \
  ../../outputs/duchamp-ufs-passive-snapshot-20261112 \
  --dtb ../phone-fdt.bin \
  --xiaomi-sources /home/mehmedamir/.cache/duchamp-xiaomi-ufs-A695BT
```

- All 30 register-array cases pass under host ASan/UBSan and ARM64 QEMU. They
  cover inherited legacy/MCQ state, pending SQ/CQ entries, queue seven, invalid
  pointers/apertures/counts, changed samples, missing permission and revocation.
- Read failures at each of the 316 capture positions leave output unchanged.
  Revocation at each of the 316 positions prevents that read and all later reads.
- The standalone ARM64 guest separately reads QEMU's actual PCI UFS device.
  It captures a cold device, then detects an inherited enabled MCQ pair. A
  mismatched boot identifier causes zero reads. PCI bus mastering stays off.
- The trace has 632 observer reads, zero observer writes and zero SCSI commands
  or completions. Exactly eight fixture writes construct the inherited queue
  pair **between** the two captures; the verifier checks their values and their
  exact position. JSON files preserve each first/last register sample.
- The production observer compiles as an Apple ARM64 Mach-O object. The XNU
  staging script includes its source/header in `bsd/dev` and the BSD build list.
  Staging tests reject pre-existing or modified observer files without edits.
  This first test suite uses a small standalone ARM64 harness. The separate
  full-kernel verification below executes the observer inside source-built XNU.

Evidence is under `outputs/duchamp-ufs-passive-snapshot-20261112` in the outer
workspace, including `verification.json`, `ufs.trace`, `native.log`, `qemu.log`,
the four register JSON captures, and `replay-regression/verification.json`.
The MT6897 register-array fixture is not a hardware emulator. The PCI test uses
QEMU's own layout, not a translated physical aperture.

## Physical integration still required

The reviewed XNU source implements `ml_probe_read()` and `ml_probe_read_64()`
as unconditional panics in `osfmk/arm64/loose_ends.c`. They must not be used as
a fault-tolerant phone reader. No unchecked physical dereference was added.

The QEMU root adapter now has a separate `sweet-qemu-ufs-snapshot=1` option.
It captures before allocating DMA or enabling PCI bus mastering. Capture errors
or nonzero refusal flags stop the virtual provider. Its boot-ID accessor uses
the existing synthetic QEMU handoff and logs once, with no per-read logging.
Full-source verification of this option passed as recorded below.

The subsequent read-provider/XNU mapping binding is documented in
[MT6897-UFS-OBSERVER-BINDING.md](MT6897-UFS-OBSERVER-BINDING.md). Its local
RAM-backed tests and real-header compilation are separate from this earlier
full-kernel milestone. The physical read authority is still absent.

Physical integration still needs a call from the real provider with a documented
readable/powered aperture and same-boot permission source. A phone capture requires a supported entry
and access contract. Before any physical storage command, separately establish
exclusive controller/queue ownership, resource ownership, PA-to-DMA translation
and the cache-maintenance owner. Evidence can come from a documented vendor
handoff or a verified initialization contract; this observer alone provides
neither. No phone commands, reboots, flashing or partition changes were made.

## Complete XNU build and execution

[Actions run 43301119194](https://github.com/Mehmed911/ios-sweet/actions/runs/43301119194)
succeeded at source `2d554f207c46f248da26b6d23bad97e3f74a8676` on the isolated ref
`codex/xnu-ufs-snapshot-20261112`. It verifies 319 input hashes and the pinned IIG
archive. The 16780440-byte complete kernel has SHA-256
`16616409bcca4ba4ea478f781e82267768f5ef457ffaebe886ae80f875014f50`.
Native disassembly confirms `qu_prepare -> qu_snapshot -> dufs_snapshot_registers`.
No kernel replay hooks or binary patches were used.

All seven MCQ cases passed on that kernel. With passive capture enabled, the
read-only GPT/HFS+ root reaches diagnostic PID 1 in 34.035 host seconds. The
same-boot marker in XNU's circular log reports 316 reads and zero refusal flags.
The first 316 traced operations are two identical 158-read samples, before any
HCI write. Normal boot then completes 33 MCQ requests, including 28 READ(16)
commands. PID 1 verifies its file and refuses write-open with EROFS. With the
snapshot option absent, the same kernel reaches PID 1 in 33.838 host seconds.
These durations describe QEMU host execution, not MT6897 timings.

An independent full-XNU test uses QTest to enable empty MCQ queues before XNU
starts, while the synthetic handoff claims cold queues. XNU records flags
`0x29` (enabled HCE, enabled MCQ and configured lists), refuses preparation and
stops after 316 reads with **zero HCI writes or SCSI commands**. An independent
PCI read after refusal is `2`: memory decoding is on and bus mastering is off.
The output block stays zero. The eight host fixture writes precede guest entry
and are retained separately from the guest-only trace.

The remaining cases verify out-of-pool DMA and missing SQ synchronization before
submission, a device-side DMA fault with one submission/no SCSI/bounded timeout,
and missing DMA/cache grants or an inherited-MCQ handoff with zero HCI traffic.
The read-only GPT image remains byte-identical. BL31 records and cache grants
are synthetic; no physical MT6897 resource, cache or DMA ownership is established.

`tools/test-duchamp-ufs-mcq-xnu.py --snapshot` checks the seven normal/fault cases;
`tools/test-duchamp-ufs-snapshot-xnu.py` checks the independent inherited device.
`tools/qemu_kernel_log.py` captures the stopped guest's circular log through QMP
`memsave`, so verification does not depend on whether a message remains visible
in the framebuffer. It changes no guest memory or existing interactive session.

The local container template is derived from the SHA-256-verified previous QEMU
image, padded to 64 MiB, as recorded in `qemu-template.json`. It is a QEMU-only
header fixture, not an installed phone Slot B backup or a flashable image.

The complete evidence archive is
`outputs/duchamp-ufs-snapshot-xnu-full-20261112` in the outer workspace. It has
95 hashed files plus `archive.json`, the seven case results, full XNU
logs, independent controller trace and `pid1.png`. The million-entry injected
DMA-fault trace is gzip-compressed, with its original digest retained.
CI preparation, selected kernel and reproduction helpers are in
`work/ci-xnu-ufs-snapshot-20261112`. No phone was accessed.
