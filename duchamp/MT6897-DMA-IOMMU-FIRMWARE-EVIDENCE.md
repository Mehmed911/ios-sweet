# MT6897 DMA, IOMMU and firmware evidence

This note records the fail-closed result for the captured POCO X6 Pro 5G
(`duchamp`) Android environment.  It does not authorize physical UFS access
from XNU.

## Reproducible result

The machine-readable report is:

- `research/mt6897-dma-ownership/live-20261101-v2/result.json`
- SHA-256:
  `71236c08c0354ff0733d44a64e505d117dfd4594e370bedd81fad3ec93d1bf4d`

The audit checks exact input receipts, exact AArch64 instructions from the
saved UFS module, pinned GKI source bodies, the captured BL31 dispatcher, the
read-only runtime reports and the successful read-only UFS-device probe.
Audit success means only that those inputs are internally consistent.

## What is proven

### DMA masks

- The live `/proc/ufs_debug` capture reports HCCAP `0x55c7051f`; its 64AS bit
  is set.
- The saved UFS module SHA-256 is
  `7043e1109b4c356a914fdc92ffbe463c0c43cb27342f6ccce1517a2086b02493`.
  Its GNU build ID matches the running UFS module.
- Its exact instruction path first calls `dma_set_mask(..., 64 bits)`.  On
  failure it calls `dma_set_mask(..., 32 bits)`.  Failure of the 32-bit call
  leaves initialization through the error path.
- The corrected read-only probe measured the live streaming mask as
  `0xffffffffffffffff` and the live coherent mask as
  `0xffffffffffffffff`: both are exactly **64 bits**.
- The same device has `bus_dma_limit=0x0000000fffffffff`. Pinned direct-DMA
  source uses `min_not_zero(mask, dev->bus_dma_limit)`, so the effective DMA
  bus-address ceiling is **36 bits**, despite the 64-bit masks.
- The module calls `dma_set_coherent_mask()` with the selected request, but it
  does not test that call's return value.

The live probe, rather than HCCAP alone, supplies the exact mask values. No DMA
mapping or transfer was issued, so reachability and firewall behavior were not
tested.

### IOMMU route

- `/soc/ufshci@112b0000` has no `iommus`, `iommu-map` or `dma-coherent`
  property in the captured topology.
- The device inherits `/soc`'s identity `dma-ranges` window of
  `0x1000000000` bytes.
- Linux exposes neither an UFS `iommu_group` nor an IOMMU supplier link.
- The live probe additionally found no `dev->iommu`, IOMMU group, fwspec or
  domain, and both `get_dma_ops(dev)` and `dev->dma_ops` were null.
- In the pinned OF path, non-PCI devices obtain an IOMMU only through the
  `iommus` property, and arm64 installs IOMMU DMA ops only when that lookup
  returns an IOMMU.
- In pinned `kernel/dma/mapping.c`, null DMA ops select the generic
  `dma_direct_*` implementation for map, scatter-gather and allocation paths.

This proves that Linux selected its generic `dma-direct` path and had no UFS
IOMMU attachment visible through the standard Linux device/IOMMU state at the
time of observation. The device has a DMA range map, is non-coherent and has a
device SWIOTLB pool pointer. None of those facts proves an identity physical
address, a SWIOTLB transfer, physical firewall bypass or cache ownership. A
platform fixup could also have changed fields other than the observed DMA-ops
pointer.

Primary source receipts are pinned to GKI commit
[`cf2c2dc91b9e9f016dc25cf095b1fe34cb5dfcb6`](https://github.com/aosp-mirror/kernel_common/commit/cf2c2dc91b9e9f016dc25cf095b1fe34cb5dfcb6),
including
[`drivers/of/device.c`](https://github.com/aosp-mirror/kernel_common/blob/cf2c2dc91b9e9f016dc25cf095b1fe34cb5dfcb6/drivers/of/device.c),
[`drivers/iommu/of_iommu.c`](https://github.com/aosp-mirror/kernel_common/blob/cf2c2dc91b9e9f016dc25cf095b1fe34cb5dfcb6/drivers/iommu/of_iommu.c),
and
[`arch/arm64/mm/dma-mapping.c`](https://github.com/aosp-mirror/kernel_common/blob/cf2c2dc91b9e9f016dc25cf095b1fe34cb5dfcb6/arch/arm64/mm/dma-mapping.c),
[`kernel/dma/mapping.c`](https://github.com/aosp-mirror/kernel_common/blob/cf2c2dc91b9e9f016dc25cf095b1fe34cb5dfcb6/kernel/dma/mapping.c),
and
[`include/linux/dma-direct.h`](https://github.com/aosp-mirror/kernel_common/blob/cf2c2dc91b9e9f016dc25cf095b1fe34cb5dfcb6/include/linux/dma-direct.h).

### Firmware/resource ownership

- The live MediaTek UFS caps are `0x6c0`, which includes the RTFF-MTCMOS bit
  `0x200`.
- The matching client uses UFS SiP function ID `0xc2000276`, including
  selectors REFCLK `8`, MTCMOS `512` and MCQ `1024`.
- The captured installed BL31 has the matching
  `MTK_SIP_KERNEL_UFS_CONTROL` dispatcher.  Its verified MTCMOS path accesses
  `0x1c001000`, `0x1c001e10` and `0x1c001e14`.
- The read-only Linux resource capture reserves
  `0x1c001000-0x1c001fff` as `power-controller@1c001000`, covering all three
  firmware addresses.

The defensible ownership classification is therefore a
**shared/delegated boundary with overlapping control**, not exclusive Linux
ownership and not exclusive firmware ownership.  Static BL31 paths do not
prove that an SMC executed at runtime or that its physical effect succeeded.

## Remaining evidence required before physical UFS

The read-only probe completed the first two former evidence requirements.
Physical UFS remains disabled because the following are still unproven:

1. A documented installed-firmware return/effect contract and the physical
   memory/firewall permissions for the UFS DMA master.
2. Cache-maintenance ownership and a reviewed non-coherent DMA implementation
   for XNU.
3. Whether any real UFS transfer needs SWIOTLB/bounce handling; pool presence
   alone is not a transfer trace.
4. A non-destructive, instrumented DMA experiment in a controlled harness,
   only after the firmware and cache contracts above are complete.
5. Keep the XNU physical UFS backend disabled until all of the above pass.

## Re-run

```powershell
python tools\audit-duchamp-dma-iommu-ownership.py `
  research\mt6897-dma-ownership\live-20261101-v2 `
  --shell-report research\mt6897-shell-runtime\live-20261101-v7\result.json `
  --runtime-report research\mt6897-live-evidence\14480520-210535\runtime-report-v7.json `
  --probe-report research\mt6897-dma-ownership\live-probe-20261101-v1\result.json `
  --client-audit research\mt6897-routing\client-audit-v1\result.json `
  --firmware-audit research\mt6897-firmware-live\20261101-v1\ufs-sip-audit-v2.json `
  --saved-contract research\mt6897-contract\saved-v1 `
  --sources research\mt6897-contract\sources `
  --iomem research\mt6897-shell-runtime\live-20261101-v7\root-iomem.stdout.txt
```

The audit itself performs no ADB access, SMC, MMIO, module loading, phone
write, partition access or flashing. Its input includes the separately
approved, completed probe session in which the module was temporarily staged,
loaded, read twice, unloaded and removed without touching any partition.
