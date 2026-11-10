# Duchamp MT6897 LK handoff contract

This document records the saved-artifact audit and a later, separately
approved hardware capture. It separates LK's own load mapping, Android's Image
header contract, and the final FDT handoff. The offline audit commands do not
contact a phone, execute firmware, access MMIO, boot XNU, or authorize flashing.

## Later hardware observation, 2026-11-06

A user-approved isolated diagnostic booted through `boot_a` and displayed the
runtime Image `_head` address `0x40000000` and inherited entry `x0=0x47c80000`.
The legible user photo and exact capture-image receipts are documented in
[PHONE-PC-X0-FLASH-TRIAL.md](PHONE-PC-X0-FLASH-TRIAL.md). The original `boot_a`
was restored afterward and verified through Android/root.

These two numeric observations now independently corroborate the earlier
static Image/FDT placement. The historical offline JSON remains immutable and
still marks runtime capture false because its saved-file inputs do not include
this later photo. The observation does not measure LK's own internal PC,
validate live FDT contents, or establish a phone capsule ownership contract.

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
this captured image. That audit alone is not a runtime capture; the later
hardware observation above separately confirms the Image address. LK computes the
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
own physical address. At the time of the static audit, incoming bootshim `x0`
had not been numerically captured, so that report does not promote its saved
inputs to a live register measurement. The later hardware observation above
now independently confirms the inherited `x0` value for the approved trial.

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

## UFS evidence at the BL31 exit boundary

The optional `--atf` input follows the kernel-boot descriptor in the pinned
BL31 capture from `tee_a`. The normal first-entry handler selects callback
group 5, whose table contains `sip_emi_set_nsr_permission` followed by
`spm_smpu_hre_first_bk`. Both precede the handler's final helper. An LK-side
snapshot taken before the secure call would miss this work. The capture
identifies the BL31 build seen in Android, while byte-for-byte equivalence
to the running BL31 remains unverified.

An acceptable hardware capture has two correlated records from the same
boot. The firmware record is emitted through a documented vendor trace or
supported diagnostic channel after the last platform work at the EL3 exit
boundary. The receiving bootshim records the same boot identifier at its
first entry and binds it to the loaded XNU image before any XNU UFS activity.
Keep both records in reserved RAM or export through the documented channel.

| Required field | What the capture must establish |
| --- | --- |
| Provenance | Firmware identity, fresh boot identifier, Duchamp identity, XNU image and live FDT digests, and the stage that supplied each observation. |
| Controller | Actual HCE state after shutdown, with the queue mode and the point at which submissions stopped. |
| Legacy queues | Transfer and task doorbells and run/stop status. Record drain after the last firmware storage operation. |
| MCQ | If enabled, cover every configured submission and completion queue, its operational state and head/tail positions, and outstanding work. If disabled, record the observed mode. |
| Ownership | An explicit grant for XNU or a documented firmware-mediated contract covering the controller, clocks and HW voter, reset, PHY, regulators and interrupts. |
| DMA and cache | The effective DMA mapping and its owner, firewall permission, IOMMU domain or direct window, bounce disposition, and who performs cache maintenance for the XNU buffers through the system cache. |

If firmware turns off register access during shutdown, the record needs the
last valid drain sample plus a firmware guarantee that no producer or DMA
can resume before the handoff. A zero doorbell alone cannot establish DMA
quiescence or grant access. The firmware-side ownership grant must come from
the authority that can issue it. The receiver's observations establish
receipt and timing. [AArch64 boot contract](https://docs.kernel.org/arch/arm64/booting.html#call-the-kernel-image)

The published Duchamp Android driver also exposes
`/proc/atf_log/atf_raw_buf`. Its read handler copies the reserved ATF buffer
and advances a separate driver offset. The saved Android FDT declares a 2 MiB
region with the expected compatible string. A future raw export can be
examined for retained entries, but the reader supplies neither a previous-boot
identity nor a UFS measurement. There is no raw export tied to the recorded
Slot B trial. [Duchamp ATF log driver](https://github.com/MiCode/MTK_kernel_device_modules/blob/bsp-duchamp-u-oss/drivers/misc/mediatek/atf/atf_log.c)

The saved stock Android logs lack this pair. The existing PC/x0 diagnostic
reports CPU entry state and has no UFS sampling or grant channel. The
[RAM launch audit](loader/MT6897-RAM-LAUNCH.md) currently has no documented
no-write entry provider for Duchamp. The optional BL31 audit records these
scope limits and leaves the physical UFS gate closed.

### Live retained LK log on Slot B

Fastboot identified Duchamp with B selected. The previously audited OEM log
handler returned 197219 bytes over USB and completed with OKAY. The log
records loading BL31 and entering Fastboot. It contains no XNU handoff
marker, no HCE or queue state, and no DMA or cache grant. The result proves
that the PL/LK export works on the phone. The Android ATF raw export and a
firmware trace from the XNU handoff remain separate and unverified.

The post-capture query still reported B selected and reported zero tries
remaining, with successful and unbootable both reported as no. This pass did
not issue a reboot, boot, slot change or partition write. The receipt and
private raw capture are under outputs/duchamp-slot-b-live-lk-log-20261111.

The installed LK also rejected the standard get_staged request with
`unknown command`. Its max-fetch-size reply was empty. The 35 registrations in
the saved LK have no upload or fetch command. The archived A/B LK hashes
match, and the saved LK build identifier matches the live version reply.
The dump_pllk_log handler uses the same retained PL/LK buffer as uefilog.
The lkmsg and lpmsg handlers map the separate pstore region, while expdb
exports crash storage. No path reviewed establishes an export of the live
ATF ring through LK Fastboot. The same-boot XNU provenance is still missing.
See outputs/duchamp-slot-b-atf-fastboot-audit-20261111.

The live pstore follow-up returned 262144 bytes through lkmsg and 65536
through lpmsg, each with terminal OKAY. After excluding the send-buffer
tails, the longest ASCII sequences were six and four characters,
respectively. Neither slice had the expected XNU markers, a boot identifier
or UFS handoff fields in ASCII or UTF-16. These are the exported console
and pmsg slices only. LK omits zone-header bytes, and other pstore zones and
the ATF ring were not read. See outputs/duchamp-slot-b-pstore-20261111.

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

To include the captured secure-side path, add
`--atf research/mt6897-firmware-live/20261101-v1/atf.bin` and use a fresh output
path. The report adds `captured_bl31_handoff`. The default report is unchanged.

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

## Slot B UFS handoff diagnostic

The optional receiver runs from the existing PC/x0 diagnostic entry. It reports
the FDT fingerprint in the framebuffer line D0 and missing handoff evidence in
D1. The fingerprint correlates the observed x0 with the bytes captured in RAM.
In D1, bits 0 through 3 mark the missing firmware trace, unknown
controller-enable state, unknown queue state, and unverified DMA delegation.
Bit 4 also appears if the FDT header or bounds check fails. The receiver
halts at the bootshim and leaves the UFS registers untouched.

Run from the repository root with a fresh output directory:

```sh
UFS_HANDOFF_PROBE=1 sh duchamp/bootshim/test_phone_capture_qemu.sh \
  work/lk-handoff-audit-v1/report.json work/slot-b-ufs-receiver-v1
```

QEMU verifies the fingerprint from guest RAM and requires D1 to be 0xf for a
valid FDT. The known-block qtest exercises the separate emulated UFS path. A
physical read requires same-boot firmware evidence of the controller and its
active queue mode, empty transfer and task queues, the resource grant, and DMA
address and cache ownership.

## Still unknown

- LK's own numeric internal PC has not been captured; the diagnostic observed
  the runtime Android Image `_head`, a separate address.
- The current photo does not display numeric CurrentEL or SCTLR values.
- Final addresses of the four dynamic reserved-memory requests are not proven.
- No safe phone capsule/source placement has been established.
- This milestone does not prove DMA/IOMMU, UFS, firmware ownership, or a full
  phone boot.

Those unknowns keep a new phone capsule/transport path closed. The approved
isolated capture route and its completed stock recovery are documented above.
