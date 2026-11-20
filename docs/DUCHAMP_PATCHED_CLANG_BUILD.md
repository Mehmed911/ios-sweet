# Duchamp patched Clang build

The kernel configuration is `DEVELOPMENT_ARM64_SWEET` on `duchamp-bootstrap` at base `d91562d9c2bd3bc33d52550c101de1009bb41dc0`, with the existing uncommitted changes included. The upstream XNU source is `xnu-8796.141.3` at `1b191cb58250d0705d8a51287127505aa4bc0789`.

## Compiler requirement

Ubuntu Clang 21.1.8 fails to parse the type arguments of `__builtin_xnu_type_signature`, `__builtin_xnu_type_summary` and `__builtin_xnu_types_compatible`. The representative compile batch produced 13 ARM64 Mach-O objects. `IOKitBSDInit.cpp`, `SweetCPU.cpp`, `bootstrap.cpp` and `hfs_vfsutils.c` failed with related errors. In the IOKit case the first failure is in `iokit/IOKit/IOLib.h` where the typed allocation template passes `T`.

UniXNU's patch implements these builtins as compile-time type operations. It walks field offsets and sizes from Clang's record layout, classifies eight-byte granules and encodes the signature and summary. The compatibility operation compares allocation layouts and handles `void` explicitly. The patch also implements `xnu_usage_semantics` and folds the operations in C++ templates. The [local compiler test](../tools/test-duchamp-xnu-builtins.cc) checks mixed records, overlapping union members, tail padding, empty types, compatibility and one typedef annotation. [Pinned UniXNU patch](https://github.com/UniXNU/UniXNU/blob/e2fdae4312d0acc3d8a52bc457101e7918095e6a/scripts/linux/llvm-xnu-builtin-type.patch)

## Inputs and configuration

| Input | Recorded value |
| --- | --- |
| UniXNU | `e2fdae4312d0acc3d8a52bc457101e7918095e6a` |
| LLVM | `58c46bae21181fb4240cf964461bea738d96d50e` |
| LLVM source archive SHA-256 | `e30ace42a3cae7cd5a69ffc46f3115bf1ba54b5dc436a2b77bd10cb0a9a0158a` |
| UniXNU patch SHA-256 | `7c9f2cb16ff1cc045d246fa6d1b6fbe6c90dc1540839a4219a0045219792dba9` |
| Host tools | Ubuntu Clang 21.1.8, CMake 4.2.3, Ninja 1.13.2 |
| Compiler build | CMake Release, host `-O1`, LLVM assertions enabled, AArch64 backend, six parallel jobs |
| Installation prefix | `/var/tmp/duchamp-clang.zZKCR0J4/install` in Ubuntu WSL |

The isolated installation leaves the system compiler and the existing ld64 and support libraries in place. The first build attempt exited 1 because the partial LLVM source staging omitted `libc/shared/math.h`. Adding the `libc` tree from the same verified LLVM archive resolved that error. The exact configure and install invocation is recorded in `build-clang.sh`, with the two attempts logged separately. The completed installation reports Clang 24.0.0git with assertions. Its executable SHA-256 is `510ca931314bf99a2b16c8d046aca8193d451d9da253ac7bb531128d5186a010`.

From the repository root in WSL, the compiler semantics test is

```bash
out=$(realpath ../../outputs/duchamp-patched-clang-20261117)
staging=$(cat "$out/linux-path.txt")
"$staging/install/bin/clang" -x c++ --target=arm64-apple-macos15.5 \
  -std=c++17 -ffreestanding -fsyntax-only tools/test-duchamp-xnu-builtins.cc
```

The component compile harness uses the archived CI flag records, the generated headers, the per-object flags from XNU's component makefiles and the current staged source. The target is plain ARM64 with `-mkernel`. The generated command and result manifests record full argument vectors, working directories, exit codes, source hashes and object hashes. Symbol inspection checks that `memdev.o` defines `_duchamp_dual_ramdisk_init` and that `IOKitBSDInit.cpo` references it.

## Compiler and source compatibility results

The initial assertions exposed C++ template desugaring. A direct attributed typedef reports pointer semantics. The same alias passed as a template type argument is canonicalized to the underlying integer type. The revised test asserts both behaviors and exits 0.

The first patched Clang build of `IOKitBSDInit.cpp` failed on four expansions of `KALLOC_TYPE_IS_COMPATIBLE_PTR`. The C++ code tried to dereference `void *` inside `typeof`. [Patch 0214](../xnu/patches/0214-duchamp-clang-kalloc-pointee-type.patch) uses Clang's type transforms to obtain the pointee while retaining the original layout comparison, pointer requirement and `void *` wildcard. The C implementation and the fallback for older C++ compilers use the existing expression. The real header regression accepts valid and erased pointers and rejects incompatible layouts, pointer-to-pointer mismatches and scalar inputs. It exited 0.

Both requested translation units compiled with exit 0. The component hashes below are from the final build, with the explicit generic CPU setting in [patch 0216](../xnu/patches/0216-duchamp-arm64-generic-codegen.patch) and the boot-argument reservation fix in [patch 0217](../xnu/patches/0217-duchamp-save-loader-boot-args-address.patch). The full commands and output digests are in `components-compile-result.json` and the symbol check is in `component-symbols.log`.

| ARM64 Mach-O object | Bytes | SHA-256 |
| --- | ---: | --- |
| `memdev.o` | 34,232 | `5dc9e449fc800c3b8447154deed5c68045de85eb3496a03efc36e060eaec44a8` |
| `IOKitBSDInit.cpo` | 338,712 | `6eca192f613c29d6acef8c484383d3f4b7dcb1ddeff2e4ff3d7fb8eeec63653f` |

The first full compile isolated two further source issues. The NFS readlink implementation initializes a `char *` from its aligned `uint64_t` stack buffer. The ARM64 SHA-256 assembly selects obsolete `qN` operands for upstream Clang. [Patch 0215](../xnu/patches/0215-duchamp-clang24-source-compatibility.patch) uses the existing UIO API's `void *` storage type and selects the existing vector-operand syntax for upstream Clang 24. Both original errors are preserved in the run directory.

## Receipts

The run directory is `../../outputs/duchamp-patched-clang-20261117` from the repository root. It contains the baseline Git diff, configuration and build logs, the stock compiler logs and the source-build commands. The [kernel link and QEMU report](DUCHAMP_NEW_XNU_QEMU_BOOT.md) describes how the resulting objects are validated and booted.
