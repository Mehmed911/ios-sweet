# Bounded UFS waits and saved Linux boot policy

The UFS transport now stops if its clock stops advancing. This changes the
production XNU QEMU adapter; the MT6897 physical providers remain closed.
All work here uses saved files and local QEMU instances. No phone, USB, ADB,
fastboot, module loading or partition operation is part of this milestone.

## Transport change

`dufs_config.poll_limit` is mandatory, in the range 1–1,000,000. A public
operation receives one shared budget: startup waits, repeated fDeviceInit
queries and retry completions consume it without replenishing it internally.
The XNU adapter selects the maximum. This is a resource bound, not a measured
MT6897 timing value. It supplements the existing millisecond deadline.

Exhaustion records `DUFS_WAIT_POLLS`; a clock deadline records
`DUFS_WAIT_DEADLINE`. Either poisons the host. Further requests fail without
I/O; there is no reset, automatic rebind, DMA reclamation or destination copy
after an incomplete read. Callbacks themselves must return: a finite poll
count cannot recover a CPU blocked inside a physical MMIO transaction.

Local validation on 2026-10-31:

| Test | Actual result | Scope |
|---|---|---|
| `test-duchamp-ufs-poll.py` | 67 native ASan/UBSan + 67 ARM64 checks | Software register/DMA fixture, frozen/backward/wrapping clocks, cumulative budgets and device-init flag loops |
| `test-duchamp-driver-core.py` | 142 checks; 78 native sanitizer guards | Actual QEMU UFS DMA driven by qtest, including a frozen clock above 4 GiB; no guest OS |
| Local XNU compilation | Both changed C translation units pass; new symbol resolves | Real generated XNU headers, no full kernel boot |

Full XNU build/guest results will be recorded below when complete. Previous
24/20 guest results for `d51e7db` do not validate this changed core.

## Captured boot policy narrows the DMA candidate

`audit-duchamp-boot-policy.py` pins the same boot/vendor-boot/FDT hashes as
[SAVED-UFS-CONTRACT.md](SAVED-UFS-CONTRACT.md). It exports only selected known
arguments and values. Full boot arguments, calibration identifiers, extracted
kernels/modules and firmware remain outside Git.

The saved FDT requests `swiotlb=noforce`, `disable_dma32=on`, and
`initcall_blacklist=ufshcd_core_init`. The embedded kernel config enables
`CONFIG_CMDLINE_EXTEND` and requests `kvm-arm.mode=protected`. The saved boot
and vendor-boot header command lines contain none of these selected policy
arguments. The vendor-boot v4 bootconfig section is empty. A bootloader can
generate or append initrd bootconfig; its runtime contents are not captured.

These interpretations use seven Git-blob-pinned files at the saved kernel
stamp commit `cf2c2dc91b9e9f016dc25cf095b1fe34cb5dfcb6`:

| Source | Meaning of the captured request |
|---|---|
| [kernel/dma/swiotlb.c](https://github.com/aosp-mirror/kernel_common/blob/cf2c2dc91b9e9f016dc25cf095b1fe34cb5dfcb6/kernel/dma/swiotlb.c) | `noforce` sets `swiotlb_force_disable`; default early and late initialization return without allocating a pool. The flag is sticky, so a later `force` does not clear it. |
| [arch/arm64/mm/init.c](https://github.com/aosp-mirror/kernel_common/blob/cf2c2dc91b9e9f016dc25cf095b1fe34cb5dfcb6/arch/arm64/mm/init.c) | `on` sets `disable_dma32`; zone initialization sets the DMA32 maximum PFN to zero. A later `off` does not clear the flag. This does not establish the controller's address width. |
| [drivers/of/fdt.c](https://github.com/aosp-mirror/kernel_common/blob/cf2c2dc91b9e9f016dc25cf095b1fe34cb5dfcb6/drivers/of/fdt.c) | EXTEND concatenates the built-in command line followed by FDT bootargs, subject to its size limit. |
| [init/main.c](https://github.com/aosp-mirror/kernel_common/blob/cf2c2dc91b9e9f016dc25cf095b1fe34cb5dfcb6/init/main.c) | `kernel.*` bootconfig arguments would precede that command line. The blacklist requests skipping the named kernel initcall; it does not prove module loading or live UFS state. |
| [arch/arm64/kvm/arm.c](https://github.com/aosp-mirror/kernel_common/blob/cf2c2dc91b9e9f016dc25cf095b1fe34cb5dfcb6/arch/arm64/kvm/arm.c) | Protected mode requires available hyp and non-VHE at parameter processing; later initialization can fail. A request is not evidence of active pKVM. |
| [asm/setup.h](https://github.com/aosp-mirror/kernel_common/blob/cf2c2dc91b9e9f016dc25cf095b1fe34cb5dfcb6/arch/arm64/include/asm/setup.h), [uapi/asm/setup.h](https://github.com/aosp-mirror/kernel_common/blob/cf2c2dc91b9e9f016dc25cf095b1fe34cb5dfcb6/arch/arm64/include/uapi/asm/setup.h) | The include chain fixes `COMMAND_LINE_SIZE` at 2048. The reconstructed built-in + FDT request needs 951 bytes including NUL, so all selected arguments fit. |

This refines the earlier “direct DMA, potentially using SWIOTLB” candidate:
under the captured policy and matching source, **the default SWIOTLB pool
must not be assumed available**. It does not exclude every vendor/per-device
pool or override. Effective DMA ops, fwspec/domain, HCCAP, coherent/streaming
masks, secure ownership and the matched BL31 effects are still missing.
Linux command-line semantics are not an XNU firmware contract.

`test-duchamp-boot-policy.py` executes three unchanged parameter function
bodies from those pinned sources with fixture globals and capability queries.
It passes 50 ASan/UBSan checks and the same 50 on ARM64 in QEMU. It covers
sticky duplicate arguments and protected-mode rejection/acceptance conditions;
it does not initialize Linux, pKVM, a SWIOTLB pool or physical DMA. Nine
auditor guard tests cover redaction, changed sources, malformed/bounded
structures and output preservation.

## Reproduce locally (Linux/WSL)

Use new output directories; the tools preserve existing output.

```sh
python3 tools/fetch-duchamp-boot-policy.py research/boot-policy-sources
python3 tools/audit-duchamp-boot-policy.py research/boot-policy-audit \
  --sources research/boot-policy-sources --boot ../phone-boot/boot_a.img \
  --vendor-boot ../phone-boot/vendor_boot_a.img --fdt ../phone-fdt.bin
python3 tools/test-duchamp-boot-policy-audit.py
python3 tools/test-duchamp-boot-policy.py research/boot-policy-check \
  --sources research/boot-policy-sources
python3 tools/test-duchamp-ufs-poll.py research/ufs-poll-check
```

Current local evidence: `research/mt6897-policy/audit-v2/result.json`,
`check-v2/result.json`, `poll-v1/result.json`, `transport-v1/result.json`,
and `compile-v1/result.json`. Source and fixture hashes are recorded there.
Physical firmware/DMA validation remains a separate, unresolved requirement.
