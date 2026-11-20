# Duchamp Linux XNU link status

**The Linux linker is able to relink the reference XNU object archive. Building the full modified source snapshot is still blocked.** This distinction matters because the reference object archive pre-dates dual-RAMDisk registration and cannot prove the new code.

## Dependency resolution

1. Started with the saved Linux Apple ld64-951.9 recipe and CI 41543710742 reference object archive. The previous command stopped at `-lfirehose_kernel`. The [source-built Firehose library](DUCHAMP_LIBFIREHOSE_BUILD.md) removed that failure. The exact retry exited 1 with three unresolved compiler-runtime symbols.
2. The two `__llvm_profile_*` functions are called by `OSKextGrabPgoDataLocked` in `xnu/libkern/c++/OSKext.cpp`. LLVM 21.1.8 compiler-rt adds bitmap and, for the size function, vtable parameters that this old XNU does not pass. Its same-named functions are incompatible with the caller. LLVM 15.0.7 has the six range arguments for size and the buffer plus six range arguments for writing. Its six kernel profiling objects compiled with the real Apple headers from the XNU build tree, Libc `a61a5933206342413af76579500f313a045c1c33`, libpthread `a6c70ca0e544347a0377babf748f831577ec24f9`, and libmalloc `d876784c79e2869ff1cce519f46905c49117f9a6`. Supplying that profiling archive removed both unresolved names. [LLVM 15.0.7 profile buffer](https://github.com/llvm/llvm-project/blob/llvmorg-15.0.7/compiler-rt/lib/profile/InstrProfilingBuffer.c), [LLVM 21.1.8 profile buffer](https://github.com/llvm/llvm-project/blob/llvmorg-21.1.8/compiler-rt/lib/profile/InstrProfilingBuffer.c).
3. The final name was `___chkstk_darwin`. The [ARM64 probe source](../tools/duchamp-darwin-stack-probe.S) implements actual page reads with the reference kernel's x9 byte-count and x10 scratch conventions. Its 48 instruction bytes matched the reference behavior exactly by comparison with the saved linked image. It assembled as a fresh ARM64 Mach-O object. This implementation lives outside the default source build. The public LLVM proposal documents the Darwin calling convention and page probe. [LLVM review D40857](https://reviews.llvm.org/D40857).
4. With those inputs, Linux ld64 exited 0. Reference inspection confirmed file-backed ARM64 text, `LC_UNIXTHREAD`, PC `0xfffffe0007480488`, required segment order, no overlap and no undefined dynamic symbols. The candidate gate exited 1 because the old objects do not define `_duchamp_dual_ramdisk_init`. No archived kernel binary was patched or used as a candidate.

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| LLVM 15.0.7 kernel profiling archive | 15,336 | `03eec4af161262277b4f7f6192fa80229e7e1c18de62ec772d42388d7d9fd120` |
| Darwin stack probe object | 416 | `2a78f4deebfbf14ae09c712fa776a6fa4188d20b7a04ff34864ac7da541d7f34` |
| Diagnostic reference relink | 22,605,984 | `94ea872909d113038aaed313055baba926b309824a2fe76657c66dc4b5868e3f` |

The default SDK marker was 10.6. An additional reference relink with explicit `-platform_version macos 15.5 15.5` passed reference inspection with the SDK marker set to 15.5, the same entry PC and 22,605,984 bytes. Its SHA-256 is `2c3ab344f9f325d172719eb14785b2080263b6670d7492b989d8f8b14035d594`. The SDK marker records link metadata. The objects retain their original build inputs. [Explicit-platform layout](../../../outputs/duchamp-linux-firehose-20261117/sdk15_5-reference-layout.log).

Exact command records include the [Firehose retry](../../../outputs/duchamp-linux-firehose-20261117/cctools-link-with-firehose.json), [profiling build](../../../outputs/duchamp-linux-firehose-20261117/cc-kext-profile-15-commands.json), [profiling retry](../../../outputs/duchamp-linux-firehose-20261117/cctools-link-with-profile15.json), and [successful reference relink](../../../outputs/duchamp-linux-firehose-20261117/stack-and-reference-link.json). The log preserves the actual driver-expanded ld64 invocation and each exit code. A clean recompilation of the six profiling files reproduced the archive hash.

## Remaining fresh source build blocker

The fresh WSL compile of staged `memdev.c` passed with no substituted compiler builtins. The equivalent `IOKitBSDInit.cpp` command failed in `IOKit/IOLib.h`'s typed allocation path. Stock Clang 21.1.8 has neither `__builtin_xnu_type_signature` nor `__builtin_xnu_type_summary`. Earlier smoke compiles supplied stand-ins and do not qualify for this link. The remaining blocker is the kernel compiler and complete clean object build. It is independent of Firehose and of the demonstrated ld64 ability to link the reference archive.

The Linux path to test next is UniXNU's real XNU-aware Clang at its pinned LLVM revision `58c46bae21181fb4240cf964461bea738d96d50e` with its builtin patch. First verify support by recompiling the two staged SWEET files without overrides. Then build all source objects from the pinned snapshot, using the SWEET 16 KiB build profile. UniXNU's documented Linux path provides a precedent and does not certify this older SWEET snapshot. [UniXNU Linux toolchain setup](https://github.com/UniXNU/UniXNU/blob/main/scripts/linux/setup-toolchain.py).

The verified Mac fallback is prepared under the 858-input `source-ready` snapshot. Its checksum inventory passed again. [Xcode 16.4 and pinned KDK reproduction](DUCHAMP_FULL_XNU_SOURCE_BUILD.md).
