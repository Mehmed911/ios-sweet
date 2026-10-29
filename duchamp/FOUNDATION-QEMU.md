# Foundation and Objective-C in QEMU

This fixture loads the original Apple iOS 16.5 restore Foundation and
CoreFoundation with the matching Objective-C, Swift and system libraries.
A small Objective-C program runs as a root child of the original launchd.
The existing Procursus FOSS launchctl observer checks its running state
and normal exit. Phone USB, UFS and boot partitions are outside the test.

## Prepare the runtime

Use the pinned restore APFS and original runtime from
[LAUNCHCTL-QEMU.md](LAUNCHCTL-QEMU.md). A full system-image download is not
needed. Extract into a new directory, excluding an unneeded libextension
symlink that 7-Zip rejects when its target contains parent components:

```sh
7z x -y -oresearch/foundation-new/apple-extracted \
  research/darwin-launchd-20F66/restore.apfs \
  System/Library/Frameworks System/Library/PrivateFrameworks usr/lib \
  '-xr!libextension.dylib'
python3 tools/prepare-foundation-runtime.py \
  research/launchctl-runtime/runtime-root \
  research/foundation-new/apple-extracted \
  research/darwin-launchd-20F66/restore.apfs \
  research/foundation-runtime-new
```

The preparer requires the restore APFS SHA-256
`abf6d0281cffd6fdead38043e0a6291189164d2c06383218adcb95d8dc25efc8`,
pins Foundation and CoreFoundation hashes, resolves required Mach-O imports,
and copies their strong dependency closure plus framework resources into
a fresh runtime. Existing base libraries must match and are not rewritten.
Weak libraries outside the closure are not installed. Apple files stay in
ignored research/ paths and are excluded from Git.

The inspected closure has 82 plain-arm64 binaries / 100,424,416 bytes and
seven resource files. Foundation is 25,031,936 bytes, CoreFoundation
8,506,176 bytes. The dependency audit follows Foundation, /bin/launchctl,
dyld and libSystem and reports missing or invalid files before boot.
source.json records binary/resource hashes and the source image hash.

## Build and run

```sh
sh tools/test-sweet-launchctl.sh \
  work/ci-104/artifact/kernel.development.sweet \
  work/qemu-multiproc.adt \
  work/launchd-final/root.hfs \
  research/foundation-runtime-new/runtime-root \
  research/libdmg-hfsplus-build/hfsplus \
  work/launchctl-foundation-new 900 foundation
```

The Objective-C program uses small declarations for the selectors tested,
with manual reference counting and Objective-C exceptions enabled. It is
linked against the actual Foundation and libobjc binaries. The observer is
compiled with SWEET_FOUNDATION_TEST=1 and does not link Foundation itself.
Both jobs remain RunAtLoad=true / KeepAlive=false.

The builder copies the 32 MiB base image, grows only that new copy to
128 MiB using the existing HFS tool, and verifies its volume header and
host file size. It creates framework directories only when absent, verifies
every installed file by re-extraction, and records all hashes. The payload
embeds the enlarged root; the QEMU runner verifies its RAMDisk range lies
inside the payload's memory window. The kernel is reused unchanged.

## Combined observations

The program must enter after dyld/framework initialization, check root and
parent identity, and create an NSAutoreleasePool. It then checks:

1. NSString uppercase conversion to DUCHAMP and an Arabic UTF-8 round trip.
2. NSDictionary/NSNumber construction with two entries, device and soc.
3. NSJSONSerialization encoding and parsing with value checks.
4. NSData atomic file write/read with byte equality in the RAM root.
5. Throwing and catching a named NSException.
6. Draining the autorelease pool before publishing readiness.

The implementation follows Apple's
[JSON parsing interface](https://developer.apple.com/documentation/foundation/jsonserialization/jsonobject%28with%3Aoptions%3A%29-8demi?language=objc),
[NSData atomic-write behavior](https://developer.apple.com/documentation/foundation/nsdata/write%28tofile%3Aatomically%3A%29),
and [manual autorelease-pool lifecycle](https://developer.apple.com/documentation/foundation/nsautoreleasepool).

After readiness, the observer prints the running PID, writes an exit-release
token, waits for that PID to be reaped, and prints the job again. The second
print must show not running, runs=1 and last exit code=0. No stop signal or
start command is sent to the target. Subsequent observer heartbeats must
confirm it stays stopped. Both CLI child processes must exit 0.

The runner exports the stopped guest RAM disk. The verifier checks all
installed bytes, pinned framework hashes, the 128 MiB volume, ordered
Objective-C markers, and the actual JSON file decoded independently on the
host as {"device":"DUCHAMP","soc":6897}. It also checks real CLI/PID exit
states and sampled framebuffer evidence. Recheck without another boot:

```sh
python3 tools/verify-sweet-foundation.py work/launchctl-foundation-new \
  --hfsplus research/libdmg-hfsplus-build/hfsplus
```

Raw logs and extracted files are under guest/; the report is
run/verification.json. This tests selected Foundation APIs in the QEMU
development kernel. It does not establish all framework behavior, network
services, Foundation/XPC integration, UIKit, SpringBoard or full iOS.

## Verified result (2026-10-30)

`work/launchctl-foundation` exited 0 with **26/26 checks passing**, including
all **94 installed/original file byte checks**, after **315.692 host seconds**.
It stopped on the second observer heartbeat, before the 900-second limit.
There were 23 sampled frames, zero unknown glyphs and no visible panic.

The Foundation program was PID 4, observer PID 3, both root children of
original PID 1 /sbin/launchd. Every ordered marker appeared: pool creation,
uppercase DUCHAMP, five-unit Arabic UTF-8 round trip, two-entry dictionary,
JSON encode/parse, 31-byte atomic file round trip, caught SweetProbe
exception, pool drain and readiness. The independently extracted JSON was
{"device":"DUCHAMP","soc":6897}, regardless of its serialized key order.

The observer's first print showed PID 4 running once. After the release
file, main returned 0 and PID 4 was reaped. The second print showed not
running, runs=1 and last exit code=0. Both CLI processes exited 0 and later
heartbeats confirmed no restart. Original launchd/xpcproxy bytes remained
unchanged. Every copied library, resource and fixture binary matched its
manifest hash in the exported guest root.

| Artifact | SHA-256 |
| --- | --- |
| Objective-C program | `eb121f6730f9bd198b1631bea0ebffaa349893379d3927c894ed88724ba7f1a6` |
| Observer | `88424f24048eb5334b14c8beaa8e8b88ca74fb7985c3028f19068adf0b2890c8` |
| Input root | `ee2c72087cec9fe87500253c0c583ca7f55aa4d78d5e4cc097bc29bd3df5c040` |
| Payload | `1ecf5feaf7f16ef85392c0abf9a9a29bb3c7c58e3e0c68a0799db7a86736b81e` |
| Exported guest root | `096c443f4ab67987ad55f287b256cc88e662aa5c204db204c681bf798f84b271` |

Foundation's pinned SHA-256 is
`182a6fb6d6c51e8e1a70e9152c84cd9d1bd65d2a1f0bda21a4ebe1be446021f2`;
CoreFoundation is
`1bc84069d4292467b750c7aafb4c3114092cb9b5fa906d9c40e61504dc883878`.
The unchanged Actions 104 kernel remained
`82fc8fe1391bea90bcce9ed2d4e8a2ff8204667f6785857873717564ec9331c9`;
the original 32 MiB base remained
`491aa78408c423c50e8b59644e416e94b643ed3eb119158d52684af4176c8b3f`.
The root was grown only in the new copy. Its ADT RAMDisk range was
0x1c24d8000 + 0x08000000, inside the 512 MiB payload memory window.

The successful local runtime is
`research/foundation-runtime-20F66-v2/runtime-root`; provenance/resources
are in its parent source.json. The first preparation attempt hit read-only
base files while trying to rewrite identical bytes. The preparer now skips
such writes; the incomplete first output was retained separately. The
manual broad extraction also recorded one rejected libextension symlink;
it is not required by the audited closure and was not reconstructed.

All six controller modes and the Objective-C program passed arm64 checks
with warnings as errors; Python and shell checks passed. No new kernel CI
build was needed. Full report and raw output are
`work/launchctl-foundation/run/verification.json` and
`work/launchctl-foundation/guest/`. Earlier images/results remain intact.
