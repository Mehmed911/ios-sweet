# Duchamp SPI2 one-shot touch diagnostic

The diagnostic accepts a trusted platform grant, waits for GPIO9 and reads
exactly one FocalTech report. The parser checks the controller status, CRC,
packet format and native coordinate bounds. It does not register an interrupt,
program a DMA address or access a physical device by itself.

## Evidence and ownership

| Resource | Evidence on Duchamp | Needed at XNU handoff |
| --- | --- | --- |
| SPI2 | DTB maps CS0 to the controller at `0x11012000/0x100`. The stock driver completed 14 real 100-byte reads through its DMA branch. | Exclusive controller and pad access, IRQ ownership and a bounded start/completion/quiesce implementation. |
| Touch IRQ | GPIO9 is routed via the MediaTek pin controller. Linux reported IRQ 56 for the touch line and IRQ 462 for SPI2 completion in the recorded boot. | Bind the DT interrupt specifiers through XNU's IRQ provider. Linux virtual IRQ numbers cannot be used as hardware interrupt IDs. |
| Clocks and power | The stock driver enables the parent, selector and bus gate. Live Android snapshots showed GPIO11–14 in SPI mode, reset GPIO60 high, AVDD GPIO73 high and MT6368 VTP at 1.8 V. | Confirm handoff state and delegate these resources to XNU. The probe requires an awake application-mode sensor. |
| DMA | The controller's DT compatible selects the extended DMA registers. The driver requests a 36-bit mask. The saved `/soc/dma-ranges` declares a 64 GiB identity window. | Prove actual bus addresses for both pinned buffers, the effective address width and direct or IOMMU mapping. Prove the buffers do not require bounce. |
| Cache | The SPI2 node has no `dma-coherent` or `iommus` property. Stock Android enables SWIOTLB in its kernel config. | Establish the coherency domain, system-cache ownership and which operations reach the SPI2 point of coherency. A missing DT property cannot prove that an IOMMU or bounce is unused. |

[Stock ID and resource checks](../../MT6897-SPI2-ID-PROBE.md) ·
[Pinned MediaTek SPI source](https://github.com/mt6897-devs/android_kernel_device_modules_6.1/blob/a805f95d61dbf0b2959c9262acc626893114321d/drivers/spi/spi-mt65xx.c) ·
[Linux DMA mapping guide](https://docs.kernel.org/core-api/dma-api-howto.html)

## QEMU

The ARM64 model uses separate CPU and simulated device views of the two DMA
buffers. It checks missing and stale grants, overlaps and out-of-range addresses,
the exact order of cache operations, timeout quarantine and bad CRC.

```sh
python3 tools/test-mt6897-spi2-probe.py
python3 tools/test-mt6897-spi2-probe.py --capture work/duchamp-touch-20261109-v1/android-verified.json
```

The XNU replay uses the existing QEMU fixture with one 100-byte report in
`reports` and boot arguments `sweethidtest=15 sweet-qemu-spi2=1
sweet-qemu-spi2-dma-probe=1`. It checks that the incomplete grant runs no
cache operations or transfer, then performs the sequence on guest RAM and
parses one captured frame. The QEMU provider has no MediaTek register or
interrupt access. Its physical and device addresses are simulation labels.

## Physical run requirements

1. Start the diagnostic using a proven RAM launch provider and preserve a
   normal Android recovery path. The saved LK audit found no registered RAM
   execution command. The installed Android configuration has both
   `CONFIG_KEXEC` and `CONFIG_KEXEC_FILE` disabled.
2. Supply a platform grant tied to the boot generation and hold it through
   release. Pin two disjoint 128-byte buffers for the 64-byte cache-line
   diagnostic and pass separate CPU, physical and device addresses. Keep the
   buffers isolated from framebuffer and reserved memory. IRQ and DMA waits
   are each bounded at 250 ms.
3. Wait for GPIO9, clean TX to PoC, clean and invalidate RX, then complete
   those operations before starting SPI2. Issue `01 a0 00 5b` and the rest
   of the 100-byte transaction with CS0 asserted once. Verify completion
   and DMA idle before invalidating RX and returning bytes to the CPU.
4. Record one completion, the verified byte count, CRC and decoded report
   in RAM. Keep the buffers and mappings quarantined if the engine may
   still be active. A boot takes one attempt, including any failure.

The software is staged for the test. The physical provider and its
non-persistent launch entry remain pending.
[RAM launch audit](../../loader/MT6897-RAM-LAUNCH.md)

Use the saved LK image to reproduce the launch gate offline.

```sh
python3 tools/audit-duchamp-lk-ram-launch.py --lk ../phone-firmware/lk_a.bin \
  --require-provider --output work/spi2-ram-launch-preflight.json
```
