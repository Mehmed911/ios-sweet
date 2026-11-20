# Duchamp software graphics boundary

Date: 2026-11-19. Branch: `duchamp-bootstrap`; HEAD: `d91562d9c2bd3bc33d52550c101de1009bb41dc0` plus preserved uncommitted work.

**No Metal backend is implemented by this change.** The existing CPU compositor remains a separate, working Darwin test protocol. Publishing its name as IOAcceleratorES would not make it implement the original Metal ABI.

## Requirements established from the actual build

The original 20F66 function `getMetalPluginClassForService` at `0x181a39ba4` reads provider properties used to locate a bundle/class. The bounded local cache evidence contains `MetalPluginName`, `/System/Library/Extensions`, `.bundle`, and `MetalPluginClassName`. The actual 20F66 selector stubs are also resolved in `metal-plugin-selector-stubs.json`: `bundleWithPath:`, `classNamed:`, `principalClass`, `isSubclassOfClass:` and `initWithAcceleratorPort:`. This is binary-level call-site evidence, not execution of a loaded plugin. Original MTLRegisterDevices invokes this path only after obtaining a nonzero service. The live BackBoard trace stops before it, so no original GPU IOUserClient type, external-method selector set, command-buffer format, feature bitset or shader contract has been exercised. None is invented here.

| Facility | Verified state |
| --- | --- |
| General IOKit matching and real surface client | Operational in the original-library guest probe |
| IOSurface allocation / mappings / Mach-port alias | Operational for the tested BGRA case; full isolation remains partial |
| Custom Darwin CPU compositor | Existing real Z-order, alpha, dirty-region and presentation tests |
| Original Metal plugin for a QEMU CPU renderer | Missing |
| Qualified 20F66 MTLDevice / command encoder ABI | Missing |
| Original Metal shader compilation/execution and synchronization | Unverified / not implemented |
| Adapter from original QuartzCore requests to the custom compositor | Missing |
| Authentic BackBoard/SpringBoard rendered surface | Not verified |

The reusable compositor receives its own `org.duchamp.qemu.compositor` Mach protocol and imports real IOSurface capabilities, validates bounded extents, composites on CPU, and presents through existing AppleCLCD. Original QuartzCore/Metal do not automatically speak that protocol. Its successful pixel comparisons are evidence for its advertised CPU operations, not for Apple's graphics ABI.

## UniXNU comparison

The pinned MIT reference implementations are useful for the sequence of service discovery, real plugin creation, resource validation and command completion:

- [AdrenoMetal cc0a4e8](https://github.com/UniXNU/AdrenoMetal/tree/cc0a4e8e57d20f4a4698753c2530875f2b10c0ca): NativeAdrenoMetalPlugin.mm, NativeBridgeMetalFrontend.mm, bridge/NativeMetalObjects.rs and NativeOfflineGPU.cpp.
- [Adreno740 be70fb1](https://github.com/UniXNU/Adreno740/tree/be70fb13ed19d5fdf139d27977da6f54078cf50a): real resource preparation before publication.

Their OriginalAcceleratorABI.h explicitly describes a supplied **iOS17** base. It is not 20F66 ABI evidence. The host Metal server uses a real host Metal device; source availability does not provide such a device on the Linux test host. The offline bridge also has page-table assumptions that need qualification against this port's 16 KiB kernel mappings. Adreno-specific firmware, registers, shader backend and SMMU/GMU programming are not portable Mali-G615 implementations. No reference GPU code or private class replacement was copied into this kernel.

A genuine CPU/Vulkan-backed implementation remains a possible future engineering project, but would need a 20F66-qualified plugin/runtime ABI, real supported command execution, accurate capability reporting, IOSurface resource bindings and completion/presentation synchronization. A class name, nil-to-nonnull substitution or silent-success selector is insufficient. Unsupported work must return an error. This phase implements the independent surface error correction and bounded client transport rather than advertising an unimplemented renderer.

Evidence directory: `C:/Users/Mehmedamir/Documents/Codex/2026-10-23/referenced-chatgpt-conversation-this-is-an/outputs/duchamp-ioacceleratores-20261119`. The exact new source-linked kernel is `C:/Users/Mehmedamir/Documents/Codex/2026-10-23/referenced-chatgpt-conversation-this-is-an/outputs/duchamp-ioacceleratores-20261119/kernel/kernel.development.sweet`, SHA-256 `4ae22e3d38d0be2372fc66703db6b5b957803c55b743ed4190c4725a0a17cedd`. Its receipt verifies all 1127 object inputs. The prior kernel `97adb397…` remains unchanged. This is a full relink with a newly compiled source object, not a prebuilt-kernel binary patch.

## Next justified implementation boundary

Qualify a legally reusable 20F66-compatible plugin and a real execution backend before publishing an accelerator match. Record the original requested user-client type/selectors only when that genuine provider exists, then implement and test the smallest supported resource/render/commit subset. Continue using the separate CPU compositor as a pixel oracle, without labelling its clients or frames as SpringBoard. Physical Mali support is a separate hardware task.
