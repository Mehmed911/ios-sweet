# Original iOS syslogd receiving ASL messages in QEMU

This fixture runs the unmodified iOS 16.5 20F66 restore /usr/sbin/syslogd
under the original Apple launchd. Two small C programs send legacy ASL
messages. The observer uses pinned Procursus FOSS launchctl 1:1.1.1 and
reads the file written by the daemon. Phone USB, UFS and boot partitions
are outside this test.

## Inspection and local preparation

The syslogd binary is thin plain arm64, targets iOS 16.5, uses /usr/lib/dyld
and directly loads /usr/lib/libbsm.0.dylib and /usr/lib/libSystem.B.dylib.
Its original bytes have SHA-256
`86838d9149bb898e3d39266fea884c6c92eeac1e6486c072b135a879c9eeaabe`.
The original 347-byte launch job has SHA-256
`86ce6512803e6a20c04834f155a38e1b1a24ff66c9452a57850f65bf2056d5fe`.
It is Disabled=true / KeepAlive=true, advertises com.apple.system.logger,
and sets ASL_DISABLE=1 for the daemon process.

The inspected Apple open-source reference is
[syslog at 69d8586](https://github.com/apple-oss-distributions/syslog/tree/69d8586e9a599c304e1b702a9c2830e2f78126d5).
The reference explains CLI arguments, configuration rules, ASL flags and
the transport; it is not proof of source/build equivalence to this binary.
Imports, load commands and strings were separately inspected locally.
Required ASL exports are present in the pinned runtime.

Reuse the pinned local restore APFS from LAUNCHD-QEMU.md and choose new
extraction/runtime directories:

```sh
7z x -y -oresearch/syslogd-20F66-new/apple-extracted \
  research/darwin-launchd-20F66/restore.apfs \
  usr/sbin/syslogd System/Library/LaunchDaemons/com.apple.syslogd.plist
python3 tools/prepare-syslogd-runtime.py \
  research/launchctl-runtime/runtime-root \
  research/foundation-runtime-20F66-v2/runtime-root \
  research/syslogd-20F66-new/apple-extracted \
  research/darwin-launchd-20F66/restore.apfs \
  research/syslogd-runtime-20F66-new
```

The libraries argument supplies the matching libbsm from the earlier
Foundation extraction. The new closure includes only dependencies needed
for syslogd/launchctl/dyld: 41 binaries, 10,877,472 bytes, no missing strong
dependencies. The preparer validates the original APFS/syslogd hashes and
job properties, records every file hash and keeps all Apple files local.
It refuses to overwrite an existing output.

## RAM-only configuration

The builder copies the original 32 MiB launchd HFS root. The daemon's
executable and Apple libraries remain unchanged. Its copied job is enabled,
RunAtLoad=true / KeepAlive=false, with root/System identity and diagnostic
arguments:

```text
/usr/sbin/syslogd -d /private/var/tmp/syslogd-debug.log -config iphone
  -klog_in 0 -udp_in 0 -bsd_out 0 -remote 0 -launchd_in 0 -m 0
```

These select the iPhone configuration and disable unused input/output
modules. The ASL Mach service stays registered. ASL_DISABLE=1 is retained
for the daemon itself, avoiding self-logging through its own ASL client.
The two probe jobs explicitly set ASL_DISABLE=0. Exactly four jobs are
installed: syslogd, both probes and observer, all without KeepAlive.

The versioned [ASL configuration](syslogd-asl.conf) selects only the
fixture's facility/marker and writes raw records to
/private/var/log/sweet-asl.log. The directory already exists in the base;
an empty /private/etc/asl directory is also created in the copy.

The probe calls asl_open with NO_REMOTE | SHIM_NO_TRACE (0x20000004).
This prevents the ASL-to-os_log shim from routing the test into a different
service, and avoids client-side notifyd filters. It verifies a nonzero
ASL service port and checks the runtime's _asl_evaluate_send result:
SEND_ASL must be set; SEND_TRACE and local file-output bits must be clear.
These are version-specific ASL diagnostics, not a claim about modern
unified logging.

Each probe sends three unique tokens through asl_new/asl_set/asl_send,
with sender, local0 facility, notice level and fixture/client/sequence
fields. It never opens the daemon's output path. After sending, both
probes remain alive until the observer sees all six raw records, including
each real sender PID/UID/GID. They then close normally.

The observer waits for the actual syslog.pid and daemon debug readiness,
prints its launchd state, and releases the probes. It reads the output
file without writing it. Four real CLI prints must show syslogd running
once with the same PID and both probes stopped with exit code 0/runs=1.
Two final heartbeats require the daemon to remain alive and probes to
stay stopped. The daemon remains running when the guest is stopped and
its RAM disk is exported; this does not test graceful daemon shutdown.

## Run and independently verify

```sh
sh tools/test-sweet-launchctl.sh \
  work/ci-104/artifact/kernel.development.sweet \
  work/qemu-multiproc.adt \
  work/launchd-final/root.hfs \
  research/syslogd-runtime-20F66-new/runtime-root \
  research/libdmg-hfsplus-build/hfsplus \
  work/launchctl-syslogd-new 1200 syslogd
python3 tools/verify-sweet-syslogd.py work/launchctl-syslogd-new \
  --hfsplus research/libdmg-hfsplus-build/hfsplus
```

The verifier extracts the stopped guest root, compares every installed
file and original launchd/xpcproxy/syslogd hash, and checks actual CLI,
PID and gate files. It independently parses six raw ASL records and
compares their messages, custom fields, sender names, levels and
reported PID/UID/GID against the expected sender processes. The daemon's own __asl_server_message debug
receipts must contain each token once. This distinguishes real daemon
receipt/file output from a successful client return or console echo.

Reports are run/verification.json; raw files and CLI output are under
guest/. Coverage is legacy ASL receipt/file output by one original daemon.
It does not establish os_log/logd, notifyd, log rotation, arbitrary input,
UIKit, SpringBoard, full iOS or MT6897 hardware compatibility.

## Verified result (2026-10-30)

`work/launchctl-syslogd` exited 0 with **43/43 checks passing** after
**397.172 host seconds**. It stopped on the second observer heartbeat,
before the 1200-second limit. There were 31 sampled frames, zero unknown
glyphs and no visible panic.

The original daemon was PID 4, observer PID 3 and root probes PIDs 5/6.
All six sends returned 0 with runtime evaluation 0x00030005: legacy ASL
selected, trace/local-file output disabled. The daemon's own MIG debug
receipts contained each token once. The independently extracted raw
output contained exactly six records, with matching sender names,
PIDs, UID/GID 0, local0 facility, notice level and custom sequence fields.
This checks the expected root senders; it does not test forged identity
fields or unprivileged clients.

All four CLI prints exited 0. Both probe jobs showed not running, runs=1
and last exit code=0. The daemon's before/after prints were identical:
running, PID 4, runs=1. It stayed alive while both probes stayed stopped
through the final heartbeats. Graceful daemon shutdown was not tested.
launchd logged persona lookup warnings and the legacy launch(3)
activation warning; neither prevented the observed ASL receive/file path.

All **49 installed file hashes** and original Apple launchd/xpcproxy/
syslogd hashes matched. Nine observer compilation modes and the C probe
passed arm64 checks with warnings as errors; Python/shell checks passed.
This was one VM run. No kernel change or new Actions build was needed.

| Artifact | SHA-256 |
| --- | --- |
| Original syslogd | `86838d9149bb898e3d39266fea884c6c92eeac1e6486c072b135a879c9eeaabe` |
| Probe 1 | `81d467a90d7b76a5427b3c62832ec9589c9b6d8fa16e84a80726310ef813f6b8` |
| Probe 2 | `6b4b55dce920698153bbf6e56b09cff5c95890ae05a064c4f5d7b02279adf305` |
| Observer | `b8731a57adffe79f10ddea2cffbb321635da1d3844659ba3e697d4ea1571ae26` |
| Input root | `24a366af70ac1e3d30cda31e6cad4708c80f47bb899f8278cd194f3df159cc7d` |
| Payload | `16c324fe03a318c8b2031e89c4f2407be0f2787ed64dab7eab7b1244b4b2bfee` |
| Exported root | `bdf674d4e60e53d321aa98e38c39306846d323f2500cf67d7604c35d4ed056eb` |
| Raw ASL log | `1e4be882410f11880afc0e9821d7e55c51ce35eb1ecdd8ba0ded54103ffdb65a` |

The unchanged Actions 104 kernel remained
`82fc8fe1391bea90bcce9ed2d4e8a2ff8204667f6785857873717564ec9331c9`;
the original base remained
`491aa78408c423c50e8b59644e416e94b643ed3eb119158d52684af4176c8b3f`.
