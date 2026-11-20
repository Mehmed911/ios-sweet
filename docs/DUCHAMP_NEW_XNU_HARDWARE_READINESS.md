# Duchamp source-built XNU hardware readiness

**Decision — BLOCKED.** The 32 MiB root and 8 MiB writable RAM disk fit the archived Duchamp layout and the stock boot image's measured compressed region. The candidate passed host validation and a QEMU bootshim transfer. A hardware trial still needs evidence for the expanded source-image range and the final RAM and DMA state at Slot B handoff, an approved way to load the unsigned candidate, and reconfirmed recovery access.

## Preserved baseline

The workspace is on `duchamp-bootstrap` at `d91562d9c2bd3bc33d52550c101de1009bb41dc0` with the existing working-tree changes. The kernel is `xnu-8796.141.3` at `1b191cb58250d0705d8a51287127505aa4bc0789`, compiled with isolated UniXNU-patched Clang 24.0.0git at LLVM `58c46bae21181fb4240cf964461bea738d96d50e` and linked with cctools ld64 951.9. The 19,541,944-byte kernel SHA-256 is `e7b51ecb16fe9ad21a78455714b2bf26c1dee1fbc3a6a7f0cb3971a9cd569457`. All 1,126 linked objects came from the recorded source build. The layout and QEMU runs used that exact digest. [Build and boot details](DUCHAMP_NEW_XNU_QEMU_BOOT.md)

The run directory is `../../outputs/duchamp-xnu-hardware-readiness-20261117` from the repository root in WSL. It contains the tracked and staged diffs, the full status list, and a hash-verified archive of 62 untracked source and documentation files. Existing work artifacts stayed in place. `build-manifest.json` pins the kernel, compiler, source-build receipts, current bootshim sources, seed images, archived inputs and test results. The prior build receipts retain the compiler setup, all compile arguments and the exact ld64 command. The new `qemu/commands.json`, `qemu/compact-var.cmd` and per-run command records retain the new launch arguments.

## Archived phone comparison

The saved `boot_b.img` from the November 11 Slot B trial has SHA-256 `545112503a5e9052db709572cc840758619f2b7e27c9aa58c0af2a3924a8f6a8`. Its legacy-LZ4 Image contains the byte-identical historical phone payload. Rebuilding that payload from the old `e465723a…` kernel, phone ADT and HFS+ seed produced the same bytes. The archived user photo and trial receipt report original launchd, syslogd and notifyd on the phone using one writable RAM root. [Saved image and source provenance](DUCHAMP_FINAL_BL31_XNU_HANDOFF.md#exact-proposed-artifacts-and-backups)

| Item | Historical phone image | New phone candidate and QEMU boundary |
| --- | --- | --- |
| Kernel entry | Virtual `0xfffffe0007480488`, physical `0x1c1480488` | Virtual `0xfffffe00074aa488`, physical `0x1c14aa488`. Plain ARM64 Mach-O, `LC_UNIXTHREAD`, zero unresolved symbols. |
| Kernel mappings | Ten populated Mach-O segments. `__TEXT` at `0xfffffe0007004000`, executable text at `0xfffffe00072e4000`. Payload virtual base `0xfffffe0006000000`. | Same populated segment names and virtual base, with executable text at `0xfffffe00072e8000` and new segment extents. The full segment tables are in `kernel-and-device-tree-comparison.json`. The high physical window derives from the archived phone map even though the QEMU test uses the same numeric kernel window. |
| CPU handoff and MMU | LK Image base `0x40000000` and inherited FDT pointer `0x47c80000` corroborated by the earlier PC/x0 capture. The bootshim gates XNU entry on EL1, `SCTLR_EL1.M/C/I=0`, entry alignment and a full aligned boot-args page. | The shim masks interrupts, applies the existing barriers and branches with the boot-args physical address in `x0`. XNU's bootstrap builds its 16 KiB mappings. The QEMU test exercises the branch and mappings. Final physical EL, MMU and cache state remain specific to the new boot. [Bootshim gate](../duchamp/bootshim/handoff_ready.c), [LK evidence](../duchamp/MT6897-LK-HANDOFF-CONTRACT.md) |
| FDT, ADT and boot arguments | Saved LK FDT is 485,760 bytes. The XNU phone ADT describes a single boot CPU, the high DRAM window and the phone framebuffer. The old profile used `rd=md0 rootrw=1`. | Incoming FDT remains a separate shim input. The pinned phone ADT is extended only with the two RAM disk properties. The candidate uses `rd=md0 rootrw=0 duchamp_dual_ramdisk=1 cpus=1`. The host materializer verifies every copy range and the exact 608-byte command-line field. |
| GIC, timer and topology | Phone ADT GICD `0x0c400000 + 0x40000`, GICR `0x0c440000 + 0x200000`, virtual timer PPI 27 and 13 MHz. The Android FDT describes eight CPU nodes. The previously tested XNU profile enables CPU0 only. | The candidate keeps that phone profile. The QEMU twin instead uses `0x08000000 + 0x10000`, `0x080a0000 + 0x100000` and 62.5 MHz, still with PPI 27 and one CPU. Physical interrupt delivery, clock continuity and additional CPU startup remain outside the new tests. |
| Diagnostics | Phone framebuffer `0xfcc2f000`, 1220×2712, stride 4992. The captured FDT describes UARTs and the Android records show no verified board debug console. | Framebuffer stays the review channel. `serial=3` supplies no new proof of native UART. The existing physical shim stops the watchdog after the handoff gate and draws framebuffer markers. The QEMU twin disables the phone watchdog operation. [Archived console evidence](DUCHAMP_ANDROID_A_RECOVERY_VERIFICATION.md#real-trace-interfaces-on-this-firmware) |

The phone ADT and command line omit UFS configuration. No UFS code was linked into the bootshim. The XNU build retains its existing closed physical UFS gate. The boot path under review uses only memory devices for the root and writable volume.

## RAM ranges and package fit

The saved FDT declares physical DRAM `[0x40000000, 0x340000000)`. The existing preflight accepted the full `[0x1c0000000, 0x1e0000000)` XNU window for both candidates. The audit compared all 52 fixed reservations, four dynamic requests, the archived initrd and FDT extents. Neither XNU window intersects any of those ranges. The host materializer verified all copies including both HFS+ volumes, ADT, boot arguments and padding. Injecting either a fixed reservation or a dynamic allocation range over md1 made the actual preflight return reserved-memory error 24.

| Range, end exclusive | 32 MiB md1 | 8 MiB md1 |
| --- | --- | --- |
| md0, 32 MiB read-only | `[0x1c2820000, 0x1c4820000)` | Same address and size |
| md1, writable | `[0x1c4820000, 0x1c6820000)` | `[0x1c4820000, 0x1c5020000)` |
| ADT and boot-args page | `0x1c6820000`, `0x1c6824000` | `0x1c5020000`, `0x1c5024000` |
| End of reservation | `0x1c6828000` | `0x1c5028000` |
| LK Image source extent | `[0x40000000, 0x452c1dd0)` | `[0x40000000, 0x43ac1dd0)` |

Both source extents clear the historical FDT and all fixed reservations. The portions beyond the old Image end at `0x4300e7b0` intersect the possible allocation ranges of the two modem DPMAIF cache and no-cache pools. These are allocation requests in the saved FDT. Their final physical placement and owner at LK exit remain unverified. The new high reservation also extends beyond the archived phone payload's planned end at `0x1c4570000`. The saved map establishes non-overlap with declared ranges. It supplies no same-boot confirmation of final placement or exclusion of inherited DMA. [LK reservations](../duchamp/MT6897-LK-HANDOFF-CONTRACT.md#ram-and-reserved-memory), [DMA evidence and constraints](DUCHAMP_UFS_DMA_SAFETY.md)

| Local artifact | Result |
| --- | --- |
| `native-32m-var/payload-phone.bin` | 86,656,236 bytes. SHA-256 `da9333d266b997d42279275aee830384f1022e105b400e66de1857b86738b57e`. Host validation passed. The 86,777,296-byte raw Image failed the existing packer's 64 MiB uncompressed cap, exit 1. No envelope was produced for this profile. |
| `native-8m-var/payload-phone.bin` | 61,490,412 bytes. SHA-256 `4f4ea161e1657999f653d856c65ec927b9e64fa2e0a50512405ecd5f92deb07e`. The 61,611,472-byte raw bootshim Image embeds the complete payload and fits below the saved FDT. |
| `native-8m-var/boot-v4-envelope.img` | 14,905,344 bytes, including a 14,899,270-byte legacy-LZ4 kernel. SHA-256 `5b3eea1f4948d3d3d8bc0faedb922de947b5d02f083957d6a13ffc9c48336db0`. Preserves the stock v4 header fields apart from kernel length. Leaves 1,413,120 bytes before the saved stock data-region boundary. It is an unsigned lab envelope. |

The payloads rebuilt byte-identically with their saved seeds. The compact envelope also repacked byte-identically and decompressed back to the exact bootshim Image. The raw-size cap comes from the local packer and the compressed-region limit comes from this device's archived boot image. [Android boot header v4](https://source.android.com/docs/core/architecture/bootloader/boot-image-header), [ARM64 Image fields](https://docs.kernel.org/arch/arm64/booting.html)

## Regression results

| Case | Exact source-built kernel result |
| --- | --- |
| Default 32+32 MiB RAM disks | 11/11 checks and 74/74 service checks, exit 0. Original launchd ran as PID 1. The guest md0 dump matched its seed. |
| Compact 32+8 MiB RAM disks | 11/11 checks and 74/74 service checks, exit 0. md1 mounted at `/private/var`. Root writes returned EROFS. md1 returned ENOSPC after 8,126,464 bytes and recovered capacity. |
| Darwin | 17/17, exit 0. Mach IPC, file reads and private mappings passed. Dynamic PID 2 used dyld/libSystem and exited 0. Static PID 3 exited 42. |
| Failure profiles | All five passed. Missing md1, missing mount point, mount failure, bad permissions and incorrect `/var` alias stopped before original launchd. |
| Compact QEMU bootshim twin | Guarded ARM64 transfer, return-slot contents and framebuffer witness passed. The twin used the QEMU ADT and omitted the phone watchdog write. |

## Conditions for a later hardware review

1. Corroborate the stock LK and BL31 handoff for the exact expanded candidate. Account for final source-buffer placement, regions used by modem DMA and the additional high-memory reservation. Establish that firmware-owned DMA cannot write either region through the passive boot. Keep physical UFS disabled throughout.
2. Establish a supported boot path under the phone's existing boot policy for the exact compact artifact. The archived positive boot used a different envelope. Identify the exact image hashes and distinguish the required LK/FDT handoff from XNU's own ADT and boot arguments.
3. Reconfirm Android A's current installed build and all recovery image hashes before a future approved attempt. This turn rehashed the six archived A artifacts and three archived B artifacts against the earlier read-only receipts. Use the exact working Magisk-patched `init_boot_a` backup and retain the separate OTA stock reference. Verify the actual pre-attempt B triplet and its rollback copies.
4. Reconfirm a reachable bootloader Fastboot or verified recovery path and a manual route back to Android A. Plan the abort point before any later test. Preserve LK, BL31, Android A and shared userdata, and account for the shim's existing watchdog behavior. [Recovery reconciliation](DUCHAMP_ANDROID_A_RECOVERY_VERIFICATION.md), [A/B selection contract](https://source.android.com/docs/core/architecture/bootloader/updating#support-for-slots)

All work in this report was offline. The phone, boot slots, partitions and physical UFS were untouched. The workspace remains uncommitted.
