# Duchamp DMA/IOMMU read-only probe

This diagnostic module exposes the already-bound UFS device's public Linux
DMA and IOMMU state through one read-only sysfs attribute. It is intentionally
narrower than a storage driver.

It reports through
`/sys/devices/platform/soc/112b0000.ufshci/sweet_dma_iommu_contract`:

- the exact streaming and coherent DMA masks and their bit widths;
- the bus DMA limit, inherited DMA-range presence and coherency flag;
- whether `get_dma_ops()` and the device's own `dma_ops` field are populated;
- whether a SWIOTLB pool is attached to the UFS device;
- whether an IOMMU private object, group, firmware spec or domain exists;
- the firmware-spec ID count and first/last IDs;
- the numeric IOMMU domain type and whether it is a DMA domain.

The sysfs attribute is created with mode `0444` and removed when the module is
unloaded. The module does **not** allocate or map DMA memory, issue storage commands,
read or write MMIO, execute SMC calls, attach an IOMMU domain, change clocks or
power, or write to the phone's filesystems or partitions. It does not expose
kernel pointers.

The source is pinned to the captured Duchamp kernel release
`6.1.57-android14-11-gcf2c2dc91b9e-ab11782407` and the matching GKI commit
`cf2c2dc91b9e9f016dc25cf095b1fe34cb5dfcb6`. A build is not evidence that the
module can be loaded: the resulting `vermagic`, symbol CRCs, CFI metadata and
module policy must all be checked against the captured vendor modules first.

Loading any module changes the running kernel. Do not copy or load the output
on a phone without a separate explicit approval and a documented unload and
recovery procedure. Local build and static verification do not require phone
access.

## Phone tests and corrected build

The first 2026-11-01 candidate is unsafe. A separately approved phone test
caused a kernel panic in `mod_sysfs_setup()` before the module's init function
ran. Live BTF and the six captured vendor modules proved that the phone uses a
1088-byte (`0x440`) `struct module`, while that candidate used 1024 bytes
(`0x400`). Its manually supplied `module_layout` CRC concealed the mismatch.
The artifact is retained only as
`duchamp_dma_iommu_probe.ko.UNSAFE-DO-NOT-LOAD` for regression testing.

The mismatch was caused by preparing the tree without the captured Pahole 1.23
tool. Kconfig silently removed `CONFIG_DEBUG_INFO_BTF_MODULES=y`, which removed
two fields and shifted the later `struct module` members. The verifier now
fails closed on both the complete section size and the init/exit relocation
offsets observed in every pinned vendor module.

A corrected candidate is retained under
`work/duchamp-dma-iommu-probe-v2-local-only/`. It uses Android Clang 17.0.2,
Pahole 1.23 and the captured configuration. It has:

- `struct module` size `0x440`;
- init relocation offset `0x170`;
- exit relocation offset `0x3d8`;
- the exact captured `vermagic` and eight symbol CRCs;
- SHA-256 `96cd9bf422f8924c1c11b33c92d042ec0ea7fb864e756712fe45e5261be27518`.

After a fresh explicit approval, this exact v2 file loaded successfully on the
captured target kernel. Two reports were byte-identical, the module unloaded,
the staged file and sysfs attribute were removed, and kernel taint stayed
`12805`. The measured values were:

- streaming and coherent masks: both `0xffffffffffffffff` (64 bits);
- `bus_dma_limit`: `0x0000000fffffffff` (36 bits);
- `get_dma_ops()` and `dev->dma_ops`: null;
- IOMMU private object, group, fwspec and domain: absent;
- device SWIOTLB pool pointer: present;
- non-coherent DMA with a DMA range map present.

Pinned GKI source maps null DMA ops to the generic `dma-direct` path. These
observations do not prove a physical firewall bypass, identity DMA addresses,
actual SWIOTLB use, successful UFS DMA or XNU cache correctness. See
`PHONE-TEST-2026-11-01.md` and
`research/mt6897-dma-ownership/live-probe-20261101-v1/result.json`.
