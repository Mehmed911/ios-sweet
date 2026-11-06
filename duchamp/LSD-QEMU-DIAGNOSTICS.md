# Original lsd: first runtime diagnostic in QEMU

## Actual result, 2026-11-06

The first original LaunchServices daemon fixture **did not pass**. QEMU ran
for 76.501 host seconds, and the verifier correctly returned failure. All 106
installed files plus original launchd/xpcproxy matched their recorded hashes.
The unchanged kernel booted the copied 128 MiB HFS RAM root and original
launchd started the diagnostic controller as root PID 3.

The real CLI kickstart returned zero and printed PID 6. The first CLI print
reported `user/501/com.apple.lsd`, running, program `/usr/libexec/lsd`, runs=1,
execs=1 and initialized=1. launchd subsequently reported PID 6 `[lsd]` exiting
due to SIGABRT sent by lsd itself. The final print showed not running and last
terminating signal Abort trap 6. The controller timed out before validating
the native mobile identity and endpoint/stability checks. Neither UID/GID
runtime validation, service stability nor an application request passed.

The sampled framebuffer showed failed lookups for `com.apple.logd` and
`com.apple.containermanagerd`. These are observed missing runtime services;
their temporal proximity does not establish which exact fatal branch caused
the abort. The visible sample had no kernel panic and zero unknown glyphs.
There was no phone access, flash, new kernel build, physical UFS or GPU test.

## Pinned setup and scope

Original lsd is plain arm64/iOS16.5, 57,424 bytes, SHA-256
`cb9a5082ac7448e1ff8ee30e45925909568f39e6f4dc30e0bbbdf4332c27d0e4`.
Its original job SHA-256 is
`9728a545bd4cdde11d2f264ef547c5a15717964d8029b37fa71ffa23010b3a78`.
The job's mobile username, thirteen native Mach names, arguments and
on-demand policy are preserved; stdout/stderr are redirected to a RAM log.
The controller creates/chowns only conventional mobile home Library/Caches,
Preferences and Logs directories in the copied RAM filesystem.

The fixture adds the previously tested notifyd and on-demand cfprefsd jobs
with explicit diagnostic overrides, original executable bytes and matching
strong library closure. It reuses kernel
`e465723a540844817a5b9cb36c14984d660f9a8e41f6638240527b469189182b`
and QEMU ADT
`a881410d04a3cec3b7ebd9bee91f510c755683b94f5a26d71c47301fff7417d8`.
Strong closure completeness did not establish these additional service
dependencies, user initialization, dynamic imports or native RPC success.

launchctl warns that this job belongs to the user/foreground domain and
redirects the System spelling to user/501. The final observer source therefore
uses `bootstrap_look_up_per_user(..., 501, ...)`, whose ABI is declared in
[Apple's bootstrap_priv.h](https://github.com/apple-oss-distributions/launchd/blob/main/liblaunch/bootstrap_priv.h)
and exported by the local libxpc. This correction and bounded CLI child cleanup
compile/link successfully in `work/lsd-probe-final-build-v1`; the endpoint
branch was never reached in v1 and remains unexecuted. The failed v1 source
snapshot is preserved unchanged. A bootstrap lookup returns a send right;
it does not prove a reply from lsd or successful LaunchServices operation.

## Follow-up: actual support executables inspected

Six original binary/job files were selectively extracted from the same local
20F66 full OS image into `work/lsd-support-audit-v1/apple-extracted`. Source
size and nanosecond mtime matched the preceding SHA-verified receipt; the
4.7 GB hash was inherited from that receipt, not recomputed in this follow-up.
The source and older files were preserved. No network download was made.

| Executable | Missing strong frameworks in inspected roots |
| --- | --- |
| `/usr/libexec/containermanagerd` | ContainerManagerCommon, ContainerManagerSystem, ContainerManagerUser |
| `/usr/libexec/containermanagerd_system` | Same three |
| `/usr/libexec/logd` | CacheDelete |

These four exposed missing paths are a lower bound: their own transitive
imports cannot yet be traversed. None of these new support executables was
run with an incomplete closure.

The actual container jobs default to root and preserve mobile defaults,
`_installd` bundle ownership and root system-container ownership. They contain
conditional user/system split arguments; the regular daemon also declares
an upcall at host special port 25 and crash policy. logd runs as `_logd` and
publishes five Mach names plus `/var/run/syslog`. These identities, feature
flags, arguments and resources must be resolved from the matching system
before enabling a combined fixture. Do not substitute empty services or
silence a failed check to claim LaunchServices readiness.

## Query feasibility remains static evidence

Inspection of original CoreServices (SHA-256
`4a0a92937739cb822207a08fdb7b95206684433f32a6170efecf22187250896d`)
found `_LSGetStatus(void)` using an internal synchronous XPC query. Its zero
return alone is insufficient: the wrapper initializes the result to zero and
has no error handler. A reply callback with a separately recorded error path
would be required for a future response witness. No native query was run.

The named internal synchronous-proxy helper has a symbol but no Objective-C
method metadata in this binary. Do not assume that symbol can be invoked as
an ordinary selector. Static analysis found an exported proxy factory and
registered domain getter, but their use remains a separate untested fixture.

libsystem_containermanager (SHA-256
`8293c9483cee2eb7b3a48cc481b884705447eed2144f2855ce94ab5e4b0a1868`)
has fatal initializer branches for sandbox-query, XPC-pipe/routine and
container-path/identifier errors. They are candidate branches, not an
attribution of PID 6's SIGABRT. Capture abort/dispatch evidence if the failure
persists after the real matching support services are available.

## Private evidence and replay

| Artifact | SHA-256 |
| --- | --- |
| `work/lsd-qemu-v1/evidence/verification.json` | `3ec19b4e1ad47d2c8efa4bc5535e8e7f284909c9c4477e485d6630a3a3b7ec1e` |
| Initial root | `392a97d4f84f0c3399f2a4b7821dd4d71832b2d91350989196567fede0a8229c` |
| QEMU payload | `377256b9155a125688797e7cb39e5a0a3d01d69fec777022bd13938975bce494` |
| `work/lsd-support-audit-v1/audit.json` | `4423b5df9d88942bfa9cce2371865bc07245c3fb30cf0f678b4e26bdbf537966` |
| Support extraction receipt | `2e40cee8599eaff9c57e20abb5236c62d1ed22fefa61e28f965ff72b80b47561` |

The runtime directory retains native CLI output, framebuffer samples, saved
RAM filesystem, executable hashes and the compiled source snapshot. The
support directory retains exact original jobs/conditional arguments, input
verification method and extracted file hashes. Apple files remain outside git.

```sh
python3 tools/test-duchamp-lsd.py --output work/lsd-NEW --seconds 240
```

This repeats the bounded startup diagnostic, not a successful end-to-end
service test. The final source has a compile/link-only per-user lookup fix.
Before a useful new runtime attempt, acquire/audit the matching four missing
frameworks and their imports, integrate the real container/log providers with
their resolved original policies/resources into a separate fixture, and add
a real native request/reply witness. The SystemOS/Cryptex copy was partial at
this first diagnostic. The subsequent [complete acquisition and export audit](SYSTEMOS-CACHE-RECOVERY.md)
resolves all strong source paths, but exposes missing standalone bind/rebase
metadata and external cache references. Runtime loading remains unvalidated.
Physical-phone state remains original Android restored, with no recovery due.
