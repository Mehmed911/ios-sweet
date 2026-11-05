# Duchamp resident loader protocol core

This directory contains a transport-independent, one-shot staging state
machine for a future RAM-only Duchamp loader.  It has no USB, Fastboot, MMIO,
SMC, storage or partition code.

The state sequence is:

```text
EMPTY -> RECEIVING -> READY -> RUNNING -> RETURNED
                                      \-> FAILED
```

Transfers must be sequential and exactly fill the announced size.  A bounded
mutation receipt is recomputed before preparation.  Any malformed transfer,
changed payload, preparation failure, unexpected return or oversized result
latches failure.  Returned and failed instances reject every new operation
with `RELOAD_REQUIRED`; there is intentionally no reset API.

The caller must serialize transport access while `run()` is active.  The core
is deliberately single-threaded and does not treat its non-cryptographic
mutation receipt as authentication.  Staging and result buffers must be
disjoint, receive buffers may not alias staging memory, and every public
operation revalidates state counters and capacities before using them.

`resident_xnu.c` is the bridge to the existing
`guard -> plan -> materialize` path.  It requires explicit physical addresses
for the live FDT and staging buffer, automatically adds both to the occupied
range list, rejects overlap with loader-owned ranges, and never branches to
XNU.  The future transport must additionally supply every loader, stack, page
table and USB-buffer range in `occupied[]`.

Run the complete local suite with a new output directory:

```sh
sh duchamp/loader/test_resident.sh PHONE_FDT SWEETXNU_PAYLOAD OUTPUT
```

The suite runs native ASan/UBSan protocol tests, materializes a real payload
through the bridge, proves an in-window staging address is refused before any
write, links the complete core as a freestanding AArch64 object with no
undefined imports, and runs the protocol state machine as an actual AArch64
Image on QEMU virt.

This milestone does not provide a phone transport.  HakiOS's Qualcomm UEFI USB
backend is not reusable on MT6897.  A future MT6897 provider must be based on a
documented LK/firmware or MTU3 gadget contract and remain separate from this
core.

The first such provider is the inherited-RAM path documented in
`MT6897-LK-TRANSPORT.md`.  It consumes an immutable capsule that LK has already
loaded with a temporary boot image.  It deliberately does not claim or call a
resident LK USB ABI.
