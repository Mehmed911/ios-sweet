# Removing and reloading a service in QEMU

This extends the [launchctl lifecycle fixture](LAUNCHCTL-QEMU.md). It uses
unchanged Apple iOS 16.5 launchd/xpcproxy, the pinned **Procursus FOSS
launchctl 1:1.1.1**, and one diagnostic C service. The CLI is not supplied
by Apple. The test operates entirely on a copied RAM root in QEMU.

## Replay

Use the runtime and single-job base image described in LAUNCHCTL-QEMU.md.
Choose a new output directory; previous images are never overwritten:

```sh
sh tools/test-sweet-launchctl.sh \
  work/ci-104/artifact/kernel.development.sweet \
  work/qemu-multiproc.adt \
  work/launchd-final/root.hfs \
  research/launchctl-runtime/runtime-root \
  research/libdmg-hfsplus-build/hfsplus \
  work/launchctl-bootstrap-new 720 bootout-bootstrap
```

The final argument selects a separate controller build with
SWEET_BOOTSTRAP_TEST=1. Omitting it retains the earlier SIGTERM/kickstart
scenario. Both builds use the same target service, runtime and kernel.

## Evidence required

The controller starts as a root child of the original launchd at PID 1.
It waits for the target's readiness file, verifies the actual executable
path, and executes five separate CLI processes:

| Step | CLI arguments | Required observation |
| --- | --- | --- |
| Before | print system/org.sweet.qemu.c-service | exit 0, running, old PID |
| Remove | bootout system/org.sweet.qemu.c-service | exit 0; old PID subsequently reaped / ESRCH |
| Missing | print system/org.sweet.qemu.c-service | after five seconds, exit 113 and the expected missing-service message |
| Reload | bootstrap system /System/Library/LaunchDaemons/org.sweet.qemu.c-service.plist | exit 0 |
| After | print system/org.sweet.qemu.c-service | exit 0, running with a different positive PID |

bootout receives the exact service target. It never receives the bare
system domain. Removing the registration must leave the plist readable.
The host also compares the saved guest plist's SHA-256 with its bytes in
the base image and checks RunAtLoad=true / KeepAlive=false.

The new instance must publish its own PID after identity, SIGTERM policy
and RAM-file checks. The stale PID file alone cannot satisfy readiness.
The controller verifies the new executable path and final running state,
then keeps checking the process while both daemons produce heartbeats.
No direct stop/start signal is sent to the target by the controller.

The expected missing-service result is based on the pinned source:
[bootstrap.c](https://github.com/ProcursusTeam/launchctl/blob/v1.1.1/bootstrap.c)
implements load/unload requests;
[xpc_private.h](https://github.com/ProcursusTeam/launchctl/blob/v1.1.1/xpc_private.h)
defines ENOSERVICE=113;
[launchctl.c](https://github.com/ProcursusTeam/launchctl/blob/v1.1.1/launchctl.c)
and [xpc_helper.c](https://github.com/ProcursusTeam/launchctl/blob/v1.1.1/xpc_helper.c)
format the missing service and system domain. The controller checks the
exact wait status 0x00007100, so a crash or unrelated CLI error cannot count
as a successful removal. The host checks the complete error text too.

The runner stops on a visible panic, controller failure, or the second
controller heartbeat after CONTROL PASS, with a 720-host-second limit.
It exports the guest RAM disk while QEMU is stopped. The verifier then
extracts the trace, every raw CLI output, readiness file, plist and original
executables. It also inspects the sampled framebuffer for both target
instances and their subsequent heartbeats.

Recheck the saved image without booting again:

```sh
python3 tools/verify-sweet-launchctl.py work/launchctl-bootstrap-new \
  --hfsplus research/libdmg-hfsplus-build/hfsplus --scenario bootout-bootstrap
```

The result is run/verification.json; raw guest files are under guest/.
This tests one service under the development kernel. Phone hardware,
USB, UFS, boot partitions and full iOS are outside this experiment.

## Verified result (2026-10-30)

`work/launchctl-bootstrap` exited 0 with **27/27 checks passing** after
**399.932 host seconds**. The runner stopped at the second controller
heartbeat, before its 720-second limit. There were 31 sampled frames,
zero unknown glyphs and no visible panic.

The controller was PID 3, with parent PID 1 /sbin/launchd. The first print
showed target PID 4 running. bootout exited 0 and PID 4 was reaped. After
the five-second gap, print exited 113 with exactly:

```text
Could not find service "org.sweet.qemu.c-service" in domain for system
```

bootstrap then exited 0. The readiness file changed to 9, and the final
print showed PID 9 running. Both target and controller produced subsequent
heartbeats. The saved guest plist was byte-identical to the base, with
SHA-256 `004e41dbd0bc0d0f1ef88a7ee73c6ae228c55a5e7d8728704289dc244380083c`.
The target binary also retained the previous lifecycle test's exact bytes.
Original Apple launchd/xpcproxy and the pinned Procursus CLI hashes passed.

| Artifact | SHA-256 |
| --- | --- |
| Target | `465d9bed7e2d6765c121d4cb5f330cd123b48ab9f387c3a5feaceb171bd4677f` |
| Controller | `ef31d135fdf0120e930b77f7c34724a5cb44589ce8bed7b75d8194ee2f3c0bd8` |
| Input root | `949814247b6e88a4d466518d0dc88bdce01cd13066e9fb7120590afc87585b58` |
| Payload | `fe12ca6fd72cf90be45a82a9f807bc4147c46115e9a996ccaa761b9bb575d38b` |
| Exported guest root | `d2bbb6a6910f100fac9bff93a7c1f646f27fe0c63451ba8fa3d2a8cd951b51e4` |

The unchanged Actions 104 kernel was reused, SHA-256
`82fc8fe1391bea90bcce9ed2d4e8a2ff8204667f6785857873717564ec9331c9`.
The initial base root remained
`491aa78408c423c50e8b59644e416e94b643ed3eb119158d52684af4176c8b3f`.
No new kernel CI build was needed. All five raw CLI outputs, trace and
readiness file are preserved in `work/launchctl-bootstrap/guest/`;
the complete report is `work/launchctl-bootstrap/run/verification.json`.

Both controller modes passed arm64 C syntax checks with warnings treated
as errors; the shell and Python checks passed too. Rechecking the previous
SIGTERM/kickstart saved guest still passed 22 checks, while the earlier
SIGTERM-ignored failure remained rejected even though it had no panic.
