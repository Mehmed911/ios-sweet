# Duchamp QEMU — original 20F66 Metal discovery

Date: 2026-11-19. Result: **BLOCKED_BY_GRAPHICS_DEPENDENCY**. First-frame verification: **false**. Physical-device state: **BLOCKED_BY_MEMORY_EVIDENCE**, unchanged.

## Exact observed boundary

The original `backboardd` process, PID 25 / task-unique birth 90, reaches the actual 20F66 `MTLRegisterDevices` implementation. The successful query produces no accelerator iterator:

| Operation in the original Metal path | Observed result |
|---|---|
| `IOMasterPort` | `KERN_SUCCESS` (0), main port 9987 |
| `IOServiceMatching("IOAcceleratorES")` | Nonnull CF dictionary, 0x102634f00 |
| `IOServiceGetMatchingServices(main, matching, &iterator)` | `KERN_SUCCESS` (0), iterator **0 / MACH_PORT_NULL** |
| `IOIteratorNext(iterator)` | Service **0** |
| `MTLDeviceClassFromService` | Its call's return site is not reached in this registration pass |
| Original device-array selection | Count 0 |
| `MTLCreateSystemDefaultDevice` | Nil in 40 logged direct-return samples |

The first interface that fails to yield the required resource is **IOServiceGetMatchingServices**, despite its success return code. The following iterator call confirms that no accelerator service is selected. This shows no published `IOAcceleratorES` provider is returned to this process in this query, not an observed failure of GPU user-client creation, capability validation or command submission. Those later stages remain unproved. This observation alone is not a global audit of every task's registry visibility. A zero device count does not establish that all other display/startup dependencies work.

The accepted trace's correlated sequence numbers are **526, 528, 529, 530, 531**. See `C:/Users/Mehmedamir/Documents/Codex/2026-10-23/referenced-chatgpt-conversation-this-is-an/outputs/duchamp-metal-iosurface-20261119/metal-discovery-result.json` and `C:/Users/Mehmedamir/Documents/Codex/2026-10-23/referenced-chatgpt-conversation-this-is-an/outputs/duchamp-metal-iosurface-20261119/metal-enumeration.jsonl`. Original executable UUID: `E81FD7FD-034F-3195-A4F5-3C692536E5AA`; actual shared-cache UUID: `E5420DB3-30D0-33AA-8B7E-05B5038BB46D`.

## Source and binary evidence

The executed source-built kernel is `97adb3971c14e1c8f1fd42b18623b183d32edf9d882dc99a2c216b5dc229d001`, full source-link receipt `db250b3319dd4fc84edd930b12b4123bc7549a8111c22c7d1995dd54d2f42e54`, all 1,127 input hashes revalidated. No CI reference kernel or original executable was patched.

These unslid addresses are independently symbolicated and byte-bound to the local 20F66 cache:

| Site | Address |
|---|---|
| `MTLDeviceArrayInitialize` block | `0x181a3142c` |
| `MTLRegisterDevices` | `0x181b115ec` |
| Return from primary-port lookup | `0x181b11618` |
| Return from matching-dictionary creation | `0x181b11644` |
| Return from matching-services query | `0x181b11654` |
| Return from first iterator advance | `0x181b11688` |
| Return from device-class lookup, after nonzero service only | `0x181b11698` |
| Device-array count branch | `0x181a34448` |
| Direct `MTLCreateSystemDefaultDevice` return to QuartzCore | `0x18837b740` |

The class string at `0x181b74481` is `IOAcceleratorES`; the reviewed instructions load its address immediately before the matching call. The branch at `0x181b11688` goes to cleanup for a zero service, before the device-class/plugin path. The actual ADRP/ADD/BR stubs resolve the calls to IOKit exports, not guessed private signatures. Bounded disassembly, exact bytes, stub targets and symbols are saved in `mtl-register-disassembly.json`, `mtl-iokit-stubs.json` and `trace/trace-config-v3.json` in `C:/Users/Mehmedamir/Documents/Codex/2026-10-23/referenced-chatgpt-conversation-this-is-an/outputs/duchamp-metal-iosurface-20261119`.

The linked XNU source snapshot is `/var/tmp/duchamp-clang.zZKCR0J4/kernel-workspace/dxb/xnu/`. In `iokit/Kernel/IOUserClient.cpp`, `internal_io_service_get_matching_services` at line 2660 checks the primary port, decodes the dictionary, calls `IOService::getMatchingServices`, and sets `*existing=IOUserIterator::withIterator(found)` with success. `withIterator` at line 444 returns NULL if `found` is NULL. This explains why a successful query can still return a null handle in this implementation. Source intent and runtime output agree here; this is QEMU evidence, not hardware observation.

Apple's [IOServiceGetMatchingServices documentation](https://developer.apple.com/documentation/iokit/1514494-ioservicegetmatchingservices) describes matching registered services. The actual return values above come from this run, not from the documentation. Existing BackBoard opens for other services succeed; the result is not generalized to all IOKit facilities.

## Instrumentation and limits

[Passive observer](C:/Users/Mehmedamir/Documents/Codex/2026-10-23/referenced-chatgpt-conversation-this-is-an/work/ios-sweet-duchamp/tools/duchamp-render-passive.gdb) uses hardware breakpoints and reads only. [Preparation](C:/Users/Mehmedamir/Documents/Codex/2026-10-23/referenced-chatgpt-conversation-this-is-an/work/ios-sweet-duchamp/tools/prepare-duchamp-metal-trace.py) adds 15 fixed Metal/IOKit sites, executable-cache return mappings and component hashes to the existing source-bound profile. The separate `.symbols` file's synthetic mapping is excluded from allowed runtime return addresses; unknown runtime mappings are rejected. [Bounded cache helper](C:/Users/Mehmedamir/Documents/Codex/2026-10-23/referenced-chatgpt-conversation-this-is-an/work/ios-sweet-duchamp/tools/duchamp_cache_code.py) uses Capstone 5.0.7 without invoking the previously failing Objective-C metadata analyser.

User return addresses must belong to one known executable cache mapping and their actual instructions must match the pinned file bytes. Returns retain PID, task-unique birth and thread identity. The [classifier](C:/Users/Mehmedamir/Documents/Codex/2026-10-23/referenced-chatgpt-conversation-this-is-an/work/ios-sweet-duchamp/tools/duchamp_metal_discovery.py) rejects incomplete, reordered, wrong-identity or wrong-iterator traces. Fixed Metal callsites retain their reviewed 20F66 matching contract when generic IOKit logging has reached its cap. These are controlled-VM execution receipts, not cryptographic firmware attestation or new hardware authorization grants.

Generic IOKit sites are globally disabled after 80 observations; hot repeated Metal/default-device sites are disabled after 40, with explicit `site_observation_capped` events. Idle return breakpoints are disabled until a real matching call re-arms them. Fixed device-registration, CA and kernel surface hooks stay active. Later absence at a disabled site is not evidence that a process never called that API.

The earlier uncapped-return run caused the native LaunchServices reply check to time out before SpringBoard was launched. That run is retained as failed/limited, not counted as 22/22 or first-frame evidence. The accepted retry reduced observer overhead; it did not lengthen or remove the service check. A subsequent complete run preserved 22/22 native services but failed the diagnostic's unsupported zero-width expectation (23/24). That test-oracle correction and retained failure are detailed in the IOSurface report.

## Tests and next step

Accepted original services: **22/22**. New trace-classifier/cache-boundary tests: **20/20**; existing observer tests **22/22**; source-profile gates **7/7**; large-RAM boundaries **6/6**. Exact commands, exits and log hashes: `C:/Users/Mehmedamir/Documents/Codex/2026-10-23/referenced-chatgpt-conversation-this-is-an/outputs/duchamp-metal-iosurface-20261119/targeted-commands.json`, `regression-commands.json` and `final-manifest.json`.

The next graphics implementation requires a genuinely functioning renderer/provider with a qualified 20F66 runtime ABI. Publishing a class name or returning an invented Metal object would only move the failure and is not a fix. The independent original-IOSurface contract results are documented separately. SpringBoard's other unresolved launchd dependencies and display configuration remain independent questions.
