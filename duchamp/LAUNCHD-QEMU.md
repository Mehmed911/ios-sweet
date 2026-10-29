# Original launchd and one C service in QEMU

This test keeps Apple's original iOS 16.5 restore `launchd` and `xpcproxy`
unchanged. It uses the existing Actions 104 kernel and a copy of the tested
dynamic-library HFS RAM root. No phone, USB, UFS, or boot partition is used.
It is a development-kernel experiment, not a complete iOS installation.

## Reproduce

First prepare the dynamic C root described in [DYNAMIC-USERLAND.md](DYNAMIC-USERLAND.md).
The runtime extraction helper now also extracts launchd, xpcproxy, and the
restore image's group/master.passwd files. Existing extraction directories
are preserved; use a fresh output directory:

```sh
python3 tools/prepare-darwin-runtime.py research/darwin-launchd-20F66 \
  --img4 research/dyld-runtime-20F66/096-03566-084.dmg
sh tools/test-sweet-launchd.sh \
  work/ci-104/artifact/kernel.development.sweet \
  work/qemu-multiproc.adt \
  work/userland-dynamic-final/root.hfs \
  research/darwin-launchd-20F66/runtime-root \
  research/darwin-launchd-20F66/runtime-root \
  research/libdmg-hfsplus-build/hfsplus \
  work/launchd-new 180
```

The final output directory must not exist. The duplicated runtime-root
arguments separately identify the original executable/account source and
the libraries used to link the C service.

`launchdsuffix=sweet` selects the static development entry
`/usr/appleinternal/sbin/launchd.sweet`, using the existing source path in
XNU's load_init_program(). It opens console descriptors, checks its PID is
1, and execs `/sbin/launchd` without a fork. This supplies
`DYLD_SHARED_REGION=avoid` while preserving PID 1. It contains no fallback
that starts the service itself.

The original launchd must discover the single RunAtLoad job
`org.sweet.qemu.c-service` in `/System/Library/LaunchDaemons`.
Its C service requires parent PID 1 and asks the kernel for that parent's
executable path with proc_pidpath(), requiring `/sbin/launchd`. It then
checks a RAM-file roundtrip and continues numbered five-second heartbeats.
The job redirects stdout/stderr to the actual devfs console.
It specifies UserName=root, GroupName=wheel and LimitLoadToSessionType=System;
the C program checks real/effective UID 0. Job-key semantics are described in
[Apple's launchd.plist reference](https://github.com/apple-oss-distributions/launchd/blob/main/man/launchd.plist.5);
this test separately verifies their behavior with the supplied iOS binary.
No DYLD variable is put in the job: launchd rejected it in the first service
probe, and the restore runtime successfully loaded without it.

The builder creates private/var directories and var/tmp/etc symlinks, checks
the original Apple file hashes, and re-extracts all installed regular files
to compare their bytes. User IDs/groups come from the restore image; test
password fields are replaced by `*`. No Apple binaries or extracted account
files are committed to Git. launchd retains its embedded __TEXT,__config;
`/System/Library/xpc/launchd.plist` is not assumed to override it.
The HFS directory listing must contain exactly the single expected job file.

## Diagnostics and interpretation

The runner's optional `--snapshot-interval 10` saves decoded frames under
`run/frames/`, in addition to the final `fb.txt`. Each memory dump pauses
the VM's virtual clock and resumes it afterward. These are sampled circular
screens, not a complete serial or syscall trace.

`run/verification.json` requires original-image hashes, the PID 1 exec
marker, launchd's own announcement, the service's PID/parent/path checks,
RAM-file success, increasing heartbeats, and no visible panic.
`no_panic_observed` alone never passes the test.

The first probe reached original launchd and failed with:
`unable to resolve 'mobile': 114 - The specified username does not exist`.
The root-only account fixture was replaced by the source image's account
IDs/groups. The second probe hit the interrupt-duration watchdog while an
external observer dumped live framebuffer memory. That observation was
removed; captures now pause virtual time. Neither failure is counted as a
successful service boot.

## Verified result (2026-10-30)

The final complete wrapper run in `work/launchd-final` exited 0 after 180
host seconds. All 15 checks passed with 14 sampled frames, zero unknown
glyphs, and no visible panic. Original launchd remained PID 1 and the single
root/System C service reported PID 3, PPID 1, UID/EUID 0, parent executable
`/sbin/launchd`, successful RAM-file verification, and continuing heartbeats.
Original xpcproxy was observed spawning the service in the system domain.

The first service probe, `work/launchd-probe-3`, passed its 12 earlier checks
but used the user/501 domain. The final explicit root/System job passed the
stricter checks, including a single process identity. The verifier rejects
the failed original probe; absence of a panic is insufficient.

The original dynamic root remained unchanged (SHA-256
`750fc8ec3e2452a708da00aa078a8f6b65d7f27333c18cba17add0899ea67c91`).
The final service SHA-256 is
`6adbe9d1fb35a1833b273507aeb2b0e9c75450d73274a3410937aa0c495d24de`;
root `491aa78408c423c50e8b59644e416e94b643ed3eb119158d52684af4176c8b3f`;
payload `42f784c42bbf31745502f5e11b2727f8cc2b4365f3b42c2cbaf004c7ffa781a8`.
The existing kernel was reused; no new kernel build or phone test was needed.

Nonfatal messages include a missing MRM cache, a jetsam limit request
returning EINVAL, and unavailable persona lookup. A successful single job
does not prove those facilities or the wider iOS service graph. Production
signing enforcement, SpringBoard, device drivers and MT6897 UFS are outside
this test. The next QEMU experiment is status/stop/restart via original
launchctl.
