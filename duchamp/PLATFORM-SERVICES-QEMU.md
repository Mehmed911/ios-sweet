# Original platform services and UI daemon probes in QEMU

## Runtime scope

The batch uses original 20F66 launchd, xpcproxy, dyld, the intact shared cache,
logd, containermanagerd and lsd. After the native LaunchServices response is
verified, an optional second phase starts original runningboardd/backboardd.
All execution is in QEMU. No phone connection, partition write, physical UFS
or Mali test occurred. SpringBoard was not started and no GUI frame was proven.

On 2026-11-07, V9 passed all 13 core checks and all four requested UI checks
in 117.640 host seconds. Original logd (PID 7, UID/GID 272),
containermanagerd (PID 5, root), lsd (PID 13, mobile), runningboardd
(PID 19, root) and backboardd (PID 22, mobile) retained their verified
identities across six five-second health samples. Separate native mobile
clients, PIDs 16 and 25, received the LaunchServices callback before and
after the UI phase. All 134 installed-file roundtrips matched; source root,
base image and tested sources were unchanged. The saved root and exact
`PLATFORM SERVICES DONE status=0` marker were both verified.

V6 had passed only the initial UI process checks in 85.266 seconds. The longer
V8 follow-up caught backboardd aborting near the sixth health sample because
its original event-processor configuration was missing. V9 adds that exact
source resource and passes the full health/response stage. Failed runs are
preserved with their original verdicts. Each run preserves its own input disk
and frozen sources. Timings exclude source acquisition and root preparation;
this is a short diagnostic observation, not a long-term stability guarantee.

## The concrete crash fix

The first combined runs kept logd/lsd alive but containermanagerd repeatedly
segfaulted. Explicit root/System launch context fixed an unwanted user-domain
relocation, but did not fix the fault. Adding the matching SystemVersion.plist
also did not fix it; both failed trials remain preserved.

A QEMU hardware breakpoint at the pinned kernel's EL0 synchronous vector
captured the user registers and frame-pointer chain before the fault handler.
The capture has `FAR_EL1=8`, `x0=0`, and the matching cache slide. Symbolication
of the actual frames identifies:

```text
__CFGetNonObjCTypeID + 88
CFDateFormatterSetFormat + 52
CFDateFormatterCreateISO8601Formatter + 812
-[NSISO8601DateFormatter init] + 140
___43-[MCMMigrationStatus _iso8601DateFormatter]_block_invoke + 44
```

The minimal root lacked `/usr/share/icu/icudt70l.dat`. Adding the original
matching ICU data and format file stopped that repeated crash. The programs
and kernel were unchanged. The new client separately verifies the original
NSISO8601DateFormatter produces `1970-01-01T00:00:00Z` for epoch zero in GMT.
V5 and subsequent trials kept the three providers alive and received a real
LaunchServices callback. This is a resource/initialization fix in the QEMU
root, not a new MT6897 driver.

| Original resource | Bytes | SHA-256 |
| --- | ---: | --- |
| `/usr/share/icu/icudt70l.dat` | 30,447,056 | `d2d5f82e30f4c193d48da78604381fa551adab548e2533e1ae6139538336f736` |
| `/usr/share/icu/icutzformat.txt` | 3 | `327d09f9e798492441b2a7839e2ce11498c64ae4c36ea98e248b89c5fc3172fe` |
| `/System/Library/CoreServices/SystemVersion.plist` | 570 | `46457f81a04a81f462bfa0ab24693eff2140ce81a254e64354e43bd0b996dd22` |
| `/System/Library/BackBoard/EventProcessorConfiguration.plist` | 1,313 | `1360a59a33789cebea9db2f652ddaf42c6978158a98c2fce72cb43810ea9ed01` |

These were extracted from the previously SHA-verified matching full-OS image.
For these bounded extractions its exact size/mtime matched the prior receipt;
the large source hash was inherited, not freshly recomputed. Extracted file
sizes/hashes and the SystemVersion build/version are checked independently.

## A real response, and the meaning of 0x300

The client runs as a separate mobile job created by the original launchd.
Merely changing the UID of a system-bootstrap fork child had produced XPC
error 4099. A native user job supplies the corresponding bootstrap context.

The read-only request uses the original CoreServices proxy factory and the
registered `_LSDReadService`/`_LSDServiceDomain` classes. The completion block
records its invocation separately from the error handler. The original
`_LSGetStatus()` wrapper must then return the same value. Its default zero
alone is never considered response evidence.

The server method calls `_LSDatabaseGetSessionStatus`; the result is an
unsigned bitfield, **not OSStatus**. Inspection of the matching binary shows
`0x100` set for `isSeeded`, and `0x200` set when `isSeedingComplete` is false.
The inspected CoreServices UUID `BE76D898-0FFF-3A71-B63F-3C609B6F7742` matches
the image in the live source cache. The observed `0x300` therefore proves a
reply with seeded state and incomplete seeding; it does not establish a ready
application registry. The early V5 verifier incorrectly required zero and
failed despite the observed callback; that historical failed report is kept.
Six regression cases cover the corrected distinction, wrapper-only default
zero, contradictory/out-of-range values, transport errors and duplicate replies.

The final client records:

```text
LSD NATIVE ICU ISO8601 PASS 1970-01-01T00:00:00Z
LSD NATIVE STATUS REPLY status=768
LSD NATIVE QUERY RESULT reply=1 error=0 status=768
LSD NATIVE WRAPPER status=768 matches=1
LSD NATIVE DATABASE seeded=1 seeding_complete=0
LSD NATIVE TRANSPORT PASS status=768
```

These are LaunchServices response checks. The other daemon identity checks
are short process-liveness observations, not proof of every private RPC,
display service, assertion-management operation or long-term stability.

## Separate large RAM fixture

`tools/qemu-service-ram.py` builds a new 10 GiB sparse, file-backed QEMU RAM
mapping on the native Linux disk. The kernel-managed window is 4 GiB; the
3 GiB HFS+ md0 contains the original cache plus writable service state. Kernel
segments, ADT, boot arguments and the root are streamed into their validated
ranges, avoiding whole-image Python byte strings. At a stopped guest the
shared RAM backend supplies a saved HFS+ range for log and installed-file checks.
The source image is hash-checked unchanged after execution. The 10 GiB backing
file is retained natively and excluded from exported copies.

This is a separate QEMU layout. The phone ADT/512 MiB payload path, kernel
artifact and existing runner were not modified. The kernel remains
`e465723a540844817a5b9cb36c14984d660f9a8e41f6638240527b469189182b`.
The new layout first booted the original small launchd root through its C
service heartbeat 3 in 45.089 seconds. Six layout safety tests passed.

Provider binaries, native job arguments/Mach names and source policies are
hash checked. Diagnostic job changes are recorded: output redirection,
KeepAlive false and crash-loop panic suppression; MCM's intended root/System
context is explicit. UI jobs start only after the core reply gate, with
runningboard's root/System context explicit and backboard's native mobile
identity retained. The source accounts and feature-flag files are preserved
in the copied root. None of the services was replaced with an empty stand-in.

The follow-up test clears the native client's old output before a new request
and assigns it to mobile. V7 exposed a harness defect: creating that file as
root:root 0644 caused xpcproxy EACCES for the mobile job, so the verifier failed.
The ownership is now explicitly 501:501; neither checks nor service credentials
were relaxed. Four verdict tests require all requested UI checks, including
health samples and the repeated native response, to affect the overall result.

## Private evidence

| Artifact | SHA-256 |
| --- | --- |
| Small-root RAM-loader baseline result | `72fae2df6854c8fd9c15b9da7256756ac74484d5c9e00270c10f3c34c586a394` |
| `work/platform-null-trace-v1/null-fault.json` | `5601fc1a59d99513e95ed0e00c2840a0fa17967260279b22599920fc63331bb5` |
| CoreServices UUID identity receipt | `3fcff4b6eebc49ec510f7f6288a860f6e0ddb62d04af62f6a1c07b3804ab6159` |
| Source status-bit disassembly excerpt | `ee8be1e7fa844acb109fe263be4b036cc457b8f29c71ec63fdc2f15ca3c1108f` |
| ICU extraction receipt | `f54d767fc93a4eadaa69c1c0435c42c27e04aad3785375a498094173e8640ebe` |
| SystemVersion extraction receipt | `85f0d140762e61131fcc8957558affb81001f6f2b371bfc9a92cc349e920feb8` |
| V6 verification | `e28cc0f30fff9d721c0bb32dc8812f91dd370facb15c06037f6425e3daa78c37` |
| V6 inputs | `8feb1d15ac1e3c7bdea121ba461e6edeecee47d1ee853a65dfef5cc7031b530a` |
| `work/platform-services-qemu-v9/evidence/verification.json` | `2fa5bf57b43f00258dd7dab6c9d31bd1b63457ec2b0a528305447e2210067ab2` |
| V9 inputs | `010c5ee20955ea026ff0dc366e9cc192a66490f1f57cf9198d7c63d0c458ba7b` |
| V9 source root | `da5a0c9ef7d9a9002c642f01f731a5c4b8b37d4dc74a342104e4aa00a930dc6f` |
| V9 saved controller log | `48d44e790496d0da13116504303fa9c163654ad0882da2ca6f8c6e4c32d27528` |
| V9 first native reply | `b2ff983327505d44759ae45c908e4a1152876d85d4717c7595ec267e6599636c` |
| V9 native reply after UI | `cbfb232faf951d92c40cc8d3ff955bf6fd1d87711549dcc1842da8fdd49f98c4` |

Detailed artifacts, downloaded Apple files, accounts, original jobs and all
failed runs stay private under `work/` and the native working directories.
The GDB diagnostic used WSL gdb-multiarch 17.1; its eight local dependencies
added 52.1 MB. The breakpoint reads the guest exception state and user stack;
it does not patch guest instructions or access a phone.

## Replay

Use Ubuntu/WSL with the already acquired private prerequisites from the
[source cache](SYSTEMOS-CACHE-RECOVERY.md), [intact-cache runtime](SHARED-CACHE-QEMU.md)
and matching resource receipts above. Existing output directories are refused.

```sh
python3 tools/test-qemu-service-ram.py
python3 tools/test-duchamp-ls-status.py
python3 tools/test-platform-service-verdict.py
python3 tools/test-duchamp-platform-services.py \
  --output work/platform-services-NEW --seconds 360 --ui-probes
```

Without `--ui-probes`, only the three-provider/native-response stage runs.
This is not a clean-checkout fixture: private original runtime/cache/resource
artifacts and existing compiler/HFS/QEMU tools remain required. Source scripts,
compiler output, original policies and installed-byte roundtrips are retained
with each run. See the result JSON's explicit scope before using any milestone.

The longer UI check is material: V8's original backboardd emitted an uncaught
`NSInternalInconsistencyException` from `BKHIDPrimaryEventProcessorFactory.m:55`,
reporting Cocoa 260 / POSIX ENOENT for the event-processor plist. A three-second
startup check had missed that delayed failure. The original 1,313-byte plist
is installed without changing its classes or processor chains. The controller
now records each of the five process identities in every health sample and
attempts the final LS query whenever lsd remains alive, even if a UI daemon
fails; a UI failure still prevents overall success.

The final backboard log still warns that `_BKRuleResolutionTranscript`
exists in both the daemon and BackBoardHIDEventFoundation. No assertion,
display/input operation or resolution of that warning was established by
the liveness checks. The fixture can also see an initial logd SIGTRAP before
the controlled kickstart; success describes the selected, verified processes
and response interval, not a boot with zero process exits.

The subsequent [native UI-readiness fixture](UI-READINESS-QEMU.md) verified
completed LS session seeding, a registered original SpringBoard bundle and
actual BackBoard display MIG replies. It also records guarded SpringBoard
trials and their concrete failures. Process liveness and display-query replies
do not prove rendered output or input delivery. Physical MT6897 storage,
resource ownership and graphics remain separate unproven work.
