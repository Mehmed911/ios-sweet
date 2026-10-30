# XNU virtual UFS adapter and MT6897 clock leaves

This work adds an opt-in BSD adapter for the previously tested UFS read core.
The default md0 route remains available. The MT6897 physical backend still
returns unsupported; no phone, USB, boot partition or real UFS/GPU was used.

## Virtual storage route

`tools/stage-duchamp-qemu-ufs.py` runs after the existing semantic BSD
checkpoints. It stages the **unchanged** `drivers/ufs_readonly.c/.h` plus
`xnu/qemu_ufs.c`, adds them to the BSD source list and adds `rd=qufs0` as
a separate root choice. The existing Qualcomm implementation is not reused.

The adapter:

- registers `qufs0`/`rqufs0` BSD block/character devices, queries geometry,
  checks request bounds and reports residual bytes/errors before biodone;
- refuses write opens, character writes and block write requests; it has no
  arbitrary CDB or SCSI WRITE path;
- serializes its one polled queue, copies reads through a bounce buffer and
  supports physical 4096-byte blocks over the BSD logical sector size;
- reserves contiguous DMA memory permanently, validates its physical pages,
  and uses physical clean/flush operations plus barriers around transfers;
- preserves poisoned/in-flight allocations after failure rather than trying
  an automatic reset or freeing potentially live DMA buffers.

Only the disposable virtual LUN is exposed, with HFS+ directly at its start.
This is not a phone GPT/partition-selection implementation. The prototype
does not implement asynchronous queues, hot teardown, sleep/power management
or MediaTek firmware initialization. Virtual execution cannot prove physical
cache coherency or an MT6897 DMA/IOMMU contract.

Before PCI mapping it requires an explicit boot argument, exact fixture ADT
identity/resources and Cortex-A76 MIDR. That core is not present in MT6897.
This is an accidental-use guard, not hardware authentication. PCI ID/class,
cold configuration and BAR readback are also checked. The new host profile
rejects writable root arguments, Qualcomm nodes and any fallback RAMDisk.

QEMU uses `virt,gic-version=3,highmem-ecam=off`, slot 4, ECAM
`0x3f000000+0x1000000` and BAR `0x10000000+0x1000`. The actual generated
QEMU DTB confirms the ECAM and PCI memory window. GIC addresses and virtual
timer ID are checked separately from the physical MT6897 addresses.

## Verification

The initial kernel integration commit is
[51bd2ca](https://github.com/Mehmed911/ios-sweet/commit/51bd2ca39c97d441df912a9a12e31cf24ea7a601).
Its full kernel build is
[Actions 41131664525](https://github.com/Mehmed911/ios-sweet/actions/runs/41131664525).
That initial build succeeded but its first guest test failed. The PAN-safe
fix is [9a10068](https://github.com/Mehmed911/ios-sweet/commit/9a10068375fa1320d802e3d30fe951f8b1a07f4f),
successfully built in [Actions 41133993461](https://github.com/Mehmed911/ios-sweet/actions/runs/41133993461).
That exact new kernel passed both guest tests below on 2026-10-31 local time.

| Actual test | Result |
| --- | --- |
| `research/xnu-ufs/guest-v2/verification.json` | **20/20 checks**, exit 0; HFS+ root mounted through the new virtual UFS adapter, matching root/block-device identity, PID 1 raw/offset/file reads, EFAULT handled, write-open refused with EROFS, later heartbeat; 80.493 host seconds, 16 sampled frames |
| `research/xnu-ufs/md0-regression-v1/verification.json` | **10/10 checks**, exit 0; same new kernel, established md0 root and static PID 1, later heartbeat; 89.932 host seconds, 18 sampled frames |

Neither run observed a panic; framebuffer decoding reported zero unknown
glyphs. Sampling is not a continuous execution trace or a long-term stress
test. Both source disk images and the selected kernel remained byte-identical.
The virtual-UFS run had no fallback ADT RAMDisk and used QEMU's read-only
drive. Its test sources were also unchanged during execution. The local
runner includes an existing seven-line `MEMORY READY` diagnostic change left
uncommitted; that diagnostic classification branch is not exercised by these
full-boot tests.
Exact working-source hashes are in the verification report.

Artifact pins:

- Run head: `9a10068375fa1320d802e3d30fe951f8b1a07f4f`.
- Kernel artifact ID: `13015622163`; downloaded ZIP SHA-256
  `cb11ed54942844c14f12346a1c3c8121d90777a9038896442e4c1be5181c668f`,
  equal to GitHub's reported artifact digest.
- Kernel SHA-256: `c40bebddeaea04c11ca8f4812de8160490ba8933ee68bc63a9481ed257d82109`,
  also matching the artifact's `SHA256SUMS`.
- Disposable virtual-UFS root SHA-256:
  `5f4f6b5c5a7947dcab9e2c56f668b719053b89a5f07dc256f255e11fdbec3440`.
- md0 regression root SHA-256:
  `e5b5c1b68c00db65ae31d8d29baef6ab88c8131e29940d8ce7b810536726414a`.

Additional local evidence:

- Both C translation units compiled against the Actions 104 generated BSD
  headers. Their imports resolve against the baseline kernel/each other.
- The Linux C++ attempt cannot validate Apple's XNU-specific compiler
  builtins; its failure log is retained. The initial full Xcode CI successfully
  compiled/linked that translation unit; the fix changes only the BSD adapter.
- `tools/test-qemu-ufs-profile.py`: 19 tests passed. Synthetic metadata tests
  cover read-only flags, duplicate/foreign roots, CPU/firmware/resource gates,
  wrong GIC addresses and RAMDisk/Qualcomm-node rejection.
- `research/xnu-ufs/fixture-v4` contains a fresh offline HFS+ root and static
  signed PID 1. `/dev` exists before a read-only mount. Builder extraction
  verifies the exact init and 1024-byte test file. The old base is unchanged.

The guest test requires actual mount/rootvnode, PID 1, matching `stat64('/')`
st_dev and block-node st_rdev (with the correct inode types), raw/offset reads,
handled EFAULT for bad user memory, EROFS for write-open, exact file bytes and a
later heartbeat. Early printf/IOLog does not necessarily reach the framebuffer;
the device-identity syscall check supplies direct runtime evidence instead.
It pins the kernel hash and checks that the host image
remains unchanged. The marker `QEMU RAM ROOT MOUNTED` is a legacy checkpoint
label used after any successful root mount in this kernel. It alone is not
proof of the root source; the test additionally requires qufs0 device identity and
forbids an ADT RAMDisk.

Replay with a fresh output directory and the exact newly built kernel:

```sh
python3 tools/build-duchamp-ufs-fixture.py research/qufs-fixture-new \
  --base-root work/qemu-rootvnode-98/root-with-launchd.hfs \
  --adt work/qemu-multiproc.adt \
  --hfsplus research/libdmg-hfsplus-build/hfsplus
python3 tools/test-duchamp-ufs-xnu.py \
  --kernel PATH_TO_NEW_KERNEL --kernel-sha256 ACTUAL_SHA256 \
  --fixture research/qufs-fixture-new --output research/qufs-guest-new \
  --ci-run 41133993461 --ci-head 9a10068375fa1320d802e3d30fe951f8b1a07f4f
```

## Preserved raw-read failure and fix

`research/xnu-ufs/guest-v1` failed after 70.61 host seconds. The initial kernel
SHA-256 was `d5516019fa0a141415f47bdd72b50d53a6f35120b407301248c6eafc75acb74d`.
HFS+ mount/rootvnode and PID 1 entry were observed, then the raw read aborted
at `memmove+0x48`, called by `qu_strategy+0x1c0`, with FAR at the user stack.
The physio/B_PHYS mapping supplied a user VA to a plain kernel memcpy, which
cannot access that memory with PAN enabled. The failed report/image/logs are
preserved; this run is not counted as a pass.

Raw reads now use `uiomove()` from a private, CPU-only snapshot. The controller
lock is released before copying to user memory, so a copyout page fault can
re-enter VFS without deadlocking the same controller. Scratch storage is freed
on all exits; it is never a DMA target. Block strategy rejects B_PHYS instead
of treating a user VA as a kernel pointer.

`research/xnu-ufs/uio-model-v1/result.json`: **18 ASan/UBSan checks** passed
using the actual extracted qu_read/qu_error bodies with instrumented UIO,
allocation, lock and transfer stubs. Cases include multi-chunk/offset reads,
partial copy faults, transfer failure, EOF and allocation failure. This is a
control-flow model, not XNU VM/PAN emulation. The real guest regression passed
handled EFAULT followed by a successful HFS file read and a later heartbeat.

## Implemented MT6897 leaf-clock subset

`drivers/mt6897_ufs_clocks.c` implements the six AO/PDN leaf gates against a
caller-supplied, explicitly authorized register interface. It has no physical
MMIO backend and is not linked into the virtual kernel adapter. The register
and ID facts come from pinned primary sources:

- [clk-mt6897-peri.c](https://github.com/mt6897-devs/android_kernel_device_modules_6.1/blob/a805f95d61dbf0b2959c9262acc626893114321d/drivers/clk/mediatek/clk-mt6897-peri.c)
- [clk-gate.c](https://github.com/mt6897-devs/android_kernel_device_modules_6.1/blob/a805f95d61dbf0b2959c9262acc626893114321d/drivers/clk/mediatek/clk-gate.c)
- [MT6897 clock IDs](https://github.com/mt6897-devs/android_kernel_device_modules_6.1/blob/a805f95d61dbf0b2959c9262acc626893114321d/include/dt-bindings/clock/mt6897-clk.h)

| Provider | IDs / bits | Parent |
| --- | --- | --- |
| ufscfg_ao, `0x112b8000` | 0 TX symbol, 1 RX0 symbol, 2 RX1 symbol | f26m_ck |
| ufscfg_ao, `0x112b8000` | 3 UniPro system | ufs_ck |
| ufscfg_pdn, `0x112bb000` | 0 UFSHCI UFS | ufs_ck |
| ufscfg_pdn, `0x112bb000` | 1 UFSHCI AES | aes_ufsfde_ck |

Both banks use status offset `4`, disable/set offset `8`, enable/clear offset
`12`; a cleared status bit means enabled. The implementation writes one mask
only when state changes, checks status with a bounded timeout and faults the
context after an I/O error/timeout. It never attempts rollback of shared
resources. Authorization is a caller precondition, not firmware verification.

`research/xnu-ufs/clocks-v2/result.json`: **123 model checks**, ASan/UBSan,
exit 0; freestanding ARM64 compilation passed with no undefined imports.
All six providers/IDs/names match the previously captured DTB report. This is
a register-model result, not a MediaTek hardware or power-on test.

```sh
python3 tools/test-mt6897-ufs-clocks.py research/clock-check-new \
  --hardware-report research/mt6897-drivers/hardware-v1.json
```

## Remaining physical platform work

Six topckgen mux/source references are deliberately not implemented by the
leaf-gate API. Nor are PMIC supplies, M-PHY, reset timing, SiP power/RTFF-
MTCMOS, secure ownership or DMA/IOMMU mapping. The
[UFS variant](https://github.com/mt6897-devs/android_kernel_device_modules_6.1/blob/a805f95d61dbf0b2959c9262acc626893114321d/drivers/ufs/ufs-mediatek.c)
initializes these in a larger framework-dependent sequence; enabling six
gates cannot substitute for that sequence. The captured reset data marks
status reporting unsupported, so reading a status bit cannot establish reset
completion without the matching reset/firmware contract.

Next: establish the matching firmware ownership and power/PHY/reset sequence,
then connect a physical backend to the tested transport. Keep MediaTek root
selection unsupported until then. Mali still needs a matched CSF firmware,
GPU MMU, queues/fences/power and an iOS graphics interface; the existing
software raster test is not GPU acceleration.

Subsequent local sequencing and DMA-ownership work is documented in
[MT6897-PLATFORM.md](MT6897-PLATFORM.md). It implements and tests the captured
version-1 PHY delegation policy and power/reference-clock/reset sequence,
while leaving physical firmware, regulator and IOMMU providers unimplemented.
