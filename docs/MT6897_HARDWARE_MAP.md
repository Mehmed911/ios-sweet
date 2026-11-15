# MT6897 hardware map

The canonical generated facts are [hardware.json](../devices/duchamp/hardware.json),
not addresses copied from another SoC. Generator:
devices/duchamp/tools/hardware.py, using the saved final FDT SHA-256
`9c49589f70044127be8941a9ea5537977f440ccd5ac15cfd24e120c8a1181d29`.
It verifies the digest before parsing and excludes bootargs and identifiers.

| Resource | Captured declaration | Access at XNU entry |
| --- | --- | --- |
| RAM | `/memory`: PA 0x40000000, size 0x300000000 | Not wholly free; subtract reservations and live allocations |
| Reservations | 56 `/reserved-memory/` nodes, plus FDT reserve map; dynamic ranges explicitly UNKNOWN | Never relocate into a reservation by copying a foreign layout |
| GICv3 | 0x0c400000 / 0x40000, GICR 0x0c440000 / 0x200000 | Existing bring-up; fresh ownership UNKNOWN |
| ARM timer | `/timer`, 13,000,000 Hz, resolved PPI data in JSON | Architectural counter history is separate from current IRQ ownership |
| UART | Four DT UARTs 0x11001000 through 0x11004000, 0x1000 each | Active console, pinmux and clock ownership UNKNOWN |
| UFS HCI | 0x112b0000 / 0x3000; host + eight MCQ IRQ declarations | Physical reader remains disabled |
| UFS PHY | 0x112a0000 / 0x10000 | PHY/power/reset ownership UNKNOWN |
| MCQ runtime | Pinned Xiaomi header and current Linux: SQD 0x2800, SQIS 0x2814, CQD 0x281c, CQIS 0x2824, stride 0x30 | No grant inferred from offsets |
| Touch | `/soc/spi2@11012000/xiaomi_touch@0`, focaltech,n11a-3683g-spi | Actual clocks/GPIO/DMA ownership under XNU UNKNOWN |
| GPU | `/soc/mali@13000000`, 0x480000, arm,mali-valhall | G615 target, no copied G52/G57 initialization |
| Display | Panel alternatives, display blocks and inherited framebuffer reservation in JSON | Cold init, active panel selection and accelerated scanout UNKNOWN |
| Inherited framebuffer | Existing mt6897_platform.c: 0xfcc2f000, stride 4992, 1220x2712x32 | Historical console proof; not a new display driver |
| USB | USB/PHY/extcon declarations and providers in JSON | Actual XNU controller/PHY initialization UNKNOWN |
| PMIC, clocks, resets, domains | Provider references and register declarations in JSON | Declarations do not delegate them to XNU |
| DMA/IOMMU | UFS has no iommus binding in this final FDT; dma-ranges is recorded | Absence does not prove bypass, cache coherency or exclusive ownership |

Historical entry PC `0x40000000` and x0 `0x47c80000` are recorded in
duchamp/PHONE-PC-X0-FLASH-TRIAL.md. They do not prove those values are invariant
across firmware updates. QEMU uses its own guarded entry/FDT addresses; its ADT
and PCI addresses must not enter a physical configuration.

Every generated node records register_access and resource_ownership_at_xnu as
UNKNOWN. Unsupported non-MMIO `reg` encodings are UNKNOWN, not coerced into
invented addresses. Missing DTBO applicability, retained pmsg behavior, cache
ownership and cold initialization have explicit acquisition instructions in JSON.
