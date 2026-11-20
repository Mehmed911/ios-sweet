# Duchamp — original 20F66 IOSurface compatibility

Scope: original IOSurface public APIs in ARM64 QEMU, exact source-built kernel `97adb3971c14e1c8f1fd42b18623b183d32edf9d882dc99a2c216b5dc229d001`. Physical-device status remains **BLOCKED_BY_MEMORY_EVIDENCE**. No native Mali, GPU command submission or SpringBoard rendering compatibility is claimed.

## Runtime qualification

An original-library diagnostic Mach-O, [sweet-iosurface-contract.m](C:/Users/Mehmedamir/Documents/Codex/2026-10-23/referenced-chatgpt-conversation-this-is-an/work/ios-sweet-duchamp/tools/sweet-iosurface-contract.m), executes as UID 501 after the authentic BackBoard/SpringBoard service checks. It dynamically resolves public functions from the original cache's IOSurface framework, checks the cache UUID, and labels its own process and data explicitly. It never presents a frame, creates a Metal device or substitutes for SpringBoard. It is an unsandboxed diagnostic child of the system controller after a UID/GID change, not an original application launched in SpringBoard's sandbox/bootstrap context.

Accepted result: **PASSED (original public API; same-process Mach-port round trip)**. Checks: **24/24**. Process PID: 37. Surface ID: 2; allocation: 16384 bytes; dimensions: 64×32; row pitch: 256; format: 0x42475241; Mach port: 0xb03.

Actual transcript: `C:/Users/Mehmedamir/Documents/Codex/2026-10-23/referenced-chatgpt-conversation-this-is-an/outputs/duchamp-metal-iosurface-20261119/trial-4/guest/iosurface.log`. Creator task, process birth, `fTask` ownership agreement, user mapping and returned surface identifiers are recorded in `C:/Users/Mehmedamir/Documents/Codex/2026-10-23/referenced-chatgpt-conversation-this-is-an/outputs/duchamp-metal-iosurface-20261119/iosurface-events.jsonl`. This diagnostic surface is never attributed to SpringBoard.

The diagnostic exercises:

1. Real creation from the six public geometry/allocation/format keys.
2. Returned geometry, ID and allocation bounds.
3. Original lock/unlock and writable CPU mapping.
4. Writes of a bounded BGRA pattern into the actual mapped bytes.
5. A real `IOSurfaceCreateMachPort` right and `IOSurfaceLookupFromMachPort` lookup.
6. Alias ID/geometry and byte-by-byte shared-memory agreement.
7. Releasing the creator while retaining the alias, then releasing the alias and deallocating the Mach right.
8. Rejection of an invalid global ID, a null Mach port and width 16,385 (beyond this port's 16,384 limit).

Mach port names are task-local: the numeric right is correlated with PID 37 / birth 128, not treated as global authority. This is a **same-process** Mach-port round trip. It is not proof of cross-process transfer, sandbox compatibility, use-after-exit cleanup, full memory-isolation correctness, concurrency, every pixel format or a complete leak audit. Apple documents the port's ownership and required deallocation in [IOSurfaceCreateMachPort](https://developer.apple.com/documentation/IOSurface/IOSurfaceCreateMachPort%28_%3A%29); the actual checks use original runtime functions, not mocked replies.

## Source audit of the linked implementation

Exact source: `/var/tmp/duchamp-clang.zZKCR0J4/kernel-workspace/dxb/xnu/iokit/Kernel/arm/SweetSurface.cpp`, bound to the source-link receipt. Copies and source/object hashes are retained in `C:/Users/Mehmedamir/Documents/Codex/2026-10-23/referenced-chatgpt-conversation-this-is-an/outputs/duchamp-metal-iosurface-20261119/source-evidence/`.

| Area | Implemented path | Limits |
|---|---|---|
| Allocation | `create`, line 650; dictionary parse, layout, `IOBufferMemoryDescriptor`, zeroing | 64 KiB property cap; dimensions ≤16384; per-buffer ≤256 MiB; total wired cap 1536 MiB. Larger/full-format compatibility not inferred from this small test. |
| IDs | `sweet_surface_insert_locked`, line 119; fixed table and user count | IDs are global identifiers, not proof of authorization or producer identity. |
| Process ownership | `initWithTask`, line 447, records `fTask` | Tracer compares actual caller task. This does not implement a new access policy. |
| Mappings | `addRef`, line 507; data/state mappings in owning task | State mapping uses read-only mode. Data is writable as required by this diagnostic. |
| Repeated lookups | `addRef` reuses the existing per-client reference | Framework cache-alias behavior is intentionally preserved. |
| Mach-port lookup | selectors 34/35, `externalMethod`, line 725 | Lookup-from-port resolves an object in the client's task and checks its type. Global-ID lookup is a different legacy interface. |
| Reference counting | `sweet_surface_get/put`, lines 137/156 | Last table user removes its retain; this is source behavior, not a complete runtime leak proof. |
| Destruction | `SweetSurfaceRef::free`, line 368; client close at 470; `SweetSurface::free`, line 81 | Releases data/state mappings, table user, memory/state descriptors; full crash/concurrency lifetime qualification remains outstanding. |
| Pixel transfer | Existing framebuffer CPU-copy path | No claim of GPU texture import, arbitrary planar formats or CoreAnimation rendering. |
| Other selectors | Existing default handler accepts/ignores several properties/notifications | These are pre-existing compatibility gaps. They were not used as proof of Metal or original graphical correctness and were not expanded. |

A future GPU/software-Metal broker must use task/session ownership and validated transferred rights for its resources. A guessed global surface ID alone is insufficient. No Adreno memory-management or register path was imported.

## SpringBoard ordering and attribution

Original BackBoard's Metal registration query is observed. SpringBoard main entry and health are observed in the accepted run. Original-process surface creation count: **0**. SpringBoard CA context commits observed: **0**.

No observation establishes that SpringBoard created an IOSurface before its own Metal initialization. Some generic Metal sites are deliberately capped globally, so later missing Metal events cannot establish a per-process ordering. The independent diagnostic's successful allocation, if present, qualifies only that client and tested API subset.

## Corrected diagnostic assumption

The first complete original-API run passed 23/24 checks and exited 1 because the diagnostic incorrectly required a zero-width surface with explicit allocation to fail. The linked `sweet_surface_layout` does not prohibit zero width when a nonzero allocation is supplied. Its acceptance is now recorded as an observation, not labelled Apple-compatible or a success criterion. The negative dimension check uses the explicit source limit of 16,384 instead. The original failed transcript and probe executable/source remain in trial-3; no kernel condition or service assertion was relaxed. Final accepted evidence is in trial-4.

## Build and integration

[Controller](C:/Users/Mehmedamir/Documents/Codex/2026-10-23/referenced-chatgpt-conversation-this-is-an/work/ios-sweet-duchamp/tools/sweet-platform-services.c) has an opt-in `SWEET_IOSURFACE_PROBE` block after original-service health. The default build's ARM64 object is byte-identical to the pre-task controller (`451625b82f509f13407a0c2ec0b036acc9d102284aa56c33a68e2cd9d0d5051f`). The probe's result is logged separately; a failed probe is never relabelled as a passing service suite.

The source kernel and original Apple binaries were not modified. The copied QEMU RAM root changes only the diagnostic controller and adds the diagnostic executable. Input hashes, ARM64 compiler/linker arguments, round-trip installation checks, actual exit/wait status and installed-file comparisons are under `C:/Users/Mehmedamir/Documents/Codex/2026-10-23/referenced-chatgpt-conversation-this-is-an/outputs/duchamp-metal-iosurface-20261119/build-v2/commands.json` and `trial-4/`.

Original service checks: **22/22**, installed-file comparisons: **295**. Existing custom graphics, window manager, live pointer, multitouch, dyld/Mach-O, launchd and filesystem regressions remain separate from original-IOSurface qualification; receipts are in `C:/Users/Mehmedamir/Documents/Codex/2026-10-23/referenced-chatgpt-conversation-this-is-an/outputs/duchamp-metal-iosurface-20261119/regression-commands.json`.
