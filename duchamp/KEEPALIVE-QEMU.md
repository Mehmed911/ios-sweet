# Automatic service restart with KeepAlive in QEMU

This fixture uses unchanged Apple iOS 16.5 launchd/xpcproxy with the pinned
**Procursus FOSS launchctl 1:1.1.1** from [LAUNCHCTL-QEMU.md](LAUNCHCTL-QEMU.md).
The original single-job RAM root and all prior results remain separate.
Only the target plist in a fresh copy has KeepAlive changed from false to
true. The controller's KeepAlive stays false, and the target C executable
is unchanged.

Apple's [launchd.plist manual source](https://github.com/apple-oss-distributions/launchd/blob/main/man/launchd.plist.5)
describes unconditional KeepAlive and restart throttling. This test waits
for readiness within bounded polling loops; it does not assume an exact
restart delay or change the throttle settings.

## Replay

Use the same runtime and single-job base as the earlier fixtures, with a
new output directory:

```sh
sh tools/test-sweet-launchctl.sh \
  work/ci-104/artifact/kernel.development.sweet \
  work/qemu-multiproc.adt \
  work/launchd-final/root.hfs \
  research/launchctl-runtime/runtime-root \
  research/libdmg-hfsplus-build/hfsplus \
  work/launchctl-keepalive-new 720 keepalive
```

The wrapper selects SWEET_KEEPALIVE_TEST=1 for the controller and passes the
same scenario to the root builder and verifier. The builder first verifies
that the base is the non-KeepAlive diagnostic fixture. It records the base
plist and hash, changes only KeepAlive in a copied plist, installs it into
the new image, and re-extracts it for byte comparison. Prior stop/restart
and bootout/bootstrap modes remain selectable with their original behavior.

## Required observations

The root controller must be a child of the original launchd at PID 1.
It executes exactly five CLI child processes:

| Step | CLI arguments | Required observation |
| --- | --- | --- |
| Before | print system/org.sweet.qemu.c-service | running, initial PID, runs=1 |
| Terminate | kill SIGTERM system/org.sweet.qemu.c-service | exit 0; initial PID reaped / ESRCH |
| First automatic restart | print system/org.sweet.qemu.c-service | running, different PID, runs=2, last signal=15 |
| Kill | kill SIGKILL system/org.sweet.qemu.c-service | exit 0; second PID reaped / ESRCH |
| Second automatic restart | print system/org.sweet.qemu.c-service | running, third PID, runs=3, last signal=9 |

All five CLI commands must exit 0. After each kill, the controller waits
for the PID readiness file to change and validates the new executable path.
The service publishes readiness only after checking its PID/parent, root
identity, explicit SIGTERM default disposition and empty signal mask, and
RAM-file round trip. The controller calls neither kickstart nor bootstrap
and never forks/execs the target itself. launchd alone relaunches the job.

The three PIDs must be distinct. The trace must contain exactly two ordered
AUTORESTART observations, matching the raw print outputs. The saved plist
must match the installed hash and differ from the base's parsed settings
only in KeepAlive. The verifier also checks the controller is not configured
for KeepAlive, checks original launchd/xpcproxy/CLI bytes, and requires the
final target and controller to continue heartbeats.

The runner pauses QEMU for framebuffer samples and the final RAM-disk export.
It stops at a visible panic, controller failure, or the second controller
heartbeat after CONTROL PASS, within the requested maximum host runtime.
The saved guest trace and all raw stdout/stderr files are extracted under
guest/. The complete result is run/verification.json.

Recheck an exported image without another boot:

```sh
python3 tools/verify-sweet-launchctl.py work/launchctl-keepalive-new \
  --hfsplus research/libdmg-hfsplus-build/hfsplus --scenario keepalive
```

The earlier [non-KeepAlive run](LAUNCHCTL-QEMU.md) verified that SIGTERM
left the job stopped for five seconds until explicit kickstart. This
scenario tests automatic restart after termination by signals. It does
not test conditional KeepAlive dictionaries, crash exception handling,
custom graceful shutdown handlers, or a full iOS installation.
Phone hardware, USB, UFS and boot partitions are outside this test.

## Verified result (2026-10-30)

`work/launchctl-keepalive` exited 0 with **33/33 checks passing** after
**450.716 host seconds**. It stopped on the second controller heartbeat
after CONTROL PASS, before the 720-second limit. The saved run has 35
sampled frames, zero unknown glyphs and no visible panic.

The controller was PID 3, parent PID 1 /sbin/launchd. All five CLI
processes exited 0. The three raw print outputs and trace confirmed:

| Observation | Initial | After SIGTERM | After SIGKILL |
| --- | --- | --- | --- |
| Target PID | 4 | 7 | 10 |
| State | running | running | running |
| launchd runs | 1 | 2 | 3 |
| Last terminating signal | never exited | 15 | 9 |

PIDs 4 and 7 were each reaped / ESRCH. Both replacements passed their own
readiness checks without any start command from the controller. The last
PID file contained 10; PID 10 and the controller continued heartbeats.
The saved guest plist matched the installed KeepAlive=true file, with no
other target property changed from the base. Original launchd/xpcproxy and
the pinned Procursus CLI hashes passed. The target C binary retained its
exact bytes from the earlier tests.

| Artifact | SHA-256 |
| --- | --- |
| Target | `465d9bed7e2d6765c121d4cb5f330cd123b48ab9f387c3a5feaceb171bd4677f` |
| Controller | `ca5fcabfe9da5ab23768841986ab9e0eada43674c2a32524ef0b7fc05cf30bb8` |
| Input root | `9ef39b5556b5d4416a89aa58e21eafd0bd0038c9f468359ba61cb6a33720a03f` |
| Payload | `d7b6d4d88ee53ec67473bf21ebea8e2fdde545b172b5a7665e3ce16aabfbaba6` |
| Exported guest root | `85b2e3958900f668387963f0fea647bc1a20f88aa83b58f30aec72a0d104de30` |
| KeepAlive plist | `7e33d9a92afeca768a5aacd4fb95ff171355444bee1c24099a6dfa136cc8f808` |

The original base plist remained
`004e41dbd0bc0d0f1ef88a7ee73c6ae228c55a5e7d8728704289dc244380083c`.
The reused Actions 104 kernel remained
`82fc8fe1391bea90bcce9ed2d4e8a2ff8204667f6785857873717564ec9331c9`;
the initial base root remained
`491aa78408c423c50e8b59644e416e94b643ed3eb119158d52684af4176c8b3f`.
No new kernel CI build was required.

The report and extracted raw files are at
`work/launchctl-keepalive/run/verification.json` and
`work/launchctl-keepalive/guest/`. All three controller variants passed
arm64 C checks with warnings treated as errors; shell and Python checks
also passed. Rechecking the prior saved guests with the updated verifier
still passed 22 stop/restart checks and 27 bootout/bootstrap checks.
