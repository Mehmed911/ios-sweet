# Duchamp firmware evidence decision

2026-11-17. Branch `duchamp-bootstrap`, HEAD `d91562d9c2bd3bc33d52550c101de1009bb41dc0`, existing uncommitted work preserved. No phone operation, commit or push.

**Native readiness: BLOCKED_BY_MEMORY_EVIDENCE. Historical export: EXPORT_INTERFACE_UNAVAILABLE within the reviewed interfaces.** Historical Slot B retention remains unknown. Independent Darwin work can continue in QEMU.

## Final assessment of existing evidence paths

The bounded source and actual saved-LK audit in `DUCHAMP_LK_BLACKBOX_HISTORY.md` remains authoritative for this task. The writer uses five rotating storage positions; `dump_count=4` is the old cursor, not ring capacity. `/proc/pl_lk` exposes the current mapped PL/LK buffer. Neither that reader, the reviewed AEE exports, nor the saved Fastboot current-log handlers establish a supported historical Slot B generation selector. No historical record was recovered.

A fresh public-documentation check found Xiaomi's official [Services & feedback logging instructions](https://www.mi.com/global/support/article/KA-11576/). They describe choosing a log category, starting capture, reproducing an issue, completing and uploading it. They do not document exporting this LK Blackbox ring, selecting a historical generation, or authenticating final BL31 memory/DMA state. No logger was started or uploaded. The reviewed public developer page supplied no readable contract for a historical exporter. Search coverage cannot rule out private OEM tools.

Consequently there is no justified new extraction command, offset, parser, authorization receipt or phone experiment to implement. Repeating the current A-buffer read cannot produce the missing B evidence. No additional Blackbox decoder or authorization model was added.

## Facts still required

| Missing fact | Component that must establish or independently validate it | Why current evidence is insufficient |
| --- | --- | --- |
| Actual B input/output allocations and decompression capacity | The matching LK allocator/decompressor, after its actual allocation decisions, with complete bounds and returned status | The 140 MiB request and the A allocation at `[0x334a00000,0x33d600000)` do not give B addresses. |
| Buffer lifetime, release and reuse through final handoff | LK's final allocator state and every subsequent firmware writer, including BL31 | An allocate/free message does not prove the free succeeded or exclude later reuse. Blackbox export occurs before final secure handoff. |
| Payload, kernel, ADT and both RAMDisks owned by XNU at entry | Final BL31/platform memory-policy owner, corroborated with the actual kernel-entry context | A bootshim checksum or CPU interval map cannot establish another stage's ownership decisions. |
| Modem/peripheral DMA exclusion or verified completion | Platform protection controller/firmware owner plus the relevant DMA-master firmware; actual retained master/stream/domain policy | No applicable post-BL31 protection state or drained in-flight transaction evidence exists for these extents. CPU non-overlap alone is insufficient. |
| IOMMU routing, domain owner, mapping epoch and persistence | The actual SMMU/IOMMU configuration owner and platform secure firmware where applicable | Linux A domain observations do not establish what B retains or replaces. No domain/stream IDs are invented. |
| Final BL31 exit to actual XNU entry, same boot and slot | Supported firmware trace producer with independently justified origin, plus correlated entry measurement | LK banners, host-selected slots, nonces, digests and ordinary console output alone do not authenticate resource assertions. |
| Cache-maintenance scope and responsible owner | Platform cache/interconnect owner and documented DMA-coherency contract | A barrier, CPU clean instruction or controller-disabled bit does not by itself establish system-cache ownership or completed DMA. |

Even a genuine historical allocation log would resolve only part of the first two rows. It would not authorize physical UFS access.

## Frozen native candidate and recovery

Artifact directory (outside the repository): `../../outputs/duchamp-darwin-next-stage-20261117/`. `frozen-native-baseline.json` records the exact input paths and hashes; `recovery-freeze.json` rehashes nine saved A/B recovery/boot-chain images against the prior local audit. These are local preservation checks, not a new live-device or recovery-UI test.

| Preserved item | Size | SHA-256 |
| --- | ---: | --- |
| Source-built `kernel.development.sweet` | 19,541,944 | `e7b51ecb16fe9ad21a78455714b2bf26c1dee1fbc3a6a7f0cb3971a9cd569457` |
| Native 32+4 MiB bootshim `Image` | 57,417,168 | `2be899ce4c76a740c3006089efd25e292b42b6e59bee10722610dd4203cb426b` |
| Native Android v4 envelope | 14,888,960 | `86c23337ce9aa9cd0913592ed03063405e5b7a42dc3446a822bd753575caf1bd` |
| Saved Duchamp FDT | 485,760 | `9c49589f70044127be8941a9ea5537977f440ccd5ac15cfd24e120c8a1181d29` |

The native candidate, bootshim, memory-placement validators, firmware evidence and access gates were not changed. Native layout details remain in `../../outputs/duchamp-mt6897-safe-placement-20261117/native-4m-var/verification.json`. QEMU test images are separate copies.

## Actionable boundary

The external requirement is an existing vendor-supported read-only export with a specified producer/version/generation/slot/origin contract, or supported final-stage instrumentation that can measure the missing states. No such accessible mechanism was established. Instrumentation or a device experiment needs its own reviewed design and explicit authorization; neither was attempted.

Freeze dependent native work until new evidence arrives. Continue the real-process IOKit/framebuffer/HID tests described in `DUCHAMP_DARWIN_NEXT_STAGE.md`; those results cannot clear this hardware blocker.
