# Duchamp MT6897 physical memory map

**Decision — `BLOCKED_BY_MEMORY_EVIDENCE`.** Both offline layouts have non-overlapping candidate regions. The low staging Image intersects unresolved allocation ranges in the archived FDT. Exclusive ownership and DMA isolation for staging and the full XNU runtime window are unverified for the proposed Slot B boot.

## Inputs and authority

| Evidence | What it establishes | Scope |
| --- | --- | --- |
| Archived 485,760-byte Android FDT, SHA-256 `9c49589f70044127be8941a9ea5537977f440ccd5ac15cfd24e120c8a1181d29` | One declared DRAM bank `[0x40000000, 0x340000000)`, 52 fixed reservations, four dynamic requests and an empty FDT header reserve table. | Historical Android FDT. |
| Captured stock DTBO and extracted base DTB | The sole entry of the DTBO table matches the archived 85,308-byte overlay. `fdtoverlay` succeeded. The recomposed tree contains the four dynamic requests. The archived Android FDT adds 52 `mblock-*` nodes and a 22,552-byte `/memory/mblock_info` property. | Static declarations and historical firmware additions. The recomposed tree SHA-256 is `769563bb390023f56809357e847edfda938ff5ce9c88fba1cd7d756d72154e05`. |
| Archived LK, vendor-boot header and physical diagnostic | The previous physical probe displayed `PC=0x40000000` and `x0=0x47c80000`. The vendor-boot header and archived Android iomem reservation corroborate the FDT address. The LK audit identifies LK's own static bootstrap mapping at `0x50700000`. | Historical paths and captures. |
| Archived BL31 and FDT | `mblock-4-BL31-reserved` covers `[0x48800000, 0x48a00000)`. ATF log RAM covers `[0xbfe00000, 0xc0000000)`. The pinned static BL31 audit identifies EMI and SMPU callbacks before non-secure release. | Static code and reservations. Their final permissions and the allocator state at the new handoff remain unknown. |
| Archived Android A iomem | Captures Android runtime allocations, including a reserved range at `[0x41b40000, 0x41f40000)` inside the modeled staging interval. | Android A only. Its owner and lifetime across a new B boot are unverified. |

See [LK handoff evidence](../duchamp/MT6897-LK-HANDOFF-CONTRACT.md), [final BL31 analysis](DUCHAMP_FINAL_BL31_XNU_HANDOFF.md) and the [DTBO metadata receipt](../../../outputs/duchamp-mt6897-safe-placement-20261117/dtbo-evidence.json).

## Physical intervals

Ranges are half-open. The shared XNU window `[0x1c0000000, 0x1e0000000)` avoids all fixed reservations and all four possible allocation ranges in the archived FDT. Its lower bound abuts the archived `dramc-rk0` reservation. Treat the whole 512 MiB window, including gaps and the allocator tail, as an XNU memory claim. The framebuffer remains in its separate reserved range `[0xfcc2f000, 0xfffff000)`.

| Region | 32+8 MiB | 32+4 MiB |
| --- | --- | --- |
| Decompressed Linux Image under LK | `[0x40000000, 0x43ac1dd0)` | `[0x40000000, 0x436c1dd0)` |
| Bootshim code, data and BSS | `[0x40000000, 0x400158e0)` | Same |
| Shim stack from linker symbols | `[0x400158e0, 0x4001d8e0)` | Same |
| Embedded payload begins | `0x4001d8e0` | Same |
| Historical incoming FDT | `[0x47c80000, 0x47cf6980)` | Same historical bound |
| XNU Mach-O segments, including zero-fill | `[0x1c1004000, 0x1c2820000)` | Same |
| XNU physical entry | `0x1c14aa488` | Same |
| md0, read-only HFS+ | `[0x1c2820000, 0x1c4820000)` | Same |
| md1, writable HFS+ | `[0x1c4820000, 0x1c5020000)` | `[0x1c4820000, 0x1c4c20000)` |
| ADT page | `[0x1c5020000, 0x1c5024000)` | `[0x1c4c20000, 0x1c4c24000)` |
| Boot arguments | `[0x1c5024000, 0x1c5028000)` | `[0x1c4c24000, 0x1c4c28000)` |
| Early VM and allocator tail | `[0x1c5028000, 0x1e0000000)` | `[0x1c4c28000, 0x1e0000000)` |

The built kernel locates `_bootstrap_pagetables` at PA `0x1c1180000` inside `__DATA_CONST`, with interrupt and exception stacks at `0x1c2110000` and `0x1c2118000` inside `__BOOTDATA`. In the source build snapshot, `osfmk/arm64/start.s` references the built-in tables and `osfmk/arm64/arm_vm_init.c` sets `avail_start` from `topOfKernelData` before allocating later tables. The bootshim materializer copies segments and zero-fill, places the ADT and records the runtime memory size in boot arguments. These writes and early allocator use require physical ownership. [Shim linker script](../duchamp/bootshim/shim.ld), [layout planner](../duchamp/loader/plan.c), [materializer](../duchamp/loader/materialize.c)

## Offline checker

The [map generator](../tools/build-duchamp-memory-map.py) binds saved FDT and kernel bytes to preflight receipts and rehashes both packaged artifacts. It records candidate regions, reservation scopes and unknown DMA isolation in the [machine-readable map](../../../outputs/duchamp-mt6897-safe-placement-20261117/mt6897-physical-memory-map.json). The map has SHA-256 `9a07f42c09d05a610af5d52a6bfeefe6341bf48d6cefe223b9b6ea90071799a7`.

The [checker](../tools/duchamp_memory_placement.py) rejects zero and overflowing sizes, non-integer values, invalid alignments, gaps in declared RAM, incompatible or overlapping regions, fixed reservations and unresolved dynamic matches. A dynamic request without bounds may intersect any candidate region. It has no hardware authorization path and cannot turn values in a JSON file into ownership or DMA grants. Exit 1 means physically blocked and exit 2 means malformed input. The actual map returns exit 1 for both candidates. The structural findings are confined to low staging, where each Image intersects both possible DPMAIF ranges and the first 64 KiB MKP range. [Checker output](../../../outputs/duchamp-mt6897-safe-placement-20261117/placement-verifier.json)

The [layout report](DUCHAMP_SAFE_PAYLOAD_LAYOUT.md) records the exact tests. The [modem report](DUCHAMP_MODEM_MEMORY_ANALYSIS.md) identifies the missing allocation and isolation evidence.
