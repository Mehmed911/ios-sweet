# Two C services and orderly shutdown in QEMU

This fixture runs a Unix-domain socket server and client as separate root
children of Apple's unchanged iOS 16.5 restore launchd. A third diagnostic
job observes them through the pinned Procursus FOSS launchctl 1:1.1.1.
The runtime, kernel and base image are the same as [LAUNCHCTL-QEMU.md](LAUNCHCTL-QEMU.md).
All three jobs use RunAtLoad=true and KeepAlive=false.

## Replay

Use a new output directory:

```sh
sh tools/test-sweet-launchctl.sh \
  work/ci-104/artifact/kernel.development.sweet \
  work/qemu-multiproc.adt \
  work/launchd-final/root.hfs \
  research/launchctl-runtime/runtime-root \
  research/libdmg-hfsplus-build/hfsplus \
  work/launchctl-ipc-new 720 ipc
```

The IPC scenario builds sweet-ipc-server.c into /sbin/sweet-launchd-service,
the path of the base's existing c-service job. That job's plist stays
byte-identical to the base. The builder adds /sbin/sweet-ipc-client and its
own job, plus the observer compiled with SWEET_IPC_TEST=1. The builder
requires exactly the server, client and observer job files and verifies
installed bytes by re-extraction. Older scenarios retain their C target.

## Communication and exit sequence

The server installs and reads back a SIGTERM handler and empty signal
mask, listens at /private/var/tmp/sweet-ipc.sock, then publishes readiness.
The client waits for that readiness before connecting. Both sides query
LOCAL_PEERPID from the kernel and validate the peer's actual executable
path. The three processes also check root identity and parent PID 1 with
path /sbin/launchd.

The socket uses AF_UNIX / SOCK_STREAM. Each request and reply is a
32-byte frame with a magic value, version, operation, sequence, both PIDs,
payload and XOR checksum. Three requests carry 0x10203001 through
0x10203003; replies XOR the payload with 0x5a5a5a5a. Every field is
validated against the expected frame. Both processes record the actual
requests/replies in separate fsynced RAM logs. This is a diagnostic local
protocol; the checksum is not an authentication mechanism.

After all replies, the client closes its socket, publishes its own PID,
and waits for the observer's release file. The server must see EOF and
return to its idle listener. The observer executes exactly five CLI
processes:

| Step | Required evidence |
| --- | --- |
| print server | running with its actual PID, runs=1 |
| print client | running with its actual PID, runs=1, after the exchanges |
| release client, then print client | old PID reaped; registered but not running; exit code 0; runs=1 |
| kill SIGTERM server | CLI exit 0; handler sets a shutdown flag, normal execution performs cleanup |
| print server | old PID reaped; not running; exit code 0; runs=1 |

The third row uses one print command; writing the release file is an
ordinary RAM-file operation. The observer sends no signal to the client.
Its main function returns 0. The server's signal handler only sets a
volatile integer flag. The normal execution path closes the listener,
unlinks the socket, fsyncs its final log and returns 0. launchd must report
normal exit 0 rather than termination by signal 15. The observer checks
neither process nor socket reappears during its subsequent heartbeats.
It never forks/execs either service or issues kickstart/bootstrap.

## Evidence and limits

The small Darwin ABI declarations in sweet-ipc.h were checked against
the local XNU 22.6 source in work/ci-40753321990/xnu: bsd/sys/un.h,
socket.h, poll.h, signal.h and _types/_timeval.h. The LOCAL_PEERPID path
was inspected in bsd/kern/uipc_usrreq.c. Socket timeouts are 30 guest
seconds. Read/write helpers handle partial transfers and EINTR; peer
readiness and observer waits are bounded. The whole VM has a host time
limit and stops early on a visible panic, diagnostic failure, or the
second observer heartbeat after IPC CONTROL PASS.

The verifier extracts the stopped guest's RAM disk. It compares both raw
transcripts against all three expected frames, checks both peer PID
queries, original and fixture executables, job profiles, real CLI exit
states, and the absence of the socket in the saved directory listing.
Framebuffer samples are supporting evidence. Recheck without rebooting:

```sh
python3 tools/verify-sweet-ipc.py work/launchctl-ipc-new \
  --hfsplus research/libdmg-hfsplus-build/hfsplus
```

Raw files are under guest/ and the complete report is
run/verification.json. This covers one connection, three request/reply
pairs, a normal client exit and SIGTERM cleanup of an idle server after
peer EOF. It does not test XPC/Mach services, active-request cancellation,
multiple simultaneous clients or a complete iOS userland. Phone USB, UFS
and boot partitions are outside this experiment.

## Verified result (2026-10-30)

`work/launchctl-ipc` exited 0 with **38/38 checks passing** after
**428.675 host seconds**. It stopped on the second observer heartbeat,
before the 720-second limit. There were 33 sampled frames, zero unknown
glyphs and no visible panic.

The observer was PID 3, server PID 4, client PID 5. All three were root
children of original PID 1 /sbin/launchd. Both socket endpoints returned
the matching peer PID through LOCAL_PEERPID and passed executable-path
validation. Both independent transcripts recorded these exact exchanges:

| Sequence | Request value | Reply value |
| --- | --- | --- |
| 1 | 0x10203001 | 0x4a7a6a5b |
| 2 | 0x10203002 | 0x4a7a6a58 |
| 3 | 0x10203003 | 0x4a7a6a59 |

The client closed the connection; the server recorded EOF. The observer
printed both running jobs, released the client, and verified its natural
exit. It then sent SIGTERM to the server, whose normal execution closed
the listener, unlinked the socket and returned 0. Both final prints showed
not running, runs=1 and last exit code=0. Neither reported signal death.
Both PIDs were reaped. The saved RAM-root listing contained no socket;
subsequent observer heartbeats confirmed both processes stayed stopped.
All five CLI child processes exited 0.

Original Apple launchd/xpcproxy and the pinned Procursus CLI bytes passed
their hash checks. The saved fixture executables matched their installed
hashes. The server plist stayed byte-identical to the base, with SHA-256
`004e41dbd0bc0d0f1ef88a7ee73c6ae228c55a5e7d8728704289dc244380083c`.

| Artifact | SHA-256 |
| --- | --- |
| Server | `f89ef4d320f554bf13f5e284efb6f4ba4d61235c6d6cf5140fe91edc04f88972` |
| Client | `fc9b79e2d48729ff45b6abe6909325b69a499e7660aabe821af5d1e605cf866f` |
| Observer | `2bc3845ccdfa148c36411c271046816ded93a732c1ae3b0844308dae41fc30f2` |
| Input root | `aa4e450a621daa745ed915bc97fe3ce3dd605b7e25e5f4fa2bf9d3bbec8c53f0` |
| Payload | `55a093b2d3b86c5850bdad77a1d28d8eb0e024d326687d6ce409d7b493a034bf` |
| Exported guest root | `47800e98c2f14a64e2c8b5ee7a28164b370d5fc1afc4cb8575458e10237de9f7` |

The unchanged Actions 104 kernel was reused, SHA-256
`82fc8fe1391bea90bcce9ed2d4e8a2ff8204667f6785857873717564ec9331c9`;
the initial base root remained
`491aa78408c423c50e8b59644e416e94b643ed3eb119158d52684af4176c8b3f`.
No new kernel CI build was needed. The server, client and all controller
modes passed arm64 C checks with warnings treated as errors; Python and
shell checks passed. Rechecking the previous saved KeepAlive run with its
verifier still passed 33 checks.

The report and raw files are at `work/launchctl-ipc/run/verification.json`
and `work/launchctl-ipc/guest/`. Prior roots and test results were retained.
