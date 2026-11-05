# MT6897 LK/UEFI RAM provider gate

## Scope

`mt6897_ram_provider.c` is the common fail-closed gate between a future
Duchamp LK/UEFI RAM caller and the existing immutable capsule transport.  It
does not discover or call undocumented LK functions, perform storage I/O,
write a partition, touch MMIO, change exception level, or branch to XNU.

The provider accepts only a runtime contract that proves all of the following:

- the caller identifies itself as LK, UEFI, or an explicitly enabled QEMU
  rehearsal;
- the entry PC and incoming `x0` were observed at the current entry, rather
  than copied from static image metadata;
- execution is at EL1 with stage-1 translation, data cache and instruction
  cache disabled;
- the entry PC is inside the loader image (and equals the image base for the
  raw LK/Linux Image path);
- `x0` equals the declared physical FDT address, and the bytes at that address
  contain a bounded FDT header;
- loader image, FDT, immutable capsule, staging RAM and XNU output window have
  valid, non-overflowing ownership ranges and do not overlap;
- an embedded capsule is wholly contained in the loader image;
- the capsule fits the separately owned staging window.

The report includes the observed PC, `x0`, FDT address/size/receipt and all
ownership ranges.  It is checksummed.  Success permits the capsule transport
only.  `xnu_jump_allowed` is always zero; final architectural handoff remains a
separate reviewed gate.

## Current integration

The existing `LK_RAM_TRANSPORT=1 QEMU_ONLY=1` bootshim mode now constructs the
contract from its actual runtime `_head`, inherited `x0`, linked capsule and
fixed QEMU staging/XNU windows.  The capsule transport is not called unless the
provider gate succeeds.  The QEMU harness reads and verifies the full provider
report in guest RAM.

QEMU is a rehearsal provider, never phone evidence.  The build still rejects
`JUMP=1`, and the provider report must show `xnu_jump_allowed=0`.

Run the complete local proof with fresh paths:

```sh
sh duchamp/bootshim/test_lk_ram_bootshim.sh \
  ../phone-fdt.bin path/to/payload-phone.bin \
  ../phone-boot/boot_a.img work/mt6897-ram-provider-v1
```

The suite runs the native failure matrix first, then boots the freestanding
AArch64 image in QEMU and verifies both the provider report and the existing
capsule/materializer report.

## Verified local result

The 2026-11-06 run in `work/mt6897-ram-provider-v1` passed:

- native fail-closed matrix: 16 checks;
- AArch64 image: 50,395,536 bytes, no ELF relocations;
- runtime entry PC: `0x40200000`;
- inherited FDT `x0`: `0x48000000`;
- FDT receipt: `0x7b77c30777d766c5`;
- immutable SWEETXNU bytes: 50,269,904 in 768 bounded reads;
- XNU entry/boot-args plan: `0x1c1480488` / `0x1c456c000`;
- segment count: 11;
- exception record: clear;
- capsule transport: allowed;
- XNU jump: blocked.

The complete suite result was
`mt6897-lk-ram-bootshim-suite: PASS qemu-only no-phone`.  These addresses are
QEMU observations and must not be substituted for Duchamp runtime values.

## Phone gate

No current Duchamp firmware interface supplies a no-write caller for this
provider.  LK and UEFI kinds exist so that a documented future caller can use
the same checked contract; selecting either kind does not create such a
caller.  Phone execution remains blocked until a vendor-supported RAM entry
mechanism captures the runtime PC and `x0` and owns non-overlapping source,
staging and destination ranges.
