# MT6833 to MT6897 UFS source comparison

Community source: commit `c24467f3074d9bfbd7cb92e2d20beacd91e468b5`,
`mtk/mt6833/drivers/storage/hakios.mt6833_ufs.c` (336 lines).
Source-extracted ASan/UBSan test reproduces `success=1 changed_bytes=0` with HCS
ready. No device was accessed. A claimed successful mount in metadata is not
supported by this read implementation.

| Function | Actual dependencies/assumptions | Disposition for Duchamp |
| --- | --- | --- |
| ufs_rd / ufs_wr | Direct volatile MMIO at hard-coded MT6833 0x11270000/0x2300; no ownership/error boundary | Do not copy. Use the separately gated MT6897 observer and verified window 0x112b0000/0x3000 |
| ufs_wait_idle | Up to two million reads of HCS bit 0; assumes inherited ready link | Not queue-quiescence proof; existing bounded observer reports inherited HCE/list/MCQ state |
| ufs_read_sectors | Checks arguments/status; no CDB, UTRD, PRDT, DMA, completion or destination copy | Not reusable. Existing ufs_readonly.c implements actual NOP/query/capacity/read packets; this change adds bounded INQUIRY |
| find_partition | Reads an unfilled allocation, then assumes LBA 0x20000 and 0x800000 512-byte blocks, even without valid GPT | Reject. Existing ufs_gpt.c validates GPT/CRC/GUID/bounds; no invented partition or userdata use |
| ufs_strategy | XNU buf/lock interface, 512-byte arithmetic, UFS_MAX_BLOCKS; underlying read is absent | Interface concept only. Existing qufs adapter translates against discovered block geometry; no direct struct copy |
| ufs_ioctl / open | Read-only entry checks and disk ioctls | Keep existing EROFS behavior; a read-only interface cannot repair a missing transport |
| hakios_mtk_ufs_root / devfs | ml_io_map and bdevsw/cdevsw registration; no PHY/clock/reset/DMA setup | Do not activate on MT6897. Existing XNU physical root selector stays unsupported |

No MediaTek PHY initializer, clock/reset implementation, IOMMU/DMA allocator,
UIC command issuer, query-descriptor reader, SCSI submission, MCQ engine or IRQ
handler exists in that file. SCSI opcode defines alone are not implementations.

Linux comparison is pinned at `fa2933aac170dd19c6a7f0d7b81a8f537e40915c`:

| Linux function/file | Dependencies and required XNU adaptation |
| --- | --- |
| drivers/ufs/host/ufs-mediatek.c: ufs_mtk_init | Variant state, matched DT capabilities, MCQ IRQ discovery, PHY binding, reset handles, runtime PM, clocks and PHY power; cannot be replaced by checking HCS |
| ufs_mtk_mphy_power_on | PHY framework, optional VA09 regulator/firmware controls, error unwinding; exact MT6897 provider ownership required |
| ufs_mtk_setup_clocks / ufs_mtk_setup_ref_clk | Common clock framework, runtime PM and platform-specific policy; no foreign register copy |
| ufs_mtk_op_runtime_config | MTK runtime offsets 0x2800/0x2814/0x281c/0x2824, stride 0x30; already separately modeled from QEMU offsets |
| ufs_mtk_mcq_config_resource / ufs_mtk_config_mcq_irq | Valid IRQ resources, queue-capability derived configuration, handlers and completion synchronization |
| drivers/ufs/core/ufshcd.c / ufs-mcq.c | DMA mappings, query/UIC/SCSI queues, timeout/error handling, teardown; Linux types/services are not XNU APIs |

Pinned Xiaomi source `3c4ccd07d5624879555ec710c11bb8818e5cb5c6` remains the
device-specific platform reference. Generic Linux cannot certify the installed
LK/BL31 handoff or system-cache ownership. No firmware call or MMIO was executed.

Implemented now: a fixed standard INQUIRY CDB, validated direct-access response,
bounded existing request/retry budget and unchanged output on error. It is
opt-in only for the guarded QEMU root adapter. No arbitrary CDB or write API
was added. Actual physical capabilities, DMA/cache grants, PHY/clock ownership,
query descriptors and on-device block reads remain prerequisites/unimplemented.
