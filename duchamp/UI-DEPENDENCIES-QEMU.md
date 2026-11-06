# UI dependencies and CPU IOSurface sharing in QEMU

## Result, 2026-11-06

Actual local Apple executables and launch jobs were inspected, and a new
QEMU probe passed **14/14 checks in 35.806 host seconds**. It loaded the
unchanged IOSurface, Foundation, IOMobileFramebuffer and MiniDisplay libraries,
created a 64x32 BGRA surface, and shared all 2,048 pixels across two independent
executed processes. This is CPU-accessible shared buffer evidence, not a
display swap, Mali acceleration, a complete GUI, or phone validation.

The phone was not accessed this turn. Its last verified state remains original
Android restored after the preceding combined-services trial.

## Actual daemon dependency inspection

Twelve executable/job files (1,738,851 bytes) were selectively extracted into
the new private `work/ui-daemon-scan-v1/apple-extracted` directory from the
existing full OS member `research/launchctl-20F66/096-04088-077.dmg`.
The source is 4,728,546,953 bytes, SHA-256
`64354ba3475d3c34d6fc531f75585a7b24af0fdb7a3a8a2bdf95c7f351a3f290`,
CRC32 `028fc181`, matching its saved IPSW ZIP index. Inputs were preserved.
This is local source provenance, not a new whole-image signature verification.

All six extracted executables are thin plain arm64, subtype 0, iOS platform 2,
minimum iOS 16.5. Strong Mach-O imports were recursively resolved against the
extracted files and existing matching Foundation/cfprefs runtime roots.

| Executable | Currently exposed missing strong paths | Result |
| --- | ---: | --- |
| SpringBoard | 1 | Missing `SpringBoard.framework/SpringBoard` |
| backboardd | 29 | Missing QuartzCore, CoreGraphics, Metal, BackBoardServices, BoardServices, HID and other frameworks/libraries |
| runningboardd | 2 | Missing RunningBoard and RunningBoardServices |
| mediaserverd | 6 | Missing AudioToolbox, CoreMedia, CoreMotion, MediaToolbox, PhotoLibraryServicesCore and libAudioToolboxUtility |
| splashboardd | 8 | Missing UIKit, QuartzCore, CoreGraphics, BaseBoard, Celestial, FrontBoardServices, SplashBoard and SymptomDiagnosticReporter |
| lsd | 0 | Complete strong closure: 88 binaries, 106,575,136 bytes; not yet executed in this new fixture |

Counts are exposed missing paths in the inspected roots, not the final number
of dependencies still needed. An unavailable framework's own imports cannot
yet be traversed. Weak imports, dynamic dlopen targets, signatures, service
protocols and kernel/driver compatibility are separate runtime questions.

The actual jobs assign SpringBoard/backboardd/mediaserverd/splashboardd/lsd to
`mobile`; runningboardd has no explicit UserName. backboardd owns
`com.apple.CARenderServer`, display/HID services and `PurpleWorkspacePort`;
SpringBoard owns the frontboard system-app service and `PurpleSystemAppPort`.
lsd publishes thirteen `com.apple.lsd.*` endpoints and is normally on demand.
The original jobs were recorded, not enabled or guessed from service names.

The full OS file index provides the executable/job paths, but does not contain
the missing UIKit/QuartzCore/board framework binaries or a dyld shared cache.
The saved manifest maps Cryptex1,SystemOS to `096-04666-078.dmg`; only a partial
local copy was found in the inspected paths. No extra download was performed.
Do not infer that directory/resource entries contain executable library bytes.

## Available lower graphics libraries

Standalone originals from the small restore extraction exist at
`research/foundation-20F66/apple-extracted`:

| Library | Bytes | SHA-256 |
| --- | ---: | --- |
| IOSurface | 301,936 | `9e35ccdd66a72d02809741d476bb67eda4462a198c790267ae19b66fc8ecac53` |
| IOMobileFramebuffer | 169,216 | `c28d2dfa6117eaad413eb3d88c79ae183e234af4defe42d938783620103f62b6` |
| MiniDisplay | 109,632 | `ec987046344826d11e0b6a8380847c17e6be277622b6cc5fef6e341c6e4d7bd5` |

Their combined strong closure is 81 binaries. Framework resources from the
pinned Foundation runtime are also preserved. The audit rejects conflicting
provider bytes and unresolved paths rather than assuming compatibility.
Six public-input unit tests passed: missing required imports, weak-import
scope, conflicting providers, arm64e rejection, unresolved rpaths and traversal.

## Actual QEMU execution

`tools/test-duchamp-ui-surface.py` copies the original single-service launchd
RAM root, grows only the new copy to 128 MiB, installs and verifies the closure,
and replaces its job with `org.sweet.qemu.ui-surface`. The legacy job filename
is retained; the installed label and program are explicitly different.

It reuses phone-proven kernel SHA-256
`e465723a540844817a5b9cb36c14984d660f9a8e41f6638240527b469189182b`
and QEMU-specific ADT SHA-256
`a881410d04a3cec3b7ebd9bee91f510c755683b94f5a26d71c47301fff7417d8`.
No kernel patch, phone image, physical UFS or hardware MMIO is added.

The new Objective-C probe runs as PID 3, a root child of original launchd.
It loads the original libraries, creates surface ID 2 (stride 256, allocation
16,384 bytes), locks/writes it and verifies same-process lookup. A fresh
posix_spawn/exec child PID 4 looks up that ID, checks every pixel and rewrites
every pixel with a second pattern. After normal child exit, PID 3 verifies
the complete writeback and saves an exact result file. It flushes HFS data
and catalog before publishing each stop-capable heartbeat.

The saved guest has ordered parent/child logs, two or more heartbeats and the
exact result. All 90 installed files plus original launchd/xpcproxy match their
recorded hashes. Test sources were frozen before compilation and match the
current sources. An independent read-only review found no material issue.

The public API calls follow Apple's [IOSurface functions](https://developer.apple.com/documentation/iosurface/iosurface-functions?language=objc),
including [atomic ID lookup](https://developer.apple.com/documentation/iosurface/iosurfacelookup(_:)?language=objc).
IOMobileFramebuffer's exported GetMainDisplay symbol is resolved but never
called. No display swap, GPU command, physical DMA/cache contract or input
event is exercised. The built-in SweetSurface implementation supplies the
tested kernel-side sharing; this does not authenticate Apple's closed driver.

## Evidence and replay

| Private artifact | SHA-256 |
| --- | --- |
| `work/ui-dependencies-v1/audit.json` | `74aaaed40f1292e72eab934a4edd3c78165d63b31a78a7d581f90a4c5b792b26` |
| `work/ui-daemon-scan-v1/audit.json` | `d2548ff02dd2c53383a42e22ce20eabef8853f50cd4459a057c3f46fdd2cd980` |
| `work/ui-daemon-scan-v1/extraction-receipt.json` | `2e51fe8085ebce51f8d40b177d127241b692a4d025fed4217740ce71b10b9898` |
| `work/ui-surface-qemu-v3/evidence/verification.json` | `3b1ae8542e0f84beb341ec25d5ad2634a99bcdc767d9044b21bfcdace81ccdb9` |
| QEMU payload | `1d0f3987c54d40309c8ac976ed3564091729cac321f727a63abef3a979340087` |
| Initial HFS root | `10ed2fc8043e5c8d0515e2544bb741b82fd49ab6357c7589ac5d14f943f1d524` |

The full private daemon summary and original job dictionaries are
`work/ui-daemon-scan-v1/{summary,launchjobs}.json`. The extraction receipt
contains the exact local 7-Zip command, source checks and extracted hashes.
Use new paths when repeating; no downloaded Apple binary, dump or private
artifact is part of the commit.

```sh
python3 tools/audit-duchamp-ui-runtime.py \
  --root research/cfprefs-runtime-20F66-v2/runtime-root \
  --root research/foundation-20F66/apple-extracted \
  --require /System/Library/Frameworks/IOSurface.framework/IOSurface \
  --require /System/Library/PrivateFrameworks/IOMobileFramebuffer.framework/IOMobileFramebuffer \
  --require /System/Library/PrivateFrameworks/MiniDisplay.framework/MiniDisplay \
  --output work/ui-audit-NEW.json
python3 tools/test-duchamp-ui-surface.py \
  --audit work/ui-audit-NEW.json --output work/ui-probe-NEW --seconds 600
python3 tools/test-audit-duchamp-ui-runtime.py
```

The first preparation attempt v1 hit the old HFS helper's catalog-delete
assertion before QEMU. The copied job is now replaced in place. v2 showed all
CPU-sharing runtime markers, but saved HFS logs/result were absent, so the
host verifier correctly rejected it. The sync-before-stop change produced
v3's full saved-evidence PASS. All failed artifacts remain preserved.

## Next bounded checkpoint

Test the original `lsd` in a separate QEMU fixture using its actual job,
mobile identity and native endpoints. Record startup, any dynamically missing
dependencies and a bounded client request before attempting higher UI jobs.
Strong closure alone does not establish successful daemon execution. Obtain
and audit the matching missing GUI frameworks before attempting SpringBoard
or backboardd. Phone UFS, firmware ownership and Mali remain independent work.
