# MT6897 register backends and raw SMC — 2026-10-31

This milestone adds real command/register encoders and an AArch64 SMC
instruction conduit. They are exercised by native/ARM64 register models and
a separate QEMU EL3 monitor. They are **not linked into XNU or bound to phone
MMIO**. Installed firmware identity, active secure-resource ownership and an
UFS-to-IOMMU route remain unverified. The physical UFS root path stays disabled.

## Pinned evidence

Seven vendor files were downloaded and checked against exact Git blob IDs
from
[a805f95](https://github.com/mt6897-devs/android_kernel_device_modules_6.1/tree/a805f95d61dbf0b2959c9262acc626893114321d).
The catalog is `drivers/mt6897-backend-sources.json`; source receipts and hashes
are in the local result. The saved DTB was rehashed to
`9c49589f70044127be8941a9ea5537977f440ccd5ac15cfd24e120c8a1181d29`
before resolving regulator phandles, PMIC IDs, SPMI resources and IOMMU nodes.
Only selected hardware facts are reported, not private boot arguments.

| Captured binding | Matched source |
| --- | --- |
| UFS vcc -> MT6363 SID 4, VEMC, always-on, enable ramp 680 us | [mt6363-regulator.c](https://github.com/mt6897-devs/android_kernel_device_modules_6.1/blob/a805f95d61dbf0b2959c9262acc626893114321d/drivers/regulator/mt6363-regulator.c), [register definitions](https://github.com/mt6897-devs/android_kernel_device_modules_6.1/blob/a805f95d61dbf0b2959c9262acc626893114321d/include/linux/regulator/mt6363-regulator.h) |
| UFS vccq -> MT6319 SID 8, vbuck3, provider compatible mediatek,mt6315_8-regulator, ramp 256 us | [mt6315-regulator.c](https://github.com/mt6897-devs/android_kernel_device_modules_6.1/blob/a805f95d61dbf0b2959c9262acc626893114321d/drivers/regulator/mt6315-regulator.c), [register definitions](https://github.com/mt6897-devs/android_kernel_device_modules_6.1/blob/a805f95d61dbf0b2959c9262acc626893114321d/include/linux/regulator/mt6315-regulator.h) |
| mediatek,mt6897-spmi selects mt6xxx, SWINF channel 2; absent spmi-dev-mask defaults to route 0 | [spmi-mtk-pmif-core.c](https://github.com/mt6897-devs/android_kernel_device_modules_6.1/blob/a805f95d61dbf0b2959c9262acc626893114321d/drivers/spmi/spmi-mtk-pmif-core.c) |
| Display/MDP IOMMUs at 0x1e802000/0x1e810000; no UFS iommus/iommu-map on the inspected ancestry | [mtk_iommu.c](https://github.com/mt6897-devs/android_kernel_device_modules_6.1/blob/a805f95d61dbf0b2959c9262acc626893114321d/drivers/iommu/mtk_iommu.c), [MT6897 port bindings](https://github.com/mt6897-devs/android_kernel_device_modules_6.1/blob/a805f95d61dbf0b2959c9262acc626893114321d/include/dt-bindings/memory/mt6897-larb-port.h) |

The provider-compatible string, rather than the PMIC marketing name, selects
the matched MT6315 register ABI here. This does not independently identify
the installed chip revision.

## PMIF command programmer

`mt6897_pmif.c` implements channel-2 transactions with explicit little-endian
packing for 1–4 bytes and 16-bit register addresses. It validates count,
address overflow and the two supported SIDs before I/O. It accepts only the
saved route-mask-0 profile.

| Offset in authorized PMIF bank 0 | Operation |
| --- | --- |
| 0x000 | Require INIT_DONE bit 0 |
| 0x8a8 | SWINF2 state, (value >> 1) & 7 |
| 0x884 | Write data |
| 0x880 | EXT_REG_LONG command: type 3, write bit 29, SID, count-1, address |
| 0x894 | Read data |
| 0x8a4 | Clear this transaction's valid flag |

The caller must already own the initialized controller, routing, clocks and
serialization. The captured PMIF base is 0x1cc04000, span 0x8ff; all these
offsets fit that resource. No global PMIF/clock reset or interrupt setup is
attempted. Polls are limited by 10000 us and 1001 iterations, including when
the supplied clock stops advancing. An inherited valid reply is not cleared
or consumed. Failed operations latch the transport; no automatic retry.

A write waits for software-interface idle, but this is **not a PMIC ACK/NACK
or measured rail-state guarantee**. PMIC operations below additionally read
back their relevant register fields. Controller NACK/parity interrupt
handling still requires the physical integration.

## PMIC register services

`mt6897_pmic.c` implements explicit nominal-voltage requests and enable-only
operations through a serialized bus provider. It does not choose a voltage
target, disable rails, perform global probe/shutdown, or change modes.

For VEMC it reads TOP_TRAP 0x36, selects the appropriate nibble of VOSEL 0x1b40,
uses the documented 0x9c9c key at 0x39e, preserves the peer nibble and factory
VOCAL register, then relocks. It attempts relock after every unlock attempt,
including partial key-write or selector errors. A poisoned/unavailable bus
can prevent relock: that remains a latched failure requiring platform recovery,
not a claimed successful lock. Unsupported trap values fail without unlocking.
Unchanged selectors avoid protected writes.

VEMC enable updates only bit 0 of 0x1c23 and applies the captured 680-us delay
when newly enabled. The source's 16-entry nominal voltage table is used
exactly, without rounding or trim programming.

For SID-8 vbuck3 it writes selector 0x144d, enables via SET alias 0x1441/mask 4,
and applies the captured 256-us delay when newly enabled. Valid requests are
6250-uV multiples starting at 300000 uV. The matched driver advertises
n_voltages=0xbf, so selectors stop at 190 (1187500 uV). Selector 191 is refused
even though the linear-range endpoint and DTB maximum include 1193750 uV.
This conservative boundary avoids silently extending the source driver's
advertised selector count.

Authorization must cover all consumers, voltage safety, PMIC ABI and shared
regmap/bus ownership. Readback confirms programmed bits, not calibrated output
voltage, rail stability or physical PHY readiness. There is no supplied phone
SPMI mapping, scheduler lock, regulator-vote manager or DVFSRC implementation.

## Firmware transport

`mt6897_smc.S` executes SMC #0 with x0–x7 and captures x0–x3 while following
the SMCCC/AArch64 register-preservation contract. It is a raw conduit, not a
firmware implementation and not an automatically installed callback.

`mt6897_firmware.c` accepts only the previously implemented UFS MTCMOS and
reference-clock request shapes. It validates unused arguments, requires
per-request authorization and a matched-firmware reply verifier. Unknown
responses latch the service, preserve raw diagnostics and leave the caller's
success output untouched. There is no guessed a0/a1 normalization.

The separate
[reference UFS firmware handler](https://chromium.googlesource.com/chromiumos/third_party/arm-trusted-firmware/+/f3083e2e6c508d58f9bce1b2fce5eeb0903a4c6d/plat/mediatek/drivers/ufs/ufs_ctrl.c)
returns zero for the MTCMOS selector even when its CONFIG_MTK_MTCMOS body is
compiled out. This demonstrates why zero alone cannot prove a hardware effect.
That reference is not the installed MT6897 firmware or compatibility evidence.

The ARM64 test boots a purpose-built QEMU EL3 monitor, enters nonsecure EL1,
executes the actual raw SMC instruction, verifies all eight incoming registers,
four returned values, output guards and a policy-wrapper call, and exits
successfully. The monitor's deterministic reply is test data; it performs no
MT6897 power operation. No monitor binary or phone image is installed anywhere.

## IOMMU register programmer: deliberately partial

`mt6897_iommu.c` implements TTBR installation and bounded full/range TLB
invalidation for the source-defined display/MDP GEN2 register layout:

- require an exclusively owned, quiescent, already powered/configured normal
  domain with TLB_SYNC_EN, a fresh CPE status and an empty inherited TTBR;
- accept an externally built, synchronized, matched ARM_V7S/MTK_TTBR_EXT table;
  write/read back its **already encoded** TTBR at 0x000;
- write INV_SEL 0x02c = 3, INVALIDATE 0x020 = 2 for full invalidation;
- for ranges, encode 34-bit addresses with low page bits carrying upper
  address bits, write 0x024/0x028, then INVALIDATE = 1;
- poll CPE_DONE 0x12c for at most 1000 us / 101 iterations, then clear it;
  failures latch state, with no fallback reset or table reclamation.

These are actual register-programming algorithms, tested with a register
model. They do **not** implement page-table allocation/encoding, SMI/stream
routing, multi-IOMMU shared-domain coordination, power/clock/security setup,
fault interrupts or physical DMA reachability. The caller's table-authorized
flag is an external precondition, not proof generated by this API.

UFS client selection is unconditionally refused before authorization or any
register access. The available source profiles are multimedia/APU IOMMUs; a
different undocumented UFS route must not be invented from them. GPU/Mali
internal MMU and CSF remain separate work.

## Actual results

`research/mt6897-backends/check-v2/result.json`: **PASS**, exit 0.

| Test group | Native ASan/UBSan | Same models executing on ARM64 |
| --- | ---: | ---: |
| PMIF | 105 | 105 |
| PMIC over the PMIF command model | 193 | 193 |
| Firmware policy/provider failures | 39 | 39 |
| IOMMU register programming/errors | 87 | 87 |

The same 424 model checks passed on both hosts. An additional **12 checks of
two actual SMC calls across EL1/EL3** passed in QEMU and printed
MT6897 ARM64 MODEL PASS. The five
standalone production objects (including the SMC assembler) compiled for
freestanding ARM64 with no undefined imports. The secure fixture uses strict
alignment and a byte-wise runtime with MMU/cache off; it emulates no MediaTek
PMIC or IOMMU peripheral. QEMU reports version 10.2.1
(Debian 1:10.2.1+ds-1ubuntu3.3), saved in
research/mt6897-backends/qemu-version.log; the saved commands identify the
machine options.

The final secure ELF SHA-256 is
`8dba37ef2d3ca4c44c559623fe86be0346b6e79b048e36ffca28fea763fd607d`.
Seven source Git blobs matched, the saved DTB matched, and all test/production
source hashes were unchanged during the run. Check-v1 was an earlier passing
case set, retained separately; check-v2 adds protected-register enforcement
and every fallible PMIF-write/PMIC-transaction point. Neither is a phone test.

Replay in a fresh directory:

```sh
python3 tools/test-mt6897-backends.py research/backend-check-new \
  --fdt ../phone-fdt.bin --sources research/mt6897-backends/sources
```

The optional inputs are existing saved files only. The script does not
discover a device, use ADB/fastboot, write partitions, mount a real disk or
install firmware. Existing output directories are refused.

Next physical work remains a matched installed-firmware contract and effect
verification, trusted XNU MMIO/cache/locking adapters, PMIF error handling and
resource/vote ownership. A full IOMMU driver additionally needs the matching
table builder and actual client routing; the UFS route is still unresolved.
