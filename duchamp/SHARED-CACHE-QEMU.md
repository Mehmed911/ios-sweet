# Original shared cache loading through read-only QEMU storage

## Actual runtime result, 2026-11-06

The matching, untouched iOS 16.5 / 20F66 shared cache now loads in QEMU.
The final source's `work/shared-cache-qemu-v4/evidence/verification.json`
passed all 13 checks in **32.843 host seconds**. Its SHA-256 is
`1aa834e63097cb1a07d5640177da6d2500b2322afdc3cba231f04874fcc8fb54`.
The prior v3 trial also passed all 13 checks in 49.343 host seconds, report
SHA-256 `3da48e77694343e15a0e4386d1e4d4199f3af7cc8ec3cfb127795843ac532969`.
These timings are two local trials, not a controlled performance benchmark.

The original dyld executed the diagnostic child as PID 2 with parent PID 1.
The guest reported:

```text
SWEET SHARED CACHE: DYNAMIC MAIN pid=2 ppid=1
SWEET SHARED CACHE: UUID E5420DB330D033AA8B7E05B5038BB46D
SWEET SHARED CACHE: RANGE base=0x198f24000 bytes=2850996224
SWEET SHARED CACHE: FRAMEWORK index=0 incache=1 class=MCMError
SWEET SHARED CACHE: FRAMEWORK index=1 incache=1 class=CDRecentInfo
SWEET SHARED CACHE: PASS step=uuid-range-frameworks-objc
```

The probe requires the exact live cache UUID and a nonempty mapped range.
For ContainerManagerCommon and CacheDelete it requires a successful
`dlopen(RTLD_NOW)`, the loaded Mach-O header inside that range with
`MH_DYLIB_IN_CACHE`, and the original Objective-C class name obtained through
the runtime. A zero process exit or a dependency path listing cannot satisfy
these checks. The API declarations were checked against Apple's
[dyld-1066.8 private header](https://github.com/apple-oss-distributions/dyld/blob/dyld-1066.8/include/mach-o/dyld_priv.h)
and exports of the matching local libdyld.

This establishes library loading and basic Objective-C metadata access. It
does not establish container/log daemon operation, a native LaunchServices
reply, original launchd with this disk fixture, a GUI, GPU execution, or
physical phone storage. Previously extracted analysis dylibs remain blocked
as standalone inputs; none was used in this test.

## Storage and source boundaries

The [recovered source cache](SYSTEMOS-CACHE-RECOVERY.md) contains 44 files
including local symbols. This test installs the **43 runtime components /
2,722,512,896 bytes** into a new 3 GiB HFS+ disk, omitting `.symbols`.
Every runtime component is hash-checked against the pinned v4 acquisition
receipt and extracted back from HFS+ for a second hash check.

The existing strictly opted-in QEMU UFS adapter presents that disk read-only.
The kernel's 512 MiB memory window is unchanged, the payload has no RAMDisk,
and the payload itself remains only 16,715,616 bytes. The intact cache is
read from virtual storage as needed. The early `QEMU RAM ROOT MOUNTED` marker
is inherited generic text; it is not a claim that this fixture used md0.

The original dyld is extracted back and compared with the matching source.
The test replaces `/sbin/launchd` only in its new offline disk copy with a
small static diagnostic parent. That parent forks and the child execs the
dynamic C probe. Neither an original base image nor a phone partition is
modified. The host disk's hash is checked again after QEMU exits.

| Input | SHA-256 |
| --- | --- |
| Phone-proven kernel, reused unchanged in QEMU | `e465723a540844817a5b9cb36c14984d660f9a8e41f6638240527b469189182b` |
| Base QEMU ADT | `a881410d04a3cec3b7ebd9bee91f510c755683b94f5a26d71c47301fff7417d8` |
| Base HFS fixture | `491aa78408c423c50e8b59644e416e94b643ed3eb119158d52684af4176c8b3f` |
| Source cache receipt | `30eb89efbe8fb1c63b6599a9ecffad13b6b956f644e9ef91cf351b61b97f1fab` |
| v3 read-only test disk | `711ac6eb423086bf56285dea9f41302dcef8dacebcdaf5918703f72c43739e84` |
| v3 payload | `5aba40f16dd814bc2c2a1126677bcfca222c87fa61c650eb7756364f8eb7a465` |
| v4 read-only test disk | `3e23c283d5847ccf9e556f2300df8050d30ad8487e759e92689dd2765a9f71bf` |
| v4 payload, identical kernel/ADT/cmdline to v3 | `5aba40f16dd814bc2c2a1126677bcfca222c87fa61c650eb7756364f8eb7a465` |
| v4 private inputs receipt | `1b7e4c71739f50029b8e485367663d1659802c66889afb4461173aebb44c3723` |

The native working directory is disk-backed under the WSL user's cache,
because this machine's `/tmp` is tmpfs. It is retained, and the entire run,
frozen sources, inputs and result are exported into the requested new private
output. No large image is read into one Python byte string when validating
the QEMU disk: header checks and SHA-256 use bounded reads. All 20 profile
tests passed, including the new guard against whole-image reads.

## Earlier failed trials retained

- v1 lacked an offline `/dev` mountpoint on its read-only disk. Devfs and
  console-open failed before dyld. QEMU was manually stopped at 89.533
  seconds and the verifier failed. Its old `no_observed_failure` field did
  not include these markers; the final runner does. This never passed the
  overall verification.
- v2 created the mountpoint and execed the dynamic probe directly as PID 1.
  The last visible output was original libignition configuration, with no
  dynamic-main marker before the 180.250-second timeout. The verifier failed.
  The precise internal wait was not attributed. Forking isolates cache
  loading from this PID-1-specific startup path; it does not solve that path.
- v3 used the independent child and passed. A subsequent source correction
  makes the diagnostic parent block in Darwin `wait4` and uses the existing
  static fixture's `select` timeout ABI on failure, rather than busy syscalls.
- v4 reran that final source and passed all 13 checks with a new disk and
  matching source snapshots. The diagnostic QEMU exception log was about
  1 MiB, compared with about 382 MiB in the busy-parent v3 run. All failed
  and successful trial artifacts remain preserved; no process is left running.

## Replay and next work

Run inside Ubuntu/WSL from the repository with the already acquired private
source artifacts and existing clang, ld64.lld, llvm-nm, HFS+ and QEMU tools:

```sh
python3 tools/test-qemu-ufs-profile.py
python3 tools/test-duchamp-shared-cache.py --output work/shared-cache-NEW --seconds 180
```

Existing output directories are refused. A PASS requires all runtime checks,
the exact stop marker, unchanged disk/base hashes and unchanged test sources.
Framebuffers are sampled; an absence of visible panic alone is insufficient.
No new CI kernel build or phone test is needed for this fixture.

The subsequent [platform-services batch](PLATFORM-SERVICES-QEMU.md) passed
with a separate large writable QEMU md0, original launchd as PID 1, original
container/log/LS providers and a witnessed native LS reply. Original
runningboardd/backboardd also passed six five-second process health checks
and a repeated LS request. This RAM fixture does not resolve the historical
PID-1 direct disk-root wait. Application-registry completion, native display
operations and SpringBoard remain untested. The current phone RAM payload
cannot hold these runtime cache files; QEMU success does not supply physical
MT6897 UFS/DMA/IOMMU ownership or Mali support.
