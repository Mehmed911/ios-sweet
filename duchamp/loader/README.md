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
