# Live preferences, notifyd and restart recovery in one QEMU boot

This extends [the isolated NSUserDefaults test](CFPREFS-QEMU.md) using the
same original Apple runtime and unchanged Actions 104 kernel. All work
is confined to the QEMU HFS+ RAM root. It does not access a phone.

## Verified result — 2026-10-30

work/launchctl-cfprefs-batch-v2 passed **72/72 checks**, exit 0,
with **113 matching file hashes**, 1691.019 host seconds
and 70 sampled frames. Zero unknown glyphs and no visible panic.
All ten actual CLI calls exited 0. The VM stopped on the second-heartbeat
text; stopped state was verified for at least two heartbeats.

Writer PID 7, first reader1 PID 5, restarted
reader1 PID 16, reader2 PID 6; cfprefsd PIDs
9 then 13 (runs=2), notifyd PID 8
(runs=1, unchanged). Reader2 survived every phase and the new reader1
verified generation 2 before the final update. All client instances exited
normally with status 0. The saved plist has exactly the final generation 3
values/types, the jail stayed empty, and the installed Apple files matched.

The kernel is unchanged; no phone or boot-partition operation occurred.
Full local report: work/launchctl-cfprefs-batch-v2/run/verification.json.

| Artifact | SHA-256 |
| --- | --- |
| Initial root | 89388d378c8d2fc66cf942d3c60647ad0579ebb29df629903a7bad0c44469a21 |
| Payload | 8c1c249fd0940b03bfca7ac7781d721e328230a680bb59427e93545177b08635 |
| Saved RAM root | 03532c1d4e832f36ca6d3f992e1df619239afb364aa4b3ff5c9af9723658ed58 |

## Batch contract

Original launchd starts a writer and two live readers concurrently. All
three prepare the runtime using the independent empty warmup domain,
then enter the empty chroot before accessing the fixture suite
`org.sweet.qemu.preferences.batch`. Direct creation and later reading
at all three standard preferences paths must fail with ENOENT.

| Step | Preference generation | device | soc | enabled | Action |
| --- | --- | --- | --- | --- | --- |
| 1 | 1 | DUCHAMP | 6897 | true | Write and read through both live clients |
| 2 | 2 | DUCHAMP-LIVE | 8300 | false | Change the values through the same processes |
| 3 | 2 | DUCHAMP-LIVE | 8300 | false | Read the saved values after daemon and reader restart, without setters |
| 4 | 3 | DUCHAMP-RECOVERED | 6897 | true | Write again through the existing writer after daemon restart |

Each reader calls NSUserDefaults synchronize before verifying the actual
string, integer, boolean and generation. A bounded retry tolerates
temporary reconnection delay; timeout or wrong values fail the test.
The original Apple daemon/framework binaries are not modified.

## Notification semantics

After a successful write/synchronize, the writer explicitly sets the
step number and posts the private name
`org.sweet.qemu.preferences.batch.changed` through original notifyd.
The read-only recovery step also posts a wakeup after its successful
read. The notify state carries only 1, 2, 3 or 4, never preference values.

Readers use the previously verified plain IPC registration/check path.
The writer waits for both readers to verify and acknowledge each step
before advancing, so the test does not rely on counting coalesced posts.
All tokens must be cancelled and become invalid at orderly exit.

This is an explicit signal between cooperating programs. It does not
claim automatic cross-process NSUserDefaultsDidChangeNotification or
FSEvents change delivery, and it does not rely on an interpose hook.

## Restart and persistence checks

After step 2, the observer uses the real pinned Procursus CLI:

```text
launchctl kickstart -k -p system/com.apple.cfprefsd.xpc.daemon
```

The `-k` flag sends the CLI's native kill request and `-p` prints the
new PID ([Procursus 1.1.1 source](https://github.com/ProcursusTeam/launchctl/blob/v1.1.1/kickstart.c)).
The observer requires a different original cfprefsd PID and reaping of
the old one. It then waits, with a bounded timeout, for that PID to exec
/usr/sbin/cfprefsd: kickstart can return while the PID still belongs to
xpcproxy. This is a forced restart; it is not a graceful-shutdown test.

Reader 1 is then asked to stop after step 2, must exit normally, and is
started as a new PID by original launchd. Reader 2 and the writer stay
alive. The new reader starts with notify state 2 and must read generation
2 in step 3, before any new setter. Step 4 then tests new writes after
the daemon restart. The observer captures the normal exit states and
requires cfprefsd runs=2, reader 1 runs=2 and notifyd runs=1 at the same PID.

Control/readiness files carry only PIDs, step numbers, completion
acknowledgements and a stop token. The writer publishes a completion
acknowledgement only after consuming both reader acknowledgements,
before the observer may reset a restarted reader's files. No directory
descriptor or outside cwd is retained by an isolated probe.

The host extracts the saved real-root plist and requires the exact final
generation 3 values/types. It also checks all installed hashes and
original launchd/xpcproxy, the empty chroot, ordered logs, CLI results
and two final stopped-probe heartbeats.

## Run

Use the existing local runtime prepared for CFPREFS-QEMU.md and a fresh
output directory:

```sh
sh tools/test-sweet-cfprefs.sh \
  work/ci-104/artifact/kernel.development.sweet \
  work/qemu-multiproc.adt work/launchd-final/root.hfs \
  research/cfprefs-runtime-20F66-v2/runtime-root \
  research/libdmg-hfsplus-build/hfsplus \
  work/launchctl-cfprefs-batch-v2 2100 batch
```

The basic mode remains the default. The batch adds two RunAtLoad reader
jobs and uses separate probe/controller sources. The runner freezes
the C/Objective-C sources and headers into test-sources/ before compiling
them, and records input/source hashes in inputs.json. Results include
run/verification.json, captured guest files and the final RAM root.
Batch framebuffer sampling is every 20 host seconds to reduce snapshot
overhead; basic mode retains 10 seconds. The verifier requires at least
two stopped-probe heartbeats, and describes the framebuffer as sampled.

A separate compilation check using the frozen sources and the basic
preprocessor flags produced byte-identical writer, reader and controller
binaries to the successful v5 baseline. The comparisons are saved locally
in work/cfprefs-basic-build-check-v2/comparison.json; the old guest report
and images were not overwritten or rerun.

To recheck a preserved guest without overwriting its original report:

```sh
python3 tools/verify-sweet-cfprefs-batch.py work/launchctl-cfprefs-batch-v2 \
  --hfsplus research/libdmg-hfsplus-build/hfsplus \
  --report work/cfprefs-batch-recheck.json
```

Apple binaries and downloaded system images remain local and outside Git.
The test does not establish reboot persistence, sandboxed application
domains, automatic preference notifications, iOS UI readiness or MT6897
hardware compatibility.

## Preserved first attempt

work/launchctl-cfprefs-batch is a failed attempt: 1393.347 host seconds,
100 sampled frames, all 113 file hashes matched. Both live-update phases
and both explicit notification/acknowledgement sequences completed. The
saved intermediate RAM image contains exactly generation=2,
device=DUCHAMP-LIVE, integer soc=8300 and boolean enabled=false.

The controller then rejected the restarted daemon too early. The real
kickstart process exited 0 and returned PID 13; the native launchd log
identified PID 13 as xpcproxy at that point, after PID 9 was killed and
reaped. No assertion of a successful recovery is made for that attempt.
The correction waits for the executable transition before testing
identity. The initial failure report, intermediate observation and all
guest logs remain untouched.
