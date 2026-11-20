# Duchamp dual HFS+ RAMDisks in XNU

Baseline `d91562d` on `duchamp-bootstrap`. The XNU source integration, host packager, and guest verification runner are in the working tree. The two changed XNU translation units compiled as ARM64 Mach-O. A complete source-linked kernel and the end-to-end dual-RAMDisk boot on it remain pending. The archived dual-RAMDisk boot used the previous binary overlay.

## Source and mount sequence

- [Kernel registration](../duchamp/xnu/dual_ramdisk_init.inc) reads two 16-byte little-endian address and size records under `/chosen/memory-map`. `RAMDisk` describes `md0` and `DuchampDataRAMDisk` describes `md1`. The mode requires `duchamp_dual_ramdisk=1`, `rd=md0`, and a read-only root policy. A missing or malformed record, an invalid range, or an occupied device number aborts this boot before either normal root selection or launchd.
- [Range validation](../duchamp/xnu/dual_ramdisk_bounds.h) uses the ARM64 kernelcache physical end, the boot argument and ADT positions, and the actual `physBase`, `memSize`, and `topOfKernelData` supplied to XNU. Each volume is fully backed, aligned to 16 KiB, between 1 MiB and 64 MiB, and within the reserved boot-data tail. The producer places root, var, and the ADT consecutively. In XNU `osfmk/arm64/arm_vm_init.c`, `arm_vm_physmap_init` maps the tail from the kernel end to `topOfKernelData`, and `avail_start` begins at `topOfKernelData`.
- The [source stager](../tools/stage-duchamp-dual-ramdisk.py) wires `iokit/bsddev/IOKitBSDInit.cpp::IOFindBSDRoot` to the kernel registration. In `bsd/dev/memdev.c` it adds an internal flags-aware registration entry while retaining the original `mdevadd` API and ordinary RAMDisk handling. The existing read-only open check now applies to dual-mode `md0`. The raw write path, buffered block strategy, and writability ioctl respect the same flag. The default mode of `md1` allows writes.
- The existing BSD devfs patch keeps `/dev/console` and creates the memory-device nodes. After mounting the HFS+ root read-only, the PID 1 [bootstrap](../tools/sweet-launchd-bootstrap.S) runs [var preparation](../tools/duchamp-var-prepare.c). Preparation checks the root mount and raw `md0`, mounts `/dev/md1` at `/private/var` with `nosuid,nodev,noatime`, checks directory permissions and the `/var -> /private/var` link, and creates a witness under `/var/tmp`. The bootstrap execs the original `/sbin/launchd` as PID 1 after the helper exits successfully. A failed helper stops this exec. All changes within `md1` are session-local.
- The [XNU workflow](../.github/workflows/xnu.yml) stages the sources via the final dxb patch pass and checks that the linked SWEET kernel defines `_duchamp_dual_ramdisk_init`. The [payload builder](../tools/qemu_ramroot_var.py) requires that symbol for normal packaging and does no binary patching. It derives addresses from the Mach-O and base ADT, then emits `payload.bin`, `ramdisks.adt`, and `layout.json` with input and output digests. The [integration runner](../tools/test-duchamp-readonly-var.py) builds fresh copies of both volumes, links the probes, and records commands, exits, input hashes, guest witnesses, and seed comparisons.

## Build and run

1. Build the working tree with the macOS steps in [xnu.yml](../.github/workflows/xnu.yml) using macOS 13.5 sources, `DEVELOPMENT`, and `SWEET`. The workflow uses Xcode 16.4, the matching KDK, its pinned dxb revision, and the pinned IIG inputs. It produces `out/kernel.development.sweet` and the kernel checksum. A usable copy of the pinned IIG input archive is a build prerequisite.
2. Run the following commands from the checkout under Linux/WSL with the resulting kernel, QEMU, Clang/LLD, `llvm-nm`, and the formatter. The runner takes the existing verified services seed and its manifest. It also takes the HFS+ editor, storage-free base ADT, and locally supplied matching Darwin library root.

```sh
python3 -B tools/test-duchamp-readonly-var.py "$OUT/success" \
  --kernel "$KERNEL" --mkfs "$MKFS" --adt "$QEMU_ADT" \
  --service-fixture "$SERVICE_FIXTURE" --hfs-tool "$HFSPLUS" --runtime "$RUNTIME"

for case in missing-md1 failed-mount missing-mountpoint bad-permissions bad-alias; do
  python3 -B tools/test-duchamp-readonly-var.py "$OUT/$case" \
    --kernel "$KERNEL" --mkfs "$MKFS" --adt "$QEMU_ADT" \
    --service-fixture "$SERVICE_FIXTURE" --hfs-tool "$HFSPLUS" --runtime "$RUNTIME" \
    --case "$case" || exit
done

python3 -B tools/test-qemu-ramroot-var.py "$OUT/success/payload.bin"
sh tools/test-duchamp-darwin-ramroot.sh "$KERNEL" "$QEMU_ADT" \
  "$MACHO_ROOT_SEED" "$RUNTIME" "$HFSPLUS" "$OUT/macho"
```

`--prepare-only` produces the volumes and validated package without running QEMU. Packaging identical kernel, ADT and HFS+ input bytes was byte-for-byte reproducible. Formatting fresh HFS+ inputs uses the host tools' timestamps and volume metadata. Byte-for-byte reproducibility of freshly formatted volumes or independently linked full kernels has not been verified.

## Results and recorded bytes

The [test directory](../../../outputs/duchamp-dual-ramdisk-integration-20261116/) contains the baseline Git patch and status, exact command records, logs, and the layout manifest. The archived recovery image and service seed passed their original SHA-256 checks after the changes.

| Test | Result |
| --- | --- |
| Source staging and repeat staging against saved CI XNU files | Exit 0. The staged C and C++ compiled to ARM64 Mach-O objects, exit 0. The C object defines the registration entry and the C++ object references it. The local compile reused cached generated headers and Linux-Clang substitutions. |
| Native ASan/UBSan and freestanding ARM64 QEMU bound checks | 16/16 on each, exit 0. Includes overlapping ranges, truncation and overflow, zero and oversized lengths, misalignment, and an alternate RAM origin. |
| Host dual-volume validation and QEMU image-loader preflight | 12/12 mutation tests, exit 0. Fixed-input repack matched byte-for-byte. Both volume hashes matched at their load addresses and the layout relocated to a second RAM origin. The regular packager rejected the archived kernel, and the host verifier rejected md1's absence except in explicit negative-test mode. |
| Existing full-XNU regressions, archived CI kernel | Mach-O 17/17 and service lifecycle 74/74, exit 0. The Mach-O run verified a dynamic child exit of 0, a static child exit of 42, and an unchanged read-only root. |
| Existing packaging and bootshim regressions | Packaging 10/10 and single-RAMDisk packager 2/2, exit 0. Bootshim, handoff, XNU return, capture, and payload preflight tests passed for the baseline and the dual-layout host fixture. Existing boot-image validation passed 13/13, exit 0. Its freshly packaged 64 MiB image matched the archive byte for byte. |
| Newly compiled witness | ARM64 Mach-O compile and link exited 0. Guest verification of the new raw md0 write-open rejection needs the source-linked kernel. |
| Complete source-built dual-volume XNU, success and negative cases | Pending. WSL has no Xcode/KDK toolchain. The available `ld64.lld` reported that `-segment_order` is unimplemented. No guest launchd, md0 integrity or md1 mount result is claimed for the new kernel. |

The host fixture used the existing volumes and untouched archived CI kernel solely for layout checks. The fixture payload was never booted.

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| Host fixture md0 | 33,554,432 | `62e3bf96ed680c929a5d6446882cf6367fe012ba8ca381f5c482e4b6eaaaf033` |
| Host fixture md1 | 33,554,432 | `97adfb7c500cea1f4c6c796bed8a2ad2b3f801a7a4b347ce5cb8ef33afac2748` |
| Host fixture ADT | 4,336 | `0d9bfa06e0c8afd70910526007aa28b4a20fb507d2918a454a20eceed312596a` |
| Host fixture payload | 83,824,400 | `18a50254e17b030d733b26eeade8eb7bfa775db6dffce057d8c787e674016837` |
| Preserved single-root Android-format boot image | 67,108,864 | `545112503a5e9052db709572cc840758619f2b7e27c9aa58c0af2a3924a8f6a8` |

## MT6897 device requirements

The [saved Duchamp DTB inventory](../devices/duchamp/hardware.json) records DRAM at `0x40000000` with size `0x300000000` and 56 reserved-memory nodes. The QEMU profile uses its own 512 MiB window. The two host fixture volumes fall inside the broad DTB DRAM interval, and neither intersects a decoded reserved-memory `reg` range in the saved inventory. This comparison does not establish what LK leaves available at XNU entry. A Duchamp producer must verify the free interval for that boot, exclude firmware, FDT, framebuffer, and all live reservations, and reserve both volumes before XNU's allocator starts. It must establish that the complete transport fits the actual boot path, since the raw QEMU fixture payload is larger than the archived 64 MiB image.

Phone-side packaging, resource ownership and physical UFS are outside the proof from these tests. No phone operation, partition change, or slot change was performed.
