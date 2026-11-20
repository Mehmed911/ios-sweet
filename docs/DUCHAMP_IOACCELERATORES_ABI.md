# Original 20F66 IOAcceleratorES ABI audit

Date: 2026-11-20. Branch: `duchamp-bootstrap`, HEAD `d91562d9c2bd3bc33d52550c101de1009bb41dc0` plus preserved uncommitted work.

**Status: BLOCKED_BY_UNKNOWN_ABI.** The discovery prefix and several static connection/request shapes are established. The complete resource, command and completion ABI needed for an honest software provider is not.

## Evidence levels

- **Observed**: actual original BackBoard queries in the accepted source-kernel QEMU trace, with process/task identity and cache UUID binding.
- **Static**: instructions in the locally available original 20F66 binaries. These establish call-site arguments, not successful execution or the complete producer contract.
- **Unknown**: field semantics, lifetime, synchronization and execution behavior that are not established by those observations/instructions. No unknown field is implemented by returning zeros.

## Discovery and service identity

The observed original query is `IOServiceMatching("IOAcceleratorES")`, with userspace dictionary `IOProviderClass=IOAcceleratorES`. The kernel adds its notification-user key. IOServiceGetMatchingServices returns kr 0 and iterator 0; IOIteratorNext returns service 0. No GPU client is opened by this enumeration. This is valid empty matching, not a demonstrated error-code conversion.

Metal `getMetalPluginClassForService` uses `MetalPluginName`, `/System/Library/Extensions`, `.bundle`, and optional `MetalPluginClassName` before selecting a class and invoking `initWithAcceleratorPort:`. The exact 20F66 selector stubs were resolved; their presence is not evidence that a plugin was instantiated.

The actual 2710-image cache contains **AGXMetalA11**, not merely generic Metal: UUID `A1D04B73-670F-33D5-BE50-89366A4BEA14`, version `227.6.3.0.0`. Metal UUID is `88922408-FD68-3396-8465-3775CE66FF60`; IOAccelerator UUID is `432C7305-2785-3EA6-90D1-F6F951A61657`. Mach-O headers independently confirm ARM64 and iOS16.5. `actual-cache-gpu-images.json`, `graphics-library-identities.json` and `static-abi-summary.json` retain the identities and hashes.

The matching original kernelcache was additionally acquired from the same Apple-hosted iPhone10,3/iPhone10,6 20F66 IPSW using bounded ZIP-range extraction and CRC validation. Its version is `xnu-8796.122.4~1/RELEASE_ARM64_T8015`. This is a local analysis artifact, never executed or installed. ZIP CRC/SHA-256 are not Apple signature attestation.

Its AGXG10P_B0 personality contains `IOClass=AGXAcceleratorG10P_B0`, `IOProviderClass=AppleARMIODevice`, `IONameMatch=gpu,t8015`, `IOMatchCategory=IOAcceleratorES`, and `MetalPluginName=AGXMetalA11`. The personality's provider class is the **parent hardware nub**, whereas the userspace matching class selects an accelerator instance. Copying these Apple-hardware personality properties onto a CPU compositor would not implement that accelerator. No personality or driver is copied.

## Static interface prefix from 20F66

The following are independently decoded from original IOAccelerator/Metal call sites. They are **not observed requests from BackBoard after successful GPU discovery**.

| Endpoint / operation | Verified call shape | Exact original site |
| --- | --- | --- |
| Device open | IOServiceOpen type **1** | 0x1b2fb244c / 0x1b2fb2450 |
| Conditional device API label | selector **7**, 16 structure-input bytes; Metal supplies `Metal` | 0x1b2fb2498 / 0x1b2fb249c |
| Mandatory device descriptor | selector **2**, no structure input, requested output **0x258 = 600 bytes** | 0x1b2fb2534 / 0x1b2fb2548 |
| Mandatory secondary device query | selector **0**, requested output **64 bytes** | 0x1b2fb265c / 0x1b2fb2670 |
| Optional device query | selector **5**, requested output **24 bytes** | 0x1b2fb268c / 0x1b2fb26a0 |
| Shared-resource client open | IOServiceOpen type **2** | 0x1b2fb2d98 |
| Shared-client query | selector **7**, requested output **16 bytes** | 0x1b2fb2e08 / 0x1b2fb2e1c |
| Command-queue client open | IOServiceOpen type **4** | 0x1b2fb4284 |
| Queue submission | selector **1**, structure-input size computed as **8 + 24 × count**, count read at input offset 4 | 0x1b2fb45a8..0x1b2fb45d0 |

The original direct islands resolve to IOServiceOpen at `0x18e54c55c`, IOConnectCallStructMethod at `0x18e539be8`, and IOConnectCallMethod at `0x18e539c28`. No selector was copied from UniXNU, another iOS version, the custom compositor, or IOSurface. In particular, selector 7 has different shapes on different client types.

`MTLIOAccelDevice initWithAcceleratorPort:` calls IOAccelDeviceCreateWithAPIProperty, then configuration/shared-memory queries. The AGXA11Device constructor additionally invokes a family initializer and `setupCompiler:` with an opaque argument; this is not a qualified portable shader backend or a fabricated feature-set enum.

## First unsafe-to-invent boundary

The type1 selector2 reply is more than a success flag. Its consumer loads a 64-bit value at reply+0 as a base, reads a count at +0x14 and offsets at +0x58/+0x5c, constructs addresses and dereferences them. These are **consumer offsets**, not a complete or approved C structure definition. Returning a zero-filled 600-byte response would not establish usable memory mappings, valid offsets, ownership, synchronization or callbacks.

Still unknown:

1. Complete selector2 producer structure, field validation and mapped-memory lifecycle.
2. Required capabilities and configuration reply semantics, including the 64-byte query.
3. Surface/resource identifiers, ownership transfer and descriptor layout across device/shared/queue clients.
4. Meaning of each 24-byte queue record and its referenced GPU command data.
5. Command validation, fence/event memory, asynchronous callback and completion semantics.
6. A qualified 20F66 software plugin/runtime that actually executes supported commands and reports accurate capabilities.
7. The original kernel IOUserClient class implementation and dispatch structures for those interfaces.

The pinned ipsw tool can list original kernel personalities but reports that KEXT extraction from this non-MH_FILESET kernel is unsupported. The original image is retained; its defined symbol table does not expose the targeted IOAcceleratorES/IOGPU class definitions. That tool limitation is not proof that further manual analysis is impossible. Typed matching kernel interfaces or further independently reviewed producer/consumer analysis are still required.

The full constructor, queue, resource and relevant AGX functions are bounded by the next real code symbol in `bounded-functions.json`; convenient fixed-size neighboring-function dumps are not treated as ABI evidence for the named function. `resolved-static-calls.json` records the supported ADRP/ADD/BR island resolution without pointer-tag guessing.

Evidence: `C:/Users/Mehmedamir/Documents/Codex/2026-10-23/referenced-chatgpt-conversation-this-is-an/outputs/duchamp-ioacceleratores-abi-20261120`. See [machine-readable ABI claims](C:/Users/Mehmedamir/Documents/Codex/2026-10-23/referenced-chatgpt-conversation-this-is-an/outputs/duchamp-ioacceleratores-abi-20261120/static-abi-summary.json), [original kernel acquisition receipt](C:/Users/Mehmedamir/Documents/Codex/2026-10-23/referenced-chatgpt-conversation-this-is-an/outputs/duchamp-ioacceleratores-abi-20261120/apple-kernelcache-receipt.json) and [source references](C:/Users/Mehmedamir/Documents/Codex/2026-10-23/referenced-chatgpt-conversation-this-is-an/outputs/duchamp-ioacceleratores-abi-20261120/reference-source-receipts.json).
