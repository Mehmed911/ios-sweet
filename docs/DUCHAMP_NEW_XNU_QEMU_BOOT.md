# Duchamp source-built XNU link and QEMU boot

## Build inputs

The Linux build plan contains 1,126 compile commands for `DEVELOPMENT_ARM64_SWEET`. It starts with the 1,105 inputs in the saved XNU component file list, adds four objects named separately by XNU's final link recipe and includes the 17 new standard BSD sources present in the current tree. HFS+, libpthread and BearSSL were staged from their pinned dependencies. The captured build snapshot supplies generated headers, MIG and IIG output, compiler configuration and linker metadata. Its 82 `.defs`, 17 `.iig` and one `.master` inputs match the current sources byte for byte. The staged build refreshed the changed exported `sweet_early.h` and regenerated `version.c` with XNU's `newvers.pl`. The saved build tree was extracted with object and archive files excluded.

The source compile manifest records the command, source digest and output location for each unit. The link harness accepts the file list only after every planned compile succeeds and every object matches its recorded digest. The harness applies XNU's section-segment naming rules for hibernation, the libsa bootstrap object and the final constructor to copies of the new objects. The three pre-existing, source-built link dependencies are checked against their digests.

The first complete compile produced 1,126 ARM64 Mach-O objects after the three source compatibility fixes. ld64 then reported an unresolved `___cxa_atexit` in `bootstrap.cpo`. LLVM 24's backend lowered the explicit `KLDBootstrap` destructor to a userspace runtime call. A compile using `-mllvm -disable-atexit-based-global-dtor-lowering` produced the expected `__mod_term_func` section and removed the unresolved dependency while preserving `__mod_init_func`. The frontend-only option `-fno-register-global-dtors-with-atexit` did not change the result. The local build applies the verified backend flag to `bootstrap.cpp`. The logs and exact commands for the comparison are in `bootstrap-dtor-experiments.json` and `source-link.first.log`.

| Link input | SHA-256 |
| --- | --- |
| cctools ld64 951.9 | `865fb3ee04cde40a675157b121dc2f3e0399adbf223fb7173f79ebbfa3406e34` |
| `libfirehose_kernel.a` | `9452c8d39826db46ff2e40c0ad6ed128f95ec78557378a607d0a1e52eb7f9d7f` |
| `libcc_kext_profile15.a` | `03eec4af161262277b4f7f6192fa80229e7e1c18de62ec772d42388d7d9fd120` |
| `darwin-stack-probe.o` | `2a78f4deebfbf14ae09c712fa776a6fa4188d20b7a04ff34864ac7da541d7f34` |

The exact ld64 argument vector, generated file list digest, dependency digests and object digests are recorded in `new-kernel-link.json` once the link phase starts. `tools/duchamp_xnu_link.py` checks plain ARM64 `MH_EXECUTE`, `LC_UNIXTHREAD`, the `__start` mapping, the dual-RAMDisk registration symbol, segment protection and order, and unresolved symbol count. The build harness supplies that exact kernel image to the QEMU test commands.

## Independent regressions

| Check | Result |
| --- | --- |
| Native ASan/UBSan dual-RAMDisk bounds | 16 cases passed, exit 0 |
| ARM64 QEMU dual-RAMDisk bounds | Same 16-case source, semihosting exit 0 |
| Single-RAMDisk packaging | 2 cases passed, exit 0 |
| Preserved service payload packaging | 10 cases passed, exit 0 |
| Dual-RAMDisk layout mutations | 12 cases passed, exit 0 |
| Darwin RAM-root verifier | 9 cases passed, exit 0 after correcting the fixture argument |
| Bootshim and payload preflight | Host bootshim, handoff, XNU return, capture and payload checks passed, exit 0 |
| Saved boot-image validation | 13 checks passed, exit 0 using the preserved local fixture |

These runs exercise the utility code and preserved fixtures. Full kernel acceptance is taken from the newly linked kernel's build receipt and its own QEMU logs.

## QEMU validation procedure

The first linked 19,607,584-byte image, SHA-256 `1557426dcae2c8c060256e3392b295fa1bbf11bf5ad8e3c24fbd6137b08ad632`, passed the layout check. Both QEMU runs then reported an undefined instruction at `0xfffffe0007ae7468` in `_kprintf`, followed by a second `XPACI` in `_panic`. The failed runs were stopped before userspace. The first and last exception records and instruction disassembly are preserved in the run directory. The repeating trace was capped to avoid consuming the host disk.

The patched Clang driver had selected `apple-m1` as the Darwin CPU even with XNU's `-march=armv8.2-a+crypto`. [Patch 0216](../xnu/patches/0216-duchamp-arm64-generic-codegen.patch) makes the generic CPU explicit for the SWEET configuration. A compile of `pe_kprintf.c` then produced `XPACLRI`, the hint-space instruction that can execute on the Cortex-A76 QEMU model. The build uses the original target and instruction baseline with the explicit CPU choice.

The first generic-CPU kernel passed the 17 Darwin Mach-O and RAM-root checks. Its dual-RAMDisk boot reached `IOFindBSDRoot` and raised `DUCHAMP_RAMDISK_BOOT_WINDOW`. XNU's `arm_init()` had copied the incoming boot arguments into `const_boot_args`, so translating `PE_state.bootArgs` supplied an address inside the kernel instead of the loader's reserved page. [Patch 0217](../xnu/patches/0217-duchamp-save-loader-boot-args-address.patch) captures the loader address through the same linear mapping used in `start.s` before the copy. The [RAMDisk registration routine](../duchamp/xnu/dual_ramdisk_init.inc) now uses the captured address while keeping the original reservation, alignment, overflow and overlap checks.

From the repository root in WSL, run the revised local build and test harness with

```bash
out=$(realpath ../../outputs/duchamp-patched-clang-20261117)
bash "$out/rebuild-and-boot-final.sh"
```

The boot runs use QEMU 10.2.1. `tools/test-duchamp-readonly-var.py` builds and checks md0 and md1, reads the guest witness for `/private/var`, `/var`, `/dev/console`, EROFS and ENOSPC, compares root-image digests and verifies the original launchd and service logs. `tools/test-duchamp-darwin-ramroot.sh` exercises the dynamic and static ARM64 Mach-O probes with the same kernel in a separate RAM-root session. The harness keeps the kernel hashes, test argument vectors, payloads and guest logs in the run directory.

## Final kernel and runtime evidence

The locally built `new-xnu-qemu-final/kernel.development.sweet` is 19,541,944 bytes. Its SHA-256 is `e7b51ecb16fe9ad21a78455714b2bf26c1dee1fbc3a6a7f0cb3971a9cd569457`. The full compile passed 1,126 of 1,126, ld64 exited 0 and the layout validator exited 0. The ARM64 `LC_UNIXTHREAD` entry is `0xfffffe00074aa488` and the dual-RAMDisk initializer is at `0xfffffe0007506b60`. The segment permissions and order passed the validator. Independent `llvm-nm --undefined-only` output is empty.

| QEMU run | Result |
| --- | --- |
| Dual-RAMDisk and read-only root | 11/11 checks passed in 71.626 s, exit 0 |
| Original launchd and services | 74/74 checks passed in that same boot, including launchd PID 1, notifyd, syslogd and the ASL client exchanges |
| Darwin Mach-O | 17/17 checks passed in 94.618 s, exit 0. Dynamic PID 2 loaded dyld/libSystem with 37 images and exited 0. Static PID 3 exited 42. Mach messaging and filesystem checks passed. |
| Error paths | 5/5 QEMU regressions passed with the same kernel. Missing md1, missing mount point, bad HFS+ geometry, invalid directory permissions and an incorrect `/var` alias were detected before the original launchd ran. |

The guest identified `/dev/md1` as the writable mount source and resolved `/var` to `/private/var`. The witness showed `EROFS=30` for a write on the root, `EACCES=13` when opening raw md0 for writing and `ENOSPC=28` after writing 32,702,464 bytes to md1. It verified capacity recovery after cleanup. Both HFS+ images were 32 MiB. The md0 seed and guest memory dump share SHA-256 `d61812323879a9dca1045957b7e471d8bcc227be25ab5eac1bc0eb33fe798520`. The writable volume's SHA-256 changed from `bf935429b89635d2dbca32bab3ffa1a3d3e8e60e0a8e2fa060125d1a4239c2d4` to `b0c745c5b4d9a5113d0c857c0ceddd973c0f754f2d50a7eff7b7317beb73d78f`.

The dual-RAMDisk payload passed ADT and memory-range checks and rebuilt byte-identically from its saved inputs. Its 86,656,224 bytes hash to `224b5da8a346510bb9eb190635c15dc50b3e3ec38bcf41cc5a9a9df639215c81`. The separate Darwin payload hashes to `5265fc3e47ad23c2d7df98771dbbb3d902554dc978db04dc09ef876f194c735a`. Both runs recorded the final kernel digest. The QEMU profiles use RAM storage and supply no physical UFS configuration.

The exact compile and ld64 argument vectors are in `all-compile-result.json` and `new-kernel-link.json`. The QEMU arguments and subprocess receipts are in `new-xnu-qemu-final/dual-ramdisk/commands.json`, `final-dual-ramdisk.cmd` and `final-darwin-macho.cmd`. The guest witnesses, decoded framebuffer logs and image digests are in the QEMU subdirectories. `final-macho-verification.json` contains the Darwin process and filesystem assertions. `final-negative-regressions.json` records all five error cases. The missing-md1 check uses the unique panic prefix because the full message wraps across framebuffer rows.

This result covers the isolated WSL build with the recorded generated headers and verified support libraries. Physical Duchamp boot, UFS ownership and DMA remain outside the tested configuration.
