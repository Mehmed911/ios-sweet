# MT6897 UFS power policy and DMA ownership — 2026-10-31

This milestone implements a source-pinned **power-sequencing subset** and
streaming-DMA ownership API. Native and ARM64 model tests pass. The modules
have no physical callbacks, are not linked into XNU, and do not establish a
working PMIC, secure-firmware or hardware IOMMU backend. MT6897 root selection
remains unsupported. No phone, USB, UFS hardware or boot partition was used.

## What the source and captured DTB establish

Vendor sources are pinned to
[a805f95](https://github.com/mt6897-devs/android_kernel_device_modules_6.1/tree/a805f95d61dbf0b2959c9262acc626893114321d).
Six downloaded source files were checked against their exact upstream Git
blob IDs; the IDs are in `drivers/mt6897-platform-sources.json`. Source dumps
and the device DTB remain outside Git.

| Fact | Consequence implemented |
| --- | --- |
| Captured PHY `/soc/ufsphy@112a0000` has `mphy-ver=1`; [phy-mtk-ufs.c](https://github.com/mt6897-devs/android_kernel_device_modules_6.1/blob/a805f95d61dbf0b2959c9262acc626893114321d/drivers/phy/mediatek/phy-mtk-ufs.c) returns immediately in power_on/off for nonzero versions | Version 1 records delegated PHY policy. There are no legacy PHY register callbacks or old unipro/mp clock lookups. This is not evidence that the physical PHY is powered. Other versions are refused. |
| The captured UFS node has `mediatek,ufs-rtff-mtcmos` and lacks `mediatek,ufs-support-va09` | The selected profile requires RTFF and refuses VA09 support. It emits neither the optional VA09 regulator operations nor its 200-us delay. |
| [ufs-mediatek.c](https://github.com/mt6897-devs/android_kernel_device_modules_6.1/blob/a805f95d61dbf0b2959c9262acc626893114321d/drivers/ufs/ufs-mediatek.c) restores RTFF before power-on, then requests reference clock | The sequencer records PHY delegation, emits MTCMOS restore then on, and follows the reference-clock PRE/request/ACK/settle/POST sequence. |
| [SiP header](https://github.com/mt6897-devs/android_kernel_device_modules_6.1/blob/a805f95d61dbf0b2959c9262acc626893114321d/drivers/ufs/ufs-mediatek-sip.h) and [SMCCC convention](https://github.com/mt6897-devs/android_kernel_device_modules_6.1/blob/a805f95d61dbf0b2959c9262acc626893114321d/include/linux/soc/mediatek/mtk_sip_svc.h) specify UFS function 0x276 with fast 64-bit SiP convention | Callback requests encode x0=0xc2000276, MTCMOS selector=0x200, REFCLK selector=8, and zero unused registers. No SMC instruction is supplied. |
| [Reference-clock definitions](https://github.com/mt6897-devs/android_kernel_device_modules_6.1/blob/a805f95d61dbf0b2959c9262acc626893114321d/drivers/ufs/ufs-mediatek.h) give offset 0x144, REQ bit 0, ACK bit 1, timeout 3000 us and default settling 32 us | One REQ write, bounded ACK polling, then the 32-us delay. A 32-poll secondary limit handles a frozen timer. Both REQ and ACK must be set, so an ignored write returning zero cannot pass. |
| Captured reset IDs 0/1/2 are UniPro/crypto/HCI at PDN 0x112bb000, assert/deassert offsets 0x48/0x4c, masks 1/2/4 | A separate host-reset sequence asserts HCI, crypto, UniPro; waits at least 100 us; deasserts UniPro, crypto, HCI. Register descriptors identify masked provider operations. No extra PHY reset is added. |

PRE_CHANGE=0 and POST_CHANGE=1 are confirmed in the
[Linux 6.1 UFS header](https://github.com/torvalds/linux/blob/830b3c68c1fb1e9176028d02ef86f3cf76aa2476/include/ufs/ufshcd.h).
The captured reset flags 0x1c combine STATUS_NONE, ASSERT_SET and DEASSERT_SET,
as defined in the
[TI binding](https://github.com/torvalds/linux/blob/830b3c68c1fb1e9176028d02ef86f3cf76aa2476/include/dt-bindings/reset/ti-syscon.h).
The pinned
[reset provider](https://github.com/mt6897-devs/android_kernel_device_modules_6.1/blob/a805f95d61dbf0b2959c9262acc626893114321d/drivers/reset/reset-ti-syscon.c)
uses masked regmap operations. The API's reset callback must provide that
provider behavior and serialization. Its success acknowledges an operation;
it cannot prove reset status, which is unavailable here. HCE enable and its
separate delay/link startup are not executed by this module.

## Power API boundary

`drivers/mt6897_ufs_platform.c/.h` accepts only the captured version-1,
RTFF-enabled, no-VA09 profile. All calls must be serialized by the caller.
Before any SiP or HCI access, the caller must supply the complete prerequisite
mask and a positive authorization callback covering:

- exclusive controller/resource ownership, link off and DMA quiescence;
- enabled, stable board rails and prepared clocks, including correct topckgen
  parents and the six previously implemented AO/PDN leaves;
- a matched secure-firmware ABI and the delegated version-1 PHY policy.

These assertions are provider preconditions, not facts proven by this API.
The SiP callback must normalize a success whose semantics were established
for that firmware. The code does not guess whether raw a0 or a1 means success.

PREPARED means only the implemented subset completed. Host reset is explicit
and separate. Neither state permits attaching the physical UFS transport by
itself. On failure, the state latches and no automatic restart/reset or shared
resource shutdown is attempted. Clock-on ACK timeout sends the source-defined
off/POST notification once and retains an unknown/faulted state; it does not
write RELEASE or free DMA memory.

## DMA/IOMMU API boundary

`drivers/mt6897_ufs_dma.c/.h` implements one private, contiguous,
caller-reserved pool with explicit CPU/device ownership. It validates
cache-line and DMA alignment, extents/overflow, direction, device aperture and
address width. It distinguishes CPU VA, physical address and the device
address returned by the mapper. Tests use nonidentity addresses in both route
modes.

Unknown routing is refused. A verified bus window and a verified IOMMU route
are separate explicit provider choices; neither is selected from an absent
DTB property. The map provider must establish the correct device/domain/stream,
mapping, contiguous device interval and opaque cookie. This module does not
program MediaTek IOMMU page tables or invent stream IDs.

A complete private allocation owns its cache lines. Transitions to/from the
device require the provider's whole-pool cache synchronization and ordering.
No coherent shortcut is inferred. A completion attempt while DMA is active
returns busy without copying data or unmapping. Mapping failure, invalid
mapper output, synchronization failure or lost authorization during DMA
poisons the pool. Poisoned/in-flight memory stays reserved; there is no
automatic unmap, allocator release or recovery API.

The source basis is the
[Linux DMA guide](https://github.com/torvalds/linux/blob/830b3c68c1fb1e9176028d02ef86f3cf76aa2476/Documentation/core-api/dma-api-howto.rst)
and
[of_dma_configure_id](https://github.com/torvalds/linux/blob/830b3c68c1fb1e9176028d02ef86f3cf76aa2476/drivers/of/device.c).
The saved DTB's /soc ancestor declares a zero-to-zero DMA window of 64 GiB;
UFS and its inspected ancestors have no iommus/iommu-map/dma-coherent
properties. These are configuration observations, not proof of active bypass,
coherency, security ownership or the controller's effective DMA mask.

## Actual local results

`research/mt6897-platform/check-v6/result.json`: **PASS**, exit 0.

- **176 power checks** and **149 DMA checks** passed natively under ASan/UBSan.
  Cases include the exact successful trace, every fallible power/reset step,
  frozen timer, absent ACK, ignored REQ write, timeout-notification failure,
  unknown profiles/routes, nonidentity mappings, direction-dependent cache
  copies, DMA-busy refusal, range/overflow/mask rejection, provider failures,
  revoked authorization and pinned memory after poisoning.
- The same **325 checks** passed while executing ARM64 code on QEMU Cortex-A76,
  followed by `MT6897 ARM64 MODEL PASS` and semihost exit 0. These are callback
  models executing on a real emulated CPU, not MediaTek peripheral emulation
  or XNU execution.
- Both standalone production C units compiled for freestanding AArch64 with
  general registers only; their normal-RAM objects have no undefined imports.
- The saved DTB SHA-256 was verified before reading the PHY/reset/ancestor
  properties: `9c49589f70044127be8941a9ea5537977f440ccd5ac15cfd24e120c8a1181d29`.
  All six downloaded vendor files matched their upstream Git blob IDs.
- Test ELF SHA-256:
  `3788be0f0ab3f952abf38de62f00bfbb75714a5a9b262f37518a146bead8d378`.
  Source/object hashes, command lines and logs are saved in the report folder.

The MMU/cache-off model fixture uses strict-alignment code generation and its
own byte-wise runtime. The separately compiled normal-RAM objects use the
default alignment behavior. Preserved failed attempts: check-v3 timed out
without vectors; check-v4's diagnostic vectors identified ESR=0x96000061,
ELR=0x4020486c, FAR=0x40246fcc, an unaligned store in the model's pbarrier trace
record under MMU-off memory attributes. Strict-alignment fixture code fixed
that setup issue. Check-v5 then exposed a memcpy import under that compilation
mode; the final harness checks normal-RAM objects separately and links the
strict-alignment fixture against its explicit runtime. No failed attempt is
counted as a pass.

Replay with a fresh directory (WSL/Linux, Clang/LLD, llvm-nm and QEMU required):

```sh
python3 tools/test-mt6897-platform.py research/platform-check-new \
  --fdt ../phone-fdt.bin --sources research/mt6897-platform/sources
```

The optional --fdt and --sources arguments use existing saved files only.
Without them the native/ARM64 model tests still run, but no captured-DTB or
upstream-file verification is claimed. Output directories refuse overwrite.

## Required before a physical backend

Match the installed firmware's SiP authorization, return semantics and
delegated PHY ownership; implement the actual PMIC/topckgen and masked reset
providers; establish UFS DMA reachability, device mask, domain/stream or
verified bypass, cache policy, and a quiescence/recovery mechanism. Then adapt
those providers to XNU and the tested read-only transport. The default
physical backend stays disabled until those facts are established. GPU/Mali
power and CSF submission remain a separate driver task.
