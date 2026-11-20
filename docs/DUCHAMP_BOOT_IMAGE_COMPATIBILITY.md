# Duchamp Android boot image compatibility

Both candidates pass offline Android v4 and ARM64 Image checks. **Acceptance by the physical LK for either new image remains unverified.**

## Archived configuration

- `boot_a` is 64 MiB. The archived Android header is v4, 1,584 bytes, with 4,096-byte image alignment, zero generic ramdisk bytes and zero v4 boot-signature bytes. Its legacy-LZ4 kernel blob is 16,295,649 bytes. The stock ARM64 header records `text_offset=0` and `image_size=0x21d0000`. The extracted stock Image file is 34,765,312 bytes.
- The archived v4 `vendor_boot_a` contains a 4,096-byte page size, `kernel_addr=0x40000000`, `ramdisk_addr=0x66f00000`, and `tags_addr=dtb_addr=0x47c80000`. The observed Android initrd extent is larger than its vendor ramdisk alone. The stock-like Slot B triplet previously used the matching vendor-boot image and the OTA `init_boot`. Slot DTBO and the AVB chain also affect the complete boot configuration.
- AOSP specifies the boot-v4 structure and vendor-boot relationship. AOSP also allows different verification behavior for an unlocked bootloader. Historical Android A reported orange/unlocked, and the previous B experiment displayed XNU. These observations establish the earlier device state and artifact behavior. Neither exercises the new raw size or checks the device's present policy.

[LK and stock-header audit](../duchamp/MT6897-LK-HANDOFF-CONTRACT.md), [AOSP boot header v4](https://source.android.com/docs/core/architecture/bootloader/boot-image-header), [AOSP vendor boot](https://source.android.com/docs/core/architecture/partitions/vendor-boot-partitions), [AOSP verified-boot device state](https://source.android.com/docs/security/features/verifiedboot/device-state), [Linux ARM64 Image protocol](https://docs.kernel.org/arch/arm64/booting.html)

## Preflight and remaining limits

| Item | 32+8 MiB | 32+4 MiB |
| --- | ---: | ---: |
| Raw bootshim Image bytes | 61,611,472 | 57,417,168 |
| Legacy-LZ4 kernel bytes | 14,899,252 | 14,882,794 |
| Unsigned lab envelope bytes | 14,905,344 | 14,888,960 |
| Bytes before the archived stock AVB offset | 1,413,120 | 1,429,504 |
| Bytes below the local 64 MiB raw cap | 5,497,392 | 9,691,696 |
| Extra decompressed bytes over the prior observed B Image | 11,220,512 | 7,026,208 |

`pack_boot.py` compressed both Images. Both decompressed and matched the raw Image SHA-256. The previous 32+32 MiB raw Image exceeded the local cap. The archived boot image's AVB footer and hash descriptor verify using `avbtool` and its embedded public key. The descriptor covers 16,318,464 bytes. The archived file identity is separately pinned by SHA-256. The first verification attempt reached the valid vbmeta signature and failed to resolve the descriptor's sibling filename `boot.img`. Running it again with a temporary `boot.img` alias resolved the same archive and verified both signature and partition hash with exit 0. [Packer](../duchamp/bootshim/pack_boot.py), [AVB log](../../../outputs/duchamp-mt6897-safe-placement-20261117/stock-avb-verify-retry.log)

The 64 MiB raw cap is a local packer rule. The archived 16,318,464-byte region is one signed-image boundary. Neither measurement establishes LK's maximum output size, its compressed input and scratch bounds, or the total size limit when the separate vendor and init ramdisks are present. The two envelopes are unsigned local validation artifacts. No AVB signature or policy change was used. Their exact Slot B acceptance and the LK decompressor's safety at the measured sizes are still open.

## Recovery prerequisites

The archived receipts contain six Android A artifacts and three previous B artifacts with verified stored sizes and hashes. The correct A `init_boot_a` backup is the byte-identical Magisk-patched file with SHA-256 `dec6f1f7d785db8f78735fbe18046e16d09ec8dc7655b9ec8f50a2f83cd40cb2`. The matching OTA stock image is a separate artifact. The archive includes a verified recovery ramdisk fragment and historical Fastboot recovery. Current Fastboot reachability and a working recovery session were outside this offline audit. A later review requires confirming the current build and matching backups, bootloader Fastboot access and a manual return to the known-good A installation before proposing any candidate. [Recovery verification](DUCHAMP_ANDROID_A_RECOVERY_VERIFICATION.md), [archived file-identity receipt](../../../outputs/duchamp-xnu-hardware-readiness-20261117/archived-recovery-identity.json)
