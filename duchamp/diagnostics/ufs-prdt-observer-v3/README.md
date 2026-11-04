# Duchamp passive UFS PRDT observer v3

This is an offline-only candidate that preserves the proven v2 observer and
closes two specific evidence gaps without issuing any new storage command:

- it captures exactly one live, terminated `dma_range_map` entry and reports
  its CPU start, DMA start, size and offset;
- it compares every existing mapped PRDT DMA address directly with `sg_phys`,
  and also checks both `phys_to_dma()` and `dma_to_phys()`;
- it records whether the per-device SWIOTLB pool is active or forced, and
  counts observed segments whose translated address is in that pool.

The module fails closed if the target is not the pinned Duchamp UFS device,
if the direct-DMA/no-IOMMU contract differs, if the map is absent or has more
than one range, or if the captured contract changes while observing.

It does not create DMA mappings, issue I/O, access MMIO, call firmware, alter
clocks or power, reconfigure interrupts, or attach an IOMMU domain. Local
build success does not prove runtime values, firmware ownership, cache
maintenance, or safe XNU UFS access.

Do not copy or load this module on a phone without a fresh explicit approval,
a new exact artifact hash, complete static verification, an unload procedure,
and a normal-Android recovery path. This directory contains no live runner on
purpose; the current stage is local build and verification only.

The verified local artifact is
`work/duchamp-ufs-prdt-observer-v3-local-only/artifact-v3/duchamp_ufs_prdt_observer_v3.ko`
with SHA-256
`49196936b7d6ca78f485b35fc3d7ba0407f3027ec9a70b6bae9658f1c1862f96`.
Its static-verification receipt is under
`work/duchamp-ufs-prdt-observer-v3-local-only/verification-v3/verification.json`.
See `BUILD-RESULT-2026-11-04.md` for the exact local test result and limits.
