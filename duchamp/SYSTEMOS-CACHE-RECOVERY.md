# Matching SystemOS acquired; cache dependencies available, standalone loading blocked

## Concrete result, 2026-11-06

The complete matching iOS 16.5 / 20F66 SystemOS member is now available locally.
The ZIP metadata matched the saved build manifest/index, extraction passed
size/CRC checks, and the APFS image has SHA-256
`2279bf443856fcb6a3f00b1fa06a32ba02a66fdf6ab6b12019462c7498aafdd3`.
Its exact size is 2,726,297,600 bytes; 1,094,826,706 compressed bytes were
downloaded through ranges from the existing official Apple IPSW URL.

The recovered dyld cache has **44 components / 3,314,368,512 bytes**, UUID
`E5420DB3-30D0-33AA-8B7E-05B5038BB46D`. The pinned ipsw CLI successfully parsed
2,710 indexed library records. This establishes local acquisition and parsing,
not execution, full system authentication or phone compatibility.

Eight selected derived exports now resolve all strong imports of both
container daemons and logd in the inspected matching roots:

| Entry | Resolved binaries | Bytes | Missing/invalid strong paths |
| --- | ---: | ---: | --- |
| containermanagerd | 87 | 102,555,520 | 0 |
| containermanagerd_system | 87 | 102,555,536 | 0 |
| logd | 93 | 109,247,128 | 0 |

No new QEMU or phone test was run with these derived exports. The previous
lsd runtime still has its original failed verdict. The phone remains last
verified in restored Android; no partition operation occurred this turn.

## Source acquisition and strict compression recovery

`tools/acquire-duchamp-systemos.py` pins the exact ZIP entry tuple and checks
the saved manifest's 20F66 Cryptex1,SystemOS path against the live archive
index before downloading into a new directory. It preserves older partial
files. The existing remotezip code checks the final uncompressed size and
ZIP CRC before giving the member its final filename. A streaming SHA-256 and
technical APFS file listing are recorded. Signature authentication is not
claimed by those checks.

The existing 7-Zip 26.00 extracted the ordinary cache components but rejected
three ZBM resource-fork compressed files. All partial outputs/logs remain
preserved. A source build of upstream
[apfs-fuse](https://github.com/sgan81/apfs-fuse) supplied its read-only APFS
reader and [algorithm-14 decoder](https://github.com/sgan81/apfs-fuse/blob/master/ApfsLib/Decmpfs.cpp).
The small GPL-2.0-or-later adapter `tools/read-systemos-zbm.cpp` reads the image
without mounting any filesystem. It follows the exact cache path, requires
the expected inode, compression algorithm and uncompressed size, and creates
its destination exclusively. It does not enable lax decoding.

| Component | Inode | Decoded bytes | SHA-256 |
| --- | ---: | ---: | --- |
| `.42.dyldlinkedit` | 88 | 333,955,072 | `05256dce35f488828f2316e5651a24cfbcb48a751597be0303657cede2f9128f` |
| `.28.dyldlinkedit` | 73 | 19,906,560 | `224304a92780f0ad69618da3aaddffe8e0474d88614a280a26c39820757899f1` |
| `.symbols` | 90 | 591,855,616 | `791bcbc49a7d175d5625f927f0157cece242aeb46d53da0f22f8c7a1aa17bf51` |

All three decodes passed. Unsupported component input was rejected, an
existing output was rejected with identical before/after hash, and a non-APFS
image was rejected without creating an output. The source helper was built
against apfs-fuse commit `66b86bd525e8cb90f9012543be89b1f092b75cf3`
and lzfse submodule `e634ca58b4821d9f3d560cdc6df5dec02ffc93fd`.
WSL build dependencies were installed locally; no host filesystem was mounted
and no upstream tool was installed globally.

The recovery assembler copies validated primary components into a new cache
directory and requires the cache parser to succeed. Reused ordinary files now
require a source-bound extraction manifest and a matching SHA-256 before copy.
A fresh source extraction of the 41 ordinary components produced that manifest
in `work/20F66-cache-source-regular-v1`, separately from the earlier partial
extraction. The three decoded components have their own source-bound receipt.
The initial complete v3 copy remains preserved; v4 assembles the same component
set through the stricter manifest path. Failed cache v1 and incomplete assembly
v2 are kept.
The v4 parser passed, and all 44 component hashes are identical to v3. This
independent fresh-source re-extraction strengthens the older v3 provenance;
it does not rewrite the historical v3 receipt or claim its old code performed
the new before-copy hash gate.

## Available exports and the remaining loader problem

The original four missing framework images are present in the matching cache:
ContainerManagerCommon/System/User version 477.120.3 and CacheDelete 588.120.4.
Further imports required libsandbox.1, libMatch.1, RunningBoardServices and
UserManagement. The existing ipsw tool exported these eight files with
`dyld extract --slide` into a new private directory. Each derived Mach-O UUID
was checked against its source cache record. These are transformed cache
exports, not unchanged original standalone dylibs.

The structural audit found:

- The four original framework exports have flags `0x02100085`, with the
  in-cache header flag cleared, but no declared DYLD_INFO binding/rebasing,
  CHAINED_FIXUPS or CODE_SIGNATURE commands and no section relocations.
- ContainerManagerCommon, CacheDelete, RunningBoardServices and UserManagement
  retain sampled data pointers outside their own segments into cache address
  ranges. Independent inspection also found external selector/class/CFString
  references and cache stub slots in Common/CacheDelete.
- Clearing an in-cache flag and applying slide information does not reconstruct
  standalone imports, Objective-C optimization dependencies or authentication.
  The exporter itself describes an analysis workflow; its
  [implementation](https://github.com/blacktop/ipsw/blob/master/cmd/ipsw/cmd/dyld/dyld_extract.go)
  is not evidence of successful execution in our runtime.

`tools/audit-duchamp-cache-exports.py` records those observations and keeps
`standalone_payload_allowed=false`. Six unit tests passed, covering external
pointers without fixups, internal-pointer classification, no inference of
runtime approval from an empty sample, out-of-file segment rejection,
propagation of a failed closure subprocess with reports preserved, and rejection
of same-size corruption before cache reuse. Closure failure now propagates to
the CLI exit status; a recorded failure cannot silently become exit zero.
An absent code-signature command is recorded as an observation; this audit
does not infer the kernel's signing policy or claim that absence alone caused
the earlier lsd abort.

The v3 audit reports all strong paths resolved while still refusing standalone
runtime approval. No analysis export was inserted into a phone payload or
silently promoted into the successful original-runtime fixtures.

## Original container policy checked in parallel

Thirteen small original policy/account/resource files were extracted into
`work/container-policy-v1`. Source size/mtime matched the earlier SHA-verified
full-OS receipt; that large image's hash was inherited, not freshly recomputed
for this separate extraction.

The original container feature domain has `data_separation.Enabled=true` and
no `user_system_split` entry. Global flags have no container override. The
pinned launchd/featureflags library's static missing-key path supports false
without overrides; this is not a live observation of every override channel.
The corresponding normal main job uses fixed mobile containers, global
bundle/system modes, `_installd`/root owners and kernel-upcall=yes. The system
job's conditional Disabled=true branch follows that default. Credentials,
embedded sandbox enforcement and host special port 25 functionality remain
unproven; a static entitlement or argument is not a privilege grant.

The actual original account identities are mobile 501:501, _installd 33:33 and
_logd 272:272. Restore sources and saved RAM roots retain these identities;
password/comment edits do not constitute a UID/GID defect. No account repair
was performed or needed based on this inspection.

## Private evidence

| Artifact | SHA-256 |
| --- | --- |
| `work/20F66-systemos-v1/acquisition.json` | `be1928fd56f3405e93fb3b7ef261ee1ffb32268973e59fbbdf989fc921d623c5` |
| `work/cache-zbm-recovery-v2/receipt.json` | `3e01243036ad6c20cc86c30b449ee5b1b61da0d40dcaa32f16224eabe78dd6ba` |
| `work/20F66-cache-v3/receipt.json` | `0af7672bd9f5621d52fbc26f2198fe7df6c0efa0add169cef2cffe4bff3ad0c8` |
| `work/20F66-cache-v4/receipt.json` | `30eb89efbe8fb1c63b6599a9ecffad13b6b956f644e9ef91cf351b61b97f1fab` |
| `work/20F66-cache-v4/comparison-with-v3.json` | `6ff1fe70483fa480a70d972f76e9a52ae563ee0cf359f68f3e7f17a6f64f9c2b` |
| Source-bound ordinary-component manifest | `0ebc803c65cd8834b9fac4ff57e7b798bbc3bcec3ab79b06251180b1f8e1eeb0` |
| `work/20F66-framework-audit-v3/exports.json` | `ea2ed121819a4a45ecef91819aea1df3855850ae80a02f8dbf029010273889a9` |
| `work/20F66-framework-audit-v3/support-closure.json` | `be73d5327565a9eaf208d9332c8c7703e2fab7b3d012da78504a475cd70f414d` |
| `work/20F66-framework-audit-v3/summary.json` | `f7d67dd36cf0792b2de6d313b9903a0d21866750c194bc30e25d5eb0796cc150` |
| `work/container-policy-v1/results.json` | `26a69fb2b2f133b79aff240e52242cfdb880935f1d7807317a9b965c682b05f3` |

The cache-info JSON is large and single-line; parse selected fields instead of
printing it into a console. Detailed receipts, downloaded Apple files, derived
exports, build trees and source policies stay outside git.

## Replay using the existing pinned local source/build prerequisites

Run from the repository root in Ubuntu/WSL. Each output must be a new path.
The helper expects the documented local apfs-fuse source and library build.
Those libraries were built with CMake's policy minimum 3.5 and
`CMAKE_CXX_FLAGS='-include cstdint'`; no upstream source edits were needed.

```sh
python3 tools/extract-duchamp-systemos-cache.py \
  --source work/20F66-systemos-v1 --output work/cache-regular-NEW --regular-only
python3 tools/recover-duchamp-cache-zbm.py \
  --image work/20F66-systemos-v1/096-04666-078.dmg --output work/cache-zbm-NEW
python3 tools/extract-duchamp-systemos-cache.py \
  --source work/20F66-systemos-v1 --output work/cache-complete-NEW \
  --cache-input work/cache-regular-NEW/apple-extracted/System/Library/Caches/com.apple.dyld \
  --cache-manifest work/cache-regular-NEW/component-manifest.json \
  --recovered-dir work/cache-zbm-NEW
python3 tools/test-audit-duchamp-cache-exports.py
```

To reacquire the original member rather than reuse it, run
`tools/acquire-duchamp-systemos.py --output NEW-DIRECTORY`. The export audit
takes the recorded cache-info JSON, a flat ipsw export directory, a new output
and optional `--extra` exact guest paths; it propagates closure failure while
keeping reports. All source dependencies remain private local prerequisites,
not a promise of a self-contained clean checkout.

## Next actual integration boundary

Resolve a runnable library-loading route in QEMU: preserve/map the intact
matching shared cache, or reconstruct and validate standalone binding and
Objective-C references. The intact cache is 3.3 GB and does not fit the current
512 MiB payload window; that route requires an explicit virtual storage/memory
plan and loader validation. Do not insert it into the existing phone layout.

After loader validation, use the resolved original container/log policies in
a separate QEMU fixture, then require a real lsd request/reply witness. Neither
the source closure nor namespace lookup alone establishes that result. Phone
UFS/DMA/IOMMU, Mali and a complete GUI remain separate unproven work.
