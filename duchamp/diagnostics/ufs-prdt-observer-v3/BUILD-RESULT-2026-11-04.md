# Duchamp UFS PRDT observer v3 — local result

## Result

The v3 passive observer builds for the pinned Duchamp Android kernel and
passes complete offline ABI verification. No phone, ADB, module loader, UFS
command, DMA mapping, MMIO, firmware call, flash operation or partition was
accessed during this result.

Final local artifact:

- `work/duchamp-ufs-prdt-observer-v3-local-only/artifact-v3/duchamp_ufs_prdt_observer_v3.ko`
- size: `420904` bytes
- SHA-256:
  `49196936b7d6ca78f485b35fc3d7ba0407f3027ec9a70b6bae9658f1c1862f96`

Verification receipt:

- `work/duchamp-ufs-prdt-observer-v3-local-only/verification-v3/verification.json`
- verdict: `static-verification-passed`
- source SHA-256:
  `fb67941f6dd0b921c068fceebd90cff7ad9313f570ce41ee3a6224ed04c3c855`

## Checks completed

- source safety and contract tests: `10/10` passed;
- Python syntax compilation: passed;
- kernel module build with Android Clang 17.0.2: passed;
- AArch64 module ABI and all 18 imported symbol CRCs: passed;
- vermagic and `struct module` layout: passed;
- appended module signature: absent as expected;
- strict checkpatch: zero errors and zero checks; the one warning is the
  intentional root-only `0400` sysfs report;
- Git whitespace validation for the new source and tools: passed.

## What a later approved live result can prove

The v3 report can capture the exact single live `dma_range_map` entry, compare
the raw PRDT DMA address directly with the original scatterlist physical
address, verify both translation directions, and bound SWIOTLB use for the
observed workload. Any contract change rejects the observation.

This local result does not contain runtime values and does not prove firmware
or resource ownership, cache-maintenance correctness, or safe physical UFS
access from XNU. Loading the module on the phone remains a separate operation
that requires fresh explicit approval for this exact artifact hash.

That separate approved operation later passed. Its immutable result and scope
are documented in `PHONE-TEST-2026-11-04.md` and
`PHONE-RESULT-2026-11-04.json`; the local build result above remains unchanged.
