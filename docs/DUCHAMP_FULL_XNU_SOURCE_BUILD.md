# Duchamp full XNU source build

Branch `duchamp-bootstrap`, baseline `d91562d`. The dual-RAMDisk working tree is preserved. **The full link and modified-kernel QEMU boot remain blocked.** No new kernel hash, boot log, or PID 1 result is available for the change.

## Toolchain decision

Use the CI-compatible Darwin build for the next complete attempt: Xcode 16.4, macOS SDK 15.5, Apple ld 955.13 as reported by the original CI kernel, the KDK 13.5 build 22G74 path expected by dxb, and `DEVELOPMENT ARM64 SWEET` from the macOS 13.5 XNU sources. The dxb commit is `663906528d1cd5ea8fde7de6f16de73db9511549`. See the [linker analysis](DUCHAMP_XNU_LINKER_ANALYSIS.md) for the complete diagnostic commands and image comparison.

WSL LLD 21.1.8 emits a userspace Mach-O for the controlled static-link probe. An Apple ld64-951.9 Linux port successfully emits a high-address image with the expected segment order and ARM64 thread-state entry. It cannot finish the XNU archive diagnostic in this workspace. `libfirehose_kernel` is missing, and the saved archives do not provide the complete fresh object build and `libcc_kext`. The pinned dxb needs additional Darwin build tooling. The local results establish the missing inputs and linker differences without establishing that Linux can never build the kernel.

## Source and build preparation

- [Local source build wrapper](../tools/build-duchamp-xnu-source.sh) snapshots and hashes the current source and IIG archive. The Darwin stage verifies the inventory, starts in a fresh scratch tree, captures tool versions and a verbose build log, and records the output and its layout, `.LDFLAGS`, file list, aliases and symbol sets with SHA-256 hashes. It creates a new output directory. It can be run on a Mac from the staged snapshot without a commit or push.
- [Shared dxb setup](../tools/prepare-duchamp-xnu-dxb.sh) applies the same final-source staging and plain ARM64 firehose change as the [CI workflow](../.github/workflows/xnu.yml). The pinned checkout and script preparation ran locally. The full Mac build did not run.
- [Kernel layout validator](../tools/duchamp_xnu_link.py) and [payload builder](../tools/qemu_ramroot_var.py) require the actual ARM64 kernel entry, layout, and linked dual-RAMDisk registration. The payload manifest carries the exact validated kernel SHA-256 and entry. No code was injected into a prebuilt kernel.
- The saved local IIG ZIP matches SHA-256 `1d9a9634d0abe7e3f0ddd43b1605bff77a5fb9b2abf734e762cdf96ed83fa7b7`. All 17 definitions and 34 generated files staged successfully. The previous GitHub artifact metadata URL returned HTTP 404 without authentication. The local source recipe uses the saved ZIP, so it does not depend on that URL.

## Reproduction commands

Prepare on this checkout with the saved ZIP. Use an empty destination whose parent already exists.

```sh
bash tools/build-duchamp-xnu-source.sh prepare \
  work/ci-41340697398-buildtree/artifact.zip "$SOURCE_WORKSPACE"
```

Run from that prepared directory on a Mac with the toolchain above and `jq`, `gum`, `xcodes`, `cmake` and `ninja` available to dxb.

```sh
bash "$SOURCE_WORKSPACE/source/tools/build-duchamp-xnu-source.sh" build "$SOURCE_WORKSPACE"
(cd "$SOURCE_WORKSPACE/result" && shasum -a 256 -c build.sha256)
```

The full build is sourced from the recorded snapshot. Independent byte-for-byte comparison requires two successful full builds. The output manifest records what each build actually produced.

Copy the resulting `kernel.development.sweet` and receipts to the local test host. Use that exact kernel for both the service and Mach-O cases. The full [dual-volume integration instructions](DUCHAMP_DUAL_RAMDISK_INTEGRATION.md) identify the existing local service fixture, QEMU ADT, Darwin library root, and HFS+ tools.

```sh
python3 -B tools/duchamp_xnu_link.py "$KERNEL"
python3 -B tools/test-duchamp-readonly-var.py "$OUT/success" \
  --kernel "$KERNEL" --mkfs "$MKFS"
python3 -B tools/test-qemu-ramroot-var.py "$OUT/success/payload.bin"
sh tools/test-duchamp-darwin-ramroot.sh "$KERNEL" "$QEMU_ADT" \
  "$MACHO_ROOT_SEED" "$RUNTIME" "$HFSPLUS" "$OUT/macho"
```

Require the integration logs to show both memory devices, a read-only HFS+ root, the writable `/private/var` mount and alias, console opens, original launchd PID 1, service and syslog activity, raw md0 write-open denial, `EROFS`, `ENOSPC` and a byte-identical guest md0 dump. Run the separate dynamic and static Mach-O probes using the same linked kernel hash. Run the five negative mount/profile cases listed in the integration instructions. The RAM-only QEMU integration uses a storage-free ADT and does not attach a UFS image.

## Local verification

| Check | Result |
| --- | --- |
| Kernel format verifier | 11/11 checks. The reference layout passes inspection. The candidate gate denies the unchanged archive and rejects userspace entry, wrong architecture, damaged commands, inconsistent PC, undefined symbols, overlap, and invalid protections. |
| Packaging and boot preflight | Dual-layout mutations 12/12, single-RAMDisk packager 2/2, archived payload validation 10/10, bootshim preflight passed. Normal dual packaging rejected the archived kernel before it created a package. |
| RAM bounds | 16/16 native ASan/UBSan and 16/16 standalone ARM64 QEMU. |
| Reference full-XNU regressions | 17/17 Mach-O and 74/74 service assertions. Existing boot-image validation passed 13/13 and the regenerated reference image matched the archived bytes. |
| Newly linked dual-RAMDisk QEMU | **Pending.** No candidate was emitted by either link probe. No new payload was accepted for boot. |

Exact commands, exit statuses, tool probes, reference load commands and regression logs are retained in [the verification directory](../../../outputs/duchamp-full-xnu-source-build-20261117). The immediate remaining step is to run the prepared source snapshot on the compatible Mac toolchain and then run all guest checks against its measured SHA-256. No phone access, reboot, flash, slot change, partition write, physical UFS access, Git commit or push was performed.
