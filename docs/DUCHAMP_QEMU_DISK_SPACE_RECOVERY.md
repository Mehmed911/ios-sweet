# QEMU capacity recovery without deletion

Date: 2026-11-20. Evidence: `C:/Users/Mehmedamir/Documents/Codex/2026-10-23/referenced-chatgpt-conversation-this-is-an/outputs/duchamp-abi-repair-20261120` (`OUT`).

**Resolved for this regression run. No files were deleted or relocated.** Source, working kernels, native boot candidate, Android recovery images, evidence and user files remain retained. No phone operation, WSL shutdown, VHD compaction, filesystem resizing, commit or push was performed.

## Capacity and preservation assessment

C is the only usable attached volume. `Get-Volume` reports998,012,055,552bytes for C; the two unlettered small volumes are recovery/system volumes, not relocation targets. No D destination was available. The initial interactive assessment found about2.2GiB free. WSL's apparent631GiB ext4 free space does not establish that its host-backed file can grow; host capacity was the failing resource.

The Ubuntu VHD was about317.75GiB logical size when assessed. Its NTFS metadata and contents were not compressed, compacted or moved. Source outputs contained about32GiB of `.hfs`/`.bin` files and2.59GiB of logs. Logical file sizes are not equivalent to allocated host clusters.

Before mutation, Git status, the complete tracked binary diff and existing NOTES/tool/evidence snapshots were saved in `OUT/baseline`. The25 protected native/recovery files were excluded from compression selection and rehashed after the regression: **25/25 unchanged**. The current source-built kernel and its1127 link inputs were separately verified by the existing source-kernel selector.

## Reproducible artifacts and retained evidence

Reproducible closed copies: old test `payload.bin`, `payload.rebuild.bin`, `root.hfs`, `ramdisk-final.hfs`. Logs, manifests, source inputs and archives were retained as evidence. All native/recovery paths, source directories, firmware/stock/Android/Magisk images, active VHDs and the frozen native candidate were excluded.

Relocation to another volume was not possible. Deletion was not authorized. The chosen operation was **lossless NTFS compression in place**, supported by Microsoft's [compact command](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/compact). This retains paths and readable contents. Microsoft's [WSL disk-space documentation](https://learn.microsoft.com/en-us/windows/wsl/disk-space) explains the host-backed virtual-disk context; no disk-management operation from that document was run.

## Implemented operation and accounting

1. Pilot: one closed, reproducible regression payload,86,656,224bytes. Compressed storage reported16,306,176bytes; exit0. SHA-256 before and after: `aa7c948ec39733c5af9ab712ccb1488fc26d3f2ef412dcd0918508b28c4a6c98`.
2. Prepared an explicit483-file proposal, restricted to the outputs workspace, exact names above, size>=16MiB, no reparse points and no protected paths. Saved `OUT/compression-proposal.json` before execution.
3. Applied `compact.exe /C /Q <exact-file-path>` individually. Rechecked length/type, hashed before and after, required exit0 and identical SHA-256, and retained every result in `OUT/compression-results.json`.
4. **483/483** files passed, besides the pilot. Logical bytes22,742,829,848; compact-reported stored bytes5,252,366,336. These are per-file compression statistics, not an estimate of reclaimable source or recovery content.
5. During the serialized batch, measured C free space increased from21,286,875,136 to41,109,209,088bytes (19.83→38.29GiB). Available space had already changed between the first assessment and this batch. The entire difference from the first assessment must not be attributed solely to compression; unrelated host/WSL allocation changes were not measured individually.
6. After the actual original-service regression and retained extraction artifacts, `OUT/disk-final-assessment.json` records38,156,316,672bytes free, approximately**35.54GiB**. Free space is a timestamped observation and can change.

`OUT/disk-recovery-result.json` records no deletions and identical hashes. `OUT/preserved-native-files.json` binds retained protected files to their previous known-good hashes. Compression can be reversed with the corresponding `compact /U` operation if sufficient space exists; no decompression was needed here.

## Test-space budget and actual retry

The restored original-service run required more capacity than the small32MiB Darwin tests. The host-space preflight required **>20GiB** available. The budget covers the10GiB sparse guest-memory file,3GiB final HFS+ extraction, logs and additional inspection copies with margin; sparseness is not a guarantee that the full file stays unallocated. A4GiB host-free cancellation threshold was enabled. No threshold cancellation occurred.

The input root was reused only after its saved SHA matched, avoiding another3GiB copy. The current retained native execution directory is `/var/tmp/duchamp-abi-repaired-d9oo6amx`; the guest memory, final root and installed-file inspection copies remain there. The extractor was adapted to retain individual hash-check files rather than remove temporary extraction files. Nothing from the prior SIGBUS/cancelled attempts was deleted or relabeled as successful.

Exact launch configuration and source receipts: `OUT/run-original-services.py`, `OUT/trial-1/inputs.json`, `OUT/trial-1/command.json`, `OUT/trial-1/storage-guard.json`, and the native `run` directory. The actual QEMU invocation is retained in the run metadata. It uses ARM64 `virt,gic-version=3`, Cortex-A76, one CPU,10GiB file-backed RAM and the exact source-built kernel; no physical disk or phone is attached.

The run completed with `PLATFORM SERVICES DONE status=0`, debugger exit0 and no observed panic. **22/22** original-service checks, **24/24** IOSurface checks and **26/26** IOKit checks passed;296/296 installed hashes matched. The source root remains unchanged. This repairs the incomplete regression from the earlier low-capacity attempts; it does not resolve the missing graphics ABI or prove physical-device support.

## Remaining limits

No permanent cache eviction or archive policy was imposed. Keep at least the measured20GiB preflight budget for this large fixture; inspect host capacity before another run. Additional repetitive full-VM tests were not launched because the kernel and guest binaries did not change. The existing smaller applications/compositor/window/mouse/Mach-O baselines were preserved and their evidence revalidated.

Graphics status remains **BLOCKED_BY_UNKNOWN_ABI**. Native Duchamp status remains **BLOCKED_BY_MEMORY_EVIDENCE**. No physical UFS access was enabled.
