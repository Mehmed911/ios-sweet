# HakiOS source audit — 2026-11-15

This is an offline source audit. No phone action was performed. Repository
descriptions and supplied boot photographs are not substituted for new tests.

| Repository | Pinned revision | Actual scope |
| --- | --- | --- |
| oosexgang/hakios-mt6768 | `ad65e1f4b3ba479e9d7ada98f17398b83cc6f285` | All 80 tracked blobs inventoried and textual sources scanned; boot/start/link/pack and storage paths inspected in detail |
| AnkitChoudhary-1/Hackios-mt6833-port | `c24467f3074d9bfbd7cb92e2d20beacd91e468b5` | All 690 tracked blobs inventoried; MT6833/device-light/loader/storage dependencies reviewed; the complete 336-line MT6833 UFS source inspected |
| oosexgang/hakios-xnu-kernel, mtk | `a962798418fa1ebaa06554a69955803860907c6b` | Legacy layout, loader and kernel integration reference |
| oosexgang/hakios-xnu-kernel, main | `63fc2b4633bac3af8e57dadab9f5a8d4cb940438` | Actual tools/hakios-device.py, tools/hakios-config.py, driver registry and common configuration; sparse source checkout |
| torvalds/linux | `fa2933aac170dd19c6a7f0d7b81a8f537e40915c` | drivers/ufs, include/ufs, drivers/phy/mediatek, UFS DT bindings; source reference, not copied into XNU |
| Mehmed911/ios-sweet | `60ae971` on duchamp-bootstrap | Existing verified observer/XNU baseline; all unrelated working changes retained |

The complete per-file inventories, hashes, includes and critical function-line
anchors are in [HAKIOS_REFERENCE_INVENTORY.json](HAKIOS_REFERENCE_INVENTORY.json).
The additional common-tree and Linux source hashes are in
[HAKIOS_ADDITIONAL_SOURCE_INVENTORY.json](HAKIOS_ADDITIONAL_SOURCE_INVENTORY.json).
[HAKIOS_FILE_MAPPING.md](HAKIOS_FILE_MAPPING.md) maps every file of the two device
references, including files deliberately not ported. Inventory/scanning is not
a claim of manual line-by-line review of every common userspace implementation.

## Material findings

* MT6768 uses MSDC/eMMC, Android boot header v2, gzip, entry `0x40080000`, a
  32-MiB boot partition and `XNUP` payloads. Duchamp's existing path uses v4,
  legacy LZ4, a 64-MiB boot container and `SWEETXNU`. These are incompatible.
* MT6768's loader places XNU at `0xc0000000`. Duchamp's captured FDT reserves
  that address for TEE (`0xe000000` bytes). Renaming that memory layout would
  overwrite reserved memory.
* The MT6833 UFS reader does not transfer data. It returns true after checking
  HCS, leaving the caller's destination unchanged. A source-extracted native
  sanitizer test reproduced success with zero changed bytes. Its GPT fallback
  invents partition geometry. Neither behavior is imported.
* The current legacy common `mtk` branch has no root Makefile or
  tools/hakios-device.py, despite the device README referring to those names.
  The pinned `main` branch contains them. New metadata is checked against the
  actual `main` tools, while retaining the existing ios-sweet build.
* Disabling foreign driver objects alone is insufficient: common_defconfig
  also enables runtime arguments for GPU, audio, modem and UFS. Both sets are
  explicitly disabled in the new MT6897 fragment; the native checker passes.

## Licenses and reuse

The device reference carries MIT and APSL notices. The community fork's LICENSE
assigns kernel files/driver derivatives to APSL and other project files to MIT,
with third-party notices. Linux UFS sources carry GPL SPDX notices. No Linux
implementation or MT6833/MT6768 hardware driver was copied. New SCSI work
extends the existing independent portable transport. The extracted stub test
and upstream checkouts remain private build evidence, not vendored source.

Source links: [MT6768](https://github.com/oosexgang/hakios-mt6768/tree/ad65e1f4b3ba479e9d7ada98f17398b83cc6f285),
[community MT6833](https://github.com/AnkitChoudhary-1/Hackios-mt6833-port/tree/c24467f3074d9bfbd7cb92e2d20beacd91e468b5),
[Linux MediaTek UFS](https://github.com/torvalds/linux/blob/fa2933aac170dd19c6a7f0d7b81a8f537e40915c/drivers/ufs/host/ufs-mediatek.c).
