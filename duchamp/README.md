# Duchamp device port

This directory is the device-specific port boundary for the POCO X6 Pro 5G
(`duchamp`, MediaTek MT6897). `board.toml` records values measured from the
live device tree and local read-only extraction.

The `loader/` API validates and materializes the XNU payload into a bounded
memory window and tests the MMU/cache/entry sequence through callbacks.
Those callback tests are a preflight boundary, not a MediaTek firmware
implementation. The separate local, currently untracked `bootshim/` tree
documents its diagnostic and explicit opt-in jump builds in its README.

The Qualcomm shim under `shim/` is intentionally outside this port and refuses
`duchamp` and `mt6897` targets. A MediaTek firmware backend requires its own
verified entry contract and device tests.

Current QEMU userland work is documented in [LAUNCHCTL-QEMU.md](LAUNCHCTL-QEMU.md),
[CFPREFS-QEMU.md](CFPREFS-QEMU.md) and [CFPREFS-BATCH-QEMU.md](CFPREFS-BATCH-QEMU.md).
The active results and next action are in the repository's NOTES.md.
These emulator results do not establish phone driver compatibility. The
MT6897 storage selection in `tools/apply-duchamp-bsd-checkpoints.py` still
returns `kIOReturnUnsupported`; its separate QEMU RAM path selects md0.
No MediaTek UFS access should be inferred from a successful RAM-root test.

The pinned HakiOS Metal source review and local host-test result are in
[HAKIOS-METAL-REUSE.md](HAKIOS-METAL-REUSE.md).

Portable UFS read transport, software framebuffer operations, captured-DTB
dependency resolution and their actual test results are documented in
[DRIVER-CORES.md](DRIVER-CORES.md). Its original core tests predate the separate
virtual-UFS XNU adapter; a physical MT6897 backend is still unfinished.

The opt-in XNU BSD adapter and the implemented MT6897 leaf-clock subset are
tracked in [QEMU-UFS-XNU.md](QEMU-UFS-XNU.md), with emulator and model evidence
kept separate from physical-device compatibility.

The source-pinned version-1 PHY policy, RTFF/reference-clock and reset
sequencing, DMA ownership API and their native/ARM64 model tests are in
[MT6897-PLATFORM.md](MT6897-PLATFORM.md). Firmware/PMIC/IOMMU providers are
still required before a physical backend can use these APIs.

The subsequent PMIF/PMIC command programmers, guarded raw SMC transport and
partial multimedia-IOMMU TTBR/TLB programmer are documented in
[MT6897-BACKENDS.md](MT6897-BACKENDS.md). Their local tests do not resolve
the installed firmware contract or establish a UFS-to-IOMMU route.
