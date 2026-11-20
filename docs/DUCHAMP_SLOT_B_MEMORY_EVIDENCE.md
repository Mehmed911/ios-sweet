# Duchamp Slot B memory evidence

Date 2026-11-17. Result **BLOCKED_BY_MEMORY_EVIDENCE**. No phone reads, reboot, slot selection, flashing, physical MMIO or DMA were performed in this task.

## Established facts and unresolved evidence

| Question | Available evidence | What it does not establish |
| --- | --- | --- |
| Where does LK intend to write the uncompressed Image? | Pinned LK queries `mb_kernel`; retained allocator trace reserves `[0x40000000, 0x47c80000)`. The reference Image ends at `0x436c1dd0`. | The selected normal-boot path and every writer in the new B execution. |
| What is occupied in the saved final FDT? | A bounded decoder finds 29 free-pool entries and 52 reservations. All reservations match the generated FDT nodes. | A current Slot B memory map or DMA permissions. |
| Is the high XNU window covered by historical allocator space? | `[0x1c0000000, 0x1e0000000)` lies within the archive's `[0x1c0000000, 0x33d600000)` free pool. | Exclusive XNU ownership or the absence of outstanding DMA. |
| Do kernel/DTB reservations persist? | LK contains release attempts before final FDT export; those reserved slots are inactive in the saved Android property. | Exact success, further allocations and continued protection across final BL31 callbacks and XNU entry. |
| Is modem placement fixed? | Retained LK dynamically allocates/frees `md_mem_usage`. Historical Android reservations split that region and have a different tag address. | Which reservations survive the proposed execution or whether another processor can access the payload. |
| Are decompression buffers fully bounded? | Known output length 57,417,168 and compressed input length 14,882,794; seven LZ4 blocks, verified earlier by round trip. | Actual input address, all scratch allocations, stack high-water mark and simultaneous peak in the target LK execution. |
| Do DMA/IOMMU/firewall policies exclude the candidate? | Saved DT topology, Xiaomi DMA consumers and BL31 callback intent. | Final effective master permissions, mapping epochs, drain completion or persistence. |

The full source/binary and log references are in [the allocation audit](DUCHAMP_LK_MEMORY_ALLOCATION_AUDIT.md). The machine-readable record is `outputs/duchamp-memory-ownership-20261117/corroborated/memory-ownership-audit.json` at workspace level. No observation from Android A is promoted to a fact about XNU on B.

## Real channels examined

The existing archives already establish which interfaces actually returned data. This task inspected those archives and their source references without reconnecting to the phone.

| Channel | Device-specific evidence | Limits for this task |
| --- | --- | --- |
| OEM retained LK log over Fastboot | A verified 197,219-byte export with a terminal OKAY and the observed allocation trace. | Contains entry into Fastboot, no actual XNU boundary. Re-entering Fastboot would violate the current no-reboot constraint and would not by itself fill that gap. |
| `/proc/atf_log/runtime_snapshot`, `raw_dump_all` | Historical Android-root captures returned 131,072 and 2,097,152 bytes; pinned Xiaomi `tfa_debug.c` implements the reader. | Recorded Android A BL31 output has no final B/XNU allocation/isolation pair. The reader does not cause firmware to record missing events. |
| `/proc/pl_lk`, pstore and bootprof | Existing archived Android reads and LK source/log inventory. | Available captures lack the required final BL31 and XNU pair; another boot can overwrite retained content. |
| Incoming FDT and existing passive bootshim record | PC/x0 capture and bounded FDT SHA-256 collector already exist. The new host parser can interpret the saved mblock property. | A bootshim can report bytes it receives; it cannot certify DMA exclusion, effective secure permissions or truthful ownership by itself. No new physical collector was enabled. |
| UART | Four UART nodes in the saved DTB; archived Android consoles were ramoops/ttynull. | Supported board connection, electrical specification and final secure-stage output have not been verified. No debug pins, mux or ports were touched. |
| Firmware instrumentation or independent trace | The final LK/BL31 code locations are identified. | No accessible, supported retail channel demonstrating final allocator and master-isolation state is available in the saved evidence. CoreSight/TF-A capability elsewhere is not a Duchamp channel. |

See [the existing recovery and channel audit](DUCHAMP_ANDROID_A_RECOVERY_VERIFICATION.md), [final handoff review](DUCHAMP_FINAL_BL31_XNU_HANDOFF.md), and [Xiaomi ATF reader](https://github.com/MiCode/MTK_kernel_device_modules/blob/3c4ccd07d5624879555ec710c11bb8818e5cb5c6/drivers/misc/mediatek/atf/tfa_debug.c).

## Smallest evidence collection that could change the decision

1. Obtain the matching supported LK allocation trace or vendor-approved instrumentation. Record every allocate/free affecting the compressed input, scratch, output, FDT and proposed high window. Capture the allocator's last state before `MTK_SIP_KERNEL_BOOT`, with actual loaded-image and resolved Slot B identity. The file path `lib/mblock/mblock.c` and loader function `boot_linux_fdt` are identified in the saved binary; the complete matching source file for the loader must come from the firmware supplier.
2. Observe the final BL31 boundary **after** group-5 EMI/SMPU callbacks and the later final helper, using a vendor-supported producer or independently controlled observation. The isolation owner must account for modem and other masters, their translations or bypass routes, admitted transactions and permitted future writers over both candidate extents. No UFS register read is needed merely to parse the FDT, but a CPU-side map cannot substitute for this isolation evidence.
3. Bind the last firmware observation to the actual bootshim entry and actual XNU entry in the same execution. Capture entry coordinates, exact FDT/ADT bytes, measured image identities and event order. A nonce/hash helps correlate bytes; it does not establish who measured them or authorize ownership.
4. Ensure an existing supported trace buffer is itself reserved and its owner/lifetime established before writing diagnostic records. Do not place a new ring buffer in an arbitrary apparently free address. A copied map's hash alone supplies no provenance.
5. Reconcile the measured intervals and isolation lifetime on the host. If any required region, writer, drain or later policy change is unknown, keep the candidate blocked.

Implementing a new LK allocator logger or BL31 final-exit producer would change firmware and requires matching source, a supported build/signing path, documented debug policy and separate approval. Wrong reservations, trace-buffer writes, ABI changes or an unaccepted secure image can prevent Android/recovery from booting. No such firmware build or hardware experiment was executed. Prefer existing supported telemetry where it can actually supply the missing facts. The current blocker cannot be resolved by another synthetic authorization record.

## Recovery and execution boundary

Android A, the prior B images and their archived recovery receipts remain untouched. The previous recovery reconciliation is historical, not a new connection check. Any later hardware proposal needs independently verified current A/B backups, exact candidate and rollback hashes, Fastboot reachability and a manual return-to-A procedure. This document does not approve or initiate that proposal.

The next external requirement is a supported final-boundary allocation/isolation record or the matching firmware source and documented instrumentation path. Until then, additional offline relayout or compression cannot establish physical ownership.
