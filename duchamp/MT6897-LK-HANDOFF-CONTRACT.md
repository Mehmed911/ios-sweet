# Duchamp MT6897 LK handoff contract

This document records only facts reproduced from the saved Duchamp artifacts.
It deliberately separates LK's own load mapping, Android's static Image header
contract, and the final FDT handoff.  None of the checks below contacts a
phone, executes firmware, accesses MMIO, boots XNU, or authorizes flashing.

## Pinned evidence

| Artifact | SHA-256 |
| --- | --- |
| `lk_a.bin` | `f85373d3b4cdf3c959e38bbbfe198a2857e03a5266c6f2a40c319549a5ba957a` |
| `boot_a.img` | `1b972f4f1c98428f2fca1e7c1c8cf463e0122a70a290e482be3230c7838e3e12` |
| `vendor_boot_a.img` | `d1d1887eba4f7b4920fc4292de5cf4e9aa6e7ce474a6b45ffeb4141434743e49` |
| final live FDT | `9c49589f70044127be8941a9ea5537977f440ccd5ac15cfd24e120c8a1181d29` |
| saved `/proc/iomem` | `b6bf43ce2bcbe1d5d425b46977afe238653859f61403339b674a2c065054f833` |

`tools/audit-duchamp-lk-handoff.py` rejects any different receipt.

## Three different address facts

### 1. LK's own bootstrap mapping

The exact 16 MiB `lk_a` package starts with an `lk` entry whose raw AArch64
payload begins at partition offset `0x200` and has size `0xf1c70`.  Its stage-1
mapping record at partition offset `0xd6200` is:

```text
physical base  0x0000000050700000
virtual alias  0xffff000050700000
mapped bytes   0x0000000012000000
```

The startup literals use the same high virtual alias.  This proves the static
bootstrap mapping expected by this exact LK binary.  It does not constitute a
captured PC from a particular phone boot, so the report keeps
`runtime_pc_register_captured=false`.

### 2. Android Image load contract

The exact vendor-boot v4 header declares `kernel_addr=0x40000000`.  The stock
boot kernel expands from legacy LZ4 to an ARM64 Image with:

```text
text_offset = 0
image_size  = 0x021d0000
flags       = 0x0a
```

Consequently `0x40000000` is the static Android Image load/entry contract for
this captured image.  It is not a direct runtime PC capture.  LK computes the
kernel target dynamically from the boot image and its memory allocator.

### 3. Final live FDT handoff

The vendor-boot header declares both `tags_addr` and `dtb_addr` as
`0x47c80000`.  The saved final live FDT is `0x76980` bytes, and the matching
runtime `/proc/iomem` capture contains exactly the page-rounded reservation:

```text
47c80000-47cf6fff : reserved
```

This independently corroborates `0x47c80000` as the final FDT placement for
the captured Android boot.  The DTB does not contain a property describing its
own physical address, and the incoming bootshim `x0` value was not numerically
captured.  The report therefore does not promote this evidence to a live
register measurement.

## LK-to-secure-monitor handoff

The LK Linux handoff is not a direct branch.  The exact instruction sequence at
partition offset `0x10054` prepares SMC function `0xc2000115`, a runtime kernel
target and a runtime final-FDT target.  The trampoline at partition offset
`0x10cd4` executes `smc #0`.

At the callsite, LK supplies the secure trampoline in `x0`, the function ID in
`x1`, the kernel target in `x2`, the FDT target in `x3`, and zero in `x4`.  The
wrapper/trampoline presents the secure monitor with the function ID in `x0`,
kernel target in `x1`, FDT target in `x2`, zero in `x3`, and one in `x4`.
Neither target address is a fixed literal in `lk_a`.

## RAM and reserved memory

The final FDT declares one 12 GiB RAM range:

```text
[0x40000000, 0x340000000)
```

The audit parses 52 fixed reserved-memory ranges and four dynamic allocation
requests.  Important fixed ranges include BL31 at
`[0x48800000,0x48a00000)` and the framebuffer at
`[0xfcc2f000,0xfffff000)`.  The four dynamic requests are not final physical
allocations and therefore remain a runtime-layout uncertainty.  The FDT header
has no `/memreserve/` entry for the FDT itself; the FDT placement evidence comes
from vendor-boot metadata and the saved runtime map.

## Reproduce the audit

Run from the repository root under the local Linux environment, using a new
output path:

```sh
python3 tools/audit-duchamp-lk-handoff.py \
  --lk ../phone-firmware/lk_a.bin \
  --boot ../phone-boot/boot_a.img \
  --vendor-boot ../phone-boot/vendor_boot_a.img \
  --fdt ../phone-fdt.bin \
  --iomem research/mt6897-live-evidence/14480520-210535/iomem.txt \
  --output work/lk-handoff-audit-v1/report.json
```

The verified local result is:

```text
duchamp-lk-handoff: PASS lk=0x50700000 image=0x40000000 fdt=0x47c80000 execution=blocked
```

## Separate fail-closed phone-layout path

`duchamp/bootshim/build.sh` now has an offline-only `PHONE_LAYOUT=1` mode.  It
requires the exact audit report, rejects every payload, transport, materialize,
ready, return and jump option, links at the static Android Image contract, and
emits no execution-capable transport.

The first assembly instructions require `_head == 0x40000000` and inherited
`x0 == 0x47c80000`.  Whether the checks pass or fail, the image immediately
enters `WFE` before clearing BSS, calling C, stopping the watchdog, drawing to
the framebuffer, touching MMIO, copying a payload, or branching to XNU.  This
is a layout artifact, not a phone test image.

```sh
cd duchamp/bootshim
SHIM_OUT=out-phone-layout-v1 \
PHONE_LAYOUT=1 \
PHONE_CONTRACT=../../work/lk-handoff-audit-v1/report.json \
sh ./build.sh
```

The verified build result is:

```text
duchamp-phone-contract: PASS execution=blocked
duchamp-phone-layout: PASS base=0x40000000 bytes=40848 fdt-ceiling=0x47c80000 execution=blocked
```

The verifier also requires zero relocations, no undefined symbols, an empty LK
capsule section, and absence of XNU jump, payload and LK transport symbols.

## Still unknown

- The numeric LK-to-Image runtime PC has not been captured.
- The numeric incoming Linux `x0` FDT pointer has not been captured.
- Final addresses of the four dynamic reserved-memory requests are not proven.
- No safe phone capsule/source placement has been established.
- This milestone does not prove DMA/IOMMU, UFS, firmware ownership, or a full
  phone boot.

Those unknowns keep the phone path execution-blocked by design.
