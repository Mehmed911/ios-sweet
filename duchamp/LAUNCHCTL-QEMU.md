# Service control through launchctl in QEMU

This fixture uses Apple's unchanged iOS 16.5 restore launchd/xpcproxy with
the **Procursus FOSS launchctl 1:1.1.1**, not an Apple-supplied launchctl
binary. The restore, update, and system image file lists inspected for this
build contain no launchctl. No phone files are needed for this experiment.
The controller calls the published CLI; it does not replace it or synthesize
its XPC replies.

The tool's [upstream source](https://github.com/ProcursusTeam/launchctl/tree/v1.1.1)
implements print, kill and kickstart through libxpc requests to launchd.
The official rootful Procursus package and its libiosexec dependency are
pinned by SHA-256 and extracted into a local directory, without installing
host or phone packages. Apple binaries and downloaded dependencies remain
under ignored research/ paths.

## Prepare and run

Start with the runtime and initial HFS root from [LAUNCHD-QEMU.md](LAUNCHD-QEMU.md).
Use new output directories:

```sh
python3 tools/prepare-launchctl-runtime.py \
  research/darwin-launchd-20F66/runtime-root research/launchctl-runtime
sh tools/test-sweet-launchctl.sh \
  work/ci-104/artifact/kernel.development.sweet \
  work/qemu-multiproc.adt \
  work/launchd-final/root.hfs \
  research/launchctl-runtime/runtime-root \
  research/libdmg-hfsplus-build/hfsplus \
  work/launchctl-new 720
```

The base is copied. Its original launchd/xpcproxy bytes and sole target job
are verified first. The builder installs the audited runtime, the C target
with a PID readiness file, and a separate root/System controller job. All
installed regular files are re-extracted and byte-compared. Exactly the
target and controller job files must be present.

The runtime audit follows the CLI's LC_RPATH=/usr/lib to resolve
@rpath/libiosexec.1.dylib. The tested closure has 39 files / 10,551,232 bytes.
The pinned CLI SHA-256 is
`11527b7bb1027f10a7d994815efbe81df3b692ca9df8b172b6a1f656c6cc028d`;
libiosexec is
`9d8f0b10be02f9829854e11dc4a86f70dbfd0f0322f3a3a996716e4d38214391`.
The preparation script records package URLs/hashes and the upstream version
in source.json. The CLI binary is copied unchanged.

## What is checked

The controller must be root with parent PID 1 and parent path /sbin/launchd.
The target publishes its PID only after its own identity and RAM-file checks.
It also queries and logs its inherited SIGTERM disposition/mask, explicitly
sets SIG_DFL and an empty mask, and reads both back before publishing readiness.
This defines the diagnostic service's signal policy; it does not patch Apple
launchd or disable a kernel check.
The controller then executes these commands as separate child processes:

| Step | CLI arguments | Required observation |
| --- | --- | --- |
| Before | print system/org.sweet.qemu.c-service | exit 0, running, original target PID |
| Stop | kill SIGTERM system/org.sweet.qemu.c-service | exit 0, old PID reaped / ESRCH |
| Stopped | print system/org.sweet.qemu.c-service | after five seconds, job exists with no PID |
| Restart | kickstart -p system/org.sweet.qemu.c-service | exit 0, different positive PID |
| After | print system/org.sweet.qemu.c-service | exit 0, running with the new PID |

After kickstart the controller waits for the new target PID readiness file
and checks its actual executable path. It does not issue a direct stop or
start signal to the target. kill(pid, 0) is used only to query existence.
A timed-out CLI child may be killed by the controller; that is a test failure.
The target and controller both continue heartbeats after CONTROL PASS.

Each CLI's stdout/stderr goes to a distinct RAM file. The controller writes
an ordered trace, fsyncs it, and syncs the root after success. The QEMU runner
pauses virtual time for samples and exports the ADT's actual RAMDisk range
at the final stop using --save-ramdisk. It validates that range lies inside
the payload's RAM window. This writes run/ramdisk-final.hfs on the host.
720 seconds is an upper bound. The run stops early on a visible panic,
controller failure, or the second controller heartbeat after CONTROL PASS.
The runner records the actual elapsed host time and matched stop marker.

The host verifier extracts the raw CLI outputs and trace into guest/,
checks their statuses/order, old/new PID values, the stopped interval, both
target instances, and final heartbeats. It also verifies unchanged executable
bytes from the saved guest image. Results are in run/verification.json.
Sampled framebuffer logs remain supporting evidence rather than the only
source of command output.

This is QEMU development-kernel coverage for one service and one CLI version.
It does not establish full iOS, production signing policy, or MT6897 hardware
support. Phone USB/UFS/boot partitions are outside the test.

The first probe stopped after CLI print returned 0 because the controller
had opened its capture file O_WRONLY, then attempted to read it (EBADF).
It now uses O_RDWR. A second probe successfully printed the running job and
sent SIGTERM; launchd logged value 0xf, but the target continued heartbeats.
That run correctly failed rather than treating a successful CLI exit as
proof that the service stopped. Signal setup/readback was then added to the
target. Each failed image and its extracted output remains separate.

## Verified result (2026-10-30)

The complete run in `work/launchctl-signals` exited 0 with all **22 checks**
true after **412.973 host seconds**. It stopped on the second controller
heartbeat after CONTROL PASS, before the 720-second limit. There were 32
sampled frames, zero unknown glyphs, and no visible panic.

All five CLI commands exited 0. The first print showed PID 4 running.
launchd logged SIGTERM delivery; PID 4 was reaped and the stopped print
contained no PID. kickstart printed 9, the readiness file changed to 9,
and the last print showed PID 9 running. The controller and restarted
target both continued heartbeats. Raw command output is preserved under
`work/launchctl-signals/guest/` and the full report is
`work/launchctl-signals/run/verification.json`.

Both target instances reported inherited SIGTERM=ignored and mask=0, then
read back SIG_DFL with an empty mask after explicitly setting them. The
earlier failed run was therefore a diagnostic service signal-policy issue;
the successful signal request alone had not proven termination. This tests
default SIGTERM termination, not a custom signal handler or shutdown cleanup.
The strict verifier rejects that earlier no-panic/CLI-success failure.

Final SHA-256 values:

| Artifact | SHA-256 |
| --- | --- |
| Target | `465d9bed7e2d6765c121d4cb5f330cd123b48ab9f387c3a5feaceb171bd4677f` |
| Controller | `2425fbdf5d19ce32eaf90bf6b3bc967afec5bcd57aa7fed011e8c508958b3001` |
| Input root | `6304a5a91fd1b6cf223912f710139df443d2de3bb1fc5934ad926a301d419e3d` |
| Payload | `e4ac257dacec131822e5d864dc232046028f52ba0b25f73d6075d573c916def6` |
| Exported guest root | `072372b543a717b9c06ca0e4bdee7ed634a9a87f43efa53be92e6e64bba08071` |

The Actions 104 kernel was reused unchanged (SHA-256
`82fc8fe1391bea90bcce9ed2d4e8a2ff8204667f6785857873717564ec9331c9`).
The previous launchd input root remained
`491aa78408c423c50e8b59644e416e94b643ed3eb119158d52684af4176c8b3f`.
Neither Apple executable was patched. Replaying this test needs only the
small restore runtime and pinned Procursus packages, not the full system image.

For removal of the registration and reloading the same plist, see
[the separate bootout/bootstrap scenario](BOOTSTRAP-QEMU.md). The stopped
print above intentionally tests a job that remains registered.

For automatic restarts after SIGTERM and SIGKILL, see the separate
[KeepAlive scenario](KEEPALIVE-QEMU.md).

For two C services exchanging local socket messages, a normal client exit
and a server that handles SIGTERM and cleans up, see [IPC-QEMU.md](IPC-QEMU.md).

For native libxpc dictionaries and launchd starting a Mach service on
demand, see [XPC-QEMU.md](XPC-QEMU.md).

For a program using the original Foundation and Objective-C runtime, see
[FOUNDATION-QEMU.md](FOUNDATION-QEMU.md).
