# Duchamp SPI2 and FocalTech ID probe

This diagnostic runs inside the already booted, rooted stock Android system.
It streams a shell script into the existing ADB session and uses the bound
Linux drivers. It requires no boot image, module load, partition write, or
direct MMIO. The stock LK audit still has no standalone RAM boot provider.
[RAM launch audit](loader/MT6897-RAM-LAUNCH.md)

## Verified against the saved DTB and driver source

Saved DTB SHA-256 `9c49589f70044127be8941a9ea5537977f440ccd5ac15cfd24e120c8a1181d29`.

| Resource | Saved configuration |
| --- | --- |
| SPI2 | `0x11012000`, size `0x100`, compatible `mediatek,mt6985-spi`, pad 0, CS0 |
| Clock path | Topckgen ID 140 `univpll_d6_d2` → Topckgen ID 72 `spi2_sel` → `spi2_ck` → PERICFG_AO ID 14 `peraop_spi2_bclk` |
| SPI pins | Mode 1 on GPIO11 SCLK, GPIO12 CSB, GPIO13 MISO, GPIO14 MOSI |
| Touch GPIOs | GPIO60 reset, GPIO9 touch IRQ. The saved IRQ specifier is `<9 0x2008>`. |
| Digital supply | MT6368 `mt6368_vtp`, fixed 1.8 V from `iovdd-supply` |
| Analog enable | GPIO73, active high. The stock FocalTech driver reads the DT property named `goodix,avdd-gpio`. |

The Linux SPI controller chooses the declared parent and enables the bus clock
via runtime PM. The board advertises a 15 MHz ceiling. The touch driver uses
SPI mode 0 with eight bits per word. Each ID read takes a ten-byte transaction
and fits the 32-byte FIFO. Clock enable state, measured rail voltage and
firmware ownership after a standalone handoff require separate evidence.
[MediaTek SPI driver](https://github.com/mt6897-devs/android_kernel_device_modules_6.1/blob/a805f95d61dbf0b2959c9262acc626893114321d/drivers/spi/spi-mt65xx.c)
· [Clock bindings](https://github.com/mt6897-devs/android_kernel_device_modules_6.1/blob/a805f95d61dbf0b2959c9262acc626893114321d/include/dt-bindings/clock/mt6897-clk.h)
· [Pin definitions](https://github.com/mt6897-devs/android_kernel_device_modules_6.1/blob/a805f95d61dbf0b2959c9262acc626893114321d/include/dt-bindings/pinctrl/mt6897-pinfunc.h)
· [FocalTech power and GPIO source](https://github.com/mt6897-devs/android_kernel_device_modules_6.1/blob/a805f95d61dbf0b2959c9262acc626893114321d/drivers/input/touchscreen/focaltech_3683g/focaltech_core.c)

The saved FocalTech binary checks application-mode registers `0xA3` and
`0x9F` for `0x56` and `0x72`. The boot-mode signature `0x36B3` is separate.
The driver's stored IC ID can be filled from the model table after a boot-mode
match, so it cannot prove that those two application-mode reads succeeded.
[ID mapping](https://github.com/mt6897-devs/android_kernel_device_modules_6.1/blob/a805f95d61dbf0b2959c9262acc626893114321d/drivers/input/touchscreen/focaltech_3683g/focaltech_common.h)

## Run on stock Android

Run preflight with the phone in Android and ADB authorized. Use `--adb` for an
ADB executable outside the current PATH and `--serial` to select a device
when necessary.

```text
python tools/probe-duchamp-spi2-id.py
```

The probe requires the saved DT wiring and the loaded FocalTech and MediaTek
module build IDs. It checks the device bound to SPI2 CS0 instead of assuming
a Linux bus number. It prints available clock, pinmux, GPIO and regulator
snapshots without mounting debugfs. A suspended SPI controller at idle can
resume automatically for a transfer. An unavailable snapshot remains unknown.

Keep Android awake for the fresh test.

```text
python tools/probe-duchamp-spi2-id.py --read-id
```

The opt-in mode sends the literal three-byte requests `A3\n` and `9F\n` to the
driver's volatile sysfs debug endpoint. In the pinned implementation, the two
hex characters select the read branch and the newline completes the request.
The driver serializes the SPI transfer and checks its status and CRC. The
probe stops on a mismatch, a driver error, or a stale response. It does not
invoke the reset, boot-mode, firmware update, or arbitrary register endpoints.
[Debug handler source](https://github.com/mt6897-devs/android_kernel_device_modules_6.1/blob/a805f95d61dbf0b2959c9262acc626893114321d/drivers/input/touchscreen/focaltech_3683g/focaltech_ex_fun.c)
· [FocalTech SPI source](https://github.com/mt6897-devs/android_kernel_device_modules_6.1/blob/a805f95d61dbf0b2959c9262acc626893114321d/drivers/input/touchscreen/focaltech_3683g/focaltech_spi_v2.c)
