# Duchamp read-only root with writable RAM-backed var

This QEMU profile keeps the 32 MiB HFS+ system volume read-only and mounts a separately formatted 32 MiB HFS+ volume on `/private/var`. It uses XNU's existing BSD memory devices and HFS+ mount support. Both byte ranges come from the QEMU loader's initial RAM image. The phone, Android A recovery path and physical UFS are outside this profile.

## Layout

| Path | Source and permissions |
| --- | --- |
| `/` | HFS+ on `md0`, 32 MiB at guest physical `0x1c2568000`. `rd=md0 rootrw=0` selects the root device and keeps its VFS mount read-only. It contains the original executables, configuration under `/private/etc`, job plists and the bootstrap. |
| `/private/var` | HFS+ on `md1`, 32 MiB at guest physical `0x1c4568000`. The mount point is an existing root-owned directory with mode `0755`. The mount uses `nosuid,nodev,noatime`. |
| `/var`, `/tmp` | Root symlinks to `/private/var` and `/private/var/tmp`. The bootstrap verifies the `/var` target and mounted vnode identity. It requires root-owned mode `1777` on `/private/var/tmp`. |
| `/dev`, `/etc` | `/dev` exists in the image before boot so devfs can mount over it and expose console and memory devices. `/etc` resolves to read-only `/private/etc`. |

The writable volume starts with empty state directories `tmp`, `run`, `log`, `db`, `root`, `mobile` and `empty`. The fixture also seeds `log/com.apple.xpc.launchd`, `db/com.apple.xpc.launchd` and `db/launchd.db`. Paths underneath the read-only mount point are covered by the new HFS+ mount.

## Service path audit

| Process or subsystem | Writable paths observed in the fixture or referenced by the inspected binary |
| --- | --- |
| Original `launchd` and `xpcproxy` | `/private/var/tmp/com.apple.launchd.XXXXXXXXXX`, `/private/var/db/com.apple.xpc.launchd`, `/private/var/db/launchd.db`, `/private/var/log/com.apple.xpc.launchd`, `/var/run/utmpx` and mobile state beneath `/var/mobile`. The console and `/dev/null` are devfs endpoints. |
| Original `notifyd` | Configured trace `/private/var/tmp/notifyd-debug.log`. Binary references include `/var/run/notifyd_%u.status`, `/var/run/notifyd_jetsam.log` and `/var/log/notifyd.log`. The test exercises the notification-center **Mach** endpoint. |
| Original `syslogd` | `/var/run/syslog.pid`, `/private/var/tmp/syslogd-debug.log` and configured `/private/var/log/sweet-asl.log`. Retained path strings include `/var/run/lockdown/syslog.sock` and default ASL and crash log paths under `/var/log` and `/var/mobile`. The fixture exercises `com.apple.system.logger` via native Mach IPC. |
| Diagnostic jobs | `/private/var/tmp/launchctl-control.log`, per-job `launchctl-*.txt` state reports, `ipc-asl*.log`, PID/completion files and ASL/notify gate files. The standalone C service variant also uses `sweet-launchd-service.data` and `sweet-service.pid` there. |

The audit covers the supplied fixture's actual outputs, job arguments and the binaries' additional path strings. The latter are leads for wider service profiles. They do not show that each optional path was opened in this run. [Service controller](../tools/sweet-launchctl-control.c), [syslogd configuration](../duchamp/syslogd-asl.conf), [original fixture](../duchamp/PHONE-SERVICES-BATCH.md)

## Mount sequence and implementation

1. The host copies the pinned services image and prepares `/dev`. It formats a fresh regular file for the writable volume with the host `mkfs.hfsplus`, seeds its directories and verifies it fits the existing 512 MiB guest RAM window. The payload binds the two non-overlapping file and memory ranges to ADT `RAMDisk` and `DuchampQemuVar`.
2. XNU's original `IOFindBSDRoot()` registers the root memory device. The QEMU-only overlay wraps that existing call in the pinned CI kernel and registers `md1` with the existing memory-device driver when the ADT reservation matches the range immediately after the root. The overlay lives outside production kernel builds and phone packaging. The pinned kernel's single original branch and its empty executable padding are checked before creating the private kernel copy. [XNU memory devices](https://github.com/apple-oss-distributions/xnu/blob/xnu-8796.121.2/bsd/dev/memdev.c), [memory-device registration](../duchamp/xnu/ramroot_var_register.c), [QEMU packager](../tools/qemu_ramroot_var.py)
3. The optional static PID 1 bootstrap forks the preflight executable. It verifies the read-only root and `/var` link, calls Darwin `mount("hfs", ...)` on `/dev/md1`, and verifies the distinct writable mount with `statfs()`. It checks `EROFS`, fills a scratch file to `ENOSPC`, deletes it, and creates an exclusive witness file via `/var/tmp` that it reads back via `/private/var/tmp`. The witness records what was observed in that boot. A nonzero result stops before the original launchd exec. [Bootstrap](../tools/sweet-launchd-bootstrap.S), [preflight](../tools/duchamp-var-prepare.c), [HFS mount ABI](https://github.com/apple-oss-distributions/hfs/blob/main/core/hfs_mount.h)
4. PID 1 reaps the preflight child, then execs the unchanged original restore `/sbin/launchd` with the existing dynamic linker environment. The verifier reads executable and job hashes from the stopped guest root dump, and runtime logs and state from the separate stopped guest var dump. Each QEMU invocation initializes RAM from the original payload. Captured dumps are evidence files. [QEMU runner](../tools/qemu-sweet.py), [service verifier](../tools/verify-sweet-syslogd.py), [integration runner](../tools/test-duchamp-readonly-var.py)

## Scope and next requirements

The layout is pinned to one old CI kernel hash and its storage-free QEMU ADT. The overlay exercises the real XNU code path, with no full kernel rebuild this run. A maintained kernel integration would stage the bounded second memory-device registration as normal source and run the same tests on a freshly built artifact. The service fixture uses original restore binaries and standalone libraries under the development kernel's policy. It does not cover an entire Darwin service graph, general IPC clients, graphics or production signing. Widening the fixture will require explicit treatment of each additional daemon's writable directories, bootstrap domain, user/group, launch dependencies and shared-cache requirements.

## Test results

| Test | Result |
| --- | --- |
| Existing full XNU Mach-O and read-only HFS+ baseline | **17/17**, exit 0, **94.798 s**. [Guest report](../../../outputs/duchamp-readonly-var-20261116/baseline-macho/run/verification.json) |
| Existing full XNU services baseline, writable root | **74/74**, exit 0, **71.440 s**. [Guest report](../../../outputs/duchamp-readonly-var-20261116/baseline-services/qemu-proof/run/verification.json) |
| Full XNU read-only root and writable var | **10/10 integration checks** plus **74/74 service checks**, exit 0, **71.486 s**. Original launchd remained PID 1. `syslogd` PID 5 and `notifyd` PID 8 served probes 6 and 7. Syslogd wrote six verified ASL records to the writable volume. Both diagnostic clients exited 0, and launchctl observed each stopped after one run while the two daemons remained running. [Integration report](../../../outputs/duchamp-readonly-var-20261116/split-services-verified/verification.json), [service report](../../../outputs/duchamp-readonly-var-20261116/split-services-verified/service-verification.json) |
| Root write and capacity error paths | The guest reported `EROFS=30` on root create. The data volume reported `ENOSPC=28` after **32,702,464 bytes** of scratch writes, recovered space after cleanup, then created the witness and service logs. The stopped root dump matched the input image byte for byte. [Same-boot witness](../../../outputs/duchamp-readonly-var-20261116/split-services-verified/witness.txt) |
| Guest fail-closed cases | Missing `/private/var` and absent `md1` produced separate `ENOENT=2` diagnostics. A `0700` tmp directory and a `/var` link to `/private/etc` were rejected. All four retained devfs, preserved the root dump, and stopped before the original launchd exec. [Missing mount point](../../../outputs/duchamp-readonly-var-20261116/validated-missing-mountpoint/verification.json), [mount failure](../../../outputs/duchamp-readonly-var-20261116/validated-missing-md1/verification.json), [permissions](../../../outputs/duchamp-readonly-var-20261116/validated-bad-permissions/verification.json), [alias](../../../outputs/duchamp-readonly-var-20261116/validated-bad-alias/verification.json) |
| Packaging and preservation | **7/7** dual-image layout cases, **10/10** historical services packaging cases and **9/9** native read-only evidence checks. Fixed-input repacks matched byte for byte. The original unmodified bootstrap rebuild and saved phone image digests matched. [Dual-image layout tests](../tools/test-qemu-ramroot-var.py) |
| Fresh QEMU boot using the exact same earlier dual-volume payload | The input var seed contained no witness. The next guest recreated the witness with an exclusive create, and the read-only root dump matched again. The previous data dump was never used as an input. [Dump comparison command and exit status](../../../outputs/duchamp-readonly-var-20261116/same-seed-reboot-dump-check.command.json) |

One early host authoring attempt failed in the old HFS utility's delete path and was replaced by formatting a clean data volume. An initial guest run on the Windows shared filesystem reached launchd but timed out before the service assertions. The Linux-local runner moved frequent QEMU writes off that shared filesystem. A following run passed the 74 services assertions but missed early lines in the circular screen capture. The final runner verifies those early checks from the same boot's exclusive var witness file.

| SHA-256 artifact | Digest |
| --- | --- |
| Successful dual RAM payload | `42acd96f666c9e5f58a1dad02df4aff645a4ae73dfd6dd74a6e7838f2afd7ed0` |
| Read-only root and post-run root dump | `62e3bf96ed680c929a5d6446882cf6367fe012ba8ca381f5c482e4b6eaaaf033` |
| Writable var seed before boot | `97adfb7c500cea1f4c6c796bed8a2ad2b3f801a7a4b347ce5cb8ef33afac2748` |
| Writable var after services ran | `92c8e4502de41da83f1cc43a7b4fcf0baaa0ce56674e1800fabec9b21ccbfa01` |
| Derived QEMU kernel | `ace24ed3338d88abaf66e126b746169a930a5a4104196a65588734d50b22cf8d` |

## Reproduce

Use the existing local runtime inputs from the archived 74-check services fixture and a host HFS+ formatter. This run extracted the Ubuntu `hfsprogs` 540.1.linux3-6build1 package into the private output directory without installing it. The archive SHA-256 is `b00c8ffa61541c8809a637ff080afee28836440730c1b192b6ca5a266f6948e6`.

```sh
python3 -B tools/test-duchamp-readonly-var.py /path/to/new-output \
  --mkfs /path/to/mkfs.hfsplus
```

The [private receipts directory](../../../outputs/duchamp-readonly-var-20261116) contains the baseline Git patch, untracked source archive and test manifest. The per-case `commands.json` records exact command lines, exit codes and logs.
