# Duchamp UFS PRDT observer — phone test 2026-11-01

## Authorization and target

The user separately approved:

1. a normal Android reboot to clear the stale `sweet_ufs_probe_v1` tracefs
   instance;
2. one temporary load of the exact observer artifact with SHA-256
   `fb5b1a887bced8e4b0fbf498ebafc21d4856b4f57bbf2795f1d469bd8c9984c3`.

The reboot returned to normal Android. The boot ID changed, the stale tracefs
instance disappeared, and the observer was absent before the live run.

Pinned live target:

- device: `duchamp`;
- hardware: `mt6897`;
- slot: `_a`;
- kernel: `6.1.57-android14-11-gcf2c2dc91b9e-ab11782407`;
- UFS module GNU Build ID:
  `df7eecc22450fb6e6eceaaef4b3fe8ceb46b2a84`;
- battery: 40 percent;
- root: available.

## Result

The fail-closed runner completed successfully. The workload delta was:

- commands: 371, all reads;
- segments: 17,437;
- PRDT address mismatches: 0;
- PRDT length mismatches: 0;
- `dma_to_phys()` mismatches: 0;
- SWIOTLB segments: 0;
- segments outside the live bus limit: 0;
- DMA, translated-physical or original-physical overflows: 0;
- rejected hook calls, hook errors and unknown directions: 0;
- runtime contract changes: 0.

The live `bus_dma_limit` was `68719476735` (`2^36 - 1`). Of the complete
observation, 16,475 segments were above 4 GiB and all stayed inside that
36-bit limit. The historical runner classification was
`dma-equals-original-phys-no-swiotlb-under-pinned-contract`.

That legacy label describes the observed equality between
`dma_to_phys(sg_dma_address)` and `sg_phys`. It does not establish that the raw
DMA address stored in PRDT numerically equals the CPU physical address. The
device has a `dma_range_map`, and its live entries were not captured by this
observer.

The observer's report remained coherent and complete. The runner intentionally
does not claim that every observed command was caused by its file reads because
the hook has no workload tag.

## Cleanup and safety result

- observer loaded once and unloaded successfully;
- staged phone file removed;
- observer sysfs state removed;
- boot ID unchanged during the live run;
- kernel taint unchanged at `12805`;
- no new WARNING, SError, RCU stall, hung task, lockup, KASAN or use-after-free
  line was found;
- no reboot, partition access, flash, cache drop, SELinux change, tracefs
  control change, firmware call or MMIO access was requested by the runner or
  observer.

An independent post-run check confirmed that neither the module nor its staged
file remained on the phone.

## Evidence and conclusion

Evidence directory:

`research/mt6897-dma-ownership/prdt-observation-20261101-v1/`

`result.json` SHA-256:

`81f1210b67a659103d3c4c863dd6baafd85e39dfb77132b4382efab1a91de5d4`

`tools/interpret-duchamp-prdt-observation.py` pins this exact receipt and emits
only the narrower claims described below. It explicitly keeps raw DMA identity,
firewall bypass, cache ownership and XNU resource ownership false.

This establishes that inverse DMA translation returned the original
scatterlist physical address, without observed SWIOTLB use, while the pinned
dma-direct/no-IOMMU/36-bit contract remained valid. It does not prove raw DMA
and CPU-physical numeric identity, secure-firmware permission, XNU cache
maintenance, or that XNU may safely own and program UFS MMIO.
