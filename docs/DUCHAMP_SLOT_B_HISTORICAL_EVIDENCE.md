# Duchamp Slot B historical evidence decision

2026-11-17. Branch `duchamp-bootstrap`, HEAD `d91562d9c2bd3bc33d52550c101de1009bb41dc0`; work remains uncommitted.

**Historical recovery result: EXPORT_INTERFACE_UNAVAILABLE within the reviewed, permitted interfaces.** Physical readiness remains **BLOCKED_BY_MEMORY_EVIDENCE**. No historical Slot B XNU record was recovered or authenticated. No phone operation was performed in this task.

## What is established

1. The actual saved Duchamp LK uses the storage-backed `blackbox` label, and the archived device listing names that label. The matching writer is at saved file `0x51a24`; its final normal-boot caller is `0x10050`.
2. Source-level ring behavior is **five positions**, not the previously inferred four. The A banner's `dump_count=4` is the pre-write cursor. A valid writer run advances that cursor to 5 and the printed generation 794 to an intended stored generation 795. These are decoded source semantics, not a recovered record 795.
3. The prior real A log contains `mb_avb [0x334a00000,0x33d600000)`, a later free message and a Linux-jump announcement. Existing root `/proc/pl_lk` acquisition worked on A. It cannot select a prior storage generation.
4. Official MiCode current-log and AEE/reboot-reason readers examined here provide no verified Blackbox history selector. Actual Fastboot current-log handling likewise does not select a stored generation. A different-device decompilation or guessed OEM command is not an applicable interface.
5. New static checks pass 28/28; current-log observation checks pass 16/16. These results neither recover an old B record nor authorize physical access.

Exact instruction locations, reader source lines, capture hash and public primary-source links are in [the implementation audit](DUCHAMP_LK_BLACKBOX_HISTORY.md). Artifacts are outside the repository at workspace `outputs/duchamp-lk-blackbox-history-20261117/`; `targeted-checks.json` records the actual commands, exits and log hashes.

## Evidence categories must remain separate

| Category | What a complete genuine LK historical record could establish | Current result / remaining limit |
| --- | --- | --- |
| LK allocation | Actual reported `mb_avb` PA/size, output reservation and allocation order for that record's boot. | Available only for A. Proposed B address, mapping and input pointer remain unknown. A pool request size is not an actual B address. |
| Allocation lifetime | Ordered allocation/free/unmap messages and visible subsequent users, if the complete trace includes them. | A free message does not prove its return status. Reuse, omitted messages and post-export allocations must be accounted for. No complete B lifetime trace. |
| Final memory ownership | Would require measurements after all relevant owners release/transfer memory and final firmware policies take effect. | LK writes Blackbox before the secure handoff. Its allocator snapshot does not prove final BL31/XNU ownership. |
| DMA isolation | Would require actual master/stream/domain routing, retained mappings, in-flight drain or exclusion and persistence over XNU extents. | Not established by a CPU allocation map, PGD-clean message, counter, checksum, HCE state or absence of overlap. No such B evidence recovered. |
| BL31-to-XNU handoff | Final-exit and actual-entry observations with independently justified origin, ordering, slot and exact image/DTB binding. | A pre-handoff Linux-jump banner and XNU-related strings do not prove the branch executed or the final policy. No correlated final pair. |

## Conditions for accepting a future supported export

No historical parser was implemented for an unavailable export contract. If a vendor-supported export becomes available, preserve its raw bytes first and identify the exact firmware/container version before implementing a decoder.

- **Origin:** document the actual supported reader/producer and independent chain of custody. An untrusted copied file plus its recomputed digest must not acquire trust. Checksums can detect changes, not authenticate firmware assertions.
- **Completeness/integrity:** validate every header, record/section extent, length and actual write result against the verified format. Reject partial reads, impossible bounds, conflicting IDs, mixed generations and damaged data. Header writes occur before PL/LK payload copying; fresh metadata alone does not prove complete bytes. Do not infer integrity algorithms for unknown fields.
- **Generation/freshness:** correlate the intended B attempt with the actual stored generation and record cursor. Account for the producer's pre-increment banner, 32-bit wrap, reset/reinitialization, five-position reuse and any skipped/failed writer runs. Elapsed time or current cursor alone cannot prove an older record survived.
- **Slot/image:** require corroborated B selection plus the exact loaded kernel/boot chain and actual XNU-entry context. A record with an XNU string, an old host `set_active` transcript or a current Android A UUID is insufficient. No verified typed slot/digest field was identified in the inspected record construction.
- **Allocations/bounds:** capture actual pool PA/size, VA-to-PA mapping and loaded-input pointer/size; full decompression capacity and reservations; final payload/ADT/md0/md1 bounds; ordered lifetime/release results and other processors' reservations. Missing observations remain unknown.
- **Firmware/DTB:** establish actual producer-image identity and received DTB/ADT bytes through a justified independent source. A build property or banner is corroboration, not a substitute for firmware identity.
- **Authority:** even an accepted historical allocation trace must not enable UFS, MMIO or DMA. Preserve the existing authorization gate. Final ownership, isolation and cache responsibility require their own authoritative evidence.

The hardened existing observation reader rejects corrupt printed headers, wrong/missing boot IDs, wrong slot, incomplete allocation traces and inconsistent acquisition bytes. It deliberately leaves freshness and origin unauthenticated. This is not evidence that an unimplemented historical binary decoder has passed corruption or authentication tests.

## Why retention cannot yet be decided

The desired B generation, its raw record and the current stored ring headers were not acquired. Intervening successful writer invocations may have reused its position; a failed boot may never have reached the writer. Neither possibility is asserted as fact. No physical partition read was made to test them, and no raw-memory scan was performed.

The three archived current-memory/pstore exports provide no relevant historical Blackbox record. Their sole `blackbox` match is the old block-device label listing. Public source/search coverage establishes the reviewed interfaces' behavior, not the absence of proprietary OEM tools. Therefore neither availability nor loss of the desired B bytes can be claimed.

## Preserved baseline and next action

The exact 32 MiB md0 + 4 MiB md1 candidate, source-built XNU, saved FDT, bootshim and prior 50-test memory baseline remain unchanged. Earlier 13/13 LZ4 guard results were not rerun because those sources and inputs did not change. No UFS path, firmware, phone boot state, Android A/B partition, recovery image or authorization gate was modified. No commit or push was made.

The concrete next requirement is an existing Xiaomi/MediaTek **read-only export contract for the Blackbox ring from the current Android session**, or a previously exported complete B record with independently verifiable origin. It must identify generation, slot and exact image context. If no such supported interface is supplied, stop dependent recovery/hardware work; do not replace it with a guessed partition operation or a simulated authorization record.

Even after historical allocation recovery, final BL31 policy and modem/peripheral DMA isolation at actual XNU entry remain blockers. Recovering old LK text alone cannot clear them.
