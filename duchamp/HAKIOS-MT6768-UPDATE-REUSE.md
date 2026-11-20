# HakiOS MediaTek update: bounded reuse for Duchamp

Reviewed on 2026-10-31 against these immutable upstream revisions:

- `oosexgang/hakios-xnu-kernel` at
  `a3384e031eb1e605cf37adaefc19991f04f6274b`.
- `oosexgang/hakios-mt6768` at
  `b60346c8ae50b539c51a1156899cc86f161bba5c`.

The updated MT6768 repository documents an Infinix Hot 20 port using a
bare-metal loader, an XNU device tree and boot arguments, read-only eMMC/MSDC,
MT6358 PMIC support and Mali-G52. It is useful evidence that a MediaTek-specific
handoff and return path can work, but it is not hardware compatibility evidence
for POCO X6 Pro (`duchamp`): Duchamp uses MT6897, UFS, different power/clock
domains, different IOMMU topology and a different Mali generation.

## Reused now

Only the generic loader-return contract was adapted:

- an aligned `XNULDRST` slot embedded in XNU;
- a loader-side scan restricted to already validated copied segments;
- physical return-stub and physical-minus-virtual fields;
- an early exception return carrying ESR, ELR and FAR;
- bounded head/tail log retention and a RAM diagnostic record.

The Duchamp implementation is deliberately smaller than HakiOS's full return
path. It does not preserve UEFI, write storage, stop device drivers or assume a
specific SoC. The channel is intended first for QEMU and later for a separately
approved RAM-only diagnostic after the normal restore path is revalidated.

## Explicitly not reused

- MT6768 register addresses and clock/power sequences.
- MSDC/eMMC code or its root-device assumptions.
- MT6358 PMIC programming.
- Mali-G52 bring-up and firmware assumptions.
- touch, SCP, CONNSYS and board firmware.
- any flash, GPT carving, `boot_a` writing or system-image script.

These parts remain separate MT6897 work and must be derived from Duchamp's
captured DTB, matching kernel sources and measured firmware behavior.

## Local verification

- return-slot unit test: unique match, missing match, duplicate match,
  alignment failure and range failure.
- bounded-log unit test: full copy, head/tail copy and invalid-source rejection.
- freestanding ARM64 bootshim build with the return stub linked.
- QEMU visual return-channel test.
- QEMU materialization of an older payload without `XNULDRST`, which must show
  the slot-missing failure and refuse handoff.
- XNU patch application checked against the preserved patched build tree.

No phone, UFS device, boot partition or Android installation is touched by
these tests.

## Full build and slot-ready result

The integration was built by GitHub Actions run `41207662670` from commit
`53fd59bce25bad9d8c29076a6c920a2a24c86826`. The XNU Build, collection and
`xnu-kernel` artifact upload steps succeeded. The run's aggregate status is
failure only because the separate, large `xnu-buildtree` artifact upload
failed after the kernel had already built; this does not invalidate the kernel
artifact.

- downloaded artifact ZIP SHA-256:
  `4c4643bba51a3c30ccc25904febbeb3c66c1c338f6423c7ab4708afa494fec89`;
- `kernel.development.sweet` SHA-256:
  `7d5245301ffdd137ea4e959168d54ba9582188ff0e11b3d57566b4b3770b227c`;
- the final kernel contains exactly one `XNULDRST`, exported as
  `_duchamp_loader_return_slot` at `0xfffffe00074817d8`;
- new payload SHA-256:
  `804e75819c43b45b4b9b4c6e1a0afd92b8bfe6c3fcb4a4bc7b5a72100c61d831`;
- no-jump bootshim Image SHA-256:
  `208b0d516d0e66dfa6afd275fd20c0faf7927ad971693746fb776cdd2cd323bd`.

The final 8 GiB QEMU test used the captured Duchamp FDT, `MATERIALIZE=1`,
`RETURN=1` and `READY=1`, with no `JUMP`. It passed both the framebuffer
`slot-ready` pattern and a direct physical-memory check:

- slot PA `0x1c14817d8`;
- patched return-stub PA `0x402017f4`;
- checkpoint `0`;
- physical-minus-virtual `0x201ba000000`.

This proves the bounded loader-return handoff in QEMU. It does not prove a
physical MT6897 boot and does not authorize a phone trial.

## QEMU-only JUMP and early-return result

The first JUMP build attempt, Actions run `41213039556`, was rejected rather
than tested: the `0210` patch had an invalid hunk count, so `git apply` skipped
it and the collected kernel was byte-for-byte identical to the preceding
kernel. The hunk was corrected in commit
`a913f62d64da212b6f2999f17bd052c364477e4c` and checked against the exact
preserved CI source tree before rebuilding.

GitHub Actions run `41215450424` then completed successfully, including the
XNU Build step itself. The resulting artifacts and local images are:

- downloaded `xnu-kernel` artifact ZIP SHA-256:
  `ec6b92631c3ce4cdbb3b18a9911a8469435228b0190146d669e4451d795b59e2`;
- `kernel.development.sweet` SHA-256:
  `e7902b4c4c85079810b701aba4058b87411470916ff5d1862d1c38cd5602e7a0`;
- payload SHA-256:
  `1c113f818327a9d287601a738e3be04fcaa2dd808a60fcc9ad657759de0dee3d`;
- QEMU-only JUMP bootshim Image SHA-256:
  `932d016c3f77588b38586c8650c4a7b42fed4b5d2e5afd0a183ab14220d7250b`.

The final kernel differs from the no-JUMP kernel, contains exactly one
`XNULDRST`, and disassembly of `_start_first_cpu` shows `brk #0xd0` at
`0xfffffe0007482174`, after installing `VBAR_EL1` and before enabling the MMU.
The trigger requires both a non-zero loader return stub and the exact
QEMU-only checkpoint `0x4455434851454d55`; checkpoint zero follows the normal
path.

The 8 GiB QEMU test used the captured Duchamp FDT and verified physical memory
through QMP in addition to the framebuffer result. It passed with:

- return-slot PA `0x1c14817d8`;
- bootshim return-stub PA `0x402017f4`;
- return-record PA `0x40215190`;
- reason `1`;
- `ESR_EL1 = 0xf20000d0` (the intentional `BRK #0xd0`);
- `ELR_EL1 = 0x1c1482174`;
- `FAR_EL1 = 0`;
- physical-minus-virtual `0x201ba000000`.

This proves that XNU entered its early exception vector and transferred
control back to the bootshim in QEMU. It remains a deliberately bounded
QEMU-only diagnostic: no phone command, flash operation, UFS access or boot
partition change was performed.

## Normal-JUMP regression

The same kernel and payload were also built with `JUMP=1`, `RETURN=1` and a
normal checkpoint value of zero. The QEMU test requires both an XNU stage-0
framebuffer marker and an entirely zero 104-byte return record. It passed:

- normal-JUMP bootshim Image SHA-256:
  `79c064889f4153705fc8d69bed59dd18ef4e367ae435d66f9c1f798cb8e8ff1a`;
- return-slot PA `0x1c14817d8`, stub PA `0x402017f4` and checkpoint `0`;
- return-record PA `0x40215180` remained all zero;
- XNU stage-0 marker contained `360916` white pixels after ten seconds.

The intentional-return image was then rerun with the same test harness and
again returned reason `1`, `ESR_EL1 = 0xf20000d0` and
`ELR_EL1 = 0x1c1482174`. Together these are an A/B regression: checkpoint zero
enters XNU without returning, while only the exact QEMU checkpoint triggers
the bounded early return. Both runs used QEMU and the captured FDT only; the
phone remained untouched.

`duchamp/bootshim/test_jump_pair.py` now derives the return-slot PA and
physical-minus-virtual delta from the payload, derives the stub and record
addresses from each bootshim ELF, and runs both sides of this regression with
one command. This removes the manual address calculations from future builds.
