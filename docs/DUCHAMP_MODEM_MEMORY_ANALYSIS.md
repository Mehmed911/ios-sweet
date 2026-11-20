# Duchamp modem reservations and DMA isolation

The reconstructed base plus overlay has two dynamic DPMAIF nodes. The archived Android FDT carries the same requests alongside 52 added physical `mblock-*` nodes. These are distinct evidence for a dynamic allocation policy and for fixed addresses in one recorded boot.

| Archived FDT region | Physical extent or request | Evidence scope |
| --- | --- | --- |
| `mblock-40/39/38/36-md_mem_usage` | `[0xed780000, 0xee000000)`, `[0xd4000000, 0xdb070000)`, `[0xd3d00000, 0xd3f50000)`, `[0xd0000000, 0xd3c60000)` | Fixed addresses in the archived FDT, all `no-map`. Cross-boot stability is unknown. |
| `mblock-37-ap_md_c_smem`, `mblock-28-ap_md_nc_smem` | `[0x8a000000, 0x8cf60000)` and `[0x8e000000, 0x8e130000)` | AP/modem shared reservations, both `no-map`. Current fabric permissions are unknown. |
| `mblock-35-ccci_tag_mem` | `[0xbf2f0000, 0xbf300000)` | Fixed tag memory in the archive, `no-map`, compatible `mediatek,ccci_tag_mem`. |
| `ccci-dpmaif-cache-memory` | `0x190000` bytes, 4 KiB alignment, allowed within `[0x40000000, 0x130000000)` | Dynamic request. |
| `ccci-dpmaif-nocache-memory` | `0x50000` bytes, same alignment and allowed range, `no-map` | Dynamic request. |
| `mkp-kernel-code-protection-memory` | `0x10000` bytes, allowed within `[0x40000000, 0x40010000)` | Separate dynamic request, intersects the start of both modeled Images. |
| `ssmr-reserved-cma-memory` | `0x8000000` bytes, 16 MiB alignment, allowed within `[0x80000000, 0x140000000)`, reusable | Separate dynamic request, outside the modeled staging and XNU window. |

## What Linux and the firmware evidence establish

The pinned Xiaomi driver looks up each DPMAIF compatible node, takes the base and size from `of_reserved_mem_lookup()`, and maps those allocations for the AP. The Linux device-tree allocator resolves `size` and `alloc-ranges` during early initialization. The Xiaomi driver's receive path also maps payload buffers with `dma_map_single()` and `dma_map_page()` and can use coherent allocations. The historical Android dmesg recorded active DPMAIF TX and RX queues. This identifies Linux's participation and the existence of DMA. The boot-specific DMA routing, retained descriptors, outstanding transactions and accessible address space at XNU entry are unknown. [Xiaomi reserved-memory consumer](https://github.com/MiCode/MTK_kernel_device_modules/blob/3c4ccd07d5624879555ec710c11bb8818e5cb5c6/drivers/misc/mediatek/eccci/hif/ccci_dpmaif_resv_mem.c#L57-L155), [Xiaomi buffer mapping](https://github.com/MiCode/MTK_kernel_device_modules/blob/3c4ccd07d5624879555ec710c11bb8818e5cb5c6/drivers/misc/mediatek/eccci/hif/ccci_dpmaif_bat.c#L113-L135), [Linux reserved-memory allocator](https://github.com/torvalds/linux/blob/master/drivers/of/of_reserved_mem.c)

The added `mblock-*` addresses and the archived Android runtime map must be kept as historical evidence. The proprietary `mblock_info` property was measured and hashed. Its format, completeness at final BL31 exit, and ownership semantics have no verified decoder for this installed firmware. The pinned BL31 binary audit shows EMI and SMPU callbacks at the kernel handoff. Their presence cannot establish the final protection coverage or which modem and DMA reservations survive the transfer. `no-map` constrains CPU mappings by the operating system. DMA isolation requires separate fabric, MPU or IOMMU evidence. [Property receipt](../../../outputs/duchamp-mt6897-safe-placement-20261117/mblock-property-evidence.json), [BL31 handoff evidence](DUCHAMP_FINAL_BL31_XNU_HANDOFF.md), [existing DMA safety analysis](DUCHAMP_UFS_DMA_SAFETY.md)

## What blocks a new B image

The previously observed B Image ended at `0x4300e7b0`. The additional staged bytes span `[0x4300e7b0, 0x436c1dd0)` for 4 MiB and `[0x4300e7b0, 0x43ac1dd0)` for 8 MiB. Each span is inside both DPMAIF allocation ranges. This is a possible address conflict. The actual earlier B boot and Android A allocations do not establish an exclusive claim for either additional extent in a later boot.

A supported evidence source needs to bind slot, Image identity and boot identity to the final allocator and protection state. It must identify compressed input, output and scratch while LK decompresses, then enumerate surviving LK/BL31 and modem reservations before the first new write. For all relevant masters, it must establish which limits, translations or fabric rules exclude both staging and the full XNU window throughout their lifetimes, or verify drain and continued exclusion. A final CPU-side memory map alone leaves the earlier staging write and outstanding DMA unresolved. The existing traces do not contain this evidence. The phone and all firmware and modem settings were left untouched.
