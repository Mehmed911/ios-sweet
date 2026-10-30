# Original notifyd, cross-process notifications and ASL filters in QEMU

This scenario adds the original iOS 16.5 20F66 system-image notifyd to the
tested [syslogd fixture](SYSLOGD-QEMU.md). Apple executable/library bytes
remain unchanged. Five jobs run in a copied RAM root: notifyd, syslogd,
two probes and the observer. No phone/USB/UFS/boot-partition operation
belongs to this scenario.

## Source and dependencies

The system-image index identifies /usr/sbin/notifyd (128704 bytes) and
/System/Library/LaunchDaemons/com.apple.notifyd.plist (797 bytes).
The actual extracted executable is plain arm64, iOS 16.5, with direct
libSystem.B/libbsm.0 dependencies and /usr/lib/dyld. Pinned SHA-256:

| Artifact | SHA-256 |
| --- | --- |
| Original notifyd | `819c8ec6b3bee5cd2f1dcbe0b2b698418c411b4c126f2f97cbdae932c1972907` |
| Original job | `627b24feb59a493a50f488bc62ec9e878c333757d4ddb7786a977650ed9b1a05` |

The source is member 096-04088-077.dmg of the same Apple 20F66 IPSW used
for the earlier restore runtime, system volume SydneyF20F66.D22D221OS.
Local extraction used the existing APFS range cache and 7-Zip, selecting
only those two files. The archiver completed with two files / 129501 bytes.
The partially materialized APFS cache is not a complete image digest or
an independent Apple signature verification. Keep extracted Apple files
and cached image data out of Git.

The inspected reference is
[Apple Libnotify-312 at 885677b](https://github.com/apple-oss-distributions/Libnotify/tree/885677be0379101ccf37b46f8da81dbc17d6d301).
It informs ABI, initial-check semantics, state/cancel calls and daemon CLI
arguments. The binary's LC_SOURCE_VERSION and the library's project string
both identify version 312; no byte-for-byte source/build equivalence is claimed.

After obtaining the matching executable/job in a fresh extraction tree:

```sh
python3 tools/prepare-syslogd-runtime.py \
  research/syslogd-runtime-20F66/runtime-root \
  research/foundation-runtime-20F66-v2/runtime-root \
  research/syslogd-20F66/apple-extracted \
  research/darwin-launchd-20F66/restore.apfs \
  research/notifyd-runtime-20F66-new \
  --notifyd-root research/notifyd-20F66/apple-extracted
```

The preparer refuses to overwrite an existing output and verifies both
notifyd hashes in addition to the original syslogd/restore checks.
The combined strong dependency closure has 42 binaries / 11006176 bytes
and no missing dependencies. Its source.json records the original jobs,
binary hashes, source image member and reference source commits.

## RAM configuration and coverage

The new job retains com.apple.system.notification_center and the
com.apple.notifyd.matching event publisher from Apple's original plist.
It adds RunAtLoad=true, KeepAlive=false, root/System execution and:

```text
/usr/sbin/notifyd -d -log_file /private/var/tmp/notifyd-debug.log -shm_pages 0
```

The documented zero-page option selects IPC for passive notifications,
avoiding a shared-memory dependency in this first integration. This
fixture does not test notifyd's shared-memory pages or dispatch callbacks.
Both system daemons keep ASL_DISABLE=1 to avoid recursive self-logging;
the probes use ASL_DISABLE=0.

## Grouped probe sequence

The first two attempts used notify_register_check with zero shared pages.
They are preserved as work/launchctl-notifyd and work/launchctl-notifyd-v2.
The second recorded registration status 0, followed by successful state
lookup returning 0x0000000700000003 instead of the new name's zero state.
The native daemon log showed the requested name registered, then
get_state_2 with name_id=0. The value matches its PID 7 and protocol 3.

In the matched
[312 server implementation](https://github.com/apple-oss-distributions/Libnotify/blob/Libnotify-312/notifyd/notify_proc.c),
register_check initializes name_id=0 and, with nslots=0, delegates to plain
registration without updating that output. The client caches zero and
queries the internal IPC-version name. The fixture therefore uses plain
registration, whose NID_UNSET causes get_state to resolve the actual name
by token. The zero-state and all subsequent exact-state assertions stay
intact. No original daemon/library patch is applied. This does not claim
register_check/get_state works with zero shared pages in this runtime.

Failure diagnostics now print each native return separately and sync
before a FAIL marker. The first early stop did not preserve most newly
created log directory entries in the exported HFS image; the second
attempt retained the detailed log after the added sync.

Both probes call notify_register_plain for the same non-self namespace
name, org.sweet.qemu.notify.integration. Each verifies state=0, consumes
the initial changed=1 result, and requires the next check to be quiet.
Only then does it publish readiness to the observer.

The observer checks both daemon jobs and releases the begin gate:

1. Probe 1 sets state 0x1020304050607001 through a separate plain
   publisher token and posts the name. Both probes must observe changed=1
   and read the exact state from the daemon.
2. After both receivers finish, probe 1 cancels its check token. The token
   must become invalid and notify_check must return INVALID_TOKEN (2).
3. Probe 1 sets state 0x1020304050607002 and posts again. Probe 2 must
   receive/read the second state. Probe 1's cancelled token must remain
   invalid after that post. Both probes clean up their remaining tokens.

The synchronization files contain only done tokens. State values travel
through libnotify; the files do not carry notification payload/state.
This tests polling/check semantics over native IPC between two processes.

The observer then registers the ASL master-filter name, sets its state to
0x300ff, reads it back and posts com.apple.asl.remote. The probes open
ASL with SHIM_NO_TRACE=0x20000000, leaving NO_REMOTE clear. Each evaluates
its messages and requires the remote-control TUNNEL bit to be set before
sending three legacy ASL records to syslogd.

The existing raw-file checks must still find six exact messages and
sender identities. The observer restores the master state to zero, posts
the change and cancels its control token, then releases the probes to
exit. Final CLI prints and two heartbeats require the same two daemon
PIDs/runs=1 and both probes stopped with exit code 0. Neither daemon is
shut down gracefully by this fixture.

## Run and saved verification

```sh
sh tools/test-sweet-launchctl.sh \
  work/ci-104/artifact/kernel.development.sweet \
  work/qemu-multiproc.adt \
  work/launchd-final/root.hfs \
  research/notifyd-runtime-20F66-new/runtime-root \
  research/libdmg-hfsplus-build/hfsplus \
  work/launchctl-notifyd-new 1500 notifyd
python3 tools/verify-sweet-syslogd.py work/launchctl-notifyd-new \
  --hfsplus research/libdmg-hfsplus-build/hfsplus --notifyd
```

The verifier checks saved daemon/probe logs, actual CLI outputs,
ordered notification observations, cancellation results, ASL evaluation
bits, the restored master state, all six raw records and installed file
hashes. Use --report with a different path when rechecking an older saved
guest. The earlier syslogd guest was rechecked with the extended verifier
and a separate report; its original result was preserved.

This does not establish shared-memory notification delivery, callback
concurrency, daemon restart recovery, arbitrary clients, modern os_log,
UIKit, SpringBoard, full iOS or MT6897 driver compatibility.

## Verified result (2026-10-30)

`work/launchctl-notifyd-v3` exited 0 with **74/74 checks passing** after
**536.613 host seconds**. It stopped on the second observer heartbeat,
before the 1500-second limit. There were 42 sampled frames, zero unknown
glyphs and no visible panic. All **51 installed file hashes** and original
Apple launchd/xpcproxy/syslogd/notifyd hashes matched.

The observer was PID 3, original syslogd PID 4, probes PIDs 5/6 and original
notifyd PID 7. Both plain registrations returned 0, read state zero,
observed initial changed=1 and then quiet=0. Both probes received
0x1020304050607001. After probe 1 cancelled, only probe 2 received
0x1020304050607002; the cancelled token stayed invalid with check status 2.
The original daemon's debug log confirmed name registration, posts and
cancellation, with the fixture name resolved to name_id 1.

The ASL master state was set/read back as 0x300ff through notifyd and its
change was posted. Both probes had NO_REMOTE clear and every ASL
evaluation was 0x00230005, showing the remote-control TUNNEL bit. All six
raw records independently matched the expected tokens, fields and root
sender identities. The master was restored to zero and its token cancelled.

All six real CLI prints exited 0. Both daemon before/after prints matched:
same PID, running, runs=1. Both probes finished with exit code 0/runs=1 and
stayed stopped through the final heartbeats; both daemons stayed alive.
The fixture does not test graceful shutdown or restart recovery.

The two failed attempts described above remain separate. The successful
local runtime is `research/notifyd-runtime-20F66-v2/runtime-root`, containing
the same pinned 42 binaries and updated matched-version provenance.
Ten observer compilation modes and both probe configurations passed
arm64 checks with warnings as errors; Python/shell checks passed.
The final extended verifier also rechecked the earlier syslogd guest:
43/43 passed in `work/syslogd-notify-final-recheck.json`, without replacing
its original report. No kernel change or new Actions build was needed.

| Artifact | SHA-256 |
| --- | --- |
| Probe 1 | `d75e313663319e78e301954ece5698e8fc2c4f7527b8324494a9c82ff0003267` |
| Probe 2 | `4c75ae7555275a5cc7a906c408cb6944451979aafab3bdd56f62f0ef38555f7f` |
| Observer | `f364f0dee8bef980589bdff407e35d7bb77e134248234967f9c7519513d23b28` |
| Input root | `3e800f071990192fefd69684477618532c85ab85accbd74f750a51c2f70e6baf` |
| Payload | `eacdc56581aa13cc14c0fd36feb8041a1e71b0aacb14715793d4ece58e8a676e` |
| Exported root | `e942200c5f595f8918aa7e39935d2e39bc4aea0999af57eac19d7f442e5b9583` |
| Raw ASL log | `f41a71dafad74ffd53ecc98175fcf71957487dc4423cbe4010140f77f3c17bce` |

The unchanged Actions 104 kernel remained
`82fc8fe1391bea90bcce9ed2d4e8a2ff8204667f6785857873717564ec9331c9`;
the original base remained
`491aa78408c423c50e8b59644e416e94b643ed3eb119158d52684af4176c8b3f`.
