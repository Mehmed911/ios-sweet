# Duchamp LK UFS shutdown analysis

## Inputs and scope

The local audit matched the saved LK partition and saved BL31 sample against
their pinned SHA-256 values and reran the existing entry audit from
`tools/audit-duchamp-lk-handoff.py`. The firmware is analyzed as data.
Offsets below are file offsets, including the LK container header.

| Input | SHA-256 |
| --- | --- |
| Saved `lk_a.bin` | `f85373d3b4cdf3c959e38bbbfe198a2857e03a5266c6f2a40c319549a5ba957a` |
| Saved BL31 `atf.bin` | `716222a632e4a0623a2e467e17f1d36f38a37f79a1c026447fe724e75e90e07e` |
| Saved final Duchamp Android FDT | `9c49589f70044127be8941a9ea5537977f440ccd5ac15cfd24e120c8a1181d29` |

The November 11 image audit matched saved LK to the then-installed B image.
The retained Fastboot log from B reported earlier UFS and M-PHY initialization.
The archived XNU trial booted from the RAM root. The saved BL31 runtime
identity is supported by the Android banner. Byte identity with the firmware
running during the Slot B XNU trial and a same-boot state record are missing.
[Prior Slot B audit](DUCHAMP_SLOT_B_UFS_HANDOFF.md)

## What the saved shutdown code does

| Step | Verified static action | Runtime boundary |
| --- | --- | --- |
| Enter platform cleanup | LK `0x10070` branches to the final wrapper at `0x196b8`. At `0x196e8` it calls cleanup `0x3b0c`, which calls UFS shutdown `0x79e0c` at `0x3b14`. | The UFS routine precedes the secure kernel-boot handoff and other platform cleanup. |
| Bootloader secure service before notification | The shutdown calls `0x7a490` at `0x79e24`. One branch invokes the bootloader UFS service with selector `0x10` and value `1`. The matching handler in the saved BL31 sample takes the RPMB HMAC unmapping path at `0x44f38`. The error string at `0x61a65` identifies that mapping. | The call is conditional, and the shutdown caller discards its result. This is secure mapping teardown in the sampled code. It supplies no host clock, power, or DMA drain evidence. |
| Disable the auto-hibernate idle timer | LK `0x79e30` stores zero to the HCI's AHIT at offset `0x18`. | The write attempts to disable the timer. It supplies no observation of the link state. |
| Notify the UFS device of power-off | The call at `0x79e34` enters `ufs_poweroff_notify` (`0x784d8`). The builder at `0x750a0` produces a six-byte START STOP UNIT CDB with power condition 3 (PowerDown). The dispatch at `0x769dc` writes a slot bit to the legacy transfer doorbell at HCI offset `0x58` and follows it with a completion wait. The notification can retry on error. | The caller advances regardless of return status. This command can request a UFS device power mode. It supplies no proof that the command completed, that UniPro entered Hibern8 or link-off, that queues drained, or that rails were removed. |
| Run the second auxiliary helper | LK `0x79e3c` calls `0x78130`. If the auxiliary pointer is present, one path clears bit 0 at that object's offset `0x90`. The other calls the sampled BL31 bootloader UFS handler with selector `2` and value `0`. The matched BL31 descriptor is at `0x66040`, names `MTK_SIP_BL_UFS_CONTROL`, and points to handler `0x44e64`. Its helper at `0x44f84` conditionally clears bit 0 at `0x112b8090` and performs a discarded read at `0x112b2240`. | The DTB places the cleared bit in the UFS always-on syscon. Xiaomi's documented clock gate table uses other offsets there. A subsequent selector audit identifies bit 0 as the device reset-level control in the saved code. The runtime branch, pin state, reference clock and bus gates remain unmeasured. [Reset selector cross-reference](DUCHAMP_UFS_OWNERSHIP.md#identifying-the-always-on-syscon-bit) |
| Disable the controller | LK `0x79e48` stores zero to HCE at HCI offset `0x34`. It then returns at `0x79e54`. The direct shutdown routine contains no HCE readback, timeout on HCE, or post-store queue sample. | HCE deassertion and no further in-flight DMA are unverified. No explicit HCI, UniPro, crypto, PHY or device reset-pin assertion was identified in the decoded routine. |

Register names are corroborated by the pinned Android kernel header.
PowerDown condition 3 and the START STOP UNIT CDB construction are independently
visible in the same kernel source. [UFSHCI registers](https://github.com/aosp-mirror/kernel_common/blob/cf2c2dc91b9e9f016dc25cf095b1fe34cb5dfcb6/include/ufs/ufshci.h#L26-L56),
[device power modes](https://github.com/aosp-mirror/kernel_common/blob/cf2c2dc91b9e9f016dc25cf095b1fe34cb5dfcb6/include/ufs/ufs.h#L496-L503),
[Linux START STOP builder](https://github.com/aosp-mirror/kernel_common/blob/cf2c2dc91b9e9f016dc25cf095b1fe34cb5dfcb6/drivers/ufs/core/ufshcd.c#L9383-L9397),
[Duchamp UFS clock providers](https://github.com/MiCode/MTK_kernel_device_modules/blob/3c4ccd07d5624879555ec710c11bb8818e5cb5c6/drivers/clk/mediatek/clk-mt6897-peri.c#L274-L327)

## Final BL31 handoff

LK hands off CPU execution through its separate kernel-boot secure call.
The saved BL31 kernel-boot descriptor at `0x65500` points to `0xb63c`.
Its callback table calls `sip_emi_set_nsr_permission` and
`spm_smpu_hre_first_bk` before final exit. This is later than the
bootloader UFS service calls above. The audited callback chain supplies
no UFS-specific post-cleanup sample, no positive read-access receipt,
and no documented transfer of clock, reset, PHY, IRQ or DMA ownership.
The LK cache transition is a CPU cache routine. It supplies no system
cache ownership or DMA quiescence evidence. [Pinned LK/BL31 audit code](../tools/audit-duchamp-lk-handoff.py),
[entry contract](../duchamp/MT6897-LK-HANDOFF-CONTRACT.md)

**Verified limit.** Saved firmware can attempt to stop the host, request
device PowerDown and conditionally request device reset through BL31. Final HCE,
legacy/MCQ queue state, link state, functional clocks, rails, MTCMOS,
PHY readiness, effective reset lines and the non-secure access policy
on the actual Slot B XNU boot remain unmeasured. No known-good
preserved controller state follows from the disassembly.

## Reproduction and hardware blocker

The outer workspace's `outputs/duchamp-mt6897-ufs-init-20261115` holds
`lk-bl31-audit.json`, `lk-shutdown-disassembly.txt`,
`lk-shutdown-followups.txt`, `lk-bl31-shutdown-route.txt` and
`lk-bl31-shutdown-effects.txt`. Each ranged disassembly was produced
with AArch64 GNU objdump and a file-offset VMA adjustment on the
hash-matched local input. The existing LK audit passed its nine
offline unit checks and the pinned source audit. No firmware call
was executed.

Either strategy needs a trusted receipt tied to the actual Slot B
XNU entry, after the last LK storage operation and the final BL31
callbacks. For a preserved-controller handoff, require measured
quiescence plus positive state and lifetime evidence for every reused
resource. For independent initialization, require ownership and the
ability to establish and verify a cold baseline, including DMA
isolation before any reset. See the
[initialization design](DUCHAMP_MT6897_UFS_INIT_DESIGN.md).
