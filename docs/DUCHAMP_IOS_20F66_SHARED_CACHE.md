# iOS 16.5 / 20F66 intact shared-cache integration

Validated in QEMU on 2026-11-18/19. Physical status remains
`BLOCKED_BY_MEMORY_EVIDENCE`. No phone, ADB, Fastboot, physical UFS,
firmware, slot, commit or push operation was performed.

## Result

The two previously missing load-time dependencies are present in the user's
matching cache. A separate 3 GiB RAM-root boots the **existing source-linked
XNU**, maps that cache, runs original launchd as PID 1, and starts original
backboardd and SpringBoard through launchd. BackBoard returns two native
display-information replies; both processes pass six five-second identity
checks. This establishes dependency/startup progress, **not rendered iOS UI**.

Evidence directory, relative to the repository: `../../outputs/duchamp-ios20f66-integration-20261118/`.
The compact `native-primary/` records are sufficient to review the native-job
observations; private images and complete logs remain in `native-jobs-1/evidence/`.

## Original executable metadata

| Field | backboardd | SpringBoard |
|---|---|---|
| Path | `/usr/libexec/backboardd` | `/System/Library/CoreServices/SpringBoard.app/SpringBoard` |
| Bytes | 1,182,960 | 112,048 |
| SHA-256 | `686f26a6a7b749fd0ae30acca704022da8cb6f85b5c39a0e0e09e25ffd00d273` | `7926a1ba0b115cf45102b2c3d8e4eb7bc9c84bcf70b573d2a798690d9148059c` |
| UUID | `E81FD7FD-034F-3195-A4F5-3C692536E5AA` | `40EC75F0-76C1-3DEB-85F1-39369B09E9D5` |
| CPU/subtype | ARM64 / 0 | ARM64 / 0 |
| Platform, minimum, SDK | iOS, 16.5, 16.5 | iOS, 16.5, 16.5 |
| Interpreter | `/usr/lib/dyld` | `/usr/lib/dyld` |
| LC_MAIN file offset | 38500 | 16296 |
| LC_RPATH | none | `@executable_path/Frameworks` |
| Direct imports | 45 strong, 1 weak | 4 strong |

Both are executables, so neither has an LC_ID_DYLIB install name. Their raw
load commands, CodeDirectory metadata and entitlements are saved in
`backboardd-macho.json`, `SpringBoard-macho.json`, `*-signature.txt` and
`*-entitlements.plist`. The observed CodeDirectory is ad hoc; its presence or
computed hash is not an independently verified Apple signature chain.
No executable was patched or re-signed in these trials. They match the
pre-existing local extraction receipts. No arm64e subtype occurs in either
executable or its recursive strong cache closure. This is not a claim that
every unexecuted instruction path or private ABI is supported.

## Cache identity and provenance

- Main UUID: `E5420DB3-30D0-33AA-8B7E-05B5038BB46D`.
- Format: `dyld_v1   arm64`; platform iOS; reported OS version 16.5.
- Main cache plus 42 runtime subcaches: **43 files, 2,722,512,896 bytes**.
- An additional `.symbols` file is not required at runtime. Its separate UUID
  is `DB615077-8DAA-3B6E-836D-D965E18ADA97`.
- 2,710 Mach-O records, including dyld's LC_ID_DYLINKER record.
- Runtime UUIDs match the inspection tool's mapping UUIDs. There are 51
  non-overlapping runtime mappings from `0x180000000` through `0x229eec000`;
  mapped bytes total 2,716,762,112. The full reserved span is 2,850,996,224 bytes.
- All 43 file sizes and SHA-256 values match
  `work/20F66-cache-v4/receipt.json`, receipt SHA-256
  `30eb89efbe8fb1c63b6599a9ecffad13b6b956f644e9ef91cf351b61b97f1fab`.

The acquisition record identifies Apple's iPhone10,3/iPhone10,6 16.5 20F66
restore, with SystemOS member `096-04666-078.dmg`, SHA-256
`2279bf443856fcb6a3f00b1fa06a32ba02a66fdf6ab6b12019462c7498aafdd3`.
The existing receipt distinguishes ordinary extracted components and lossless
ZBM recovery. These provenance and byte-integrity records are not a new
cryptographic verification of the restore's secure-boot chain. No third-party
dump was downloaded and no Apple binary was published.

`StudyLog.framework/StudyLog` and `SpringBoard.framework/SpringBoard` are
cache images, not empty replacement framework files. The experiment installs
the intact runtime cache rather than exporting cache-only Mach-O images as
standalone replacements. Cache structure references:
[Apple dyld cache format](https://github.com/apple-oss-distributions/dyld/blob/main/include/mach-o/dyld_cache_format.h),
[DyldSharedCache interface](https://github.com/apple-oss-distributions/dyld/blob/main/common/DyldSharedCache.h).
These references explain the format; the local receipts establish these files' identities.

## Recursive dependency graph

`tools/audit-duchamp-20f66-closure.py` consumes the actual 2,710 JSON records
from `ipsw dyld macho --all --json`. It includes the verified standalone LC_LOAD_DYLINKER interpreter, follows strong imports recursively,
handles cycles, records weak edges separately, accepts earlier minimum OS
versions, rejects architecture/platform mismatches, and leaves unresolved
runpaths unknown. Results are in `dependency-closure.json`:

| Entry | Strong-closure nodes including executable | Recorded import edges, including weak | Missing strong paths |
|---|---:|---:|---:|
| backboardd | 267 | 2,381 | 0 |
| SpringBoard | 1,005 | 16,150 | 0 |

`PRESENT_IN_SHARED_CACHE` means static availability, not successful execution
of every ABI. `AVAILABLE_AND_COMPATIBLE` for the executable is explicitly
limited to ARM64/iOS deployment metadata. No `ABI_INCOMPATIBLE` label was
invented from the absence of execution. Runtime lookup failures are separately
classified as `RUNTIME_SERVICE_MISSING` in `runtime-missing-services.json`;
the 44 observed names are an incomplete inventory, and some may be optional.
Their absence alone does not establish the cause of a missing first frame.

## Isolated memory and filesystem profile

The source kernel is SHA-256
`97adb3971c14e1c8f1fd42b18623b183d32edf9d882dc99a2c216b5dc229d001`,
19,543,912 bytes, with all 1,127 source-link inputs revalidated by
`tools/duchamp_source_kernel.py::select`. The receipt SHA-256 is
`db250b3319dd4fc84edd930b12b4123bc7549a8111c22c7d1995dd54d2f42e54`.
The CI kernel is not used as execution evidence.

The existing dual-RAMDisk bounds cap each volume at 64 MiB. This experiment
uses the existing, separately gated large QEMU single-md0 path instead:

- HFS+ md0: 3,221,225,472 bytes, intentionally writable **only in this fixture**.
- Root PA: `7558266880`; ADT PA: `10779492352`; boot arguments PA:
  `10779508736`; reserved end: `10779525120`.
- QEMU kernel RAM window: base `0x1c0000000`, 4 GiB; host sparse RAM backend:
  10 GiB, no preallocation. No block device is attached.
- Native-job input root SHA-256:
  `f369d7a1d9c4df9df5efe70ce13251e02a342c3e8fecb230ea7f21f06997d265`.
- The root contains 294 newly installed/pinned support files plus the intact
  cache already present in its pinned base. All installed bytes were checked
  again after execution. HFS header reports 343,928,832 free bytes before boot.
- The legacy HFS CLI prints its used-byte counter as a negative signed number
  above 2 GiB. Capacity was checked from the unsigned volume header and file
  length, not that display field.

Storage was checked before copying: C had about 120.7 GB free, native WSL disk
about 787 GB free, and WSL approximately 7 GiB available RAM. Only one large
cache VM ran at a time. Smaller regressions started after its teardown.
The original read-only 32 MiB md0 / writable md1 fixtures and frozen native
32+4 MiB candidate were not enlarged, relocated or replaced.

## Implementation and commands

New files: `tools/audit-duchamp-20f66-closure.py`,
`tools/test-duchamp-20f66-closure.py`, `tools/duchamp-ios20f66-runtime.c`,
`tools/test-duchamp-ios20f66-runtime.py`,
`tools/test-duchamp-source-large-profile.py`.

`qemu-service-ram.py::run_vm` now optionally validates a complete source-link
receipt; its historical pin remains the default. The source profile forbids
the historical debugger/instruction patches and 120 Hz instruction rewriting.
`test-duchamp-platform-services.py --kernel-manifest` passes the exact source
kernel through this gate. `sweet-launchd-bootstrap.S` adds an explicit
`DUCHAMP_USE_SHARED_CACHE` build option; its small-root default still supplies
`DYLD_SHARED_REGION=avoid`.

From the WSL repository directory:

```sh
python3 -B tools/test-duchamp-ios20f66-runtime.py NEW_OUTPUT \
  --kernel-manifest ../../outputs/duchamp-app-multitouch-20261118/kernel-2/build-manifest.json --seconds 600
python3 -B tools/test-duchamp-platform-services.py --output NEW_JOB_OUTPUT \
  --kernel-manifest ../../outputs/duchamp-app-multitouch-20261118/kernel-2/build-manifest.json \
  --seconds 600 --ui-probes --readiness --springboard
```

Use new output paths. Complete commands, compiler/linker outputs, hashes,
original job policies and diagnostic overrides are preserved in the evidence.
Userspace tools: Clang/ld64.lld 21.1.8; QEMU 10.2.1. No system compiler was replaced.

## Verification and limits

Direct-exec diagnostics passed 12/12, but both children terminated with
SIGTRAP 5. The proper native-job/provider fixture subsequently passed 18/18
general checks and 4/4 UI checks, with two valid display replies and a native
LaunchServices application record. The multi-variable fixture change does not
isolate a unique cause of the earlier traps. An early logd PID 3 SIGTRAP was
also observed; a later original logd PID 7 passed identity/stability checks.
This is not proof of crash-free cold startup of every daemon.

New targeted tests: recursive closure 13/13; source-profile denial gates 4/4;
large-RAM layout 6/6; native-job verdict 4/4; Mach-O preflight 21/21;
heartbeat 9/9; terminal wait decoding 7/7; dual-RAMDisk packaging 12/12.
The initial packaging test invocation omitted its required payload argument
and exited 2; its corrected invocation passed. Both logs are retained.

Fresh full-XNU regressions all exited0 using the exact source kernel:

| Suite | Passed |
|---|---:|
| Applications / multitouch | 35/35, plus 14/14 host virtual-device checks |
| Compositor | 25/25 |
| Legacy graphics | 10/10 |
| GUI/window manager | 22/22 |
| Live VirtIO mouse | 18/18, plus 10/10 host virtual-device checks |
| Filesystem / dual RAMDisk | 11/11 |
| launchd/syslogd/notifyd/Mach IPC service batch | 74/74 |
| Dynamic/static Mach-O | 17/17 |

Nested filesystem/service checks repeat in several suites and are not summed
as independent tests. The small-root regressions confirm read-only md0,
writable md1, EROFS, ENOSPC and byte-identical md0 after execution. These results
do not describe the intentionally writable large-cache fixture. Commands and
exit codes are in `regression-commands.json`; all 25 frozen native-candidate
and recovery-file hashes remain unchanged. No result from the older CI kernel
is counted toward this verification.

The next milestone is an **attributed original SpringBoard/QuartzCore frame**:
associate the producer, IOSurface, swap completion and framebuffer bytes.
BackBoard's returned 1125x2436 geometry differs from the QEMU scanout's
1220x2712; this discrepancy is observed, but its rendering impact is untested.
The current custom VirtIO shell input path is not evidence of BackBoard HID
delivery. No full GUI, physical MT6897 graphics, UFS or native boot-readiness
claim follows from this experiment.
