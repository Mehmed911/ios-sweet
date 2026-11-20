# Duchamp libfirehose_kernel build on WSL

The macOS 13.5 source manifest pairs `xnu-8796.141.3` with `libdispatch-1415.140.2` (commit `cdb61e93e803d0093635f356753a9a30c09836db`). The supplied SWEET build-tree reference uses that XNU version. Use the matching Apple release instead of UniXNU's default `libdispatch-1477.100.9` feed. [Apple macOS 13.5 manifest](https://github.com/apple-oss-distributions/distribution-macOS/blob/macos-135/release.json), [UniXNU feeds](https://github.com/UniXNU/UniXNU/blob/main/feeds.toml).

UniXNU compiles the single Apple `src/firehose/firehose_buffer.c` translation unit directly on Linux. The pwn0rz script instead builds it with Xcode as arm64e. The ios-sweet workflow uses pinned dxb and adds plain ARM64 to its firehose target. The matching Apple target specifies kernel mode, no DTrace, the atomic settings, and the Kernel.framework header paths. [UniXNU compile recipe](https://github.com/UniXNU/UniXNU/blob/e2fdae4312d0acc3d8a52bc457101e7918095e6a/scripts/build-firehose.sh), [pwn0rz build script](https://github.com/pwn0rz/xnu-build/blob/main/x.py), [ios-sweet workflow](https://github.com/dipa-studio/ios-sweet/blob/main/.github/workflows/xnu.yml), [Apple target configuration](https://github.com/apple-oss-distributions/libdispatch/blob/libdispatch-1415.140.2/xcodeconfig/libfirehose_kernel.xcconfig).

The [Linux builder](../tools/build-duchamp-firehose.py) uses Clang 21.1.8 with `arm64-apple-macos15.5`, `-mkernel`, `-nostdinc`, and the release configuration definitions. It reads the saved CI 41340697398 exported and installed headers. The pinned UniXNU `TargetConditionals.h` derives target macros from Clang. The installed `kern/debug.h` lacks the kernel `panic` declaration, so the build selects the matching XNU export for that single header. Using the unstripped export root for everything also selects guarded machine headers and prevents the Firehose tracepoint include from obtaining the commpage definition. The builder keeps the installed header order for that part. The Apple Firehose source is unchanged.

```sh
git clone --depth 1 --branch libdispatch-1415.140.2 \
  https://github.com/apple-oss-distributions/libdispatch.git "$DISPATCH_SOURCE"
python3 -B tools/build-duchamp-firehose.py "$DISPATCH_SOURCE" \
  work/ci-41340697398-buildtree/tree \
  ../references/unixnu-core/scripts/linux/TargetConditionals.h "$FIREHOSE_OUT"
```

The output `libfirehose_kernel.a` belongs in the Linux linker's library search path. Its Darwin archive has one nonempty plain ARM64 Mach-O object, `firehose_buffer.o`. The five verified exports cover create, tracepoint reserve, tracepoint flush, configuration validation and merge updates. The explicit external references include XNU allocation, chunk configuration, logd notification, the critical region callbacks, time and thread APIs, and panic. The diagnostic ld64 relink resolved those dependencies using the reference XNU objects.

Two independent output directories produced byte-identical archives.

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| `libfirehose_kernel.a` | 34,392 | `9452c8d39826db46ff2e40c0ad6ed128f95ec78557378a607d0a1e52eb7f9d7f` |
| `firehose_buffer.o` | 33,896 | `e2cb455fd6aa0b653f64da8a7cdea8689355e51375c75f68c967eda3dfb557ab` |

[Commands and exit statuses](../../../outputs/duchamp-linux-firehose-20261117/build-firehose/commands.json), [build manifest](../../../outputs/duchamp-linux-firehose-20261117/build-firehose/verification.json).
