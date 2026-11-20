# Duchamp LK memory allocation audit

Date 2026-11-17. Branch `duchamp-bootstrap`, HEAD `d91562d9c2bd3bc33d52550c101de1009bb41dc0`, with the existing uncommitted source build preserved. The reference is the validated 32 MiB md0 + 4 MiB md1 candidate. No device transport was opened.

## Findings and evidence scope

The retained LK log explicitly reserves `mb_kernel` at `[0x40000000, 0x47c80000)`. The 57,417,168-byte reference Image fits within that historical 124.5 MiB reservation. The sampled LK binary queries that reservation, checks its base against the target, and passes its size to the decompressor. It later attempts to free the kernel, DTB and LK reservations before exporting the final memory description. The saved Android FDT's allocator property independently agrees with all 52 generated fixed reservation nodes and describes the staged Image and high XNU window as allocator free pools.

These findings establish considerably more than static DRAM declarations. They do not establish a reservation surviving into the proposed XNU execution, exclude firmware or modem DMA, or bound every decompression buffer in that execution. The retained log ends in Fastboot, and the saved FDT is from an Android boot. Neither is a final allocation record from this new Slot B candidate.

## Exact archived inputs

Paths in the following table are relative to the repository. Digests identify the saved files; they do not authenticate a new execution.

| Input | Bytes | SHA-256 |
| --- | ---: | --- |
| `../phone-firmware/lk_a.bin` | 16,777,216 | `f85373d3b4cdf3c959e38bbbfe198a2857e03a5266c6f2a40c319549a5ba957a` |
| `../phone-fdt.bin` | 485,760 | `9c49589f70044127be8941a9ea5537977f440ccd5ac15cfd24e120c8a1181d29` |
| `../../outputs/duchamp-slot-b-live-lk-log-20261111/pl-lk-live.bin` | 197,219 | `bee2a8bd4a06b44fdb8b88b8d6957e30721ab52051da91425b72684a1c3aa18d` |
| `/memory/mblock_info` within the saved FDT | 22,552 | `6ae45db8e7ef4bcb40370cc7bd7e733300cd23183f2ab9afeaf6d207cf481ea1` |
| Previous physical-memory map JSON | See manifest | `9a07f42c09d05a610af5d52a6bfeefe6341bf48d6cefe223b9b6ea90071799a7` |

The pinned analysis is reproducible with [audit-duchamp-memory-ownership.py](../tools/audit-duchamp-memory-ownership.py). Its output is `outputs/duchamp-memory-ownership-20261117/corroborated/` at workspace level. The initial complete tracked diff is preserved outside the source tree in `outputs/duchamp-memory-ownership-20261117/baseline.patch`. No existing source changes were discarded.

## LK allocation, decompression and release

All offsets below are **partition-file offsets in the pinned LK binary**. Its executable starts at file `0x200`, mapped at VA `0xffff000050700000`, PA `0x50700000`. An offset `o` corresponds to VA `0xffff000050700000 + o - 0x200`. The full matching LK C source is unavailable locally. The embedded string at `0xc31a9` identifies `lib/mblock/mblock.c`; `0xbe469` names `boot_linux_fdt`, without establishing its C file path. The audit therefore reports exact binary evidence rather than inventing source locations.

| Binary location | Audited operation | Remaining limitation |
| --- | --- | --- |
| `0xcd50..0xcda0` | Kernel input getter reads the loaded image pointer at VA `0xffff0000507f73f0` and adds the selected boot-header page size. `0xce40..0xce64` returns kernel compressed size. | The normal-boot input allocation, pointer value and complete scratch extent are not established by the retained Fastboot log. The setter at `0xd680`, called at `0x53154`, demonstrates another input path; it is not proof of the normal-boot allocation. |
| `0xfae8`, `0xfb28` | Queries `mb_dtb` and loads its reserved base and size. | Runtime result for the new image is unavailable. |
| `0xfd00`, `0xfd38..0xfd48` | Queries `mb_kernel`, loads base/size into `x4/x20`, and compares its base with the kernel target. | This is binary intent, not proof that the candidate followed this path. |
| `0xfda0..0xfdb0` | Calls decompressor at file `0xe928` with compressed input, output alias, compressed byte count and reserved size. | Passing an output size does not prove every compression branch enforces a cumulative bound. |
| `0xe928..0xe95c` | Decompressor allocates a `0xc0`-byte stack frame and saves arguments. | This frame is not the maximum stack/heap requirement of all callees. |
| `0xe9dc..0xea64` | Legacy LZ4 loop calls the block decoder with `w3=0x800000` and advances the output cursor. The saved candidate has seven compressed blocks. | The inspected loop does not carry the original reservation size as an aggregate remaining-output bound. Do not infer a general 124.5 MiB decompression guarantee. The existing exact round trip proves the saved candidate's output length offline. |
| `0xfe08`, `0xfea8..0xfec8` | Queries `BL33-reserved`, then calls the release wrapper `0x15688` for BL33, kernel target, DTB, and conditionally ramdisk. | The caller does not verify these release return values. The wrapper has failure paths. No runtime completion is claimed. |
| `0x15688..0x1577c` | Release wrapper searches reserved slots, stride `0x98`, for a matching start, then invokes the size-based release helper. | Removing allocator bookkeeping establishes neither DMA drain nor a security-policy change. |
| `0xfed8` | Calls final memory/FDT processing at `0x161c8`, after those release attempts. | Further FDT patches and platform cleanup still follow. |
| `0x16654..0x16690` | Exports `mblock_info` with exact length `0x5818`. | This exporter precedes final BL31 callbacks and actual XNU entry. |
| `0x10054..0x10070` | Requests `MTK_SIP_KERNEL_BOOT`, `0xc2000115`, with kernel and FDT targets. | This request is not the final effective memory-isolation state. |

The output directory includes disassembly for each critical range. Eleven instruction assertions and five pinned string assertions corroborate the decoder and sequence. Capstone is only used for offline decoding.

## Retained allocation log

Original line numbers refer to `pl-lk-live.bin`. A compact extract is saved as `corroborated/retained-allocation-extract.json`.

| Lines | Observation | Lifetime conclusion |
| --- | --- | --- |
| 3446–3449, 3622, 4267 | `mb_kernel` reserves `[0x40000000, 0x47c80000)`. | A reservation exists at these historical LK events. The normal-boot code later attempts to release it. |
| 3450–3453, 4268 | `mb_dtb` occupies `[0x47c80000, 0x48080000)`. | Reserved size is 4 MiB; this is larger than the saved 485,760-byte FDT. |
| 3482–3485, 4276 | `BL33-reserved` occupies `[0x50700000, 0x62700000)`. | Covers LK's declared mapping; a full input/scratch allocation trace is still needed. |
| 3490 onward, 4277 | `mb_ramdisk` occupies `[0x66f00000, 0x6af00000)`. | Separate from the embedded XNU md0/md1 destinations. |
| 4264 | Free-pool entry includes `[0x1c0000000, 0x33d600000)`. | Historical allocator availability only. |
| 4825–4827 | `ccci_tag_mem` allocated at `[0xbfdf0000, 0xbfe00000)`. | Differs from the saved Android FDT's tag allocation. |
| 4829–4831, 4840 | `md_mem_usage` allocated at `[0xd0000000, 0xf0000000)` with 32 MiB alignment, then freed in this Fastboot capture. | Do not treat the temporary 512 MiB block as a surviving XNU reservation. |
| 4867 | `system_fastboot_buffer` occupies `[0xf4400000, 0xfc400000)`. | Fastboot-specific allocation; not a normal-XNU boot map. |

These allocator operations are dynamic. The log's selected slot was B, but its verified scope explicitly lacks a kernel handoff marker. Combining that slot selection with a different XNU photograph cannot establish a same-boot trace.

## Corroborated saved mblock layout

[duchamp_mblock.py](../tools/duchamp_mblock.py) accepts only the observed v2 layout. It checks exact length, magic, version, counts, names, rank, alignment, interval overflow and overlaps.

| Field | Offset and size |
| --- | --- |
| Free count | LE64 at `0x0` |
| Free entries | Up to 128 entries at `0x8`, stride `0x18`, containing start, length and rank |
| Magic/version | LE32 `0x99999999` at `0xc08`, version 2 at `0xc0c` |
| Reserved count | LE32 at `0xc10`, zero padding at `0xc14` |
| Reserved slots | 128 slots at `0xc18`, stride `0x98`, start/length/mapping followed by a 128-byte name |

The saved archive has 29 active free entries and 52 reservations. Reserved slots contain holes; the highest active slot is 57. Scanning only the first 52 slots would miss actual reservations. Free slots after the free count contain stale bytes and are deliberately ignored. All 52 active reservation tuples, including mapping/no-map interpretation, match the fixed FDT nodes exactly. No active free/reserved intervals overlap.

The saved allocator free pools cover both the reference low Image and the high XNU window. Kernel/DTB/BL33 reservation slots are no longer active in this saved property. This is consistent with the inspected release/export ordering, without proving which release calls completed in a future B boot.

## Modem and DMA interpretation

The saved FDT selects DPMAIF version 3 at `/soc/dpmaif@10014000`. Xiaomi source pinned at `3c4ccd07d5624879555ec710c11bb8818e5cb5c6` supplies the relevant consumers.

- `drivers/misc/mediatek/eccci/hif/ccci_dpmaif_resv_mem.c`, lines 57–155, resolves cached/uncached reserved memory and calls `dma_map_single()` or `ioremap_wc()`.
- `ccci_dpmaif_bat.c`, including lines 123, 233 and 345, uses streaming/coherent DMA interfaces for data buffers.
- `ccci_dpmaif_drv_v3.c`, lines 57–138, obtains modem reserved memory and programs DPMAIF bank remaps. These are DPMAIF remaps; they do not establish the full modem/fabric/SMMU accessible address space.

[Xiaomi reserved-memory code](https://github.com/MiCode/MTK_kernel_device_modules/blob/3c4ccd07d5624879555ec710c11bb8818e5cb5c6/drivers/misc/mediatek/eccci/hif/ccci_dpmaif_resv_mem.c), [buffer mappings](https://github.com/MiCode/MTK_kernel_device_modules/blob/3c4ccd07d5624879555ec710c11bb8818e5cb5c6/drivers/misc/mediatek/eccci/hif/ccci_dpmaif_bat.c), [DPMAIF bank remaps](https://github.com/MiCode/MTK_kernel_device_modules/blob/3c4ccd07d5624879555ec710c11bb8818e5cb5c6/drivers/misc/mediatek/eccci/hif/ccci_dpmaif_drv_v3.c).

The dynamic DPMAIF `alloc-ranges` are Linux allocation requests. Intersection with the low Image is a potential policy conflict, **not proof that LK allocated modem buffers over that Image**. The historical `mb_kernel` reservation is positive counter-evidence to that simple inference. Neither observation establishes which masters can write the candidate at actual XNU entry. Absent `iommus`, allocator free space, `no-map`, and HCE shutdown each leave that question unresolved.

The saved BL31 handoff handler `0xb63c`, descriptor `0x65500`, invokes group-5 callbacks `sip_emi_set_nsr_permission` (`0x37150`) and `spm_smpu_hre_first_bk` (`0x3b5f8`). The binary SHA-256 is `716222a632e4a0623a2e467e17f1d36f38a37f79a1c026447fe724e75e90e07e`. Existing [LK/BL31 audit](../tools/audit-duchamp-lk-handoff.py) pins these bytes. Effective protection ranges, retained IOMMU translations, outstanding transactions and permitted firmware writers at final exit remain unmeasured.

## Verification

The three host suites passed 16 interval tests, 19 phase/lifetime tests and 15 bounded mblock parser tests, all exit 0. The archive audit passed 11 instruction assertions and matched 52/52 FDT reservations. The reference kernel, Image, envelope and FDT hashes were rechecked, and both embedded filesystem hashes matched their reference manifest. Exact commands, log hashes and exit codes are in `outputs/duchamp-memory-ownership-20261117/verification.json`.

Only offline Python analysis changed. No kernel, bootshim, payload, ADT or boot envelope was rebuilt. Existing QEMU results remain historical results for the preserved configuration; QEMU was not rerun in this phase.
