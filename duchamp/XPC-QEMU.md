# Native XPC and on-demand MachServices in QEMU

This fixture combines launchd MachServices registration, on-demand startup,
three native XPC dictionary request/replies, and orderly shutdown in one
QEMU run. It uses the original Apple iOS 16.5 restore libxpc, launchd and
xpcproxy with the existing 39-file runtime. Procursus FOSS launchctl
1:1.1.1 remains the observer CLI. Apple executables and libraries are not
patched for this fixture.

## Replay

Use the same single-job base as [LAUNCHCTL-QEMU.md](LAUNCHCTL-QEMU.md), with
a fresh output directory:

```sh
sh tools/test-sweet-launchctl.sh \
  work/ci-104/artifact/kernel.development.sweet \
  work/qemu-multiproc.adt \
  work/launchd-final/root.hfs \
  research/launchctl-runtime/runtime-root \
  research/libdmg-hfsplus-build/hfsplus \
  work/launchctl-xpc-new 720 xpc
```

The wrapper builds sweet-xpc-server.c, sweet-xpc-client.c and the observer
with -fblocks and SWEET_XPC_TEST=1. The old Unix-socket scenario remains
selectable as ipc. The server and client keep the previous guest executable
paths, so the old jobs and identity checks can be reused in a copied image.
The server's plist changes to RunAtLoad=false, KeepAlive=false, and
MachServices={org.sweet.qemu.mach-service: true}. Client and observer remain
RunAtLoad=true / KeepAlive=false and advertise no Mach service.

## Combined test

The client first publishes its PID and waits on a RAM-file gate. The observer
prints the server job and requires no PID, runs=0, and the registered service
name. It also checks no server PID readiness file exists. Only then does it
release the client. The client resumes its named XPC connection and sends
the first request, causing launchd to start the registered server.

The server creates a listener through
[xpc_connection_create_mach_service](https://developer.apple.com/documentation/xpc/xpc_connection_create_mach_service%28_%3A_%3A_%3A%29)
with the documented listener flag. That flag's bit 0 was also checked in
the pinned runtime's own function disassembly. Event handlers use the
default libdispatch target queue. The listener accepts one connection;
each endpoint validates the remote PID with xpc_connection_get_pid after
message activity and checks its executable path. All three processes check
root identity and parent PID 1 /sbin/launchd.

Requests carry the previous protocol's eight integer fields as XPC
dictionary entries: magic, version, operation, sequence, client/server PID,
value and checksum. The request's server field is zero because startup is
on demand; replies carry the actual server PID. The client validates that
PID against connection credentials and the executable path. All eight
fields are compared at full uint64 width. Three payloads 0x10203001..3
produce replies XORed with 0x5a5a5a5a. Independent peer logs record the values.

Replies are created using
[xpc_dictionary_create_reply](https://developer.apple.com/documentation/xpc/xpc_dictionary_create_reply%28_%3A%29),
so a missing reply context is an error. The client invokes
[the synchronous reply API](https://developer.apple.com/documentation/xpc/xpc_connection_send_message_with_reply_sync%28_%3A_%3A%29)
from its main execution, outside the connection event handler queue.
Apple documents that this API can block indefinitely; the experiment's
whole-VM host limit bounds that wait. It has no separate per-request timeout.
Received objects are released, and accepted connections retained where
their lifetime extends beyond the event callback, following
[Apple's event-handler ownership rules](https://developer.apple.com/documentation/xpc/xpc_connection_set_event_handler%28_%3A_%3A%29).

After three validated replies, the client publishes a done token and waits
for the observer's exit release. The observer prints both running jobs,
releases the client, and requires normal exit 0. The server must receive
XPC_ERROR_CONNECTION_INVALID after the client closes. It then handles the
observer's SIGTERM by setting a flag, cancelling its peer/listener objects
in normal execution, and returning 0. Shared callback state uses atomics.
Final prints must show no PID, runs=1 and last exit code=0 for both peers.
The Mach service remains registered with launchd after the server exits.

The six CLI steps are dormant-server print, running-server print,
running-client print, exited-client print, SIGTERM to server, and
exited-server print. The observer never kickstarts, bootstraps or directly
executes either service. It keeps checking both exited PIDs during its
final heartbeats. The runner exports the stopped guest's RAM disk and the
verifier checks raw transcripts, tokens, plists, executable hashes, CLI
outputs and final states.

```sh
python3 tools/verify-sweet-ipc.py work/launchctl-xpc-new \
  --hfsplus research/libdmg-hfsplus-build/hfsplus --transport xpc
```

This covers one native XPC connection and three synchronous request/replies
in the development kernel. It does not establish general XPC compatibility,
repeated on-demand activation after exit, concurrent clients, Foundation
services or a full iOS installation. Phone USB, UFS and boot partitions
remain outside the test. Keep previous roots and results separate.

## Verified result (2026-10-30)

`work/launchctl-xpc` exited 0 with **43/43 checks passing** after
**449.402 host seconds**. It stopped on the second observer heartbeat,
before 720 seconds. There were 35 sampled frames, zero unknown glyphs
and no visible panic.

The observer was PID 3 and client PID 4. The initial server print showed
no PID, runs=0 and the registered org.sweet.qemu.mach-service. After the
observer opened the begin gate, native XPC traffic caused launchd to
start server PID 6. No start command was issued. Both peers validated
connection PIDs and executable paths; their saved logs matched all three
request/reply payloads:

| Sequence | Request | Reply |
| --- | --- | --- |
| 1 | 0x10203001 | 0x4a7a6a5b |
| 2 | 0x10203002 | 0x4a7a6a58 |
| 3 | 0x10203003 | 0x4a7a6a59 |

The client cancelled its connection and returned 0 after release. The
server recorded XPC connection invalidation, handled SIGTERM, cancelled
its peer/listener and returned 0. Both final prints showed not running,
runs=1, last exit code=0; both PIDs were reaped. The server's final print
still contained its Mach service registration. All six CLI processes
exited 0 and the stopped state survived subsequent observer heartbeats.

Original Apple launchd/xpcproxy and the pinned Procursus CLI hashes passed.
The saved fixture executables matched their installed hashes. The installed
server plist SHA-256 was
`e32f6c8940f7005aa3347ec2f2663dbf5c4a86c9405d4b9c7be6dad7f8f81275`.

| Artifact | SHA-256 |
| --- | --- |
| Server | `bfb60c484b8878d658cad3182256d0b768e5273240dd7dfd4fd11b379a1c936a` |
| Client | `e321ce84071a0c6c5d01188fca0782c5435d811e753cf65506cf55543a6bec55` |
| Observer | `0ac3063243d8d2a62928e12d31ebcdff3dfa8d5de53f798827afc431f3a45170` |
| Input root | `7dba76a3799e87d7b8443f23d6eaf391ab23cb51c31246aa24641f219077dbe3` |
| Payload | `28c415f14ee8ab3c2ab7927e95cdd3197fe63f465418dd3c29d96ac9b9d465cb` |
| Exported guest root | `a90255ffc4b32bfa2fbbc6dc7798c949145537610223b0d6026356ded7aa7af1` |

The unchanged Actions 104 kernel was reused, SHA-256
`82fc8fe1391bea90bcce9ed2d4e8a2ff8204667f6785857873717564ec9331c9`.
The initial base root remained
`491aa78408c423c50e8b59644e416e94b643ed3eb119158d52684af4176c8b3f`.
No new kernel CI build or additional runtime library was required.

All five controller modes and both native XPC programs passed arm64 C
checks with warnings as errors. Python/shell checks passed. Rechecking the
previous Unix guest with the updated verifier passed 39 checks (the launch
policy is now split into two checks); its original 38-check report was
preserved as verification-original38.json and restored to verification.json.
The extra recheck is verification-xpc-tools-recheck.json in that prior run.

The new report and raw logs are at
`work/launchctl-xpc/run/verification.json` and
`work/launchctl-xpc/guest/`. Prior roots and results remain separate.
