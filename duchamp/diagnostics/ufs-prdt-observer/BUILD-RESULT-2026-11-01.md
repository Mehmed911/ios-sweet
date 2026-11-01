# Duchamp UFS PRDT observer — offline build result

## Result

The passive observer builds and passes its complete offline ABI verification.
It has not been loaded on the phone. No ADB command, storage command, firmware
call, MMIO access, flash operation or partition modification occurred during
this build and verification stage.

Artifact:

- `work/duchamp-ufs-prdt-observer-local-only/artifact-v5/duchamp_ufs_prdt_observer.ko`
- 407,280 bytes
- SHA-256:
  `fb5b1a887bced8e4b0fbf498ebafc21d4856b4f57bbf2795f1d469bd8c9984c3`

Source:

- `duchamp_ufs_prdt_observer.c`
- 14,685 bytes
- SHA-256:
  `844b98642ca41f1882682cd639b654d8384601ff0b21e19e2ad2991a9a213142`

Verification receipt:

- `work/duchamp-ufs-prdt-observer-local-only/verification-v6/verification.json`
- verdict: `static-verification-passed`

## Reproduced ABI contract

- target: AArch64 `ET_REL`;
- GKI source commit: `cf2c2dc91b9e9f016dc25cf095b1fe34cb5dfcb6`;
- compiler: Android Clang 17.0.2 based on `r487747c`;
- vermagic:
  `6.1.57-android14-11-maybe-dirty SMP preempt mod_unload modversions aarch64`;
- complete imported symbol set: 18 symbols with captured CRCs, no extras;
- `struct module`: 1,088 bytes (`0x440`);
- init/exit relocation offsets: `0x170`, `0x3d8`;
- appended module signature: absent.

The selected `Module.symvers` SHA-256 is
`f4ad6508fbcbe50484bcbc72acb3512c193358f0fc4e0205e75b9ad73320fcb3`.
Every CRC was recovered from six hash-pinned modules belonging to the captured
Duchamp software image.

## Tests

- observer source contract: 11/11 passed;
- symbol-receipt preparation: 3/3 passed;
- static verifier: 3/3 passed;
- fail-closed live-runner and cleanup lifecycle: 11/11 passed;
- Python syntax compilation: passed;
- kernel build: passed without unresolved symbols;
- strict checkpatch: zero errors after review; its `0400` `DEVICE_ATTR`
  warning is intentional because the report must remain root-only.

The final source also serializes aggregate updates into a coherent snapshot,
requires the measured dma-direct/no-IOMMU/36-bit contract before registering
the hook and at report time, and calls `tracepoint_synchronize_unregister()`
before module memory can be released.

## Remaining live boundary

A live result still requires two separately authorized runtime actions:

1. a normal Android reboot to remove the previously orphaned tracefs instance;
2. temporary loading of this exact module, followed by the bounded fixed-read
   observation and verified unload/cleanup.

The runner refuses mismatched devices, kernels, source or artifact hashes and
never performs the reboot itself. Even a successful direct-DMA observation
will not authorize XNU UFS MMIO or prove firmware/firewall and cache ownership.
