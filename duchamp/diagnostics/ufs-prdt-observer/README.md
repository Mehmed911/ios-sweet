# Duchamp passive UFS PRDT observer

This diagnostic module is a separate, more sensitive follow-up to the proven
DMA/IOMMU contract probe. It registers the Android vendor hook
`android_vh_ufs_fill_prdt`, which the pinned UFS core invokes after
`scsi_dma_map()` and after filling the UFS PRDT.

For existing UFS commands only, it counts:

- whether each PRDT address and length equals the mapped scatterlist entry;
- under a separately verified dma-direct/no-IOMMU contract, whether
  `dma_to_phys()` returns the original scatterlist physical address;
- whether the translated physical address belongs to the device SWIOTLB pool;
- whether any complete DMA extent crosses 4 GiB or the measured 36-bit bus
  limit;
- bounded minimum and maximum DMA, translated-physical and original-physical
  extents.

The single sysfs report is root-read-only (`0400`). The observer does not issue
storage commands, allocate or map DMA, read or write MMIO, invoke SMC, attach
an IOMMU domain, change clocks or power, or modify the hook's `err` result. It
does register a live kernel callback, so loading it changes the running kernel.

Do not copy or load a build on the phone without a fresh explicit approval,
an exact ABI/static-verification receipt, a documented unload procedure, and a
normal-Android recovery path. A successful local build proves only the module
artifact; it does not prove physical DMA behavior or safe XNU UFS access.

Pinned source contract:

- target kernel release:
  `6.1.57-android14-11-gcf2c2dc91b9e-ab11782407`;
- GKI source commit:
  `cf2c2dc91b9e9f016dc25cf095b1fe34cb5dfcb6`;
- vendor device-module source commit:
  `a805f95d61dbf0b2959c9262acc626893114321d`.

The GKI hook signature is
`(struct ufs_hba *, struct ufshcd_lrb *, unsigned int, int *)`. The vendor UFS
source at the pinned commit calls the hook immediately after filling the PRDT;
it does not register a competing `ufs_fill_prdt` callback.

## Verified offline artifact

The corrected offline artifact is:

- file:
  `work/duchamp-ufs-prdt-observer-local-only/artifact-v5/duchamp_ufs_prdt_observer.ko`;
- size: `407280` bytes;
- SHA-256:
  `fb5b1a887bced8e4b0fbf498ebafc21d4856b4f57bbf2795f1d469bd8c9984c3`;
- verification receipt:
  `work/duchamp-ufs-prdt-observer-local-only/verification-v6/verification.json`.

Static verification passed against all 18 imported symbol CRCs, Android Clang
17.0.2, the exact captured vermagic, a `0x440`-byte `struct module`, and init
and exit relocations at `0x170` and `0x3d8`. No module signature is appended.
This proves the local artifact contract only. A separately approved live run
of this exact artifact completed on 2026-11-01; see
`PHONE-TEST-2026-11-01.md` for the runtime result and its limits.

## Approved live capture and rerun procedure

`tools/capture-duchamp-ufs-prdt-observer.py` is the only supported live runner.
It fails closed unless the device, SoC, kernel, source hash, artifact hash,
static receipt, installed UFS module Build ID, root state and battery floor all
match. Its approval token includes the complete artifact SHA-256. It also refuses to run
while the old `sweet_ufs_probe_v1` tracefs instance exists. That instance must
be cleared by a separately approved normal Android reboot; the runner never
reboots the phone itself.

The runner stages the exact module under `/data/local/tmp`, verifies its hash,
loads it, reads a fixed allowlist of regular system files into `/dev/null`,
captures the root-only report twice, unloads the module, removes the staged
file, and verifies the boot ID, kernel taint, sysfs cleanup and new kernel-log
lines. The kernel observer takes a coherent statistics snapshot and waits for
in-flight trace callbacks before unloading. It never flashes, accesses a partition, changes SELinux or tracefs,
drops caches, invokes firmware, or performs MMIO. A fresh explicit approval is
required before running it because loading the module changes the live kernel.

The approved 2026-11-01 run passed. Its bounded workload added 371 read
commands and 17,437 segments. Every PRDT address and length matched the mapped
scatterlist, every `dma_to_phys()` result matched the original physical
address, no SWIOTLB segment was observed, and every extent remained below the
live 36-bit bus limit. The module unloaded, its staged file disappeared, the
boot ID and kernel taint stayed unchanged, and no new kernel fault line was
found. The result is preserved under
`research/mt6897-dma-ownership/prdt-observation-20261101-v1/`.

Example command to use only after that approval:

```powershell
python tools/capture-duchamp-ufs-prdt-observer.py `
  --adb C:\platform-tools-latest-windows\platform-tools\adb.exe `
  --module work\duchamp-ufs-prdt-observer-local-only\artifact-v5\duchamp_ufs_prdt_observer.ko `
  --source duchamp\diagnostics\ufs-prdt-observer\duchamp_ufs_prdt_observer.c `
  --verification work\duchamp-ufs-prdt-observer-local-only\verification-v6\verification.json `
  --output research\mt6897-dma-ownership\prdt-observation-YYYYMMDD-v1 `
  --approval-token I_APPROVE_DUCHAMP_PRDT_FB5B1A887BCED8E4B0FBF498EBAFC21D4856B4F57BBF2795F1D469BD8C9984C3
```

The completed result shows that Android's observed UFS DMA addresses equal the
original physical addresses without observed SWIOTLB use while the pinned
no-IOMMU/dma-direct contract remained true at both snapshots. This is evidence
for the installed Android route, not a generic IOVA translation proof. It does
not prove secure-world firewall permission, XNU cache-maintenance correctness,
or safe physical UFS ownership by XNU. Every rerun still requires fresh
explicit approval.
