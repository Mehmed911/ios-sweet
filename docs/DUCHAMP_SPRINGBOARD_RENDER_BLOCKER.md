# SpringBoard renderer blocker and reusable UniXNU concepts

Date: 2026-11-19. Final graphics classification: **BLOCKED_BY_GRAPHICS_DEPENDENCY**. Authentic first frame: **not verified**. Native MT6897 remains **BLOCKED_BY_MEMORY_EVIDENCE**. No phone operation, firmware change, physical UFS, commit or push occurred.

## What is established

Original BackBoard and SpringBoard run in the accepted exact-source-kernel QEMU test. BackBoard's original `MTLRegisterDevices` successfully obtains its primary port and matching dictionary, but matching `IOAcceleratorES` yields a null iterator; the next service is zero. No device-class/plugin branch follows that zero service. Original Metal's device list is empty and its default device is nil.

This narrows the blocker from an unexplained nil Metal result to **no matching published accelerator provider returned in this actual registration pass**. It does not establish that publishing a name is enough, that IOServiceOpen/capability checks would pass for a real GPU, or that SpringBoard's other startup dependencies work.

The original IOSurface public-API diagnostic is **PASSED (original public API; same-process Mach-port round trip)**, 24/24 checks, with surface ID 2. Diagnostic memory and pixels remain explicitly owned by its custom client, not SpringBoard. BackBoard's Swap 1 has surface IDs [0, 0, 0, 0]. No original producer → surface → presentation → framebuffer attribution chain was verified. The final raw scanout is retained only as diagnostic console bytes, SHA-256 `c3997b74931c673ebffa7676cbf612c896df22929ac712ed7b9e573dd26aa477`; no authentic UI screenshot is supplied.

## UniXNU source revisions and licenses

The requested URLs were followed and the actual source fetched into a new research directory, without touching prior checkouts:

| Requested repository | Resolved repository and reviewed commit | License |
|---|---|---|
| UniXNU/NativeMetal | [AdrenoMetal `cc0a4e8e57d20f4a4698753c2530875f2b10c0ca`](https://github.com/UniXNU/AdrenoMetal/tree/cc0a4e8e57d20f4a4698753c2530875f2b10c0ca) | MIT, copyright 2026 NativeMetal contributors |
| UniXNU/NativeAdreno | [Adreno740 `be70fb13ed19d5fdf139d27977da6f54078cf50a`](https://github.com/UniXNU/Adreno740/tree/be70fb13ed19d5fdf139d27977da6f54078cf50a) | MIT, copyright 2026 NativeAdreno contributors |

Exact license/file hashes and source URLs are in `C:/Users/Mehmedamir/Documents/Codex/2026-10-23/referenced-chatgpt-conversation-this-is-an/outputs/duchamp-metal-iosurface-20261119/unixnu-source-receipts.json`; clone commands and actual resolved commits are in `unixnu-fetch.json`. Third-party dependencies are not automatically covered by either top-level MIT license. No upstream implementation code was copied into the driver or advertised as working on Mali.

The [UniXNU GPU adaptation guide](https://unixnu.com/porting/gpu) describes the A740-oriented Metal/frontend/Vulkan/Turnip/kernel path and asks for board-specific memory/power/submission validation. It is design context, not validation of our MT6897 or QEMU port.

## Reusable concepts, with exact source locations

| Concept | Reviewed source | Reuse assessment |
|---|---|---|
| Original device discovery and plugin lifecycle | [NativeAdrenoMetalPlugin.mm, lines 1–92](https://github.com/UniXNU/AdrenoMetal/blob/cc0a4e8e57d20f4a4698753c2530875f2b10c0ca/NativeAdrenoMetalPlugin.mm) | The IOAcceleratorES → MetalPluginName → bundle/principal-class → accelerator-port initialization structure is relevant. That source distinguishes diagnostic nil-return mode from real published-device mode. Neither mode is a portable working GPU implementation. |
| IOSurface-backed resource lifetime | [NativeBridgeMetalFrontend.mm](https://github.com/UniXNU/AdrenoMetal/blob/cc0a4e8e57d20f4a4698753c2530875f2b10c0ca/NativeBridgeMetalFrontend.mm), especially 1388–1392, 1478–1543 | Retaining imported surfaces, validating geometry/planes, and delaying release for in-flight use are reusable design rules. Its formats, ABI and synchronization require separate 20F66 tests. |
| Real resource and queue execution | [bridge/NativeMetalObjects.rs](https://github.com/UniXNU/AdrenoMetal/blob/cc0a4e8e57d20f4a4698753c2530875f2b10c0ca/bridge/NativeMetalObjects.rs), [NativeMetalBridge.rs](https://github.com/UniXNU/AdrenoMetal/blob/cc0a4e8e57d20f4a4698753c2530875f2b10c0ca/bridge/NativeMetalBridge.rs) | These call a metal2vulkan runtime and Vulkan backend; they are not a CPU rasterizer we can enable by returning a pointer. Their real execution/resource/error contracts are useful requirements. |
| Isolated host/guest sessions and command replies | [NativeOfflineGPU.cpp](https://github.com/UniXNU/AdrenoMetal/blob/cc0a4e8e57d20f4a4698753c2530875f2b10c0ca/NativeOfflineGPU.cpp), [OfflineMetalSessionWire.h](https://github.com/UniXNU/AdrenoMetal/blob/cc0a4e8e57d20f4a4698753c2530875f2b10c0ca/OfflineMetalSessionWire.h) | Per-client sessions, bounded packets, reply validation and failure closure are useful. The broker explicitly avoids normal Metal publication and checks native 4 KiB page-table context; our current source kernel uses 16 KiB pages. It is not a drop-in backend. |
| Actual host Metal execution | [HostMetalCommandServer.mm](https://github.com/UniXNU/AdrenoMetal/blob/cc0a4e8e57d20f4a4698753c2530875f2b10c0ca/HostMetalCommandServer.mm) | It requires actual host Metal objects/frameworks. The current Linux/WSL QEMU host does not acquire that backend by installing the source. |
| Verified publication only after resource setup | [NativeAdrenoPublish.cpp, near 1380–1428](https://github.com/UniXNU/Adreno740/blob/be70fb13ed19d5fdf139d27977da6f54078cf50a/NativeAdrenoPublish.cpp) | Publication follows real VM, submit, ring, clock and context setup in that implementation. A740/GMU/SMMU/register/firmware details are not reusable unchanged on Mali. Sandbox/mailbox alternatives are not copied. |
| Handle/VM ownership | [NativeAdrenoHandleIndex.h](https://github.com/UniXNU/Adreno740/blob/be70fb13ed19d5fdf139d27977da6f54078cf50a/NativeAdrenoHandleIndex.h), [NativeAdrenoVm.h](https://github.com/UniXNU/Adreno740/blob/be70fb13ed19d5fdf139d27977da6f54078cf50a/NativeAdrenoVm.h) | Handle lifetime and owner-scoped validation are useful concepts. Hardware GPU mappings, reset, shader encoding and register interfaces remain generation-specific. |
| Original runtime ABI | [OriginalGPUProviderABI.h](https://github.com/UniXNU/AdrenoMetal/blob/cc0a4e8e57d20f4a4698753c2530875f2b10c0ca/OriginalGPUProviderABI.h) | Explicit storage/vtable declarations show the need to qualify the selected original ABI. They do not prove compatibility with our 20F66 framework and XNU build. |

These are code-audit findings, not a claim that upstream's reported hardware/UI results were reproduced here.

## Honest software-renderer options

| Option | Assessment |
|---|---|
| Existing custom Darwin CPU compositor | Already tested for its own IPC/graphics contract. It does not implement Apple's Metal object, shader or command ABI. It is not substituted for SpringBoard. |
| Original QuartzCore software path | Symbols exist in this cache, but a supported selection/configuration for the current workload has not been verified. PC/register forcing is excluded. |
| AdrenoMetal/Turnip directly in this guest | Not applicable unchanged: A740 GPU transport, execution, page/ABI and firmware assumptions differ. No Mali hardware support follows from this source audit. |
| Host native-Metal command server | A real backend when its required host frameworks/device exist. Not available on the current Linux/WSL host by source publication alone. |
| CPU Vulkan plus a qualified Metal frontend/translator | A plausible engineering architecture, not a verified implementation. It needs a compatible 20F66 frontend/plugin, actual AIR/metallib/shader translation, CPU Vulkan execution, command/resource validation, IOSurface import/presentation, correct queues/fences/error reporting and per-client isolation. No support level is advertised here. |

A minimal advertised capability must actually allocate resources, execute every advertised operation, validate command buffers and produce measured pixels. Unsupported formats/methods/shaders must return real errors. Returning a fake device or completed command is not an acceptable intermediate success. We therefore implemented and exercised independently useful IOSurface/IOKit diagnostics rather than a pretend GPU.

## Implemented changes and validation

- Passive source-bound Metal/IOKit enumeration and user-return probes with executable-cache/opcode checks.
- A trace classifier that distinguishes query errors, null matching dictionaries, null iterators and empty iterator results; PID reuse, wrong UUID/thread/iterator, incomplete and reordered evidence are rejected.
- A separate ARM64 diagnostic of the original IOSurface C API and an opt-in controller hook after original service health.
- Explicitly bounded observation and dormant-return breakpoint cleanup to avoid hot instrumentation loops. It changes the observer, not guest code or service success criteria.
- Source/recovery preservation receipts, pinned UniXNU sources/licenses, actual compiler/linker commands and three requested reports.

Accepted original services: **22/22**. IOSurface diagnostic: **24/24**. Host classifier/cache tests: **20/20**; observer tests **22/22**; source gates **7/7**; RAM layout **6/6**. Fresh exact-kernel regressions: applications/multitouch **35/35**, compositor **25/25**, graphics **10/10**, window manager **22/22**, live pointer **18/18**, filesystem **11/11**, launchd/service suite **74/74**, real Mach-O/dyld **17/17**. Separate host input checks: **14** and **10**. Repeated nested suites are not summed.

A preserved intermediate IOSurface run was 23/24 due to an unjustified zero-width rejection assertion; the accepted negative test uses the actual source dimension limit, with no production gate relaxed. Test commands, exits, input/output hashes and failed/limited attempts are in `C:/Users/Mehmedamir/Documents/Codex/2026-10-23/referenced-chatgpt-conversation-this-is-an/outputs/duchamp-metal-iosurface-20261119/final-manifest.json`. Existing uncommitted changes, 25 native/recovery-file hashes and the exact source kernel are preserved. The physical memory evidence blocker is unchanged.

## First-frame status and next useful work

No authentic SpringBoard surface/presentation/frame exists in the accepted evidence. The next implementation should qualify cross-process IOSurface right transfer and crash cleanup, then the real 20F66 renderer/provider and shader/queue contract before publishing any accelerator. SpringBoard's remaining startup waits and actual CA transaction must be traced independently. Only a nonzero original surface, its actual owner/transfer, real command or CPU execution, matching SwapEnd/presentation and framebuffer bytes can establish the first frame.
