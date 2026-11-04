# Duchamp UFS PRDT observer v3 — approved phone result

## Result

The separately approved temporary live run passed on the POCO X6 Pro
(`duchamp`, MT6897). The exact statically verified artifact was loaded once,
observed existing Android UFS mappings during a bounded read workload, and was
then unloaded. No partition, boot image, SELinux policy, tracefs control,
cache state, MMIO register or firmware interface was modified by the runner.

Pinned artifact SHA-256:

`49196936b7d6ca78f485b35fc3d7ba0407f3027ec9a70b6bae9658f1c1862f96`

Machine-readable result:

- `PHONE-RESULT-2026-11-04.json`
- size: `9143` bytes
- SHA-256:
  `0fc223d4474535f269766c268b74cab05b2028501ee234f3bab5eb1782053bc9`

## Observed DMA route

The live `dma_range_map` contained exactly one terminated entry:

- CPU start: `0x0000000000000000`;
- DMA start: `0x0000000000000000`;
- size: `0x0000001000000000` (64 GiB);
- offset: `0`;
- map classification: identity and stable for both snapshots.

The complete observer totals were 3,144 commands and 34,162 DMA segments.
The bounded workload added 1,399 commands and 29,452 segments. For every
observed segment:

- the raw PRDT DMA address equalled the original scatterlist physical address;
- `phys_to_dma()` returned that raw DMA address;
- `dma_to_phys()` returned the original physical address;
- the PRDT address and length matched the mapped scatterlist;
- the complete extent remained under the 36-bit bus limit.

The per-device SWIOTLB pointer was present, but its pool was inactive,
`force_bounce` was false, and zero observed segments used the pool. No reject,
overflow, translation error, contract change or kernel fault was recorded.

## Cleanup

Cleanup passed and was independently checked after the runner returned:

- module absent;
- root-only sysfs report absent;
- staged module file absent;
- boot ID unchanged;
- kernel taint unchanged at `12805`;
- no new kernel fault line.

## Scope

This result proves the live Linux UFS address route for the observed workload:
a stable 64-GiB identity window, raw DMA equal to CPU PA, and no SWIOTLB use.
It does not prove that secure firmware will delegate the controller to XNU,
that XNU owns clock/reset/PHY/regulator resources, that physical firewall
permission exists, or that XNU cache maintenance is correct. Those remain
fail-closed blockers before enabling the physical UFS backend.
