# Two clients, service reactivation and rejected messages in QEMU

This separate Foundation/libxpc scenario preserves the earlier
[single-client fixture](FOUNDATION-XPC-QEMU.md). It uses the unchanged
Actions 104 kernel, the original Apple launchd/xpcproxy and pinned
Foundation runtime, plus Procursus FOSS launchctl 1:1.1.1. No phone,
USB, UFS or boot partition operation is part of the test.

## Replay

Use the prepared runtime from FOUNDATION-QEMU.md and a fresh output path:

```sh
sh tools/test-sweet-launchctl.sh \
  work/ci-104/artifact/kernel.development.sweet \
  work/qemu-multiproc.adt \
  work/launchd-final/root.hfs \
  research/foundation-runtime-20F66-v2/runtime-root \
  research/libdmg-hfsplus-build/hfsplus \
  work/launchctl-foundation-xpc-batch-new 1500 foundation-xpc-batch
```

The copied RAM root grows to 128 MiB. There are exactly four jobs: the
on-demand server (RunAtLoad=false), two client jobs running the same binary
with different arguments, and the observer. Every job has KeepAlive=false.
The server and clients are Objective-C/MRC programs using blocks and
Foundation JSON; the observer remains C.

## One grouped run

The observer prints the dormant server before releasing both clients.
Each client opens its own native XPC connection and sends a credential-
checked hello. A file barrier requires both hellos to complete against the
same server PID before requests begin. A second barrier keeps both
connections open until both clients finish. Every data reply must report
two active connections; both peers' executable paths and actual XPC PIDs
are checked.

Callbacks target one private serial dispatch queue. This tests two
simultaneously live clients with serialized server processing; it does not
claim parallel execution of Foundation callbacks. The accepted peer's
target queue is explicitly set before resume, as described by Apple's
[xpc_connection_set_target_queue](https://developer.apple.com/documentation/xpc/xpc_connection_set_target_queue%28_%3A_%3A%29)
contract. Typed dictionary fields are checked through
[xpc_dictionary_get_value](https://developer.apple.com/documentation/xpc/xpc_dictionary_get_value%28_%3A_%3A%29?language=objc)
and xpc_get_type before reading their integer/data values.

Each client sends this nine-request sequence in each generation:

| Step | Input | Expected status |
| --- | --- | --- |
| 1 | Valid Foundation JSON | 0 |
| 2 | Invalid JSON syntax | 1 |
| 3 | Valid Foundation JSON after the syntax error | 0 |
| 4 | String instead of XPC data | 2 |
| 5 | Missing JSON field | 3 |
| 6 | 4097 bytes, exceeding the 4096-byte limit | 4 |
| 7 | Valid JSON with a number in the device string field | 5 |
| 8 | Envelope PID inconsistent with the connection's actual peer | 6 |
| 9 | Valid Foundation JSON after all six rejected cases | 0 |

Rejections return structured status replies on the same connection, with
no Foundation payload. They do not terminate the service. The client checks
the exact status, sequence, generation, client identity and actual server
PID. The server records the matching request/result. Native integer
envelopes are preserved and valid JSON uses the earlier Foundation hooks.
Sequences are generation*100 + client_id*10 + step, so files never collide.

After both clients finish, the observer releases their close gate. The
server requires two native connection-invalid events, then handles SIGTERM
and exits normally. The observer requires its PID to be reaped and prints
the dormant job with runs=1 and last exit code=0. Both clients remain alive.

The observer then releases the next generation's begin gate. The same two
client processes open fresh connections to the retained Mach service name.
Traffic must activate a different server PID and launchd must show runs=2.
The nine-request sequence repeats for both clients. After orderly closes
and server shutdown, both clients return 0. Final CLI prints check every
job's exit status, followed by two stopped-state heartbeats. The observer
issues print and kill commands only, with no start/kickstart/bootstrap.

The full run therefore covers two service instances, four connections,
four hellos, twelve valid requests and twenty-four rejected requests.
It is a bounded diagnostic fixture, not a production server or a fuzzer.
Unexpected traffic, extra clients or premature disconnects fail the test.

## Independent saved verification

```sh
python3 tools/verify-sweet-xpc-batch.py \
  work/launchctl-foundation-xpc-batch-new \
  --hfsplus research/libdmg-hfsplus-build/hfsplus
```

The verifier extracts the stopped guest RAM root. It checks every
installed file hash, original launchd/xpcproxy, exact job policies, nine
real CLI outputs, ordered request/reply logs, both live-client barriers,
server PID replacement and normal exits. It independently parses all
36 JSON files from the twelve valid exchanges and checks all twelve
server/client reply pairs for byte equality. It also checks per-operation
autorelease-pool drains and sampled framebuffer evidence.

Raw files are under guest/ and the report is run/verification.json.
This scenario does not prove arbitrary malformed-input handling,
unbounded clients, stress/race behavior, NSXPCConnection, UIKit,
SpringBoard, full iOS or any MT6897 driver.

## Verified result (2026-10-30)

`work/launchctl-foundation-xpc-batch` exited 0 with **83/83 checks passing**
after **916.589 host seconds**. The run finished in the background after a
conversation interruption; its saved report and raw files were reviewed
on resume, without another boot. It stopped on the second observer
heartbeat before the 1500-second limit. There were 69 sampled frames,
zero unknown glyphs and no visible panic.

Observer PID 3 and both clients, PIDs 4 and 5, were root children of
original launchd. The first server was PID 7; after its normal exit and
reaping, traffic from fresh connections activated PID 11. Both clients
remained the same processes between generations. The CLI showed runs=0
before traffic, runs=1 for the first activation and runs=2 for the second.
All nine CLI processes exited 0. Final prints for both server generations
and both clients showed last exit code=0; two later heartbeats confirmed
that the final jobs stayed stopped. The Mach service remained registered.

Both generations recorded two simultaneous live connections and all
36 data replies had active=2. Each of the six expected nonzero error
statuses appeared four times, with successful JSON exchanges before and
after rejections on the same connection. Totals were twelve valid and
twenty-four rejected requests. All 36 extracted JSON files decoded to
the expected dictionaries, and all twelve reply pairs matched byte for
byte. Valid-request autorelease pools drained in order.

All **96 installed file hashes**, plus original Apple launchd and
xpcproxy, matched the stopped guest root. Earlier images and results
remained separate. Eight observer compilation modes and both new
Objective-C peers passed arm64 checks with warnings as errors; shell and
Python checks passed. A conflicting Objective-C identifier was corrected
before boot. No kernel change or additional Actions run was needed.

| Artifact | SHA-256 |
| --- | --- |
| Server | `90894c0b02d38a112c4976cb6d6142859fc5f37e937a81f20873d6a108b61e22` |
| Client | `1543a5c511277b84f5f9daea8d3b898a2b246b5594edc17c70c4169bd4b749bd` |
| Observer | `44ca3b85ed2605305ee9bf277dd497333fb12119f6a75f6157ba7651a22d9458` |
| Input root | `62671e29f50f6fd4d97df7a05b2f0d0cbc0d92cca133e011598f9043e41815cd` |
| Payload | `ca55c15c2f94de7a0b25dedfbf29d6c583522abe0d9a3f7e03f0e7c83b9d531e` |
| Exported root | `125024bf1c51cd7bf03d262cecb06eeacf8f77c3da33826c55e7e771502d8206` |

The unchanged kernel was rehashed as
`82fc8fe1391bea90bcce9ed2d4e8a2ff8204667f6785857873717564ec9331c9`;
the original base remained
`491aa78408c423c50e8b59644e416e94b643ed3eb119158d52684af4176c8b3f`.
