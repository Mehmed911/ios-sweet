# Duchamp UFS resource ownership

## Verified source and saved evidence

The audited artifacts are the saved LK partition and BL31 sample plus the
saved final Duchamp FDT. Their SHA-256 receipts match the
[LK shutdown analysis](DUCHAMP_UFS_LK_SHUTDOWN_ANALYSIS.md). The earlier
Fastboot log reports UFS and M-PHY initialization on that boot path. The
archived XNU Slot B boot used a RAM root. Neither provides a correlated
post-cleanup UFS state or ownership record for the XNU boot.
[Previous Slot B handoff evidence](DUCHAMP_SLOT_B_UFS_HANDOFF.md)

| Area | Verified source behavior | Runtime or ownership still unverified |
| --- | --- | --- |
| PowerDown | LK `0x79e30` writes zero to AHIT. The call at `0x79e34` attempts START STOP UNIT PowerDown using the legacy transfer doorbell at `0x769dc`. The helper waits and can retry. The shutdown path continues without checking its result. | Device power mode, link state and outstanding requests after the attempt. |
| HCE and queues | LK `0x79e48` writes zero to HCE. The shutdown path returns without an HCE readback or a post-write transfer/task/MCQ sample. | Final HCE, full legacy or MCQ queue state, no-resume fencing and fabric DMA drain. |
| UFS device reset | One LK shutdown branch reaches the saved BL31 bootloader UFS dispatcher, whose selector 2 calls the shared reset-level helper. The Linux kernel client supplies the semantic cross-reference below. | Which branch ran on the XNU boot, whether its conditional store executed, and the electrical state and hold time of the reset pin. The other LK branch clears an auxiliary object's bit at offset `0x90`. Its backing address was not resolved. |
| HCI and UniPro reset | The saved FDT names HCI, crypto and UniPro resets under the PDN syscon. Xiaomi's host reset sequence is separate from its device reset operation. | Final HCI/crypto/UniPro reset state and who may manipulate each signal. |
| Clocks and PHY | The pinned MT6897 clock tables define separate AO/PDN gates and TOPCKGEN parents. The captured M-PHY is version 1. The generic Linux PHY power functions return early for nonzero `mphy-ver`. | Final parent mux, votes, bus/reference continuity, and actual PHY readiness under the XNU boot. |
| Power domain | The FDT describes rails and vendor RTFF/MTCMOS policy. Its HCI node has no `power-domains` property. The Linux driver uses firmware-mediated MTCMOS and reference clock control. A saved BL31 MTCMOS path overlaps a Linux-owned power controller range. | Effective rail/domain state, ownership and a supported, checked runtime contract for XNU. |
| Final BL31 exit | The saved kernel-boot callback path runs EMI/SMPU work after LK cleanup. | Effective non-secure read/write permissions, reset and power state, interrupt ownership and DMA route on the same Slot B XNU entry. |

The device tree supplies topology for this board. Android's runtime state
belongs to its own boot. Keep both separate from XNU ownership.
[Xiaomi host reset and clock/power code](https://github.com/MiCode/MTK_kernel_device_modules/blob/3c4ccd07d5624879555ec710c11bb8818e5cb5c6/drivers/ufs/ufs-mediatek.c),
[MT6897 clock table](https://github.com/MiCode/MTK_kernel_device_modules/blob/3c4ccd07d5624879555ec710c11bb8818e5cb5c6/drivers/clk/mediatek/clk-mt6897-peri.c#L274-L327),
[MediaTek PHY driver](https://github.com/MiCode/MTK_kernel_device_modules/blob/3c4ccd07d5624879555ec710c11bb8818e5cb5c6/drivers/phy/mediatek/phy-mtk-ufs.c#L152-L179)

## Identifying the always-on syscon bit

1. In the hash-pinned BL31 sample, the bootloader service selector 2 at
   file offset `0x44e84` calls helper `0x44f84`.
2. The separate kernel UFS dispatcher starts at `0x45008`. Selector 2
   indexes the 16-bit table at `0x52fd6` with `selector - 1`. The entry is
   42, so `0x45050 + 42 * 4 = 0x450f8`. The branch at `0x450fc` also
   calls `0x44f84` with the reset-level argument.
3. The pinned Xiaomi kernel header names that selector
   `UFS_MTK_SIP_DEVICE_RESET` and supplies the `high` argument.
   Xiaomi's reset routine drives it low to assert device reset and high to
   release it. The shared BL31 helper conditionally sets bit 0 of
   `0x112b8090` to the boolean argument at `0x44fe0`. This identifies bit 0
   as the **UFS device reset-level control in the saved implementation**.
   The companion read at `0x44fec` is HCI `0x112b2240`, the MediaTek IP
   version register. The code discards the value.

This closes the register-purpose question for this saved code. It leaves
runtime branch selection, actual pin state, controller reset and DMA
quiescence open. The AO/PDN bus-clock gate table describes separate
registers. The same-boot XNU evidence must still establish them.
[Xiaomi reset selector](https://github.com/MiCode/MTK_kernel_device_modules/blob/3c4ccd07d5624879555ec710c11bb8818e5cb5c6/drivers/ufs/ufs-mediatek-sip.h#L14-L19),
[Xiaomi active-low device-reset routine](https://github.com/MiCode/MTK_kernel_device_modules/blob/3c4ccd07d5624879555ec710c11bb8818e5cb5c6/drivers/ufs/ufs-mediatek.c#L1935-L1958),
[Xiaomi IP version register](https://github.com/MiCode/MTK_kernel_device_modules/blob/3c4ccd07d5624879555ec710c11bb8818e5cb5c6/drivers/ufs/ufs-mediatek.h#L41-L49)

The exact decoded table, firmware digest, source blob and match results
are in `outputs/duchamp-ufs-ownership-dma-20261115/reset-selector-audit.json`.
The output directory includes both dispatcher disassemblies and the
matching helper. The existing exact LK/BL31 audit and its nine unit
checks passed. No firmware operation was invoked.

## Ownership needed for future validation

A trusted authority must identify the active firmware build, actual Slot B,
the loaded XNU image, the live FDT and the final handoff boundary for one boot.
It must account for the exclusivity and lifetime of HCI access, power and
rails, clock votes, PHY, reset, interrupts, firmware control, DMA and cache.
Unknown fields or a shared owner that can subsequently reconfigure resources
block validation. The new format binds those assertions to the existing
gate lease and the independent DMA evidence. The stock LK and BL31 samples
provide no producer for this record.
[DMA safety requirements](DUCHAMP_UFS_DMA_SAFETY.md),
[handoff format and tests](DUCHAMP_UFS_HANDOFF_FORMAT.md)
