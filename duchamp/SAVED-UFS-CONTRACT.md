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
The version-2 live report records the missing runtime contract explicitly. The
saved `dma_mask_bits` and `coherent_dma_mask_bits` probes both exited with the
path unavailable. The captured sysfs capability directory contains only
`clock_scaling` and `write_booster`, and its captured debugfs listing is empty.
Consequently that sysfs/debugfs-only report records HCCAP as
`not-exposed-in-capture`; at that capture stage, the effective post-quirk
capability and both resulting masks remained unknown rather than inferred.

The later allowlisted read-only capture recursively inventories 1200 bounded
lines below the live UFS sysfs device and still finds no HCCAP- or
DMA-mask-named entry. However, the loaded `ufs_mediatek_dbg` module exposes a
read-only `/proc/ufs_debug` summary. A 20-line-bounded read reports effective
host capabilities `0x55c7051f`, host/device UFSHCI version `0x400`, and MCQ
  supported and enabled. The pinned UFSHCI definitions decode bit `0x01000000`
  as 64-bit-addressing support and bit `0x40000000` as MCQ support. This closes
  the HCCAP gap in that capture, but does not by itself reveal which streaming
  or coherent DMA mask was accepted by the DMA layer. The Android SCSI host reports `can_queue=63`,
`nr_hw_queues=8`, `sg_tablesize=128`, and `cmd_per_lun=31`. Those values prove
that the installed Android driver uses a multiqueue host, but they do not
encode the accepted streaming/coherent masks, `dma_ops`, an IOMMU fwspec/domain,
or cache ownership. The bounded kernel-log capture contains only SELinux
denials from the attempted read-only link traversal and adds no UFS fault or
DMA-contract evidence. The machine-readable capture is
  `research/mt6897-shell-runtime/live-20261101-v7/result.json`.

A later, separately approved read-only kernel probe closes the live Linux-state
gap: both masks are `0xffffffffffffffff` (64 bits), `bus_dma_limit` is
`0x0000000fffffffff` (36 bits), both DMA-ops pointers are null, and no Linux
IOMMU private object, group, fwspec or domain is attached at observation. The
pinned DMA mapping source therefore selects generic `dma-direct`. The device is
non-coherent, has a DMA range map and has a SWIOTLB pool pointer. The evidence
and fail-closed aggregate are under
`research/mt6897-dma-ownership/live-probe-20261101-v1/` and
`research/mt6897-dma-ownership/live-20261101-v2/`.

Linux selected generic direct DMA at the probe observation. That does not
establish a physical identity address or bypass secure firmware/firewalls, and
the required ownership contract remains open. The follow-up
[boot-policy audit](UFS-BOUNDS-POLICY.md) finds `swiotlb=noforce` in the saved
FDT. With the matching source this skips default SWIOTLB initialization;
the default bounce pool must not be assumed available from boot policy alone.
The later probe proves that a device SWIOTLB pool pointer exists despite the
saved `noforce` policy, but it does not prove that any transfer used it.
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

A later allowlisted, read-only ADB refresh captured only the first 256 KiB of
`/proc/atf_log/atf_log`, bounded to two seconds. It identifies the running
monitor as `BL31: lts-v2.8.6(release):2fbca47`, built at `07:19:18, Dec 18
2024`, with software marker `common_2.6.1(6897-1.2)`. This closes the release
string gap, not the source or effect-contract gap. The public upstream
[lts-v2.8.6 release](https://github.com/ARM-software/arm-trusted-firmware/releases/tag/lts-v2.8.6)
is commit `ff0bd5f`, while `2fbca47` is absent from the checked upstream and
public MediaTek mirror. No physical SMC was issued, and no return/effect
semantics, secure ownership, or UFS permission follows from the version text.

A separate explicitly read-only capture of active `tee_a` produced a 5 MiB
local file with SHA-256
`37d7d5acbe02289465af9702cbcafb1986394332a3462badda398556d32e587d`.
Its first package entry is named `atf`: the header declares 953,976 payload
bytes at offset `0x200`, ending at `0xe9078`; eight zero padding bytes are
followed by the next valid `cert1` header at `0xe9080`. The extracted payload
SHA-256 is
`716222a632e4a0623a2e467e17f1d36f38a37f79a1c026447fe724e75e90e07e`.
It contains the same runtime release, build and software identity strings at
unique offsets. This ties the captured active-slot binary identity to the
bounded runtime log; it is still not a reproducible source match.

Static inspection of that exact payload finds a service descriptor named
`MTK_SIP_KERNEL_UFS_CONTROL`, with fast 64-bit function ID `0xc2000276` and
handler address `0x48845008`. Pinned dispatcher and handler instructions route
the saved client selectors as follows:

| Selector | Captured handler path |
| --- | --- |
| REFCLK `8` | jump-table target `0x48845170`, with PRE/POST stage checks |
| MTCMOS `512` | target `0x488451ec`; on/off helper-call bodies are present |
| MCQ `1024` | target `0x48845098`; state load and result-store path is present |

Known selector paths converge on a common exit that sets `x0` to zero. This is
direct binary evidence that a zero reply alone cannot distinguish a completed
physical transition from an internally logged failure. The existing firmware
backend's independent `verify_reply` requirement therefore remains necessary.
The two MTCMOS helper bodies also expose their exact firmware-side MMIO path:
they write unlock value `0x0b160001` to `0x1c001000`, operate on control
registers `0x1c001e10` and `0x1c001e14`, and poll bits 30 and 31. This identifies
possible postcondition bits but also confirms that BL31 itself owns the path in
the captured build. XNU direct readback remains prohibited until a documented
handoff or non-invasive firmware query establishes ownership.
The static audit executed no firmware, SMC or MMIO and does not prove runtime
effects, secure ownership, or XNU UFS readiness. Machine-readable reports are
`research/mt6897-firmware-live/20261101-v1/inspection.json` and
`research/mt6897-firmware-live/20261101-v1/ufs-sip-audit-v2.json`.

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

To establish a physical contract later, evidence must still resolve the
installed monitor/build configuration and per-service effects, secure
resource/PHY/firewall ownership, actual bounce requirements, and non-coherent
cache maintenance. The separate read-only probe now resolves both effective
masks and the live Linux DMA-ops/IOMMU/SWIOTLB-pointer state. None of the
remaining physical effects can be inferred from passing this QEMU fixture.
