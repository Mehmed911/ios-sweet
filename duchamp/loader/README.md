# Duchamp loader guard

`guard.c` is a freestanding, allocation-free validation core for a future
MT6897 loader. It validates a SWEETXNU v1 payload and a version-17 FDT from the
same boot before producing entry, ADT, and boot-args addresses.

The caller must provide every range already occupied by the loader, source
payload, FDT, stack, and page tables. The guard rejects overlaps, fixed FDT
reservations, overlapping dynamic allocation ranges, unsupported cell layouts,
non-MT6897 trees, and malformed payloads.

Success only produces a plan. This module contains no copy loop, cache/MMU
transition, exception-level change, or branch to XNU.

`plan.c` consumes the validated placement and produces a dry-run execution
manifest: segment source offsets, physical destinations, copy/zero sizes, ADT
placement, framebuffer metadata, and the values needed for revision-2
`boot_args`. It also contains no memory-write or branch-to-XNU implementation.

`materialize.c` applies that plan only to a caller-provided bounded byte window.
It copies and zero-fills the validated segments, places the ADT, and writes XNU
revision-2 `boot_args`. It cannot address physical memory outside that window
and contains no cache/MMU transition or branch to XNU.

`mt6897_loader.c` is the small MT6897-facing wrapper used by local validation.
It records a bounded handoff manifest after materialization, including the
Duchamp framebuffer geometry. It is not a phone bootloader: it does not map
physical RAM, configure MediaTek DRAM, change exception levels, flush caches,
or branch to XNU. Those hardware-specific operations remain unimplemented.

The DTB passed to the guard must be the final live FDT from the same boot. The
board check accepts either the MT6897 compatible string or the exact root model
`MT6897`, because the captured Duchamp live FDT uses the latter form.
The raw DT table extracted from `vendor_boot` describes only a 1 GiB
`0x40000000` memory window on this device, while the live FDT describes the
additional high RAM range containing the current Duchamp payload window.
Passing the embedded DTB is therefore expected to fail rather than silently
creating an invalid handoff.

`mt6897_handoff.c` defines the guarded handoff order through callbacks. It is
deliberately not a register-level MediaTek implementation: the platform must
provide verified MMU, cache, translation, exception-level, and branch
operations. Missing callbacks, unaligned addresses, out-of-window entry, and
failed steps are rejected.

`mt6897_platform.c` contains only the verified profile captured from the live
Duchamp FDT: GICv3 bases, ARM timer frequency, and the current framebuffer
geometry. It is metadata for preflight and test harnesses, not a hardware
driver; it performs no MMIO and must not be used as evidence that phone boot is
supported.

## Transition contract

`mt6897_handoff.c` is the architecture-neutral MMU/cache transition layer. Its
callbacks must be supplied by a future, separately reviewed AArch64 backend in
this order:

1. Disable the current stage-1 MMU without changing exception level.
2. Clean the complete payload window from the data cache.
3. Install translation tables whose granule and attributes match the XNU build.
4. Invalidate the instruction cache and issue the required barriers.
5. Enter XNU with the validated entry and boot-args addresses.

The contract deliberately does not switch EL. An EL change requires a verified
firmware/PSCI or monitor protocol and cannot be inferred from the Android
kernel. The callbacks also cannot be implemented by reusing the existing
Qualcomm `shim/mmu.c`, whose framebuffer and GIC mappings are platform-specific.

## Reference comparison

The MT8167 `xnu_bootshim_benesse_a04br3` project is a useful design reference:
it records `CurrentEL`, parses the inherited FDT, excludes reservations and
loader memory, and requires a kernel-owned entry marker. Those ideas are
portable. Its Cortex-A35 vectors, 4 KiB translation setup, MT8167 timer/GIC,
UART, boot-image framing, and EL2-to-EL1 path are not portable to Duchamp. The
Duchamp implementation must keep the diagnostic gates while using the MT6897
live FDT and the vendor LK contract recovered from `lk_a`.

`mt6897_entry.c` implements the first fail-closed Duchamp entry gate. It accepts
only the observed EL1 contract, requires stage-1 translation plus data and
instruction caches to be off, and requires the inherited FDT pointer in `x0`
to be aligned and contained in a caller-supplied live-memory range. EL2 entry is
rejected until it is observed on Duchamp and a separately reviewed transition
is available.
