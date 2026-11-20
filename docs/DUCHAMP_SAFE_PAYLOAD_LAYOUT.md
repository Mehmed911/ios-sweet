# Duchamp safe payload layout

**`BLOCKED_BY_MEMORY_EVIDENCE`.** The 32+4 MiB configuration is the smallest tested option in this pass and is viable for the measured guest workload. Both configurations stage a larger Image than the previous physical B boot. A trusted map and DMA-isolation record for the relevant boot stages are still required.

## Options

| Option | Packed image and decompression | Runtime and safety margin | Result |
| --- | --- | --- | --- |
| A. md0 32 MiB + md1 8 MiB | Unsigned Android v4 envelope 14,905,344 bytes. The raw Image is 61,611,472 bytes. Simultaneous legacy-LZ4 input plus output would occupy 76,510,724 bytes before scratch. | A 512 MiB XNU window includes an 84,049,920-byte prefix through boot args and 452,820,992 bytes in the allocator tail. The modeled staging end is 68,936,240 bytes before the historical incoming FDT. | Exact-kernel QEMU and native offline preflight passed. Same-boot stage ownership remains unverified. |
| B. md0 32 MiB + md1 4 MiB | Unsigned envelope 14,888,960 bytes, with a raw Image of 57,417,168 bytes. Simultaneous legacy-LZ4 input and output would take 72,299,962 bytes before scratch. | Same 512 MiB window, 79,855,616-byte prefix and 457,015,296-byte allocator tail. Staging ends 73,130,544 bytes before the historical FDT. | Independent QEMU boot passed current launchd, syslogd and notifyd checks, capacity exhaustion and recovery. It fits the tested workload. It does not measure a larger Setup or production workload. |
| C. Keep the RAM volumes separately compressed until after the shim starts | A codec-only measurement compressed A's md0 to 5,115,837 bytes and md1 to 33,873 bytes. Replacing the raw volume bytes with these blobs gives a 24,818,142-byte staging estimate before decoder, metadata, alignment and outer packing changes. The two compressed inputs plus both outputs occupy 47,092,750 bytes, excluding other Image data, scratch and decoder state. There is no built Android envelope for this variant. | Decompressed HFS+ extents are still 32 MiB and 8 MiB. A future variant needs proven lifetime and non-overlap for input, output, stack and scratch. LK's outer decompression behavior is also unverified. | Only the two exact round trips were tested. No new boot candidate was created. |
| D. Use a proven smaller high DRAM claim supplied by firmware | With no format change, the A or B packed metrics stay the same as estimates. No new image was produced. A protected relocation for staging would require a supported LK loading contract. | A 256 MiB candidate window beginning at the existing base would geometrically leave 188,579,840 bytes after B's prefix. The kernel workload under this limit, ownership of the complete interval and DMA exclusion are unverified. The current low staging conflict remains. | Geometry-only comparison. Keep the 512 MiB runtime claim for the tested configurations until the firmware can establish a different one. |

The Android envelope uses 4 KiB packing. The observed entry base is 2 MiB-aligned. Mach-O destinations, the two RAM disks, ADT storage and the boot-args page use 16 KiB alignment. Modeled gaps from the incoming FDT and the old AVB offset are geometry and file margins. Actual peak decompression, firmware scratch and physical safety margins are unknown. [Memory map](DUCHAMP_MT6897_MEMORY_MAP.md), [image compatibility](DUCHAMP_BOOT_IMAGE_COMPATIBILITY.md), [compression measurements](../../../outputs/duchamp-mt6897-safe-placement-20261117/deferred-lz4-volumes.json)

## Results and exact build identity

All full boots used the source-built 19,541,944-byte XNU kernel with SHA-256 `e7b51ecb16fe9ad21a78455714b2bf26c1dee1fbc3a6a7f0cb3971a9cd569457`. Its ARM64 `LC_UNIXTHREAD` entry is `0xfffffe00074aa488`. Local native-profile envelopes were built from the independently tested seeds. The QEMU bootshim twins used QEMU-specific test settings and the same source-built kernel.

| Test | Result |
| --- | --- |
| Host interval tests | 15/15. Includes uint64 bounds, alignment, gaps, fixed and dynamic collisions, unknown placement or region role, and rejection of asserted authorization. |
| RAM disk bounds, native ASan/UBSan and ARM64 QEMU | 16 cases per environment, both exited 0. |
| Payload mutations and general packer | 12/12 independently for each new volume size, and 2/2 general payload tests. |
| Native bootshim preflight, host materializer and v4 legacy-LZ4 round trip | Passed for both envelopes. Two stock-FDT model controls accepted the high window. Four modified FDT runs refused fixed and dynamic md1 collisions with result 24. |
| Bootshim ARM64 QEMU twins | Both reached XNU and verified the return slot. Both recorded zero unexpected returns. |
| Full QEMU dual RAMDisk and services | 11/11 and 74/74 for each 4 MiB and 8 MiB guest. Original launchd ran as PID 1. md0 and its source stayed byte-identical, root writes returned EROFS, md1 was writable via both paths, ENOSPC and cleanup passed, and the console, syslogd and notifyd were available. |
| Full QEMU 4 MiB failure profiles | 5/5. Wrong `/var` alias, invalid permissions, mount failure, missing md1, and missing mount point all stopped before starting the original launchd. |
| Full QEMU Mach-O, independent profile | 17/17. Dynamic PID 2 loaded 37 images through dyld and exited 0. Static PID 3 exited 42. Mach IPC and HFS+ checks passed. |
| Physical placement checker | Exit 1 for both candidates. The high window clears archived geometry. Low staging intersects unresolved DPMAIF and MKP allocation ranges, and ownership and DMA isolation remain unverified. |

| Offline artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| A raw Image | 61,611,472 | `884ab793d005bf5d22bcd5ddd7228ec1ababdc8fa7ca51241ee0121510634561` |
| A lab envelope | 14,905,344 | `89f1cb59a46e4a1757032f472df89fa609933451124f9f2480cb77df37261b7b` |
| B raw Image | 57,417,168 | `2be899ce4c76a740c3006089efd25e292b42b6e59bee10722610dd4203cb426b` |
| B lab envelope | 14,888,960 | `86c23337ce9aa9cd0913592ed03063405e5b7a42dc3446a822bd753575caf1bd` |

The evidence bundle includes exact argument vectors, exit codes and logs for [guest runs](../../../outputs/duchamp-mt6897-safe-placement-20261117/qemu/results.json), [guest commands](../../../outputs/duchamp-mt6897-safe-placement-20261117/qemu/commands.json), [4 MiB failure profiles](../../../outputs/duchamp-mt6897-safe-placement-20261117/qemu/var-4-failures/commands.json), [bounds and packaging](../../../outputs/duchamp-mt6897-safe-placement-20261117/regressions/commands.json), [reservation guards](../../../outputs/duchamp-mt6897-safe-placement-20261117/guard/commands.json), [A native preflight](../../../outputs/duchamp-mt6897-safe-placement-20261117/native-8m-var/verification.json), [B native preflight](../../../outputs/duchamp-mt6897-safe-placement-20261117/native-4m-var/verification.json), and [Mach-O validation](../../../outputs/duchamp-mt6897-safe-placement-20261117/qemu/macho-verification.json). The [evidence manifest](../../../outputs/duchamp-mt6897-safe-placement-20261117/offline-evidence.json) records commands for rebuilding and checking the map and hashes the main receipts.

## Promotion conditions

Prove LK decompression limits and every concurrent source/scratch/output extent for the proposed image. Obtain a boot-bound final LK/BL31 allocation and protection record covering surviving modem reservations, DMA exclusion and the entire XNU window. Review the exact supported Slot B policy and verify Fastboot recovery reachability against the archived A/B baselines. The checker is offline and makes no permission grant. This phase took no action on the phone or its physical storage.
