# Foundation JSON processing over native XPC in QEMU

This fixture combines the tested [Foundation runtime](FOUNDATION-QEMU.md)
and [on-demand XPC service](XPC-QEMU.md). Both peers are compiled as
Objective-C and use original Apple iOS 16.5 Foundation/CoreFoundation and
libxpc. The observer remains a C process using pinned Procursus FOSS
launchctl 1:1.1.1. Phone USB, UFS and boot partitions are outside this test.

## Replay

Prepare the 82-binary/seven-resource runtime as documented in
FOUNDATION-QEMU.md, then choose a fresh output directory:

```sh
sh tools/test-sweet-launchctl.sh \
  work/ci-104/artifact/kernel.development.sweet \
  work/qemu-multiproc.adt \
  work/launchd-final/root.hfs \
  research/foundation-runtime-20F66-v2/runtime-root \
  research/libdmg-hfsplus-build/hfsplus \
  work/launchctl-foundation-xpc-new 900 foundation-xpc
```

The wrapper compiles the existing XPC peers as Objective-C with
SWEET_FOUNDATION_XPC_TEST=1, blocks, manual reference counting and
Objective-C exceptions. Optional hooks add Foundation processing to the
same transport/lifecycle code. The Foundation selector declarations are
shared with the standalone probe. Other scenarios leave these hooks out.
The observer selects SWEET_XPC_TEST=1 and SWEET_FOUNDATION_XPC_TEST=1.

The copied root grows to 128 MiB and contains the audited runtime, resources,
two peers and observer. The server stays RunAtLoad=false / KeepAlive=false
with its registered MachServices entry; client and observer stay
RunAtLoad=true / KeepAlive=false. The kernel, original base and Apple
libraries are not modified. Installed bytes are verified by re-extraction.

## Combined request/reply path

The observer first requires the registered server to have no PID and
runs=0. Only then does it release the client's begin gate. The client
opens its named native XPC connection and traffic starts the server through
launchd. Both sides check connection PID credentials and executable paths.

Each request keeps the existing eight-field integer envelope and adds a
foundation-json data value. The client constructs an NSDictionary with
device="duchamp", sequence and integer value, serializes it with
NSJSONSerialization, and inserts the NSData bytes with
[xpc_dictionary_set_data](https://developer.apple.com/documentation/xpc/xpc_dictionary_set_data%28_%3A_%3A_%3A_%3A%29).

The server copies the received bytes into
[NSData](https://developer.apple.com/documentation/foundation/nsdata/datawithbytes%3Alength%3A?language=objc),
parses JSON, checks dictionary/value classes and agreement with the native
envelope, uppercases the received device string, and builds a response:
device="DUCHAMP", soc=6897, sequence and XOR-transformed value. It encodes
that dictionary into JSON and attaches its bytes to the native XPC reply.
The client parses the received bytes through Foundation again and checks
all four values. The soc number is diagnostic fixture data, not a hardware
probe of the phone.

Each request encoding, server callback and client reply validation owns
and drains its own NSAutoreleasePool. No Foundation object escapes a pool;
XPC data carries the serialized bytes. Objective-C exceptions in these
hooks become diagnostic failures. JSON data is bounded to 4096 bytes.
As in the previous XPC fixture, synchronous replies run outside the event
handler queue and the whole-VM limit bounds an otherwise unbounded API.

The three valid exchanges retain their expected integer payloads. The
server atomically saves each received request and each encoded reply;
the client saves each received reply. That produces nine JSON artifacts
under /private/var/tmp/foundation-xpc-{request,server-reply,client-reply}-N.json.
The host independently decodes all nine files, checks their values, and
requires each server/client reply pair to have identical bytes. JSON key
ordering is not assumed.

The observer then runs the same six CLI checks as XPC-QEMU.md: dormant
server, both running peers, normal client exit, SIGTERM to the idle server,
and normal server exit. It requires one launch per peer and exit code 0,
with the Mach service still registered afterward. Final heartbeats must
confirm both PIDs stay stopped. It issues no start command to either peer.

## Saved verification

```sh
python3 tools/verify-sweet-ipc.py work/launchctl-foundation-xpc-new \
  --hfsplus research/libdmg-hfsplus-build/hfsplus --transport foundation-xpc
```

The report checks the native XPC lifecycle, the 128 MiB HFS root, every
installed library/resource/fixture hash, the pinned Foundation binary,
the nine independent JSON artifacts and all nine pool drains. Raw files
are under guest/ and the report is run/verification.json. Use --report
with a different host path to recheck an earlier guest without replacing
its original report.

Coverage is one on-demand activation, one connection and three valid
requests, followed by orderly exits. Invalid-input handling, concurrent
clients, repeated activation, high-level NSXPCConnection, UIKit,
SpringBoard and full iOS remain separate work.

## Verified result (2026-10-30)

`work/launchctl-foundation-xpc` exited 0 with **56/56 checks passing** after
**531.312 host seconds**. The VM stopped on the second observer heartbeat,
before the 900-second limit. All 95 installed file hashes matched in the
exported root; original launchd and xpcproxy also matched their pinned
hashes. There were 40 sampled frames, zero unknown glyphs and no visible
panic.

The observer was PID 3, client PID 4 and on-demand server PID 6, all root
children of original launchd PID 1. The initial print showed runs=0 and no
server PID while its Mach name was registered. Releasing the client gate
caused native XPC traffic to activate the server.

All three requests were 46 bytes and replies were 58 bytes. The nine
extracted JSON files independently decoded to the expected dictionaries,
including DUCHAMP, soc=6897 and the sequence-specific transformed values.
Server/client reply bytes matched exactly for every sequence. Each of the
three request pools, three server callback pools and three client reply
pools drained in order.

All six CLI commands exited 0. The client cancelled its connection and
returned 0. The server recorded connection invalidation, handled SIGTERM,
cancelled its connections and returned 0. Final prints showed not running,
runs=1 and last exit code=0 for both jobs. Both PIDs were reaped and stayed
stopped through the final heartbeats; the MachServices name remained
registered.

| Artifact | SHA-256 |
| --- | --- |
| Objective-C server | `2a72fb59c4baa0228cd578639aedb851f131d05dccf057b2f6f1036200749926` |
| Objective-C client | `ef5647df2d8ae691da4158ee99e6880fa7a65a5f5cec7fbcf031dab3bcb56870` |
| C observer | `3085749319a68c6865efc78da4fb9683808284776300a2d696eae38f37cfb694` |
| Input root | `236b7ff7bf6d753f9d70fd97c98f530198035b92da6f47d477ee7ac484ebd628` |
| Payload | `a04f5a411feb1fc09183f9c315f0d6c89396d62b9c0892a097b4f5ab9d66c5b0` |
| Exported root | `e44eddb4efe8a04e0bd9bfd1d91aa67fd8a7997251e6c503842c369d598d8032` |

The unchanged Actions 104 kernel was rehashed as
`82fc8fe1391bea90bcce9ed2d4e8a2ff8204667f6785857873717564ec9331c9`;
the original 32 MiB base remained
`491aa78408c423c50e8b59644e416e94b643ed3eb119158d52684af4176c8b3f`.
No new kernel build was needed.

Seven observer compilation modes, both integrated Objective-C peers, the
old C XPC peers and the standalone Foundation program passed arm64 checks
with warnings as errors. Python and shell checks passed. The earlier
native-XPC guest also passed the extended verifier with a separate report,
`work/xpc-integration-tools-recheck.json`, preserving its original report.
Earlier images and downloaded Apple files remain local and separate.
