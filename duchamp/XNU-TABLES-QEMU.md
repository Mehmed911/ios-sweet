# XNU integration, ARM_V7S tables and the UFS route audit

This milestone links eight MT6897 backend/table C modules and a guarded
selftest adapter into XNU. The new selftest exercises private RAM register
models through real XNU allocation, cache, clock, mutex and devfs APIs.
It does not install a physical MT6897 backend. The raw SMC assembler is not
staged into XNU, and the table addresses are never sent to phone hardware.

## Source profile and table format

The Android reference is commit
[`498f91c17b0822a09aede17d26a63bf8c6813725`](https://github.com/aosp-mirror/kernel_common/tree/498f91c17b0822a09aede17d26a63bf8c6813725).
It supplies a source/format profile, not proof of the installed phone GKI.
The exact
[`io-pgtable-arm-v7s.c`](https://github.com/aosp-mirror/kernel_common/blob/498f91c17b0822a09aede17d26a63bf8c6813725/drivers/iommu/io-pgtable-arm-v7s.c)
Git blob is `08ec39111e608f6405a5777889d6ac2eda561506`, SHA-256
`d5af4ac2b0f8156c32ea2e9221d84fb9cb5bef44efb5e36655cde73ce30abd83`.

`drivers/mt6897_v7s.c` builds offline 4-KiB mappings with IAS 34, OAS 35 and
ARM_NS / NO_PERMS / MTK_EXT / MTK_TTBR_EXT. The root has 16384 entries and
needs a 64-KiB-aligned physical address. Each L2 has 256 entries and needs
1024-byte physical alignment. CPU pointers and physical addresses are
separate inputs; both sets are checked for overlap and overflow.

An entire map request is checked for existing entries and L2 capacity before
any table bytes change. High PA bits use the source's MTK PTE extension bits;
the TTBR uses a different encoding: `(uint32_t)root_pa | (root_pa >> 32)`.
Sealing synchronizes used L2 bytes, orders them, synchronizes the root,
orders it and only then publishes the TTBR. Sync failure poisons the builder
and leaves the caller's output unchanged. There is no live unmap, replacement
or reclamation API. Allocations must remain reserved after publication or
failure until the platform proves no walker can access them.

NO_PERMS means these entries do not enforce read-only or execute restrictions.
The virtual disk's read-only policy comes from the host and transport.
Neither a sealed table nor a software translation proves hardware reachability,
client routing, SMI ownership or IOMMU fault handling. Mali's internal MMU is
separate from this display/MDP IOMMU format.

## What runs inside XNU

`tools/stage-duchamp-qemu-backends.py` runs after the existing virtual-UFS
stager. It copies 14 source/header files and adds nine C build entries. The
root-selection hook only calls `duchamp_qemu_backends_prepare()` for qufs0.
Without `sweet-qemu-backends=1` it returns immediately. With the flag it also
requires the exact fixture ADT firmware/compatible strings and the expected
Cortex-A76 MIDR before allocating anything. These are accidental-use guards,
not a cryptographic attestation of a machine.

The opt-in selftest performs these operations:

- Allocate permanent, contiguous root/L2/data buffers using XNU, resolve
  every physical page and validate contiguity. Map across the 4-GiB IOVA
  boundary, software-walk a byte offset, reject overlap and seal the table
  using XNU physical cache cleaning and architectural barriers.
- Install that encoded TTBR into a private IOMMU register model and invalidate
  its modeled TLB. Refuse the unverified UFS client before any modeled I/O.
- Exercise PMIF/PMIC encoders with an XNU mutex, clock and delay provider.
  Verify protected VEMC relocking and the selected vbuck3 fields in RAM.
- Require a zero firmware reply without a verified contract to fail, preserve
  caller output, and require unauthorized power/clock/unknown-DMA providers
  to return without touching their I/O callbacks.
- Publish a read-only `/dev/mbtest` receipt after all checks succeed. A
  diagnostic PID 1 reads and compares it, verifies EOF and requires a writable
  open to fail with EROFS.

The receipt is:

```text
DUCHAMP XNU BACKENDS PASS tables=1 mmu=1 pmic=1 fw_verified=0 physical=0
```

`mmu=1` reports the register-model test, not a physical IOMMU table walk.
Actual virtual-disk reads continue through QEMU PCI UFS and the established
read-only transport; QEMU's UFS controller does not use these MTK tables.
The selftest does not program MT6897 power, clocks, PMIF, UFS or SMI hardware.

The allocation adapter supplies separate XNU virtual-address and physical
page-number alignment masks. Source inspection of kmem_alloc_contig_guard
showed that its VA mask alone does not constrain physical alignment. Follow-up
commit `d51e7dbc207a99a5efa60b12cce83b0d49f7d2ce` requests the physical mask and
a 35-bit maximum page number, then checks the returned PA alignment and range.
The pre-fix kernel built successfully but its guest selftest failed with EIO
before publishing tables. A read-only stopped-guest monitor reproduction
confirmed root VA `0xfffffe78672a0000` but root PA `0x1c281c000` (low 16 bits
`0xc000`). The table context was still fresh. Those failed results remain in
`guest-ci107-v1` and `guest-ci107-diagnostic`, with the diagnosis recorded in
`research/mt6897-xnu/ci107-alignment-diagnosis.json`; they are not pass evidence.

## UFS DMA and firmware evidence

`tools/audit-duchamp-ufs-contract.py` accepts only the previously captured DTB
SHA-256 `9c49589f70044127be8941a9ea5537977f440ccd5ac15cfd24e120c8a1181d29`.
It also checks exact Git blob IDs for the three source files below before
interpreting their control flow:

| Source at the Android reference commit | Git blob |
| --- | --- |
| [drivers/of/device.c](https://github.com/aosp-mirror/kernel_common/blob/498f91c17b0822a09aede17d26a63bf8c6813725/drivers/of/device.c) | `91d92bfe57359d9bfa7a361718ef571e04539d53` |
| [drivers/iommu/of_iommu.c](https://github.com/aosp-mirror/kernel_common/blob/498f91c17b0822a09aede17d26a63bf8c6813725/drivers/iommu/of_iommu.c) | `3ad1461dc94fa0d47daafa619035d5fb7ee917a4` |
| [arch/arm64/mm/dma-mapping.c](https://github.com/aosp-mirror/kernel_common/blob/498f91c17b0822a09aede17d26a63bf8c6813725/arch/arm64/mm/dma-mapping.c) | `f011f4c2c968e6ed87c2f75b55d6d50be24f4ace` |

The captured `/soc/ufshci@112b0000` has no `iommus` property; its inspected
ancestry has no `iommu-map`. `/soc/dma-ranges` describes a 64-GiB window from
device address zero to CPU address zero. The source follows
of_dma_configure -> of_iommu_configure -> arch_setup_dma_ops. A pre-existing
iommu_fwspec can override absent DT properties; runtime platform notifiers,
vendor hooks and Xen/secure configuration require separate verification.

This yields a **bus-window/direct-DMA candidate**, conditional on a matching
installed GKI, no overriding configuration, a verified effective controller
address mask and the cache/ownership contract. It does not select
MD_VERIFIED_BUS_WINDOW. There is no evidence here authorizing the display,
MDP or APU IOMMU as the UFS route. The physical DMA route remains unverified.

The audit also rehashes saved `lk_a.bin` and `preloader_raw_a.bin`. They are
LK/preloader evidence, not a matched BL31/secure-monitor implementation.
Installed firmware contract verification still needs the matched monitor and
build configuration, return/effect semantics for each UFS service and trusted
resource/PHY ownership evidence. A successful raw SMC instruction test with a
purpose-built EL3 monitor, documented in [MT6897-BACKENDS.md](MT6897-BACKENDS.md),
does not supply that contract. Zero alone is deliberately not accepted.

## Validation record

- `research/mt6897-xnu/tables-v2/result.json`: 11476 native ASan/UBSan checks
  passed against six unchanged upstream encoding/decode/install function
  bodies. Allocator/cache/atomic helpers are fixture stubs; no hardware walker.
- `research/mt6897-xnu/compile-v3`: all nine C translation units compiled
  against actual generated XNU headers. The separate staging/import check
  passed six checks, and eight staging unit tests passed.
- `research/mt6897-xnu/contract-v2/result.json`: source blobs and saved DTB/
  firmware hashes matched; physical DMA route and installed firmware contract
  are explicitly unverified. Deliberately changed copies of each of the three
  reference source files were rejected by their Git-blob checks.
- Corrected full build: [Actions run 41142122133](https://github.com/Mehmed911/ios-sweet/actions/runs/41142122133),
  source commit `d51e7dbc207a99a5efa60b12cce83b0d49f7d2ce`: success.
  It ran on a temporary test branch so that the first build was not cancelled.
  Kernel artifact ID `13019712695`; ZIP SHA-256
  `4dfb5b7194e18c3e2f4185e91ed5457a44c071cf09ede0eaf53c609367a8ac80`.
  The archive digest matched GitHub and the extracted kernel matched SHA256SUMS:
  `fdbbca3def13fddcbef77d01504aeaabe41bfb3a7b7df94b4d7fd03fd015b92d`.
  Both corrected guest tests below passed with this exact kernel.

| Corrected kernel guest | Result | Host seconds | Sampled frames |
| --- | --- | ---: | ---: |
| `research/mt6897-xnu/guest-backends-v1/verification.json`, opt-in selftest | 24/24, exit 0 | 81.580 | 16 |
| `research/mt6897-xnu/guest-baseline-v1/verification.json`, ordinary qufs0 | 20/20, exit 0 | 81.570 | 16 |

All backend checkpoints were observed: synchronized tables, modeled IOMMU
with UFS refused, PMIF/PMIC locking, unknown firmware reply refused and closed
physical providers. PID 1 read the exact receipt, EOF and EROFS checks passed,
and the existing raw UFS/offset/EFAULT/HFS-content/heartbeat tests passed.
After stopping the positive guest, read-only physical monitor reads of
symbol locations independently confirmed root PA `0x1c2830000`, L2-pool PA
`0x1c2840000` and data PA `0x1c2844000`. The root was 64-KiB aligned and within
35 bits. The monitor reads do not depend on the CPU's current exception level.

Both runs had zero unknown glyphs, no observed panic, unchanged kernel and
host-image hashes, unchanged test-source hashes, read-only backing files and
no RAMDisk. Framebuffer observations are sampled, not a complete event log;
root-device identity and file/receipt comparisons are also checked by PID 1.
The working runner retains the user's pre-existing MEMORY READY classifier
change; its exact hash is recorded in both reports. That branch is not the
success condition used here and was not included in this milestone's commits.

The first table-test attempt failed in the reference-function extractor before
C tests ran; that log is retained. The first new guest fixture had an incorrect
init-source metadata field caused by a reused Python variable. The builder
was corrected and a fresh v2 fixture was created; v1 is not pass evidence.

Replay into fresh output directories, using only existing saved files:

```sh
python3 tools/test-mt6897-v7s.py research/table-check-new \
  --reference research/mt6897-xnu/sources/io-pgtable-arm-v7s.c
python3 tools/audit-duchamp-ufs-contract.py research/contract-check-new \
  --fdt ../phone-fdt.bin --gki-sources research/mt6897-xnu/sources \
  --firmware-dir ../phone-firmware
python3 tools/build-duchamp-ufs-fixture.py research/backend-fixture-new \
  --base-root work/qemu-rootvnode-98/root-with-launchd.hfs \
  --adt work/qemu-multiproc.adt --hfsplus research/libdmg-hfsplus-build/hfsplus \
  --init-source tools/duchamp-backend-init.S
python3 tools/test-duchamp-ufs-xnu.py --backends \
  --kernel "$KERNEL" --kernel-sha256 "$KERNEL_SHA256" \
  --fixture research/backend-fixture-new --output research/backend-guest-new \
  --ci-run 41142122133 --ci-head d51e7dbc207a99a5efa60b12cce83b0d49f7d2ce
```

Next physical work requires resolving those specific evidence gaps before
installing a DMA route or invoking firmware. No phone, USB, ADB, fastboot or
boot-partition operation is part of this milestone.
