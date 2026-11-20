# Duchamp safe placement decision

Date 2026-11-17. **BLOCKED_BY_MEMORY_EVIDENCE**.

The new audit corroborates historical LK staging reservations and decodes the saved firmware allocator data. It finds no demonstrated fixed-reservation collision for the reference high window. The new candidate still lacks same-boot ownership, bounded decompression workspace and DMA exclusion across LK release, final BL31 processing and actual XNU entry. Moving the payload does not establish those conditions. No physical experiment is ready for review from this evidence alone.

## Preserved reference

Branch `duchamp-bootstrap`, HEAD `d91562d9c2bd3bc33d52550c101de1009bb41dc0` with uncommitted work. The exact 32+4 MiB candidate is unchanged. Initial tracked changes were saved in `outputs/duchamp-memory-ownership-20261117/baseline.patch`. Existing untracked files were retained in place. New code is limited to offline analysis and tests.

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| Source-built `kernel.development.sweet` | 19,541,944 | `e7b51ecb16fe9ad21a78455714b2bf26c1dee1fbc3a6a7f0cb3971a9cd569457` |
| `native-4m-var/bootshim/Image` | 57,417,168 | `2be899ce4c76a740c3006089efd25e292b42b6e59bee10722610dd4203cb426b` |
| `native-4m-var/boot-v4-envelope.img` | 14,888,960 | `86c23337ce9aa9cd0913592ed03063405e5b7a42dc3446a822bd753575caf1bd` |
| Embedded md0 HFS+ | 33,554,432 | `390a9d49474bfe3440b81686784b1b3753c72ebe94ab153712e0441c05d44c4b` |
| Embedded md1 HFS+ | 4,194,304 | `d776b7a298ed458cf0f1713519020f99fdf3a05c30f96cbba56c6e4bfd9a70bb` |

Candidate paths are beneath workspace `outputs/duchamp-mt6897-safe-placement-20261117/`. Kernel path is `outputs/duchamp-patched-clang-20261117/new-xnu-qemu-final/kernel.development.sweet`. Full paths, all candidate intervals and hash checks are recorded in `outputs/duchamp-memory-ownership-20261117/baseline-preserved.json`, `baseline-reference.json`, and `corroborated/memory-ownership-audit.json`.

## Reference memory intervals

All extents are half-open. Historical FDT DRAM is `[0x40000000, 0x340000000)`. This declaration alone grants no ownership.

| Component | Physical interval |
| --- | --- |
| Bootshim code/data/BSS | `[0x40000000, 0x400158e0)` |
| Bootshim stack | `[0x400158e0, 0x4001d8e0)` |
| Embedded payload | `[0x4001d8e0, 0x436c1dcc)` |
| Tail padding | `[0x436c1dcc, 0x436c1dd0)` |
| Historical FDT reservation | `[0x47c80000, 0x48080000)`; saved FDT bytes end at `0x47cf6980` |
| `__TEXT` | `[0x1c1004000, 0x1c1168000)` |
| `__DATA_CONST` | `[0x1c1168000, 0x1c12e8000)` |
| `__TEXT_EXEC` | `[0x1c12e8000, 0x1c1b0c000)` |
| `__KLD` | `[0x1c1b0c000, 0x1c1b10000)` |
| `__LASTDATA_CONST` | `[0x1c1b10000, 0x1c1b14000)` |
| `__KLDDATA` | `[0x1c1b14000, 0x1c1b18000)` |
| `__DATA` | `[0x1c1b18000, 0x1c20d8000)` |
| `__BOOTDATA` | `[0x1c20d8000, 0x1c2124000)` |
| `__LINKINFO` | `[0x1c2124000, 0x1c2170000)` |
| `__LINKEDIT` | `[0x1c2170000, 0x1c2820000)` |
| md0, read-only | `[0x1c2820000, 0x1c4820000)` |
| md1, writable | `[0x1c4820000, 0x1c4c20000)` |
| ADT plus padding | `[0x1c4c20000, 0x1c4c24000)`; actual ADT 4,348 bytes |
| Boot arguments | `[0x1c4c24000, 0x1c4c28000)` |
| Early allocator/VM capacity | `[0x1c4c28000, 0x1e0000000)` |
| Full XNU window claimed by the payload | `[0x1c0000000, 0x1e0000000)` |

Bootstrap page tables are at `0x1c1180000` within `__DATA_CONST`. Kernel interrupt/exception stack symbols are at `0x1c2110000` and `0x1c2118000` within `__BOOTDATA`. They are subranges of the listed segments, not extra independent allocations. Virtual entry is `0xfffffe00074aa488`, physical entry `0x1c14aa488`. Loader translation is `PA = phys_base + VA - virt_base`; generic segment planning is in `duchamp/loader/guard.c` and `plan.c`.

## Lifetimes and peak usage

The existing checker already rejects kernel/RAMDisk, stack, DTB and fixed/dynamic reservation geometry conflicts. The added `check_boot_lifetimes()` performs a separate offline phase audit over `lk-decompress`, `lk-finalize`, `bl31-exit`, `bootshim-materialize` and `xnu-runtime`.

- Compressed input is 14,882,794 bytes, but its actual normal-boot address is unresolved.
- Uncompressed Image is 57,417,168 bytes. Simultaneous compressed input plus output is therefore at least **72,299,962 bytes**, excluding LK itself, FDT, other live allocations and scratch. The decompressor's immediate `0xc0` stack frame is not a bound on all callees. A complete measured peak is unavailable.
- The high materialized prefix is 79,855,616 bytes. The payload advertises a full 536,870,912-byte XNU window; the remaining 457,015,296 bytes are allocator/VM capacity, not established safe ownership.
- During payload materialization the low Image and high destination coexist. A conservative accounting of the full XNU window plus staged Image is 594,288,080 bytes, excluding FDT, LK/firmware, retained compressed input and any scratch. Their exact simultaneous lifetimes are not fully measured.
- The historical kernel/DTB claims cover LK decompression only in the conservative phase model. Missing claims after release are reported, not silently extended to XNU entry. Historical fixed reservations are conservatively kept throughout the analysis; that is an analysis assumption, not a claim about their actual lifetime.

Compression changes packed size. It does not reduce the destination or establish who owns it.

## Alternative placements

Three 512 MiB destination windows were evaluated as host-side geometry, with identical segment-relative offsets, 16 KiB alignment and the preserved low LK load contract. No alternative boot artifacts were created.

| Runtime window | Geometry against historical fixed reservations | Actual native compatibility and ownership |
| --- | --- | --- |
| `[0x1c0000000, 0x1e0000000)` | Clear; inside a saved allocator free pool. | Existing offline reference. Current native preflight explicitly expects this base and 512 MiB size. Same-boot ownership/DMA unproved. |
| `[0x140000000, 0x160000000)` | Clear; within saved free pool `[0xfffff000, 0x1bfffe000)`. | Generic relocation arithmetic is aligned. Current native preflight rejects the different base. No relocated image/MMU boot or ownership proof. |
| `[0x200000000, 0x220000000)` | Clear; inside the saved high free pool. | Same fixed-base preflight blocker, untested relocation/MMU behavior and missing ownership/DMA proof. |

All retain nine potential staging-policy findings in the original checker because the low Image intersects unresolved Linux dynamic allocation requests. The new LK evidence clarifies that these are not observed physical overlaps. Neither moving the high destination nor reducing md1 changes the unresolved low compressed-input/scratch and post-release ownership questions. The original native base guard was left intact.

## Changes and actual tests

| File | Change |
| --- | --- |
| `tools/duchamp_mblock.py` | Bounded decoder for the pinned archived LK v2 format, including reserved-slot holes and stale free slots. No hardware authorization. |
| `tools/duchamp_memory_placement.py` | Additional buffer/reservation lifetime and overlap analysis; unconditional physical denial retained. |
| `tools/audit-duchamp-memory-ownership.py` | Pinned LK/FDT/log/map corroboration, disassembly, 52-entry cross-check, candidate geometry and machine-readable evidence report. |
| `tools/test-duchamp-mblock.py` | Corruption, header/count, names, overflow/alignment, free/reserved overlap, hole and stale-slot cases. |
| `tools/test-duchamp-memory-lifetimes.py` | Modem overlap, compressed input/scratch collision, incomplete extents, incorrect lifetime, unknown DMA, malformed geometry and self-asserted grants. |
| `tools/test-duchamp-memory-placement.py` | Explicit kernel/RAMDisk collision regression added to existing interval suite. |

Final host results are **16/16 interval, 19/19 lifetime, 15/15 mblock tests**, exit 0. The real archived-input audit matched 52/52 fixed reservations and passed 11 instruction checks, exit 0. The kernel, Image, envelope, FDT and embedded md0/md1 bytes match the reference hashes. Commands, durations, exit codes and output digests are in `outputs/duchamp-memory-ownership-20261117/verification.json`.

Representative commands, run from the repository under Ubuntu WSL, are below. No QEMU test was repeated because no guest source, binary or boot configuration changed.

```sh
python3 tools/test-duchamp-memory-placement.py
python3 tools/test-duchamp-memory-lifetimes.py
python3 tools/test-duchamp-mblock.py
python3 tools/audit-duchamp-memory-ownership.py \
  --lk ../phone-firmware/lk_a.bin --fdt ../phone-fdt.bin \
  --retained-log ../../outputs/duchamp-slot-b-live-lk-log-20261111/pl-lk-live.bin \
  --reference-map ../../outputs/duchamp-mt6897-safe-placement-20261117/mt6897-physical-memory-map.json \
  --output ../../outputs/duchamp-memory-ownership-20261117/corroborated
```

## Decision and next required evidence

**BLOCKED_BY_MEMORY_EVIDENCE** is supported by unresolved input/scratch bounds, reservation lifetimes, actual same-boot high-window ownership and modem/fabric/IOMMU DMA exclusion. Existing channels provide no complete final-boundary record, a related firmware-evidence limitation. No new image-acceptance or recovery result was measured; their prior prerequisites remain in force.

The smallest useful next step is obtaining the matching supported final allocator/isolation trace described in [Slot B evidence](DUCHAMP_SLOT_B_MEMORY_EVIDENCE.md), including the last LK changes and final BL31 policy effects, correlated with actual XNU entry. Do not flash, switch slots, alter modem reservations or enable physical UFS based on this report. Android A and the known working boot path remain preserved. Work remains uncommitted and unpushed.
