# Storage and software graphics cores — 2026-10-31

This milestone implements and tests portable C cores. Its original tests
below predate XNU integration. The subsequent virtual-UFS BSD adapter and
separate MT6897 leaf-clock work are tracked in [QEMU-UFS-XNU.md](QEMU-UFS-XNU.md).
There is no MT6897 physical MMIO backend; its root-device selection still
returns `kIOReturnUnsupported`. No phone, USB, UFS hardware or boot partition
was accessed during either milestone.

## What now runs

| Component | Implemented behavior | Actual test |
| --- | --- | --- |
| `drivers/ufs_readonly.c` | Single-owner legacy UFSHCI polling, NOP, bounded fDeviceInit, READ CAPACITY(16), READ(16), wire encoding, DMA-range/alignment checks, bounded reset UNIT ATTENTION retry and poisoned-host failure handling | Actual QEMU UFS controller/DMA, generated read-only disk at low and above-4GB DMA addresses, then the existing HFS+ root image through the same transport |
| `drivers/framebuffer.c` | Validated 32-bit surfaces, rectangle fill and copy, explicit raw little-endian pixels, bounds/alias rejection, preserved row padding | Full 1220x2712 surface, stride 4992, every pixel/padding/guard byte verified on host and after ARM64 execution in QEMU |
| `tools/inspect-duchamp-hardware.py` | Bounded saved-DTB parsing, bus-address translation and phandle resolution for clocks/resets/PHY/IRQs/supplies | Captured phone DTB plus malformed/synthetic-tree tests; selected hardware data only, no bootargs or serial output |

The UFS test drives QEMU through qtest with the guest CPU stopped; it does not
boot XNU. There are no fabricated successful storage replies. Its separate
fault cases deliberately corrupt a returned task-tag copy or mask completion
to exercise rejection and timeout. The ARM graphics test executes the actual
C raster core at EL1 with MMU/caches off. Its framebuffer is ordinary guest
RAM at the measured address, not an emulated display, Mali or DSI device.

## Verified results

- `research/mt6897-drivers/core-v6/result.json`: **108/108 checks**, exit 0.
  Three QEMU cases; five exact byte comparisons each, including first/middle/
  last blocks and a 256-KiB transfer. DMA bases `0x100000` and `0x100100000`.
  Both disk images remained byte-identical. QEMU reported UFSHCI `0x400`.
- Same run: **78 native guard checks** under ASan/UBSan, exit 0. Busy inherited
  controller, bad version, absent 64-bit DMA support, bounded startup timeout,
  failed DMA preparation and invalid framebuffer surfaces were exercised.
- Same run: both production C cores cross-compiled for freestanding AArch64
  with general registers only; `llvm-nm --undefined-only` found no imports.
  This is compilation evidence for UFS, not ARM execution of the UFS core.
- `research/mt6897-drivers/framebuffer-arm-v2/result.json`: **3/3 checks**,
  exit 0. The complete RAM capture matched the host raster result, SHA-256
  `2be9fd76292a0edafb0fc52d54f2d3bf029911cfb6674554659d9a55df3ec3ac`.
- `research/mt6897-drivers/fdt-tests.log`: **20 tests**, exit 0, including all
  truncations of the synthetic DTB, invalid phandles/cells/names and ambiguous
  or missing address translations.

The existing 32-MiB HFS+ image was read through virtual UFS with DMA above
4GB, then rehashed unchanged:
`491aa78408c423c50e8b59644e416e94b643ed3eb119158d52684af4176c8b3f`.
This proves transport of its bytes; it does not prove an XNU UFS mount.
Source/object/image hashes and packet summaries are saved in the reports.
QEMU version: 10.2.1 (Debian 1:10.2.1+ds-1ubuntu3.3).

Preserved failures: core-v1 assumed a 64-bit PCI register BAR; the installed
model has a 32-bit BAR, independently of its 64-bit DMA capability. core-v2
then exposed the real cold-device UNIT ATTENTION response. The core now
accepts only valid fixed-format UNIT ATTENTION for at most three attempts;
other or malformed errors fail. The first ARM fixture overlapped QEMU's DTB
reservation; its ELF was relocated to `0x40200000`. Failed outputs stay local.

## Measured MT6897 dependencies

The captured DTB SHA-256 is
`9c49589f70044127be8941a9ea5537977f440ccd5ac15cfd24e120c8a1181d29`.
Full selected-property report: `research/mt6897-drivers/hardware-v1.json`.

| Resource | Captured value |
| --- | --- |
| UFS | `/soc/ufshci@112b0000`, `mediatek,mt8183-ufshci`, span `0x3000` |
| UFS PHY | `/soc/ufsphy@112a0000`, `mediatek,mt8183-ufsphy`, span `0x10000` |
| UFS IRQ cells | Nine GICv3 tuples of four cells; main SPI number 168, additional SPI numbers 177–184 |
| UFS clocks | 12 named references: six topckgen mux/source references, four ufscfg_ao clocks, two ufscfg_pdn clocks |
| Clock providers | topckgen `0x10000000`; ufscfg_ao `0x112b8000`; ufscfg_pdn `0x112bb000` |
| Resets | `unipro_rst`, `crypto_rst`, `hci_rst`, IDs 0/1/2 at ufscfg_pdn/reset-controller |
| Supplies | dvfsrc-vcore, PMIC vemc and MT6319 8-vbuck3 providers resolved by phandle |
| GPU | `/soc/mali@13000000`, `mediatek,mali` + `arm,mali-valhall`, span `0x480000` |
| GPU IRQ names | JOB, MMU, GPU, EVENT, PWR; four-cell GICv3 tuples |
| GPU memory providers | Physical-memory-group-manager and protected-memory-allocator references are present |

The UFS/GPU nodes do not declare `iommus` or `dma-coherent`. This is **not**
proof that an IOMMU is bypassed or caches are coherent. Bus/physical/DMA
address ownership and cache maintenance remain platform work. IRQ cell
numbers above are DT SPI numbers, not already adjusted absolute GIC INTIDs.
All generic clock/reset IDs require the matching provider implementation;
the inspector does not turn these IDs into register writes.

## Primary source review

The [Duchamp kernel manifest](https://github.com/mt6897-devs/kernel_manifest/blob/lineage-23.2/local_manifest.xml)
separates the common kernel, MediaTek device modules and vendor modules.
Pinned references used here:

- [MediaTek UFS variant, a805f95](https://github.com/mt6897-devs/android_kernel_device_modules_6.1/blob/a805f95d61dbf0b2959c9262acc626893114321d/drivers/ufs/ufs-mediatek.c):
  the compatible name matches the captured node. Initialization binds PHY,
  resets, clocks and power; RTFF-MTCMOS and reference-clock firmware calls
  matter for this tree. This match alone does not establish firmware ABI
  compatibility with the captured phone.
- [UFS SiP definitions](https://github.com/mt6897-devs/android_kernel_device_modules_6.1/blob/a805f95d61dbf0b2959c9262acc626893114321d/drivers/ufs/ufs-mediatek-sip.h):
  UFS control has explicit power/reset/reference-clock/MPHY/MTCMOS operations.
  No SiP command from this reference was executed.
- [MT6897 GPU selection, 6bceb1b](https://github.com/mt6897-devs/android_vendor_mediatek_kernel_modules/blob/6bceb1b8e3444dd6caf80ad7470c9e57bbdcd1ab/gpu/mt6897/Makefile)
  includes Valhall r38p1 and Avalon r44p1 paths. The
  [r38p1 build rules](https://github.com/mt6897-devs/android_vendor_mediatek_kernel_modules/blob/6bceb1b8e3444dd6caf80ad7470c9e57bbdcd1ab/gpu/gpu_mali/mali_valhall/mali-r38p1/drivers/gpu/arm/midgard/Makefile)
  enable CSF for MT6897. The
  [r44p1 CSF firmware code](https://github.com/mt6897-devs/android_vendor_mediatek_kernel_modules/blob/6bceb1b8e3444dd6caf80ad7470c9e57bbdcd1ab/gpu/gpu_mali/mali_avalon/mali-r44p1/drivers/gpu/arm/midgard/csf/mali_kbase_csf_firmware.c)
  requests firmware (default `mali_csffw.bin`) and validates/maps MCU data.
  The installed phone's selected DDK/firmware pair is not identified by
  this source inspection. A pixel copy cannot replace CSF/MMU/queue/power
  initialization or the iOS graphics framework interface.
- [QEMU UFS tests, 7f36b1f](https://github.com/qemu/qemu/blob/7f36b1fbeb1f6f070cd5f8eddb3edbcafac15440/tests/qtest/ufs-test.c)
  and [emulation documentation](https://github.com/qemu/qemu/blob/7f36b1fbeb1f6f070cd5f8eddb3edbcafac15440/docs/system/devices/ufs.rst)
  informed the virtual-controller setup. The tested installed binary was
  not built from this newer reference commit. UniPro/M-PHY/power behavior
  is not hardware-accurate in that model.

Vendor/QEMU sources remain in ignored research storage. The new portable
cores are independent implementations, not a wholesale Linux driver import.
The existing [HakiOS graphics review](HAKIOS-METAL-REUSE.md) still applies:
Adreno PM4/MSM transport does not supply an MT6897 Mali backend.

## Replay without a phone

Requires Linux/WSL, Clang with ASan/UBSan and AArch64 target support, LLD,
Python 3, dtc and QEMU system x86/ARM. Choose fresh result directories:

```sh
python3 tools/test-duchamp-driver-core.py research/driver-check-new \
  --root-image work/launchd-final/root.hfs
python3 tools/test-duchamp-framebuffer-arm.py research/arm-fb-check-new
python3 tools/test-inspect-duchamp-hardware.py
python3 tools/inspect-duchamp-hardware.py ../phone-fdt.bin research/hardware-new.json
```

Output directories/reports refuse overwrite. The optional root image must be
a regular HFS+ file and QEMU opens it read-only. No downloaded Apple binaries,
captured DTB or test disk belongs in Git.

## Integration boundary and next work

`dufs_bind()` requires a zero-initialized fresh host and a trusted platform
backend asserting exclusive ownership. Its readiness flag is a caller
precondition, **not** firmware verification. Callbacks must provide bounded
MMIO access, a progressing monotonic clock, DMA mapping/cache synchronization
and ordering. The core rejects live inherited queues, has no arbitrary CDB
or SCSI WRITE entry point, and limits requests to one PRD / 256 KiB. It sets
fDeviceInit as a controller/device initialization flag; read-only here refers
to stored user data. It has no interrupt/MCQ/concurrent-I/O implementation.

On timeout or other non-retryable failure the host is poisoned and cannot
rebind/resubmit through the API. DMA buffers must remain reserved until a
real platform backend proves quiescence. No automatic abort/reset or buffer
reclamation is attempted. An emulator barrier callback is not cache handling
for MT6897.

The XNU-facing read/completion adapter now has a separate QEMU configuration;
its runtime results and md0 regression belong to [QEMU-UFS-XNU.md](QEMU-UFS-XNU.md),
not to the qtest results above. Physical work still requires the board-specific
PHY/clock/reset/SiP and DMA/cache sequence from the pinned vendor source and
matching firmware evidence. Keep the phone backend disabled until that
entry/ownership contract is established. Mali acceleration needs
its own firmware/MMU/CSF/fence and power backend before any GPU submission.
Neither the software raster core nor virtual HFS+ reads establish SpringBoard
readiness, touchscreen support or complete iOS on Duchamp.
