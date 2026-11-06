# Native application-registry and display-service checks in QEMU

## Verified boundary

The final V6 fixture passed **22/22 checks** (18 core/order/process checks,
four UI-provider checks) in 187.382 host seconds. All 294 installed-file
roundtrips matched, with unchanged source root, base image, test sources and
kernel. Original SpringBoard PID 34 ran as mobile with launchd parent and exact
program path, then retained that identity across six five-second health samples.
Its bootstrap occurred only after native readiness and its installed bundle
record were verified. The exact successful stop marker was captured.

This is a successful **process/readiness test**, not a proven graphical boot.
The saved final framebuffer was visually inspected and shows the diagnostic
console, not a lock screen or home screen. `full_gui_ready=false` and
`rendering_verified=false` remain intentional. The observation is short; it
does not establish long-term stability or phone compatibility.

On 2026-11-07 the V3 readiness fixture passed 15 core checks and four UI
health checks in 142.138 host seconds. All 141 installed-file roundtrips
matched. Original launchd, dyld, the intact 20F66 cache, the existing five
providers and original installd ran locally. No phone, ADB, partition write,
physical UFS or Mali operation occurred. Kernel and source images were unchanged.

LaunchServices returned `0x100` before and after a separately witnessed native
rebuild callback: seeded and seeding complete. This is a session-state bitfield,
not OSStatus. V3 does not establish an inventory of all original applications,
or even a successful lookup of SpringBoard's own application record.

Two original BackBoard display MIG requests returned kernel status zero and
overwritten outputs `(1125, 2436, 1, 0)`, with two zero byte flags. This proves
the native reply path, not rendering or physical panel geometry. The four
float slots are deliberately kept opaque; no semantic meaning is assigned
to the fourth zero. The display profile is not a hardware-discovery result.

V4 additionally verified a native, installed, non-placeholder SpringBoard
record with the exact original bundle path. Original SpringBoard was attempted
and exited because `libobjc-trampolines.dylib` was absent. This trial failed
overall; the verified record and display replies do not establish GUI success.

## Changes supported by the failed trials

| Trial | Host seconds | Actual outcome |
| --- | ---: | --- |
| V1 | 121.648 | Existing providers stayed alive; rebuild callback denied with NSOSStatus `-54`. Display returned native replies but the first checker incorrectly required the fourth scalar to be positive. Overall FAIL retained. |
| V2 | 138.168 | Exact client entitlement fixed the denied rebuild; callback reported success and both display requests passed. LS remained `0x300` across 15 samples. Overall FAIL retained. |
| V3 | 142.138 | Added original installd/job, its native account home, scan directories and matching original SpringBoard Info/executable. LS was already `0x100` at the first query and remained complete after rebuild. Both display replies passed. Overall PASS. |
| V4 | 162.624 | Full original bundle installed; native SpringBoard record and readiness passed. SpringBoard PIDs 4 and 35 exited with an explicit missing Objective-C trampoline-module error. All 178 installed hashes matched; overall FAIL retained. |
| V5 | 176.208 | Recovered original module loaded; deferred bootstrap occurred after readiness. Original SpringBoard PID 34, mobile, passed identity and the first two health samples, then exited before the third. All 179 installed hashes matched; overall FAIL retained. |
| V6 | 187.382 | Added original icon/font resources. Native registry, SpringBoard record, display replies, bootstrap ordering and all six SpringBoard health samples passed. All 294 installed hashes matched; 22/22 PASS. Rendering remains unverified. |

The V3 additions were tested together. This trial does not isolate the causal
effect of each added file. Original installd's UID/GID 33 and launchd parent
were checked. Its original credentials, arguments and Mach name are retained;
diagnostic output/no-restart overrides are recorded in `inputs.json`.

Only the diagnostic client is ad-hoc signed with
`com.apple.lsapplicationworkspace.rebuildappdatabases=true`. The exact key is
read from the matching CoreServices entitlement constant and its server
authorization branch. The offline signer is pinned and its XML output must
roundtrip to exactly that one key. Original Apple executables and the kernel
were not patched. No readiness bit is written directly by the client.

## Native interfaces and strict verdicts

The registry client uses the matching CoreServices proxy factory,
`_LSDModifyService`, the registered service domain, and
`rebuildApplicationDatabasesForSystem:internal:user:completionHandler:`.
The separately recorded callback, transport-error state and returned NSError
code must all agree. Readiness requires an independently witnessed subsequent
read response whose seeded bit is set and incomplete bit is clear.

The display client uses `BKSDisplayServicesServerPort` and the exported
`_BKSDisplayGetMainScreenInfo` MIG stub from the intact live cache. Disassembly
of that exact image shows a port, four float pointers, two byte pointers and
the validated reply return code. Unlike the convenience getter, this exposes
the MIG error. Sentinel outputs, errors, nonfinite/invalid values, missing or
duplicate samples and contradictory exits cannot pass. The initial positive
fourth-scalar assumption was a checker defect; failed V1 evidence is unchanged.

Seven parser regression cases cover missing callbacks, denied operations,
incomplete/zero bitfields, fake success markers, MIG errors, unchanged/nonfinite
outputs, contradictory exits and the additional SpringBoard record gate. The
existing four overall-verdict regressions also passed. Runtime sources compile
with `-Wall -Wextra -Werror`; every trial retains its exact source snapshot.

## Original resource provenance

The bounded resources come from the already verified full 20F66 OS image
`64354ba3475d3c34d6fc531f75585a7b24af0fdb7a3a8a2bdf95c7f351a3f290`.
These extractions inherit that prior source hash after exact size/mtime checks;
the large image was not freshly hashed. Each extracted byte count/hash is checked.

| Resource | Bytes | SHA-256 |
| --- | ---: | --- |
| SpringBoard Info.plist | 4,367 | `2357c9d12af0d70ec201d5566d093e06da6ab6da3c48374c593cad2663839c7a` |
| SpringBoard executable | 112,048 | `7926a1ba0b115cf45102b2c3d8e4eb7bc9c84bcf70b573d2a798690d9148059c` |
| installd executable | 608,880 | `c14c7ec19117b200a0c1f3b21b33e0d40fb11fa39624f1bdef87c88d5a01d74c` |
| Original installd job | 664 | `4abce2ac51d7fe1bc4a6ec9011c33b3e0a889313f8b7ab09326846bb145edb2d` |

The full SpringBoard bundle has 38 files / 2,202,072 bytes. Its bounded-listing
extractor first rejected directory entries with empty Size; that failed output
is preserved. The corrected extraction verifies the original executable hash
and all listed regular file sizes. Files and receipts remain private.

The missing 68,080-byte Objective-C trampoline module resides in the matching
SystemOS image, not the full-OS root. 7-Zip rejects its ZBM resource-fork
compression. The existing read-only apfs-fuse adapter now accepts one additional
explicit component, `objc-trampolines`, restricted to `usr/lib`, inode 3136,
algorithm 14 and the exact decoded length. Cache-component routes retain their
old paths/inodes/sizes. The entire SystemOS image was freshly SHA-256 checked
before extraction. Decoder output hash is
`a5410b215468c275e1f861c7e605f58401e332f7f23765a6e1fbe7391d4f05df`;
Mach-O inspection reports original standalone arm64/iOS 16.5, signature metadata,
and a single strong libSystem.B import. Existing-output refusal with unchanged
hash, unsupported component refusal, and invalid-image/no-output checks passed.
This is decompression, not a derived cache export or executable patch.

V4 also showed that RunAtLoad=false alone did not prevent launchd from starting
the original EmbeddedHomeScreen job before the controller's readiness gate.
The corrected fixture installs that job under `/private/var/tmp`, verifies it
is absent from LaunchDaemons, then bootstraps it only after the native registry,
bundle-record and display gates. The verifier checks that ordering separately.
V5 verified the corrected order, module loading and actual SpringBoard identity.
Its 30-second health gate rejected a later process death rather than promoting
the first successful process check to GUI success.

V5's native exception is `NSInvalidArgumentException`, inserting a nil object
into an NSDictionary during icon preparation. The live cache base and matching
cache mapping establish slide `0x44630000`. Symbolication of the actual throw
stack identifies `ISImageBagIcon::_generateImageWithDescriptor: +328`, through
the generic-icon preparation path to SpringBoardHome's root-icon precache.
Bounded quiet disassembly and named call-stub lookups connect that dictionary
slot to a default application/App Clip asset-bag getter. This attributes the
nil producer path; it does not identify which branch/resource by runtime
register capture. The cache-wide disassembler hit its own host memory error;
it was not a guest kernel failure, and that output was not used.

The same runtime logs show missing original Helvetica.ttc/SFUI.ttf and fallback
fonts. V6 adds the exact original IconServices/MobileIcons resource trees and
those two fonts: 115 files / 9,788,380 bytes, each extracted-size/hash verified.
These are original resources, not replacement images or a patched nil check.
The additions were tested as a batch. The previous nil-dictionary exception
did not recur in V6's observation window; the exact individual resource causing
the improvement was not isolated. SpringBoard's saved stderr retains
`PLClientLogging: unknown permission type 2`.

Native failed lookups still include mobilegestalt, iconservices, searchd,
sessionservices and donotdisturb services. These are concrete follow-up leads,
not proven explanations of the absent graphical output. The next boundary is
native compositor/window-server state and actual presentation, together with
the service requests that block that path. Process health must stay separate
from that verdict.

## Evidence and replay

| Private artifact | SHA-256 |
| --- | --- |
| V1 verification | `def74201b8f7d6ff05ca15cf66f34d6e4d4e37aad92555e8f51328e0e1659e98` |
| V2 verification | `851effc52e8c044eeb849f7d111ac2456b7acb4cc6795e27ac023c1ab28c99a6` |
| `work/ui-readiness-qemu-v3/evidence/verification.json` | `84dfe91284fcace03c6b82418e9a26c09f440638517d0895af13f633dc0b73cc` |
| V3 inputs | `44991117dfdc4d57d6b04be3434f6da6cec76451e2ff16eaaa27669cc51e3d8b` |
| V3 registry log | `86c2a57b3b2d2b498e6cbcaf47c95abee9363bded69834edcf23ed9343a0d3bd` |
| V3 display log | `61fa7b7b8bbd24555862a16696f0ec2bc6a7bfd5416ac2984713c3a41dfb8712` |
| Installation/minimal-bundle resource receipt | `3b5f048c8554ae7b0396af5c5075df5995f089cc7f07343f9dcbbe9ef14c7901` |
| Full SpringBoard bundle receipt | `f2de94690e2fe824b4cf9d42ff665fcaee0efcdac5c82f80576021cb45d04fac` |
| V4 verification | `df28aa943c608508f71bafee95d8f177fcbd1688168d9f94beca0c3816af82c1` |
| Original trampoline decoder receipt | `c39473bd1118fc00d2ef4354dba477acbdef6e65ce155e2def5f2f87ac581c7f` |
| V5 verification | `75ab01846bcdceb5344970b6bd78803b7fa9b2ebc457c72d8687bb2eda5c9406` |
| Original icon/font resource receipt | `d4ffb35a6e3b476a42132b2c09132dcc2901349ac9ffc46571255881e3685b3c` |
| `work/ui-readiness-qemu-v6/evidence/verification.json` | `7d91e37d0e651b62ec251935ade0875a3a1a7fa8beb1f858bcf68871570c5dfe` |
| V6 inputs | `f2dc87ed1dec48e387b7613cfcda538b3d44275724964c41dfc55cd4fe879d56` |
| V6 source root | `8029fb33aa7805e773e10848f05af0f85349a1e1c9fe1e3dcea35890f3f9c171` |
| V6 controller log | `1a26cc92e1a2e250513bf4d7888f1f9918cc15e87f5b774b4a78037543e5b787` |
| V6 registry log | `885d365497603dd5030ee336d0b1f603abcf5ebb29eb2d85c6e35e420e61e8b7` |
| V6 display log | `e44f1ff671e334bf6994fc01baba9f12d0ccbee7c13b42c8c8fcd65280f7c76d` |
| V6 visually inspected final framebuffer | `3eaa8aa14c9c236d9b6858b1f093846aa094993b8a9864d7c02a5acce8bc5dcc` |

```sh
python3 tools/test-duchamp-ui-readiness.py
python3 tools/test-platform-service-verdict.py
python3 tools/test-duchamp-platform-services.py \
  --output work/ui-readiness-NEW --seconds 360 --ui-probes --readiness
# Additional bundle-record gate and bounded original SpringBoard trial:
python3 tools/test-duchamp-platform-services.py \
  --output work/springboard-NEW --seconds 300 --ui-probes --readiness --springboard
```

Private prerequisites from [the platform fixture](PLATFORM-SERVICES-QEMU.md)
are required; existing output directories are refused. This remains the
separate large QEMU RAM layout, not a phone image. V3's passing source is
frozen with its evidence; later SpringBoard gates are additional tests.
