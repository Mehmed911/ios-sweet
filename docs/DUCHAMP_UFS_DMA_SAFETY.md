# Duchamp UFS DMA safety

## Verified boundary

The archived Android probe identified generic `dma-direct`, no standard
Linux device IOMMU attachment, 64-bit streaming and coherent masks, and a
36-bit bus ceiling. The final FDT describes an identity `/soc/dma-ranges`
aperture and lacks an HCI `iommus` property. Android also exposes a
SWIOTLB pool pointer. These observations describe the saved Linux
configuration. Effective PA-to-DMA translation, security-controller
permission, bounce behavior, final outstanding writes and XNU cache
ownership remain unproven. The saved BL31 reset control and LK HCE write
are source observations, with no evidence of a UFS master or fabric drain
at the XNU handoff.
[Saved DMA observations and pinned sources](../duchamp/MT6897-DMA-IOMMU-FIRMWARE-EVIDENCE.md),
[firmware ownership audit](DUCHAMP_UFS_OWNERSHIP.md)

## Evidence required to exclude stale DMA

The v1 handoff model deliberately requires both an independently confirmed
drain of work already admitted to the interconnect and a continuing fence
against new stale requests. Establish these independently, in the same
boot and for the exact protected XNU physical range.

| Check | Evidence and (future) provider requirement |
| --- | --- |
| Stop prior submissions | Identify every still-capable producer and prove it cannot restart. The record covers firmware, a previous OS, interrupt/doorbell paths and any recovery path that can resubmit. Pin the fence through handoff and reset with a new isolation epoch on any change. |
| Controller queue state | Record mode, HCE observation, transfer/task run-stop and doorbell state. In MCQ, account for all configured SQ/CQ entries and interrupt/status producers. A single empty queue or last completion supplies incomplete evidence. |
| Fabric drain | Obtain the platform-defined completion or isolation acknowledgment that covers requests already accepted or translated. Wait for posted descriptor and data transactions to complete. HCE clear, zero doorbells, a reset pulse, and CPU ordering instructions cannot independently prove this outcome. |
| Direct path | Prove the real bus route, address limits, effective PA-to-DMA translation and bounce disposition. Identify an enforceable protection boundary for the UFS DMA master that prevents access to protected XNU memory after firmware cleanup. Verify its scope and ownership. A direct-address DT declaration or SWIOTLB pool is insufficient. |
| Translated path | Prove the actual SMMU/IOMMU master and stream, ownership of the old/new domain and mapping epoch, and the covered IOVA-to-PA ranges. Block the old stream, retire stale mappings, and attest the required invalidation and completion for IOTLB and any endpoint/device translation caches. Account for bypass/default domains and requests already in flight through the fabric. An invalidation enqueue alone supplies incomplete evidence. |
| Descriptors and buffers | The lease and receipt must bind prior descriptor quarantine and a separate, reviewed destination pool. Do not recycle UTRD/UCD/PRDT or task/MCQ rings and data pages until both no-resume and drain are proved. For future DMA, validate descriptor and data masks, alignment and reachability independently. A read-only media operation writes to DMA destination RAM. |
| Cache and barriers | Verify the non-coherent cache contract to the actual device-visible point, including any outer/system cache. Ensure exclusive full cache lines, no dirty aliases, clean descriptors and CPU buffers before handing them over, order publication before device notification, and synchronize/invalidate device-written buffers before CPU consumption. CPU normal-memory order, device register order, cache completion and fabric drain are separate properties. |
| Reset dependency and failure | Resolve device reset, HCI/UniPro/crypto reset, PHY and clock/power sequencing against a documented provider. A timeout or revocation stops new work. Keep existing isolation/fences and quarantined memory until independent quiescence proof. Reset or power-off can itself disturb access to the evidence or resources needed to drain. |

The model checks the declared queue coverage and busy mask, outstanding
count, positive drain/fence/isolation flags, isolation epoch, protected
range and separate snapshot, descriptor pool, cache and fence receipts.
A direct record must show a verified direct filter, with no IOMMU metadata.
An IOMMU record must show stream blocking, completed invalidation and
device-translation accounting. The DMA route must match the gate's
retained evidence. For IOMMU, the stream, domain and mapping epoch must
match both that evidence and the current trusted context. Version 1
requires zero outstanding DMA for a translated route. Neither format variant programs
hardware. Its protected interval is one contiguous envelope and must
cover all XNU memory that needs protection.

The existing route and cache modules still own their per-buffer handoffs,
and the existing activation gate remains the lease authority. The physical
transport must eventually validate these conditions before list programming,
before using DMA buffers, and across recovery. The new record supplies no
translation function or memory ownership by itself.
[Gate](../duchamp/drivers/mt6897_ufs_gate.c),
[DMA route](../duchamp/drivers/mt6897_ufs_dma_route.h),
[cache ownership and ordering](../duchamp/drivers/mt6897_ufs_cache.h),
[Linux DMA API guide](https://docs.kernel.org/core-api/dma-api-howto.html),
[Linux OF IOMMU setup](https://github.com/aosp-mirror/kernel_common/blob/cf2c2dc91b9e9f016dc25cf095b1fe34cb5dfcb6/drivers/iommu/of_iommu.c#L111-L151)

## Offline results and blockers

The new mock suite covers accepted direct and translated receipts and
refuses incomplete queues, outstanding DMA, missing drain or fence,
missing cache sync, missing direct filter or SMMU invalidation, stale
domain/stream/epoch, and invalid protected ranges. The attached virtual
UFS device recorded zero accesses across all 89 cases. The existing
DMA route, cache, gate/provider and passive register tests also passed.
[Handoff format and test receipts](DUCHAMP_UFS_HANDOFF_FORMAT.md)

Before hardware use, obtain the device-specific fabric drain and
no-resume contract, enforceable XNU range isolation, exact reset/resource
ownership and verified cache-maintenance scope. Physical UFS access
and DMA remain disabled.
