# Duchamp IOAcceleratorES provider audit

Date: 2026-11-19. Branch: `duchamp-bootstrap`; HEAD: `d91562d9c2bd3bc33d52550c101de1009bb41dc0` plus preserved uncommitted work.

**Status: BLOCKED_BY_UNIMPLEMENTED_GRAPHICS_API.** No GPU provider was fabricated or published. Existing IOSurface service/client operation is verified separately and is not an accelerator implementation.

## Exact first boundary

Original BackBoard, PID 25 / task birth 90, is bound to its original executable UUID `E81FD7FD034F3195A4F53C692536E5AA` and runtime cache UUID `E5420DB3-30D0-33AA-8B7E-05B5038BB46D`. Its opcode-bound Metal discovery sequence is recorded in `metal-discovery-result.json` and `original-graphics-events.json`.

| Operation | Actual result |
| --- | --- |
| IOMasterPort | kr 0, nonzero main port |
| IOServiceMatching("IOAcceleratorES") | nonnull dictionary |
| IOServiceGetMatchingServices | kr 0, iterator MACH_PORT_NULL |
| IOIteratorNext | service 0 |
| getMetalPluginClassForService / accelerator open | not reached by this enumeration |

The matching key is `IOProviderClass`. The original literal `IOAcceleratorES` is at unslid cache VA `0x181b74481`; `MTLRegisterDevices` at `0x181b115ec` loads it immediately before matching. The separate original-IOKit diagnostic independently observes exactly one dictionary key, `IOProviderClass=IOAcceleratorES`, and the same empty result. That diagnostic has PID 38 / UID 501, not BackBoard's identity. Do not substitute its observations for BackBoard's passive trace.

At the kernel boundary, `IOUserClient.cpp:430` additionally inserts `gIOServiceNotificationUserKey=true`. In this linked source `IOTaskRegistryCompatibility()` returns false, so that helper does not add an IOCompatibilityMatch key. The one-key dictionary above is the userspace dictionary, not a claim that the internal matching dictionary is unchanged.

The successful return code is a query result, not evidence of a selected object. The actual XNU source explains the null output: `IOService::copyExistingServices()` starts with `ctx.result=NULL`, applies class-instance matching, and can return NULL. `IOUserIterator::withIterator(NULL)` returns NULL. `internal_io_service_get_matching_services()` still returns `kIOReturnSuccess` for a valid dictionary. No error-to-success translation in the original Metal API was demonstrated.

Exact linked source references (WSL source workspace):

- `/var/tmp/duchamp-clang.zZKCR0J4/kernel-workspace/dxb/xnu/iokit/Kernel/IOService.cpp:5977` — copyExistingServices/class-instance search; `:6120` — getMatchingServices.
- `/var/tmp/duchamp-clang.zZKCR0J4/kernel-workspace/dxb/xnu/iokit/Kernel/IOUserClient.cpp:444` — null iterator handling; `:2660` — dictionary validation and success return.
- `metal-register-disassembly.json` and `device-class-disassembly.json` bind the actual 20F66 instructions; `metal-plugin-cstrings.json` records their local cache strings. `metal-plugin-selector-stubs.json` additionally resolves the 20F66 bundle/class/initializer selector stubs. Raw encoded cache pointers are not treated as decoded runtime addresses.

No defined `IOAcceleratorES`/`MetalPlugin` symbol is found in the new kernel's defined-symbol inventory. The narrower runtime conclusion is decisive: this particular BackBoard query returns no provider. It does not prove that every task sees an identical registry.

## Implemented changes

- [0218 source patch](C:/Users/Mehmedamir/Documents/Codex/2026-10-23/referenced-chatgpt-conversation-this-is-an/work/ios-sweet-duchamp/xnu/patches/0218-duchamp-iosurface-unsupported.patch): IOSurface's default external-method branch previously accepted and ignored arbitrary selectors. It now returns `kIOReturnUnsupported`, without modifying output buffers. Known implemented selectors remain unchanged.
- [source-kernel builder](C:/Users/Mehmedamir/Documents/Codex/2026-10-23/referenced-chatgpt-conversation-this-is-an/work/ios-sweet-duchamp/tools/build-duchamp-surface-contract-kernel.py): applies the patch to a separate source copy, compiles it with the preserved patched Clang recipe, replaces exactly SweetSurface.cpo among the verified source inputs, fully relinks, and checks both parent/new receipts.
- [client contract](C:/Users/Mehmedamir/Documents/Codex/2026-10-23/referenced-chatgpt-conversation-this-is-an/work/ios-sweet-duchamp/tools/duchamp-iokit-contract.h) and [IOKit transport](C:/Users/Mehmedamir/Documents/Codex/2026-10-23/referenced-chatgpt-conversation-this-is-an/work/ios-sweet-duchamp/tools/duchamp-darwin-iokit.h): reject null/dead object names and inconsistent pointer/count pairs before allocating a reply port, copying buffers or sending Mach IPC. Limits remain 16 scalars and 4096 inline bytes. These checks do not establish arbitrary pointer validity or physical DMA safety.
- [original-library probe](C:/Users/Mehmedamir/Documents/Codex/2026-10-23/referenced-chatgpt-conversation-this-is-an/work/ios-sweet-duchamp/tools/sweet-graphics-provider-contract.m): logs dictionaries, enumeration, real registry ID and client connection, supported limits, short output, invalid selector, null surface capability, invalid memory type, close/release. It never publishes a service.
- [opt-in controller hook](C:/Users/Mehmedamir/Documents/Codex/2026-10-23/referenced-chatgpt-conversation-this-is-an/work/ios-sweet-duchamp/tools/sweet-platform-services.c:261): runs the probe after original service checks. The opt-in-disabled controller object remains byte-identical (`451625b8…`). Diagnostic exit status is separately checked; native-service success is not used to mask diagnostic failure.
- [log validator](C:/Users/Mehmedamir/Documents/Codex/2026-10-23/referenced-chatgpt-conversation-this-is-an/work/ios-sweet-duchamp/tools/duchamp_graphics_provider.py) rejects missing/duplicate checks, zero client handles, false GPU claims and unsupported operations incorrectly reported as successful.

## Actual guest operation

The original IOKit library finds `IOCoreSurfaceRoot` with iterator `0x1d07`, service `0x1c03`, class `IOCoreSurfaceRoot`, registry ID `4294967577`. IOServiceOpen(type=0) returns kr 0 / connection `0x1d0b`, owned by diagnostic PID 38. Four passive kernel entry/return pairs independently confirm the same task and result values:

| Request | Actual result |
| --- | --- |
| Surface limits selector 13 | 0, 24 output bytes |
| Selector 13, only 8 output bytes | 0xe00002db |
| Unimplemented selector 0xffffffff | 0xe00002c7, not success |
| Surface lookup from null Mach capability, selector 34 | 0xe00002bf |
| Unimplemented memory type 0xffffffff | 0xe00002c2, address/size remain zero |
| IOServiceClose / IOObjectRelease | 0 / 0 |

The original public IOSurface client still passes 24/24, including actual shared bytes and same-process Mach-port aliases. Existing compositor tests separately exercise imported surfaces, audited peer identity, unauthorized owner/rectangle/replay rejection and dead-name cleanup. Global legacy IOSurface ID lookup is not a capability isolation guarantee; complete sandbox/concurrency/leak qualification is still absent. No ownership security claim is inferred from a successful port allocation alone.

Evidence directory: `C:/Users/Mehmedamir/Documents/Codex/2026-10-23/referenced-chatgpt-conversation-this-is-an/outputs/duchamp-ioacceleratores-20261119`. The exact new source-linked kernel is `C:/Users/Mehmedamir/Documents/Codex/2026-10-23/referenced-chatgpt-conversation-this-is-an/outputs/duchamp-ioacceleratores-20261119/kernel/kernel.development.sweet`, SHA-256 `4ae22e3d38d0be2372fc66703db6b5b957803c55b743ed4190c4725a0a17cedd`. Its receipt verifies all 1127 object inputs. The prior kernel `97adb397…` remains unchanged. This is a full relink with a newly compiled source object, not a prebuilt-kernel binary patch.

## Reproduction and evidence

Build command and toolchain diagnostics are saved in `kernel/commands.json`; userspace compile/link commands in `guest-build/commands.json`. `build-and-run.py` copies the pinned preboot fixture, verifies installed overrides by round-trip extraction, regenerates kernel-bound trace sites, and boots the exact new kernel. `extract-original-services.py` retains the original 22 checks and verifies all 296 installed file hashes. Inputs, launch arguments, binary hashes, full trace and logs are preserved under `trial-1`.

Use `execution-summary.json`, `provider-verification.json`, `kernel-provider-methods.json`, `targeted-commands.json`, `targeted-corrections.json` and `regression-commands.json` for actual results. Failed host test invocations are preserved separately; they are not counted as passing tests.

Physical status remains BLOCKED_BY_MEMORY_EVIDENCE. No phone operation, firmware change, physical UFS operation, commit or push occurred.
