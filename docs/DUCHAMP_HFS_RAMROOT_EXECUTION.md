# Duchamp read-only HFS+ RAM-root execution

**17/17 checks passed in full XNU on ARM64 QEMU.** The guest mounted a 32 MiB HFS+ RAM root, loaded a newly compiled 0BSD ARM64 executable through the original restore dyld, and execed a separate 0BSD static ARM64 child from the root. The guest ran for 93.376 host seconds and reached the static PID 1 harness's post-exit heartbeat. The [userspace audit](DUCHAMP_DARWIN_USERLAND_STATUS.md) describes the kernel paths and the scope of prior graphical work.

## Build and boot

| Source | Change |
| --- | --- |
| [HFS builder](../tools/build-dynamic-root.py) | Optional pre-created and verified `/dev` for devfs on a read-only root. Optional additional guest files use the same extraction and byte comparison as the runtime files. The caller's base HFS+ image stays intact. |
| [Dynamic C](../tools/duchamp-ramroot-userland.c) | Compiles for plain ARM64 iOS, uses `LC_MAIN`, `LC_LOAD_DYLINKER` and libSystem, then exercises `statfs`, directory enumeration, file reads, private file mappings, Mach messages and fork/exec/wait. |
| [Static ARM64 child](../tools/duchamp-ramroot-static.S) | Reuses `mkinit.py` to build an ad-hoc signed `LC_UNIXTHREAD` executable with no dyld or library dependency. It writes its own entry marker and exits with status 42. |
| [Guest runner](../tools/test-duchamp-darwin-ramroot.sh), [evidence verifier](../tools/verify-duchamp-darwin-ramroot.py), [native tests](../tools/test-verify-duchamp-darwin-ramroot.py) | Build and verify the two programs, mount only the embedded `md0` root with `rootrw=0`, boot the pinned kernel, and capture screen evidence and a post-run RAM-disk dump. |

The host authored a new image from the saved base and round-tripped 41 installed files, including 37 audited standalone runtime files. The first run used a base without `/dev`. Its snapshot showed RAM-root mount followed by `DEV DIRECTORY FAILED`, `DEVFS MOUNT FAILED` and `PID1 CONSOLE OPEN FAILED`. The runner exited 1. The successful run pre-created `/dev` in the copied image and booted at the same `rd=md0 rootrw=0` setting. No kernel or bootshim change was needed.

## Execution evidence

The verifier checks each marker against the captured guest console, and independently inspects the generated Mach-O load commands, ADT and RAM disk. These lines are from the [final decoded guest framebuffer](../../../outputs/duchamp-darwin-ramroot-20261116/guest-devfs/run/fb.txt).

```text
SWEET EARLY 190: DEVFS CONSOLE READY
SWEET EARLY 185: PID1 CONSOLE OPEN OK
SWEET dynamic init: starting C program via execve
RAMROOT USER: dynamic pid=2 ppid=1 images=37 libSystem=1
RAMROOT USER: HFS root readonly source=root_device flags=0400d001
RAMROOT USER: HFS directory fixture static and init present
RAMROOT USER: HFS bytes=38 EOF private VM and EINVAL verified
RAMROOT USER: ENOTDIR=20 ENOENT=2 EROFS=30 verified
RAMROOT USER: Mach loopback id=391 payload=44554348
RAMROOT STATIC: entered LC_UNIXTHREAD child
RAMROOT USER: static child pid=3 exit=42 wait=2a00
RAMROOT USER: PASS dynamic pid=2
SWEET dynamic init: C child exit 0 verified
SWEET dynamic init: still alive
```

The VM test maps the fixture privately, grants write permission to that private mapping, mutates it, unmaps it, and verifies the original file bytes and EOF. The invalid mapping offset returns `EINVAL`. The mount flags identify an HFS root mounted read-only and a create attempt returns `EROFS`. The guest's 32 MiB RAM-disk dump remains identical to the input, including filesystem metadata. The load-command and PID evidence distinguish the static child from the child that loads dyld and libSystem.

## Bounds and reproduction

The final payload's last file-backed segment occupies exactly 33,554,432 bytes at physical `0x1c2568000`. It fits the payload RAM window and matches the unique `/chosen/memory-map/RAMDisk` property byte for byte. Building the payload twice from the same kernel, ADT, arguments and finalized HFS+ input produced identical bytes. Fresh filesystem authoring can change HFS catalogue timestamps because the pinned host HFS tool uses the wall clock. The reproducibility result is for packaging from the fixed image. [HFS authoring source](https://github.com/planetbeing/libdmg-hfsplus/blob/7ac55ec64c96f7800d9818ce64c79670e7f02b67/hfs/catalog.c#L942-L1068)

| Artifact | SHA-256 |
| --- | --- |
| Read-only HFS+ root and post-run RAM-disk dump | `bbd5165c4d9cfc4a197a16b796a8c6327ff60f357716c01ae1f4e646d4f5810f` |
| QEMU payload and repeat package | `7cba7fa5ec87469d7ace48adec061f6f09bf302975f78e60bff669a027956d9f` |
| Dynamic C executable | `47b460db60885ebf72b111dc96c3bc69d56a55683e811097aa583eb22a347870` |
| Static executable | `487e09e3b1b1ac20b2c7d3f57f24dfd9345d8473cb19cf6ddb1259975934cf54` |
| Preserved historical phone services boot image | `545112503a5e9052db709572cc840758619f2b7e27c9aa58c0af2a3924a8f6a8` |

Run from the repository on WSL with the existing inputs and a new output directory.

```sh
sh tools/test-duchamp-darwin-ramroot.sh \
  work/ci-41543710742-kernel/artifact/kernel.development.sweet \
  research/mt6897-boot/bsd-service-split-ci41543710742-qemu-authorized.adt \
  work/qemu-rootvnode-98/root-with-launchd.hfs \
  research/dyld-runtime-20F66/runtime-root \
  research/libdmg-hfsplus-build/hfsplus /path/to/new-guest-output
```

## Test results

| Run | Result |
| --- | --- |
| Full XNU, read-only HFS+ and genuine C/static binaries | **17/17**, exit 0. [Guest verification](../../../outputs/duchamp-darwin-ramroot-20261116/guest-devfs/run/verification.json) |
| Full XNU, existing writable HFS+ services fixture | **74/74**, exit 0 in **71.438 s**. The original launchd, notifyd and syslogd passed the existing lifecycle and client checks. [Service verification](../../../outputs/duchamp-darwin-ramroot-20261116/services-replay/qemu-proof/run/verification.json) |
| Native host | **9/9** RAM-root evidence verifier cases on the successful payload, **10/10** preserved services packaging cases, successful C syntax check, and matching archived image digests. Running the HFS builder with its original options still installed and read back all 39 original entries. |
| Native ASan/UBSan and standalone ARM64 QEMU | **98/98** UFS handoff tests in each environment. This rechecks the existing fail-closed policy. |

Both full-XNU runs used the pinned CI kernel without rebuilding it. Exact commands, exit codes, failed first guest, successful guest and host checks are in [the receipt directory](../../../outputs/duchamp-darwin-ramroot-20261116). These runs attached no UFS device and performed no physical-device operations.
