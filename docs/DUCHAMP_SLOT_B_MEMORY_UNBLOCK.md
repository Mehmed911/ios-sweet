# Duchamp Slot B memory unblock

2026-11-17, updated with actual allocation-log evidence. Branch `duchamp-bootstrap`, HEAD `d91562d9c2bd3bc33d52550c101de1009bb41dc0`, with existing uncommitted work retained. Final readiness remains **BLOCKED_BY_MEMORY_EVIDENCE**. A read-only acquisition now preserves a real normal-boot LK allocation trace from Android **A**. It does not establish the proposed XNU **B** allocation or final DMA isolation. The subsequent [Blackbox source audit](DUCHAMP_LK_BLACKBOX_HISTORY.md) corrects the initial ring-size interpretation and finds no supported historical export under the present restrictions.

## Preserved baseline

The 32 MiB read-only md0 + 4 MiB writable md1 candidate was not rebuilt or modified. Current hashes were checked against the previous manifest.

| Artifact | SHA-256 |
| --- | --- |
| Source-built XNU | `e7b51ecb16fe9ad21a78455714b2bf26c1dee1fbc3a6a7f0cb3971a9cd569457` |
| 57,417,168-byte uncompressed Image | `2be899ce4c76a740c3006089efd25e292b42b6e59bee10722610dd4203cb426b` |
| 14,888,960-byte Android v4 lab envelope | `86c23337ce9aa9cd0913592ed03063405e5b7a42dc3446a822bd753575caf1bd` |
| Saved Duchamp FDT | `9c49589f70044127be8941a9ea5537977f440ccd5ac15cfd24e120c8a1181d29` |

Full intervals remain in [the placement decision](DUCHAMP_SAFE_PLACEMENT_DECISION.md) and workspace `outputs/duchamp-memory-ownership-20261117/baseline-reference.json`. This phase's evidence is in `outputs/duchamp-memory-unblock-20261117/`, outside the repository. `baseline-preserved.json` binds the unchanged candidate and the previous 50-test sources and manifest. Existing launchd PID 1, dual-RAMDisk and Mach-O results remain their prior verified results; those guest tests were not rerun.

The new follow-up artifacts are in workspace `outputs/duchamp-actual-lk-memory-20261117/`. Copies of both pre-update reports and `NOTES.md` are retained in its `before-document-update/` directory. New offline decoder tests and a real-log observation reader do not alter XNU, bootshim, memory policy, firmware or the candidate.

## New source-level decompression findings

The matching complete LK C tree is unavailable. Conclusions below come from the actual saved LK binary, SHA-256 `f85373d3b4cdf3c959e38bbbfe198a2857e03a5266c6f2a40c319549a5ba957a`, with 28 instruction assertions. Offsets are **partition-file offsets**. File `0x200` maps to LK VA `0xffff000050700000`, PA `0x50700000`.

### Normal input provenance is now traced

The previous audit identified the input getter but had not connected the setter to normal boot. The normal boot dispatcher at `0x10ce0` calls the load path at `0x52abc`; `0x52e7c` then calls the loaded-partition consumer at `0x52f40`. Its loop uses 32-byte partition records, reads each data pointer at entry `+8`, selects the requested boot partition, and passes its pointer through `0x53148..0x53154` to setter `0xd680`.

The setter stores that pointer at LK VA `0xffff0000507f73f0`. Getter `0xcd50..0xcda0` adds the selected header page size and returns the compressed kernel input to `boot_linux_fdt`. Thus the setter is part of the normal-boot source path as well; its actual pointer is **dynamic**, not a fixed PA recoverable from the boot header alone. For the v4 candidate, the kernel data begins after its 4 KiB boot header page. The actual loaded partition pointer, its PA translation and the resolved slot still need runtime evidence.

The saved code also traces the allocator supplying ordinary loaded partition data.

| Location | Verified instruction flow | Scope |
| --- | --- | --- |
| `0xa44f8..0xa4500` | Returns the initialized AvbOps table at VA `0xffff0000507f0c10`. Its `+0x20` preloaded-partition callback is initially null. | Initial binary data, not proof the table was never changed at runtime. |
| `0x9fbfc..0x9fd88` | Full-partition loader checks that callback. Its fallback at `0x9fccc..0x9fcf8` allocates data, stores the pointer and invokes the partition reader. | Identifies the normal allocation path without executing storage I/O. |
| `0x9fcd0 → 0xa0398 → 0x9fe48` | Fallback allocation reaches the platform AVB allocator. | No fixed input PA is encoded here. |
| `0xa4504..0xa4588` | Requests **`mb_avb`, 0x8c00000 bytes = 140 MiB**, aligned to 4 KiB, through the mblock allocator, then maps it as `vm_avb`. | Physical reservation and virtual mapping bases depend on runtime allocators. |
| `0x9fe48..0x9fec0` | Allocator obtains the mapped pool base and size through pointers at file `0xf1d10` and `0xf1e68`, rounds each allocation to a 64-byte boundary with separation, and checks the resulting offset against pool size before updating its cursor. | A source bound conditional on valid pool/cursor state and nonoverflowing actual requests. It is not a general hostile-input proof or ownership grant. |
| `0xfdb8 → 0xa458c` | After successful kernel decompression, calls the AVB pool release/unmap path. | Actual success, subsequent allocations and post-release writers remain unobserved. |

The loaded-partition layout and fallback behavior have a compatible comparison in AOSP Android 14 libavb. This is a source comparison, not a claim that the retail firmware is byte-identical to that release. [Partition structure](https://android.googlesource.com/platform/external/avb/+/refs/tags/android-14.0.0_r1/libavb/avb_slot_verify.h), [full-partition fallback](https://android.googlesource.com/platform/external/avb/+/refs/tags/android-14.0.0_r1/libavb/avb_slot_verify.c). Downloaded source digests are in `primary-source/manifest.json` in this phase's output directory.

### Exact allocator constraints and lifetime

The additional disassembly is preserved as `allocator-selection.disasm`, `allocator-normalizer.disasm`, `allocator-commit.disasm` and `pool-release-and-users.disasm` in the follow-up output. These are binary-source findings, not measurements of B hardware.

- The call at `0xa4504` supplies size `0x8c00000`, alignment `0x1000`, upper limit `UINT64_MAX`, fixed start zero, mapping flag zero and name `mb_avb`. Wrapper `0x146cc` acquires the allocator lock and calls core `0x14770` with lower bound zero. There is no caller requirement that this pool be below 4 GiB. The mapping flag is allocator bookkeeping, not a security delegation.
- The core validates size, alignment and map state. Helper `0x17154` coalesces adjacent free intervals and removes emptied entries. It is not independently established as a general-purpose sorter. The loop at `0x149cc..0x14af8` retains the last eligible free-list entry, then computes `align_down(min(free_end, limit) - size, alignment)` at `0x14b14..0x14b28`. Do not replace this with an unconditional claim of the highest physical address without also proving free-list ordering.
- An additional high-address most-significant-bit boundary check appears at `0x14aa8..0x14af4`; it does not establish modem, IOMMU, DMA or security-domain exclusion. The reservation is recorded and the selected free interval split/removed in the subsequent commit path. Active modem reservations participate in the same allocator bookkeeping. Actual reservation order and contents remain boot-specific.
- The `vm_avb` mapping helper is at file `0x6513c`. The mapped base and pool length are retained at LK VA `0xffff0000508ac2b8` and `0xffff0000508ac2b0`. The suballocator at `0x9fe48` uses cursor `0xffff0000508ac1d8`: `p = align_down(base + cursor, 64) + 64`; it updates the cursor only if `p + request - base <= pool_size`. This formula does not prove safety for arbitrary overflowing requests or an invalid base/cursor.
- After decompression, caller `0xfdb8` invokes `0xa458c`. It converts the mapping to PA, calls free wrapper `0x15688`, then mapping-release helper `0x654f8`, with error branches. This routine does not zero the old pool or clear all base/size/cursor globals, drain DMA, invalidate a foreign IOMMU or transfer policy ownership. The caller can continue after reporting a release error. A free message alone is not a verified success return.
- Once successfully released, the pool can be reused by later allocations. The current evidence does not identify every later user. Later BL33/kernel/DTB releases and final mblock export also change CPU bookkeeping. A final free-pool snapshot cannot reconstruct a released pool's original address after coalescing, nor reserve it for XNU.

### LZ4 core workspace is smaller and better bounded than the unresolved whole boot

The candidate is a known seven-block legacy LZ4 frame. The wrapper at `0xe928` passes an 8 MiB output capacity per block at `0xea30..0xea34`. The exact block routine occupies file `[0x59120, 0x59438)`. Its only external call is the saved memmove at `[0x67e98, 0x680a8)`. This memmove has no callees or stack frame; the decoder has a fixed `0x30`-byte frame. Both routines have closed direct control flow and no heap allocator call. Their temporary state uses registers, stack and the output history, rather than a separate allocated decode dictionary.

The wrapper's frame is `0xc0` bytes; `boot_linux_fdt` has a `0xa0`-byte frame. These identified simultaneously active frames total **400 bytes**. That is not the complete LK stack peak: ancestor frames, interrupts, timing and diagnostic callees outside the decoder pair remain outside this result. The 140 MiB AVB pool is a separate loaded-data allocation, not LZ4 scratch.

### Exact decoder replay found a real output-tail detail

An isolated new QEMU probe executed the **unchanged saved ARM64 decoder and memmove**, with the current candidate's exact compressed bytes. It did not boot LK, BL31 or XNU. The copied 990,320 firmware bytes in its ELF were checked byte for byte against the saved LK executable payload. The probe supplies ordinary Normal RAM via an identity map; its low virtual placement preserves the firmware routines' PC-relative references. No firmware instruction was patched.

All seven returned outputs matched the reference Image byte for byte.

| Blocks | Expanded bytes |
| --- | ---: |
| 0–5, each | 8,388,608 |
| 6 | 7,085,520 |
| Total | 57,417,168 |

The decoder also changed **four canary bytes after the logical Image end**, at relative offsets `[57,417,168, 57,417,172)`. At the historical output PA this is `[0x436c1dd0, 0x436c1dd4)`. These writes are within the supplied last-block capacity. The earlier logical file extent alone therefore understates the decompressor's workspace. A safe physical plan must account for decoder capacity/padding, not merely raw file length.

For these seven blocks, the per-call capacity envelope is **56 MiB**, `[0x40000000, 0x43800000)`, contained by the historical `mb_kernel` reservation ending at `0x47c80000`. The exact replay left the outer capacity canaries unchanged. A canary comparison records changed bytes, not every transient memory write, and neither this test nor the capacity arithmetic proves the physical execution used those addresses, reservations or permissions. No production candidate change was needed or made.

### Guard-page regression resolves the four-byte write

The new test executes the same unchanged LK decoder and memmove with real unmapped input/output end pages in isolated ARM64 QEMU. Sources: `duchamp/tests/lk_lz4_bounds.{S,c,ld}`; runner: `tools/test-duchamp-lk-lz4-bounds.py`. The ELF's 990,320-byte firmware segment is compared with the saved LK bytes after linking. No physical device operation is part of this runner.

The deliberate negative fixture maps only the last block's logical output but falsely advertises 8 MiB capacity. The first crossing write traps at original partition offset **`0x5931c`, `str x21, [x6]`**. Effective address is logical end minus four, access width eight, so four bytes cross the logical end. In the replay, the upper four bytes are zero; the normal capacity test verifies exactly those four changed bytes. The preceding `ldr x21, [x2]` at `0x59314` identifies an optimized match-copy path. These bytes are a wide-copy tail, not another length field or semantic output.

| Case | Actual result |
| --- | --- |
| Seven original blocks, each with advertised 8 MiB capacity | All returned lengths and logical output bytes match the preserved Image. Source bytes and pre-buffer canaries remain unchanged; guard pages do not fault. |
| Last block with capacity exactly 7,085,520 bytes and guard immediately afterward | Returns 7,085,520, exact output match, no crossing fault. The bounded path avoids the wide overstore for this input. |
| Last block with capacity 7,085,519 | Returns `-30642`, no boundary fault. |
| First block with capacity 8,388,607 | Returns `-4616205`, no boundary fault. |
| Zero output capacity | Returns `-1`, no boundary fault. |
| Last compressed input truncated by one byte | Returns `-30642`, no input/output boundary fault. |
| Advertised capacity deliberately exceeds mapped output | Expected write translation fault at guard `0x46000000`, ESR `0x96000047`; exact offending store and register address verified. |

Result: **13/13**, compile exit 0, QEMU exit 0, in `lz4-guards-final/verification.json` and `qemu.log`. The intentional fault is a passing negative case, not a complete LK boot. This is a fixed-fixture regression, not an exhaustive decoder memory-safety proof.

The tail is not included in the returned logical length. The wrapper advances by that returned length; the bootshim's embedded payload is bounded by its own start/end symbols (`duchamp/bootshim/shim.c`). The four tail bytes remain ordinary RAM until overwritten; no assertion is made that unrelated later code cannot inspect them. They must remain inside live output capacity throughout decoding. At the historical output base their end `0x436c1dd4` is below capacity end `0x43800000`, but the proposed B reservation/lifetime still needs actual evidence.

The combined *reserved capacities* of historical `mb_kernel` (124.5 MiB) and the source-requested `mb_avb` (140 MiB) are 277,348,352 bytes. This is not a measured boot peak. LK's own mapping, FDT, ramdisk staging, other firmware allocations and complete stack lifetimes must also be accounted for. The former 72,299,962-byte compressed-input-plus-logical-output figure is only a lower bound on data, not an upper bound on the bootloader's memory footprint.

## Actual existing runtime channel captured, limited to Android A

Read-only ADB found the connected device running `duchamp` / `mt6897`, build `V816.0.17.0.UNLMIXM`, slot `_a`. Existing Magisk root was available; no root installation or device configuration change was performed. Reading `/proc/pl_lk` as ordinary shell was denied. The existing root reader returned **257,652 raw bytes**, saved intact as `android-a-current-pl-lk-root.raw`, SHA-256 **`5731b1ad6f2cf36194cff78e0dcfeaa7ed50f3f3ff4332313174554b0d61643b`**. Acquisition stopped below its 524,288-byte limit. The Android boot-ID digest was unchanged before/after the read. This identifies the acquisition session, not authenticated LK-to-XNU continuity.

Raw acquisition commands, errors and hashes are retained in `android-readonly-capture.json` and `android-root-readonly-capture.json`. The first root receipt's broad error-substring heuristic marked `read_success=false` because real LK text contains `not found`. The real-log parser checks raw digest/size and actual LK allocation/lifetime/jump structure instead; the original receipt is retained, not silently rewritten. The initial unprivileged 37-byte permission message is not a valid firmware log even though `exec-out` returned zero.

The pinned MiCode `drivers/misc/mediatek/log_store/log_store.c`, locally saved in `outputs/duchamp-diagnostic-channels-20261111/`, shows the DRAM-backed `pl_lk_log_show()` at lines 213–233. It copies the existing log and has no UFS operation. It exposes no historical record selector. The separate proc write handler is not a way to recover B and was not used. See [reader analysis and capture plan](DUCHAMP_RUNTIME_ALLOCATION_TRACE_PLAN.md#available-records-and-their-actual-scope).

Line references below count LF-delimited lines, stripping CR only, as in `android-a-current-pl-lk.normalized.txt`.

| Lines | Actual recorded observation | Limit |
| --- | --- | --- |
| 4664 | `mb_avb` allocation `[0x334a00000, 0x33d600000)`, 140 MiB, lower bound zero, limit `UINT64_MAX`, map 0. | Real A allocator message; not the unknown B address. `vm_avb` and partition-data pointers are not logged. |
| 4989–4990 | `decompress_kernel takes 244 ms`, followed by matching `mb_avb` free message. | A different kernel image; no proof of successful unmap/free returns or the new candidate's LZ4 sequence. |
| 4970, 5327–5336, 5344 | Modem pool request, partial releases and `Trigger MD run`. | Real modem activity on A. No final B protection or DMA exclusion is inferred. |
| 4121–4125 | `platform_mtksmmu_protpgd` allocation, PGD-clean and `emi_mpu_set_protection ret=0` messages. | No stream/domain/table contents, final policy readback or coverage of XNU buffers. |
| 5695–5699 | BL33/kernel/DTB/ramdisk/boottag free messages. | Source/log ordering, not enduring XNU ownership. |
| 5797, 5808–5810 | Slot 0, Linux entry `0x40000000`, ramdisk `0x66f00000`, DTB `0x47c80000`. | Android A boot, not an XNU-entry witness. |
| 5812–5816 | OEM `blackbox` headers, printed boot index `0x31a` = 794, cursor `dump_count=4`, 8 MiB stride, and `GetPLLKlog_from_logstore ... end size:251399`. | Later instruction analysis establishes five positions for this writer, not four-slot capacity. Historical B availability/completeness and a supported export remain unverified. No blackbox partition was read or written. |

New offline reader `tools/inspect-duchamp-lk-allocation-log.py` extracts the actual pool, reported release, ordering, jump, slot and producer index with line numbers. It rejects inconsistent acquisition/slot/lifetime records, but **always** reports `physical_access_authorized=false`, `firmware_origin_authenticated=false` and `complete_slot_b_handoff_established=false`. It is an observation tool, not another authorization system. Nine tests derived from this real capture passed, including altered slot, changed boot, changed bytes, missing/duplicated allocation, mismatched release, overflow and permission-error input. See `observation-checks-final.json` and `android-a-allocation-observations.json`.

## What is still unverified, classified by next action

| Blocker or subproblem | Classification | Smallest concrete next action and required evidence |
| --- | --- | --- |
| Normal loaded-data pointer path, AVB pool request, LZ4 core calls and stack | `RESOLVABLE_FROM_EXISTING_SOURCE` | Completed to the source/binary scope above. Preserve the 28 assertions and exact decoder replay. Do not promote them to runtime ownership. |
| Actual `mb_avb` PA, mapped VA, cursor and loaded boot data PA in the proposed B boot | `REQUIRES_EXISTING_RUNTIME_TRACE` | Normal A logs now prove the allocation channel exists and retain an actual A PA. Obtain a supported export of the relevant B record with selected-image identity and mapping/input pointers. Neither A nor the old Fastboot record supplies the B values. |
| Complete LK stack/workspace peak | `REQUIRES_SUPPORTED_FIRMWARE_INSTRUMENTATION` | Matching LK source or supported stack high-water/allocator instrumentation for the actual path, including timing/logging helpers and ancestors. Record stack bounds and all allocations; a 400-byte partial call chain is insufficient. |
| Reservation state after the final release/unmap operations | `REQUIRES_EXISTING_RUNTIME_TRACE` | A retained normal-boot final mblock record and ordered allocate/free events after `0xfdb8` and the later kernel/DTB/BL33 releases. Prove completeness/retention before treating this route as available for B. |
| Effective memory ownership after final BL31 callbacks | `REQUIRES_SUPPORTED_FIRMWARE_INSTRUMENTATION` | Vendor-supported post-callback telemetry or approved independent observation, with policy semantics and actual entry correlation. No such supported producer is established in the current evidence. |
| Modem/peripheral writer exclusion, retained translations and admitted DMA | `REQUIRES_HARDWARE_VALIDATION` | The isolation owner must establish protected ranges, actual master/domain routing, drain or fencing, and persistence through XNU entry. Non-overlapping CPU buffers do not establish this. |
| Existing retail API returning a trustworthy final ownership/DMA attestation | `UNSUPPORTED` in the reviewed interfaces | No applicable API or producer was found in the reviewed stock exports/dispatch evidence. Obtain vendor documentation or supported instrumentation; do not invent SMC identifiers or tokens. This does not assert that no vendor-internal facility exists. |
| Relocating low LK output within the unchanged boot contract | `UNSUPPORTED` by the current candidate/path | The source compares the target with `mb_kernel`; header/provider changes would also need matching reservation evidence. No alternate low output was prepared. |
| Relocating the high XNU window | `REQUIRES_HARDWARE_VALIDATION` | Existing geometric alternatives do not prove exclusive ownership or DMA isolation. Native preflight currently pins the original base. Retain it until independent evidence supports any change. |

## DMA scope and relocation decision

Potential relevant non-CPU writers include modem/DPMAIF, storage, GPU, APU, SCP/SSPM/MCUPM, DSP/VCP, connectivity and display engines. Their DT nodes or reserved buffers identify dependencies; they do not show which are active during this B boot. The saved FDT declares separate MT6897 APU, display and MDP IOMMU providers. It does not supply the effective domain, stream routing, page tables or mapping epoch at final entry. No current master is assumed isolated merely because another master has a declared IOMMU.

Pinned Xiaomi DPMAIF v3 source programs modem bank remaps and uses Linux DMA APIs. These remaps do not specify every modem/fabric aperture. BL31's `sip_emi_set_nsr_permission` and `spm_smpu_hre_first_bk` run after the LK allocator/export sequence, so a pre-BL31 CPU map cannot establish their effective protection state. The required evidence includes legacy submissions and in-flight work, bypass routes, security-domain permissions and future firmware writers. See [existing DMA analysis](DUCHAMP_UFS_DMA_SAFETY.md) and [modem source references](DUCHAMP_LK_MEMORY_ALLOCATION_AUDIT.md#modem-and-dma-interpretation).

No alternate placement is independently justified. The historical high window `[0x1c0000000, 0x1e0000000)` already clears known fixed reservations. Windows at `0x140000000` or `0x200000000` have the same unresolved ownership and DMA issue, and fail the current native base policy. Above-4-GiB placement alone is not a DMA fence. The preserved base, kernel mappings, md0/md1, ADT and bootshim stay unchanged.

## Verification and actionable conclusion

New checks were limited to 28 binary assertions, the immutable-decoder replay, trace-file inspection and baseline hashing. The source audit exited 0 and final replay exited 0. Earlier probe attempts are retained: host linker selection failed first, the initial MMU-off probe timed out on an unaligned Device-memory access, the vector-enabled probe diagnosed that access, and the strict logical-end canary check exposed the four-byte tail. The final Normal-RAM probe checks the supplied capacity fence while still reporting that tail. No failed attempt was counted as a passing hardware or kernel boot.

The preceding paragraph describes the earlier seven-block probe and its preserved failed harness attempts. The new guard regression passed 13/13; the new real-log reader checks passed 9/9. Exact new commands, exit codes and log hashes are in `lz4-guards-final/verification.json`, `observation-checks-final.json` and the follow-up `verification.json`. The existing 50/50 memory-test sources and manifest remain hash-preserved, not rerun. No full-XNU QEMU regression was required because no guest source or candidate changed.

**Next action:** establish whether an existing supported read-only OEM export can recover the relevant B `blackbox`/LK record without a new boot or partition operation, as specified in [the trace plan](DUCHAMP_RUNTIME_ALLOCATION_TRACE_PLAN.md). Even a complete LK allocation trace still needs final BL31 policy/isolation and actual XNU-entry correlation. No supported existing channel reviewed here supplies that complete record. Dependent hardware work stops. Only existing Android properties, identity and the in-memory LK proc log were read; no reboot, slot change, flash, partition write, physical UFS MMIO/DMA or firmware change was performed. The candidate is unchanged; nothing was committed or pushed.
