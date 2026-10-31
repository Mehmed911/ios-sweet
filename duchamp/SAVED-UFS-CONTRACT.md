# Saved MT6897 UFS client and DMA contract audit — 2026-10-31

The saved boot images now supply a closer kernel/source profile and actual
vendor UFS client instructions. The firmware **request ABI** is corroborated
for MTCMOS and REFCLK, and isolated DMA-mask paths agree with the pinned source
in the tested cases. The installed secure-monitor **effect/return contract**
and the physical UFS DMA route remain unverified. No physical provider was
enabled and no phone, USB, ADB, fastboot or partition action was performed.

## Captured evidence and source correlation

The offline auditor verifies these saved input hashes before decompression:

| Saved file | SHA-256 |
| --- | --- |
| boot_a.img | `1b972f4f1c98428f2fca1e7c1c8cf463e0122a70a290e482be3230c7838e3e12` |
| vendor_boot_a.img | `d1d1887eba4f7b4920fc4292de5cf4e9aa6e7ce474a6b45ffeb4141434743e49` |
| Live-FDT capture | `9c49589f70044127be8941a9ea5537977f440ccd5ac15cfd24e120c8a1181d29` |

The boot-v4 kernel has release
`6.1.57-android14-11-gcf2c2dc91b9e-ab11782407`. That stamp resolves to
[`cf2c2dc91b9e9f016dc25cf095b1fe34cb5dfcb6`](https://github.com/aosp-mirror/kernel_common/commit/cf2c2dc91b9e9f016dc25cf095b1fe34cb5dfcb6).
The decompressed Image SHA-256 is
`39baa1bd10c50eaf9d91d8e2d94e6345d220a9703deec7c03dece82d9b44cdfe`;
its embedded IKCONFIG SHA-256 is
`01dc3fbdb5e4967f4d30bb62d41977ec3eb5d740e1abbe268254ac89a8a6522a`.
This is a release-stamp correlation, not a reproducible-build match or a
statement about what is running on the phone now.

The vendor-boot-v4 ramdisk contains two newc archives. The auditor extracts
only six explicitly named regular module files, ignores arbitrary archive
paths and records selected entries from modules.load. The load recipe includes
the UFS, PHY and IOMMU modules inspected here; it is not a runtime load log.
The UFS module SHA-256 is
`7043e1109b4c356a914fdc92ffbe463c0c43cb27342f6ccce1517a2086b02493`.
The module vermagic contains `6.1.57-android14-11-maybe-dirty`, and no srcversion
is present. Full vendor source/binary equivalence is therefore not established.

All 13 reference files are checked against exact Git blob IDs in
[mt6897-contract-sources.json](drivers/mt6897-contract-sources.json).
The vendor reference remains
[`a805f95`](https://github.com/mt6897-devs/android_kernel_device_modules_6.1/tree/a805f95d61dbf0b2959c9262acc626893114321d).
Its [build recipe](https://github.com/mt6897-devs/android_kernel_device_modules_6.1/blob/a805f95d61dbf0b2959c9262acc626893114321d/drivers/ufs/vendor/Makefile)
does not by itself reproduce the saved module. That module also contains UFS
core functions, including ufshcd_init; the binary instruction checks below
provide evidence about those specific paths without assuming a full match.

## DMA conclusions

The embedded configuration establishes IOMMU_DMA=y, default DMA strict=y,
default passthrough=n, SWIOTLB=y, XEN=n, 4-KiB Linux pages and 48-bit CPU PAs.
The standard ARM_SMMU and ARM_SMMU_V3 drivers are disabled in this configuration.
None of these facts assigns UFS to a particular IOMMU. MediaTek's external
modules and secure-world routing remain separate considerations.

The captured UFS node and its inspected ancestry lack iommus/iommu-map. Its
/soc ancestor declares a 64-GiB identity DMA window. The closer source profile's
[OF IOMMU path](https://github.com/aosp-mirror/kernel_common/blob/cf2c2dc91b9e9f016dc25cf095b1fe34cb5dfcb6/drivers/iommu/of_iommu.c)
can still use an existing fwspec. Furthermore,
[arch_setup_dma_ops](https://github.com/aosp-mirror/kernel_common/blob/cf2c2dc91b9e9f016dc25cf095b1fe34cb5dfcb6/arch/arm64/mm/dma-mapping.c)
does not clear an inherited dma_ops pointer when its IOMMU argument is NULL.
Both the source inspection and the local fixture preserve that distinction.

The saved ufshcd_init instructions attempt a 64-bit streaming mask when the
effective capability's CAP64 bit is set, falling back to 32 bits if that
streaming-mask attempt fails or CAP64 is absent. The coherent setter's return
is ignored on both paths. This matches the tested
[source helper](https://github.com/aosp-mirror/kernel_common/blob/cf2c2dc91b9e9f016dc25cf095b1fe34cb5dfcb6/drivers/ufs/core/ufshcd.c)
and
[dma_set_mask_and_coherent](https://github.com/aosp-mirror/kernel_common/blob/cf2c2dc91b9e9f016dc25cf095b1fe34cb5dfcb6/include/linux/dma-mapping.h).
An accepted streaming mask must not be treated as proof of the coherent mask.
The live HCCAP, effective post-quirk capability and resulting masks are absent
from this saved evidence.

The candidate is direct DMA, conditional on no inherited or overridden DMA
ops/fwspec and on the required ownership contract. The follow-up
[boot-policy audit](UFS-BOUNDS-POLICY.md) finds `swiotlb=noforce` in the saved
FDT. With the matching source this skips default SWIOTLB initialization;
the default bounce pool must not be assumed available. Vendor/per-device
overrides and runtime state remain unverified.
The source's
[direct-mapping path](https://github.com/aosp-mirror/kernel_common/blob/cf2c2dc91b9e9f016dc25cf095b1fe34cb5dfcb6/kernel/dma/direct.h)
can bounce an unreachable address when SWIOTLB is active, or fail when it is
not. The returned device address must therefore be used; a CPU PA cast is
insufficient. The fixture tests identity and translated bus windows, limits,
32-bit high-memory rejection/bouncing, forced bouncing and cache-sync branches.

No MD_VERIFIED_BUS_WINDOW or MD_VERIFIED_IOMMU decision is generated. In
particular, the display/MDP ARM_V7S table profile's 35-bit OAS is not the UFS
controller's addressing limit and supplies no UFS stream/domain assignment.

## Firmware request ABI and remaining gap

The pinned
[SiP header](https://github.com/mt6897-devs/android_kernel_device_modules_6.1/blob/a805f95d61dbf0b2959c9262acc626893114321d/drivers/ufs/ufs-mediatek-sip.h)
agrees with four call-site fragments from the saved module:

| Request | Observed inputs |
| --- | --- |
| MTCMOS op 0 / op 1 | x0=0xc2000276, x1=512, x2=0/1; x3–x7 zero |
| REFCLK PRE / POST, off/on | x0=0xc2000276, x1=8, x2=0/1, x3=0/1; x4–x7 zero |

The ELF call relocations target __arm_smccc_smc. Original offsets are relative
to the module's .text section, not callable runtime addresses. The audit stores
offsets and fragment hashes locally, without committing module bytes.

Saved LK/preloader hashes also match their existing evidence record. LK has
BL31 loader/reservation diagnostics, and the preloader has a BL31 reservation
marker. Those strings identify loader behavior; they do not identify a matched
monitor implementation, its build options, service completion semantics or
secure ownership. A zero reply remains insufficient. Additional SiP selectors,
crypto services and full firmware behavior are outside the tested subset.

## Actual local test results

`research/mt6897-contract/check-v4/result.json`: PASS, exit 0.

| Test group | Result |
| --- | ---: |
| 15 unchanged source function bodies, native ASan/UBSan | 216 checks |
| Same source cases on ARM64/QEMU | 216 checks |
| Saved DMA instruction paths versus source oracle | 244 checks |
| Saved SMC call-site instructions and unverified-reply policy | 96 checks |

The ARM64 fixture performs 12 actual SMC instructions across EL1/EL3. Six
exercise the client register/stack/result ABI; six confirm that zero replies
without a verified firmware contract are refused, preserve caller output and
latch the service closed. The monitor is purpose-built test code, not BL31
from the phone, and implements no MediaTek power or storage operation.

The fixture executes isolated saved instructions with synthetic frames and
private contexts. SMC external calls are redirected to the fixture's SMCCC
bridge. DMA external calls and exit branches are relocated to source-backed
test callbacks and controlled returns; original resource allocation, MMIO,
driver registration and cleanup are not executed. The raw vendor module and
phone boot/firmware images are never loaded for execution.

Kernel configuration, DMA support checks, IOMMU setup/hooks, SWIOTLB and cache
callbacks have explicitly modeled dependencies. The results do not demonstrate
physical DMA, hardware cache coherency or an installed monitor's effects.
All test/source/module hashes remained unchanged during the run. The final
fixture ELF SHA-256 is
`7663c6219f988f3af04fbcf0d70df81cbc6385a6e93c0c170e6aa04d7146d1ea`.

`guards-v2.log`: eight guard tests passed: wrong artifact provenance,
truncated ELF/CPIO, ELF section bounds, wrong relocation target, unsupported
archive format, modified reference source and preservation of existing output.
All earlier audit/check iterations are retained. Audit-v3 includes the final
load-recipe evidence and precise mask-policy wording; check-v4 also makes all
ASan/UBSan findings fatal. No new XNU kernel was built or booted in this
milestone; the previous XNU 24/20 results remain documented separately.

Replay under Linux/WSL with clang, LLVM tools, lz4 and QEMU AArch64 installed:

```sh
python3 tools/fetch-duchamp-contract-sources.py research/saved-ufs-sources-new
python3 tools/audit-duchamp-saved-ufs.py research/saved-ufs-audit-new \
  --boot ../phone-boot/boot_a.img --vendor-boot ../phone-boot/vendor_boot_a.img \
  --fdt ../phone-fdt.bin --firmware-dir ../phone-firmware \
  --sources research/saved-ufs-sources-new
python3 tools/test-duchamp-saved-ufs-audit.py --audit research/saved-ufs-audit-new \
  --sources research/saved-ufs-sources-new
python3 tools/test-duchamp-saved-contract.py research/saved-ufs-check-new \
  --audit research/saved-ufs-audit-new --sources research/saved-ufs-sources-new
```

The fetcher accesses pinned public source files only. The auditor and tests
operate offline on local files. Existing audit/test output directories are
refused. Captured images stay outside the repository. Extracted modules,
fragments and private logs remain under the Git-ignored research directory.

To establish a physical contract later, evidence must resolve the installed
monitor/build configuration and per-service effects, secure resource/PHY
ownership, live DMA ops/fwspec/domain/SWIOTLB state, HCCAP and both effective
masks. None can be inferred from passing this QEMU fixture, and no device
capture is attempted as part of this milestone.
