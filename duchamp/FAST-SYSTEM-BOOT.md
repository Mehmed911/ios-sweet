# Faster QEMU system boot validation

The current XNU kernel passes the original Apple-service grouped test in
a Linux-local RAM-root workspace: **72/72 checks in 86.819 host seconds**,
using QEMU's default clock. No phone, USB, physical UFS or boot partition
is accessed. SpringBoard and complete iOS readiness remain unverified.

## Host-side change

`tools/test-duchamp-system-native.ps1` copies the selected kernel, an already
verified RAM-root fixture and the small tool closure into a new Ubuntu
`/tmp/duchamp-system-*` directory through Windows' WSL UNC interface.
Frequent QEMU trace writes, framebuffer captures and HFS extraction run
on Linux's filesystem. Results are copied back after the test. Both copies
are retained; existing output is refused and original inputs are hash checked.

This avoids the high-volume trace/snapshot workload on `/mnt/c`.
Exploratory processes there were observed blocked in `p9_client_rpc`,
including QEMU worker threads. Interrupted service runs are **not passes**.
The user authorized WSL restart for cleanup. Test tools never restart WSL.

The Python runner accepts an explicit kernel hash. The preferences verifier
still defaults to its original Actions-104 kernel pin for historical replays.
The reference root, compiled probes and frozen source snapshot are reused
byte-for-byte; original Apple executables/libraries remain unchanged.

## Actual results (2026-10-31)

Kernel source: `f6dfc1e077bd196288d99d2250adfbd0b313e7b0`, from successful
[CI 41147308270](https://github.com/Mehmed911/ios-sweet/actions/runs/41147308270).
Kernel SHA256:
`f86bd430b9fdb58d93c0f38d2009b71a7d1b5f15107ea9656c045c5a2eea99ca`.
No new kernel compilation is required for this host-side change.

| Configuration | Result | Scope |
|---|---|---|
| Default clock, read-only UFS diagnostic root | 20/20, 77.515 s | Actual virtual UFS/HFS+ and diagnostic PID1 |
| `icount shift=0`, same kernel/root/payload | 20/20, 32.237 s | Experimental virtual time; about 2.4x in this pair |
| `icount shift=4`, backend selftest fixture | 24/24, 39.414 s | Different fixture, includes RAM backend/table models |
| Linux-local workspace, default clock, Apple services | 72/72, 86.819 s | Grouped preferences/notification/restart fixture; 17 frames |
| Python native-workspace replay after WSL restart | 72/72, 86.674 s | Same root/probes, default clock; all six wrapper checks pass |

The last row also passes six wrapper preservation/exit checks and matching
Windows-to-Linux source/input receipts. All 113 installed-file hash checks
pass. Original `launchd` runs as PID1, with `notifyd`, `cfprefsd`, Foundation
clients and ten real `launchctl` calls. Four ordered preference phases,
reader restart and daemon restart recovery pass. The fixture retains its
explicit notification and chroot-isolation semantics; see
[CFPREFS-BATCH-QEMU.md](CFPREFS-BATCH-QEMU.md).

The earlier Actions-104 grouped run took 1691.019 host seconds with the same
initial root and compiled probes. The new total is about 19.5x shorter.
This historical comparison uses a different kernel and host workload;
it is not a controlled hardware benchmark or a guaranteed speedup.

Instruction-count timing is optional and **not selected** for the verified
Apple-service result. Its larger service experiments were interrupted during
the filesystem investigation. Only the short diagnostics above are established
for that mode. The default clock stays unchanged. See QEMU's
[icount documentation](https://github.com/qemu/qemu/blob/v10.2.1/docs/devel/tcg-icount.rst).

Evidence under the Git-ignored `research/fast-boot/` directory:

- `system-native-unc-v1/run/verification.json`: 72 checks and 113 hashes.
- `system-native-unc-v1/verification.json`: six wrapper checks and pins.
- `system-native-unc-v1/native-workspace.json`: source/input preservation.
- `system-native-python-v2/verification.json`: successful Linux-workspace replay.
- `default-v1`, `icount0-v1`, `icount4-backends-v1`: short diagnostic reports.
- `final-verification.json`: all five positive reports, current source hashes,
  five original saved boot/FDT/firmware hashes and user-edit preservation.

## Reproduce from Windows

Use saved local files; Apple artifacts are not included or downloaded.
From the repository directory, select a fresh output:

```powershell
./tools/test-duchamp-system-native.ps1 `
  -Kernel research/mt6897-policy/kernel-ci/kernel.development.sweet `
  -KernelSha256 f86bd430b9fdb58d93c0f38d2009b71a7d1b5f15107ea9656c045c5a2eea99ca `
  -RootSha256 89388d378c8d2fc66cf942d3c60647ad0579ebb29df629903a7bad0c44469a21 `
  -Reference work/launchctl-cfprefs-batch-v2 `
  -Adt work/qemu-multiproc.adt `
  -Hfsplus research/libdmg-hfsplus-build/hfsplus `
  -Output research/system-native-new -Seconds 900
```

A Linux-native checkout can use the Python runner directly. Its
`--native-workspace` option copies inputs to a separate Linux workspace.
The Windows launcher avoids Linux-side traversal of a stalled `/mnt/c` mount.

Remaining physical milestones include MT6897 interrupts/timer/scheduler
beyond early checkpoints, firmware/resource ownership, DMA/UFS and
Mali/display/input. A QEMU RAM-root result does not close these requirements
or authorize a phone experiment.
