# Duchamp Android A recovery verification and hardware decision

**Decision: BLOCKED_BY_FIRMWARE.** The archived working Slot A boot-chain
images match the phone's current partitions, including the Magisk-patched
`init_boot_a`. The installed Slot B triplet matches the known RAM-root XNU
build. The reviewed firmware and interfaces still provide no supported,
authenticated final BL31-to-XNU trace for one actual Slot B boot. Keep
physical UFS disabled.

## Android A reconciliation

A read-only ADB inspection observed `duchamp`, MT6897, Slot `_a`, and a
completed Android boot. The same boot ID was observed before and after
the inspection. Android and vendor report Global Android 14,
`V816.0.17.0.UNLMIXM`, fingerprint
`POCO/duchamp_global/duchamp:14/UP1A.230905.011/V816.0.17.0.UNLMIXM:user/release-keys`.
The security patch is 2024-11-01, AVB reports orange/unlocked, and the
existing root session reports Magisk 30.7. The root check succeeded even
though the default Magisk application package was absent.

The recorded November 11 pre-trial baseline and live hashes agree for
`boot_a`, `vendor_boot_a`, `init_boot_a`, `dtbo_a`, `vbmeta_a` and
`lk_a`. Each has a local file that matches the current partition byte
for byte by size and SHA-256. The exact current A init-boot backup is
`work/magisk_patched-30700-duchamp-correct.img`. The prior comparison
used the separately re-packed stock-like file. The same running build
and six unchanged hashes provide no evidence of a firmware update
causing that mismatch.

| Image | Bytes | SHA-256 | Compressed ramdisk bytes | CPIO evidence |
| --- | ---: | --- | ---: | --- |
| Current and historical A, `magisk_patched-30700-duchamp-correct.img` | 8,388,608 | `dec6f1f7d785db8f78735fbe18046e16d09ec8dc7655b9ec8f50a2f83cd40cb2` | 1,991,694 | 26 entries. Magisk replaced `init`, and the overlay and `.backup/.magisk` are present. |
| Re-packed `init_boot_a.stock-duchamp.img` | 8,388,608 | `951235278eb5d4912961abbec156e7350a1648d5ec4e202b47fed0a16305055f` | 2,176,165 | 17 entries. All paths, contents, modes and ownership checked agree with the OTA CPIO. Serialization and compressed bytes differ. |
| Xiaomi Global `OS1.0.17.0.UNLMIXM` OTA init boot | 8,388,608 | `00476196f020c0e01aa1661ac731970c2e8a5bbbc262ec04627fc9a5b87f2d78` | 2,176,170 | 17 stock entries. Its covered bytes match the signed live `vbmeta_a` descriptor. This is also the init-boot image currently on B. |
| Earlier local `magisk_patched-30700-duchamp.img` | 8,388,608 | `a012dd30f8203d7cf701c760c9d2edf65fa6a86c0bf0c2931f13b6aca90ebc50` | 2,047,615 | 25 entries. Different ramdisk build metadata and a different recorded original image SHA-1. Its restored output fails the stock-like file comparison. |
| Historical pre-trial `init_boot_b.img` | 8,388,608 | `b2d762f5ad0db23180b9a4014ba20d7e6111106c6cf823accb94a0160ffd5a68` | 2,130,363 | 25 entries. A separate Magisk-patched image with the same recorded OTA origin as the live A patch. |

The five files use Android boot header v4, 1,584-byte headers, zero
kernel bytes and legacy LZ4 ramdisks. The saved
`work/magisk-restore-duchamp-stock.sh` describes the local unpack,
CPIO restore and re-pack path. Repeating it offline with the saved
Magisk 30.7 binary reproduced the **entire** stock-labeled file from
both the correct A patch and the historical B patch. Both patched
ramdisks record the OTA original's exact SHA-1
`28619712c096372643f0ef2dde9d15481ac75b29`. The bytes establish the
re-pack provenance and common original. They do not distinguish
which of those two inputs the historical script used.
[AOSP boot header](https://source.android.com/docs/core/architecture/bootloader/boot-image-header),
[Magisk v30.7 patch and restore flow](https://github.com/topjohnwu/Magisk/blob/v30.7/scripts/boot_patch.sh)

The matching stock reference is the saved Xiaomi Global OTA extraction,
whose manifest hash and build fingerprint match. The archived rooting
re-pack fails the signed init-boot descriptor even though its CPIO
contents match. The audit reverified the signature of archived
`vbmeta_a` after matching that file to the live partition, then checked
the OTA and vendor-boot bytes against its descriptors. The full OTA ZIP
signature was outside the earlier bounded extraction. The OTA
`init_boot` and the Magisk-patched working backup are two separately
verified artifacts with different roles.
[Xiaomi Global OTA](https://bigota.d.miui.com/OS1.0.17.0.UNLMIXM/miui_DUCHAMPGlobal_OS1.0.17.0.UNLMIXM_c9707e92fc_14.0.zip)

The saved `vendor_boot_a` matches the live partition and its signed
descriptor. Its v4 table contains a 13,565,240-byte type-2 recovery
fragment, SHA-256
`01d70eef8b1276c8d0136045a4591011af0ac94da341626222eea47b532f8a27`.
Prior Fastboot recovery followed by Android A startup is documented.
The current Android A startup is verified. Recovery UI boot and current
Fastboot enumeration were outside this read-only inspection. No backup
was installed or modified.

## Real trace interfaces on this firmware

Read-only checks found the **same** 953,976-byte ATF component in the live
5 MiB `tee_a` and 12 MiB `tee_b` containers. The complete containers
differ. Both ATF components hash to
`716222a632e4a0623a2e467e17f1d36f38a37f79a1c026447fe724e75e90e07e`
and match the audited BL31 `lts-v2.8.6(release):2fbca47`. The current
Slot A runtime log repeats that release string. The stored component
match does not identify the executing firmware or its handoff state
during a later B boot.

| Interface and existence on this MT6897 device | Privilege or required change | Same-boot binding, origin and recovery risk |
| --- | --- | --- |
| `/proc/atf_log/runtime_snapshot` and `raw_dump_all` exist and returned 131,072 and 2,097,152 bytes from Android A. MiCode's debug driver copies reserved ATF log RAM. | Existing Android root was sufficient for both reads. The sampled reader would need an authenticated final-boundary producer and a supported export that remains available across the XNU transition. | The current reads are bound to the live Android A boot by its boot ID. The buffers supply a BL31 banner and no authenticated B/XNU pair. Reading the existing buffers required no boot change. [MiCode ATF debug source](https://github.com/MiCode/MTK_kernel_device_modules/blob/3c4ccd07d5624879555ec710c11bb8818e5cb5c6/drivers/misc/mediatek/atf/tfa_debug.c#L175-L227) |
| `/proc/pl_lk`, `/proc/bootprof`, and pstore exist. The retained LK Fastboot PL/LK export also worked historically. The archived command audit found no raw ATF Fastboot export. | Linux reads used existing root. The historical Fastboot export required entering the bootloader. The running Android kernel has ftrace, no CoreSight driver, and kexec is disabled. No trace controls were changed. | The two live pstore entries had no final-BL31 or XNU marker in the bytes read. LK's jump logging is before final cleanup. Phase markers and ring buffers provide no authenticated firmware ownership, and a new boot can replace prior evidence. Entering Fastboot during a trial would interrupt it. [MiCode log store](https://github.com/MiCode/MTK_kernel_device_modules/blob/3c4ccd07d5624879555ec710c11bb8818e5cb5c6/drivers/misc/mediatek/log_store/log_store.c), [LK trace inventory](../duchamp/MT6897-LK-HANDOFF-CONTRACT.md#live-retained-lk-log-on-slot-b) |
| UART hardware is described by four UART nodes in the saved Duchamp DTB. The live kernel supports 8250 consoles, but `/proc/consoles` showed ramoops and ttynull. Neither DT chosen stdout-path property was available. No supported physical debug transport was verified. | A supported board connection, electrical specification and firmware output would need vendor confirmation. A change to firmware logging or UART routing may be required. No port was opened or reconfigured. | Console text could corroborate ordering in one observed boot, but cannot authenticate origin or establish resource state. Unverified pin access, mux changes or debug firmware could disturb recovery. [Duchamp hardware inventory](../devices/duchamp/hardware.json) |
| Final BL31 exit instrumentation and authorized external trace remain unverified for this retail configuration. The saved kernel-boot path runs group-5 EMI/SMPU callbacks and a later helper before the final release. | Vendor-supported firmware telemetry or authorized independent trace is required. Public TF-A PMF measures timing, and public Arm CoreSight documentation describes conditional hardware capabilities. Neither proves an exposed Duchamp channel. | A verified producer must independently bind the final event to the same resolved B boot and actual XNU entry. Instruction flow alone cannot attest resource ownership. Changing secure firmware, boot policy or debug access would jeopardize the existing boot path. [TF-A PMF documentation](https://trustedfirmware-a.readthedocs.io/en/lts-v2.14.10/perf/psci-performance-instr.html), [Arm CoreSight trace](https://developer.arm.com/community/arm-community-blogs/b/architectures-and-processors-blog/posts/how-to-debug-coresight-basics-part-1) |
| Bootshim v3 can report PC, incoming `x0` and DTB SHA-256. The existing XNU RAM-root build emits userspace service markers. | The v3 diagnostic is a separate opt-in image which halts before XNU. The installed B image does not contain it. A supported independent observer or a separately reviewed passive marker is required to associate actual XNU entry with the final firmware record. | Framebuffer and software logs are corroboration. They confer no authority and cannot be combined across boots. Changing the boot artifact would require a new preflight and recovery review. [Final capture contract](DUCHAMP_FINAL_BL31_XNU_HANDOFF.md#capture-contract) |

The LK shutdown code attempts PowerDown and HCE disable without a final
queue or fabric-drain check. The pinned BL31 code conditionally controls
the active-low UFS device reset from `0x112b8090`. These are source and
binary observations. Final reset level, HCE/queue state, resource
ownership and DMA drain at physical Slot B entry are still absent.
[Shutdown evidence](DUCHAMP_UFS_LK_SHUTDOWN_ANALYSIS.md),
[reset selector audit](DUCHAMP_UFS_OWNERSHIP.md#identifying-the-always-on-syscon-bit)

## Independent cold initialization

The XNU-side design can be developed and tested offline without modifying
BL31. Running it safely would require documented existing authority or
vendor cooperation. Cold initialization removes a dependency on preserving
LK's controller configuration, while keeping an independent requirement
to establish safe initial isolation and ownership.

| Prerequisite | What is verified | What still needs positive evidence |
| --- | --- | --- |
| Controller and IRQ ownership | MT6897 HCI range, interrupt topology and the Android driver's use of them. | Exclusive boot-specific ownership, non-secure firewall permission and pinned lifetime before XNU maps the range. An MMIO read is not a safe access test when permission or power is unknown. |
| Reset | The saved active-low device reset and separate HCI/crypto/UniPro reset topology. | Verified initial drain or external isolation, then authorized reset semantics and acknowledgements. HCE clear and reset requests alone do not establish DMA completion. |
| Clocks, power and PHY | Duchamp DTB dependencies, M-PHY version 1, and Xiaomi's published Linux firmware-mediated reference-clock and MTCMOS path. | Proven rails, ref-clock and bus-clock votes, power domain and PHY state from their owners, with a supported provider for those operations under XNU. The Linux driver does not transfer its grants. |
| DMA isolation and IOMMU | Archived Android direct-DMA observations and the saved DTB topology. Existing offline direct and translated paths guard address use. | Exact UFS master and protection range, no-resume and fabric drain, then authorized direct mapping or a verified IOMMU stream/domain/epoch with stale translations accounted for. |
| Cache coherency | Existing offline handoff and descriptor/cache policy. | Proven device-visible cache-maintenance scope and responsible owner, including any system cache and buffer synchronization. |

No new authorization model was added. The existing production gate and
offline cold-init suite remain the applicable code. There is no physical
initialization candidate under these conditions.
[Cold-init design and pinned Xiaomi/Linux sources](DUCHAMP_MT6897_UFS_INIT_DESIGN.md),
[DMA safety requirements](DUCHAMP_UFS_DMA_SAFETY.md)

## Slot B disposition and tests

The installed `boot_b`, `vendor_boot_b` and `init_boot_b` match the exact
existing RAM-root triplet documented in the
[previous candidate manifest and rollback plan](DUCHAMP_FINAL_BL31_XNU_HANDOFF.md#exact-proposed-artifacts-and-backups).
This resolves the image identity preflight without a write. The lack of a
trusted final-exit channel blocks preparation of a real test. The earlier
plan remains unexecuted. Keep the current A baseline as the recovery
reference. A later review would still require verified bootloader
Fastboot access, approved single-boot evidence collection, and a
reviewed manual return to Android A.

The existing offline suites passed, including 67 cold-init model cases,
98 handoff-format cases and 12 passive-entry cases per native sanitizer
and ARM64 QEMU environment, 44 host correlator cases, bootshim/payload
preflight, DMA route, cache, and the pinned LK/BL31 audit. The existing
CI XNU kernel passed 11 fresh QEMU regressions, with zero virtual UFS
events in the nine blocked cases.

The workspace directory `outputs/duchamp-hardware-unblock-20261116`
contains the read-only receipts, full artifact digests and test logs.
No flash, reboot, slot change, partition write, physical MMIO or
new DMA setup was performed.
