# Duchamp LK Blackbox history

2026-11-17. Repository `ios-sweet`, branch `duchamp-bootstrap`, HEAD `d91562d9c2bd3bc33d52550c101de1009bb41dc0`, existing uncommitted work retained.

**Result: EXPORT_INTERFACE_UNAVAILABLE within the reviewed interfaces and current restrictions.** The saved LK implements persistent multi-generation Blackbox storage. No supported historical export usable from the running Android session without physical UFS access, a reboot or another prohibited action was established. This is not a finding that the desired record was erased or that Xiaomi has no private diagnostic facility.

## Evidence and reproducibility

- Actual saved firmware: workspace `work/phone-firmware/lk_a.bin`, 16,777,216 bytes, SHA-256 `f85373d3b4cdf3c959e38bbbfe198a2857e03a5266c6f2a40c319549a5ba957a`. Complete matching LK C source is unavailable; the findings below are from its actual ARM64 instructions, not another board's source or decompilation.
- Prior read-only Android A capture: `outputs/duchamp-actual-lk-memory-20261117/android-a-current-pl-lk-root.raw`, 257,652 bytes, SHA-256 `5731b1ad6f2cf36194cff78e0dcfeaa7ed50f3f3ff4332313174554b0d61643b`. References count LF-delimited lines with CR removed, as in its normalized companion.
- New analysis output: workspace `outputs/duchamp-lk-blackbox-history-20261117/`. It contains disassembly, source receipts, exact test commands, hashes and `verification.json`. No phone command was executed in this follow-up.
- Public kernel sources were fetched at MiCode revision `3c4ccd07d5624879555ec710c11bb8818e5cb5c6`. Exact Git blob hashes were reproduced locally. The official `log_store.c` is byte-identical to the earlier saved community copy; its SHA-256 is `6fe42927061375e0997278e553d7f4ee1d6e2797c35a4a5ba03fd30c935d8751`. This establishes source identity, not that every installed kernel instruction matches it.

All LK offsets below are **partition-file offsets of the saved image**, not instructions to read live memory or storage. File `0x200` corresponds to LK VA `0xffff000050700000`.

## Storage, lifetime and overwrite behavior

| Question | Source/log evidence | Conclusion and limit |
| --- | --- | --- |
| Where are records stored? | Writer `0x51a24` resolves the literal `blackbox` at file `0xbef66` through `0x656cc`. Read calls use `0x65758`; write calls use `0x657c8`. These dispatch through the block-device callbacks at `+0x70` and `+0x80`. The archived Fastboot log `outputs/duchamp-slot-b-live-lk-log-20261111/pl-lk-live.bin`, LF line 4813, lists label `blackbox`, size 165,670,912 and block size 4096. | Storage-backed label `blackbox`, distinct from the current DRAM proc buffer. The literal has no A/B suffix. No current partition was opened or read. |
| Can records survive reboot? | `0x51a64..0x51a70` reads the saved table header; later code reads the content header and a selected old record, updates them and writes back. The real A log shows a pre-existing generation 794 and cursor 4. | Persistent retention is implemented. Actual successful complete writes, availability of a particular old B record and survival of intervening events remain unverified. |
| How many generations? | `0x51d08` compares the old cursor with **5**. `0x51d10` chooses 1 if equal, otherwise old cursor + 1. `0x51d30..0x51d34` selects `(new_cursor - 1) * record_stride + first_record_offset`. | **Five cyclic record positions**, conditional on valid metadata and successful writes. The sixth writer invocation reuses the first position. This is not five guaranteed complete records or five days/reboots of retention. |
| What did `dump_count=4` mean? | The content banner is printed at `0x51ccc`, before `0x51d18` stores the advanced cursor. | It was the previous cursor, **not four-slot capacity**. Earlier reports' four-slot interpretation is superseded by this instruction-level analysis. |
| Which generation belongs to the write? | `0x51ce8` prints table generation before `0x51d0c` increments its 32-bit value; `0x51e94` stores the incremented value in the selected record header at `+0x14`. | With the captured valid values, source intent is printed 794 -> persisted record 795, and cursor 4 -> position 5. No raw record 795 was recovered. Counter wrap/reinitialization must be handled; a printed number alone is not unique boot identity. |
| Is an entire record replaced atomically? | Writer issues several separate writes. Table, content and record-header writes at `0x51f2c`, `0x51f90`, `0x51fec` precede final PL/LK copy through `0x52050 -> 0x51934 -> 0x657c8`. Return tests shown use positive-byte results. | Complete atomic replacement is not established. A fresh header does not prove full payload retention. No complete 8 MiB slot overwrite or transactional integrity guarantee is demonstrated by the reviewed path. |
| Does it include allocation addresses? | `0x51934` obtains the existing PL/LK buffer and derives its write size from header fields at `+0x48`, `+0x4c`, `+0x58`, then writes those bytes. Real A lines 4664 and 4990 contain the `mb_avb` allocate/free messages. | It can store already-emitted allocator messages. It cannot manufacture missing input pointers, unmap returns or later policy measurements. Completeness of a B record is unknown. |
| Does it include slot identity? | The inspected record construction stores generation but supplies no verified typed slot/image-digest field. Real PL/LK payload can include `boot successfully on slot 0/1` and selected partition names. | Slot must be established from corroborated records and actual image/entry context. XNU strings, a host-selected slot or the record generation alone are insufficient. Unknown header fields are not guessed to be slot IDs. |

The reviewed table read uses relative offset `0x400` and size `0x400`; content-header location is read from table `+0x14`. The current printed geometry reports content header at `0x800`, first record at `0x1000` and stride `0x800000`. These describe the audited implementation and current A messages only. They are not an authorized physical extraction recipe.

The confirmed normal-boot caller is `boot_linux_fdt` at file `0x10050`, after its Linux-jump announcement and before the subsequent secure handoff call at `0x10070`. Its record therefore cannot, by itself, witness the later final BL31 policy changes or actual XNU entry. This does not establish every writer elsewhere in firmware. See `final-boot-caller.disasm`.

## Reviewed export interfaces

| Interface | Exact implementation | Can it recover the requested historical Blackbox generation now? |
| --- | --- | --- |
| Android `/proc/pl_lk` | [MiCode `log_store.c`](https://github.com/MiCode/MTK_kernel_device_modules/blob/3c4ccd07d5624879555ec710c11bb8818e5cb5c6/drivers/misc/mediatek/log_store/log_store.c), `pl_lk_log_show()` lines 213–233, open 237–240, DRAM mapping 352–361, registration 389. | **No historical selector in this reader.** It copies the mapped current buffer. Its existing root read was verified in the previous task on A; repeating it does not select an older B storage record. |
| Proc write handler | Same file lines 242–270; value zero calls `log_store_bootup()`, which changes boot/log state. | Not a read-only history-selection interface. Not used. |
| AEE current exception exports | [MiCode `aed-main.c`](https://github.com/MiCode/MTK_kernel_device_modules/blob/3c4ccd07d5624879555ec710c11bb8818e5cb5c6/drivers/misc/mediatek/aee/aed/aed-main.c), current-buffer macros lines 1329–1363, misc-device operations 2323–2362. | Reviewed callbacks expose `aed_dev.kerec.lastlog`/exception messages. No Blackbox generation-selector contract was identified. Names such as `lastlog` do not establish this storage format. No device ioctl or proc write was attempted. |
| Boot/reboot-reason export | [MiCode `mboot_params.c`](https://github.com/MiCode/MTK_kernel_device_modules/blob/3c4ccd07d5624879555ec710c11bb8818e5cb5c6/drivers/misc/mediatek/aee/mrdump/mboot_params.c), lines 1193–1215. | Reports reboot-reason state, not the five-record Blackbox ring. No evidence of historical allocator export here. |
| Fastboot `oem uefilog` | Actual saved LK handler `0x9234..0x931c` calls getters `0x141ac`/`0x141b8`, then copies the current PL/LK bytes. | No Blackbox generation input or storage-record read in this handler. Entering Fastboot would require a prohibited boot change. Not executed. |
| Fastboot `oem lkmsg`, `oem lpmsg`, `oem expdb` | Existing registry in `outputs/duchamp-diagnostic-channels-20261111/lk-diagnostic-channels.json`; saved handler slices in this output. | Memory/crash dump paths are not a documented Blackbox history selector. No supported historical export established; side effects and required mode must not be assumed safe. Not executed. |
| Archived `lkmsg`/`lpmsg`/Fastboot exports | Prior bounded raw captures searched for `blackbox`, generation and header messages. | The only match in those three files is the `blackbox` device-label listing. No historical table/content/record header or correlated B allocation trace was recovered. |
| OEM private diagnostics | No matching published tool/interface contract found in the reviewed sources/searches. | Unknown, not declared nonexistent. Requires Xiaomi/MediaTek documentation of an existing read-only export. No raw partition read, memory scan, guessed command or offset was tried. |

The pinned official log-store directory and recursive AEE tree are saved under `primary-source/`. Searches found other-device third-party reverse engineering; it was not used as authority for Duchamp fields, addresses or export commands. Source coverage is bounded: proprietary Xiaomi userspace/service tooling and the complete matching LK C tree were unavailable.

## Offline changes and tests

`tools/audit-duchamp-lk-blackbox.py` pins the actual LK hash and checks **28/28 instruction assertions**, including five-position wrap, generation increment, selected-record calculation, storage dispatch and writer/caller order. It does not execute LK, access a phone or decode an invented historical container.

The existing `tools/inspect-duchamp-lk-allocation-log.py` now checks the **printed current-buffer** Blackbox table/content metadata: magics, versions, geometry, cursor and agreement between generation messages. `tools/test-inspect-duchamp-lk-allocation-log.py` passed **16/16** cases. New negative cases cover corrupt metadata, invalid cursor/stride, conflicting/missing producer ID and missing acquisition ID. A consistently edited older generation still cannot establish freshness, provenance or historical recovery; those fields remain false even when printed metadata is internally consistent. Existing wrong-slot, changed-boot/bytes and incomplete allocation cases remain covered.

This is not a historical binary-record integrity/authentication test. Phase 3's historical parser is conditional on a supported export; that condition is unmet. No proprietary record integrity scheme, firmware identity, freshness rule or signature was invented. Both historical-recovery and physical-authorization results remain false.

Exact commands and exit codes are in `targeted-checks.json`: source audit, hardened real-A observation extraction and tests all exited 0. Unchanged original-decoder 13/13 and source-built XNU/32+4 MiB results were preserved, not rerun. No kernel, bootshim or authorization code changed.

## Decision

**EXPORT_INTERFACE_UNAVAILABLE** for a supported historical read under the allowed current boot and no-physical-UFS restrictions. Whether the old B record is retained is **unknown**. Do not report `HISTORICAL_RECORD_NOT_RETAINED` without actual generation/completeness evidence, or `HISTORICAL_RECORD_AVAILABLE` from a ring layout alone.

The smallest next external action is documentation or an existing OEM **read-only historical export**, including which generation/slot/image it returns, completeness and origin verification. If only raw storage or a boot-mode change is available, that lies outside this task and must not be attempted automatically. Final memory ownership/DMA evidence is a separate requirement even if history becomes readable. See [the historical evidence decision](DUCHAMP_SLOT_B_HISTORICAL_EVIDENCE.md).
