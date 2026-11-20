# 20F66 IOAcceleratorES ABI recovery, revision 2

Date: 2026-11-20. Branch `duchamp-bootstrap`; HEAD `d91562d9c2bd3bc33d52550c101de1009bb41dc0` plus preserved working changes.

**BLOCKED_BY_UNKNOWN_ABI.** The disk blocker is resolved and a fresh original-service regression completed. A usable original graphics-provider ABI is still incomplete. No GPU service was published, no unknown command was acknowledged as executed, and no authentic SpringBoard frame was verified. Physical status remains **BLOCKED_BY_MEMORY_EVIDENCE**.

Evidence directory: `C:/Users/Mehmedamir/Documents/Codex/2026-10-23/referenced-chatgpt-conversation-this-is-an/outputs/duchamp-abi-repair-20261120` (below, `OUT`). All phone operations, firmware changes, commits and pushes: none.

## Exact binary identity and evidence quality

The original ARM64 20F66 cache UUID is `E5420DB3-30D0-33AA-8B7E-05B5038BB46D`; IOAccelerator UUID is `432C7305-2785-3EA6-90D1-F6F951A61657`. The original AGXMetalA11 UUID is `A1D04B73-670F-33D5-BE50-89366A4BEA14`. The cache is the previously retained, Apple-IPSW-derived fixture; actual guest installation checks now revalidated all **296/296** installed files. This is content binding, not firmware attestation.

`tools/verify-duchamp-ioaccel-static.py` independently rereads **15 bounded original code intervals** from the local cache, redecodes them and verifies **29 instruction anchors**. `OUT/static-verification.json` records addresses, lengths and hashes. Unlike successful runtime requests, static code establishes what the caller would request if discovery succeeded. The **600-byte output capacity is established statically; no successful original GPU 600-byte reply has been captured**.

## Connection and request inventory

All numeric selectors below come from the actual 20F66 instructions, not an unrelated OS dispatch table.

| Client type | Operation and shape | Original address | Remaining unknown |
| --- | --- | --- | --- |
| 1 | `IOServiceOpen`, type 1 | `0x1b2fb244c`, call `0x1b2fb2450` | Real provider/client class and initialization |
| 1 | Conditional selector 7, 16 structure-input bytes | `0x1b2fb2498`, `0x1b2fb249c` | Complete label validation rules |
| 1 | Selector 2, no input, requested structure output 600 | `0x1b2fb2534`–`0x1b2fb2554` | Producer layout, mapping, ownership, synchronization |
| 1 | Mandatory selector 0, structure output 64 | `0x1b2fb265c`–`0x1b2fb267c` | Configuration values/capabilities |
| 1 | Optional selector 5, structure output 24 | `0x1b2fb268c`–`0x1b2fb26ac` | Semantics and allowed values |
| 2 | `IOServiceOpen`, type 2 | `0x1b2fb2d98` | Resource ownership contract |
| 2 | Selector 7, structure output 16 | `0x1b2fb2e08`, `0x1b2fb2e1c` | Shared-client reply semantics |
| 2 | `IOAccelSharedCreateDeviceShmem`: selector 5, one scalar input, 16 structure-output bytes | `0x1b2fb2f2c`–`0x1b2fb2f68` | Scalar meaning and mapping provenance; the wrapper copies a u64 and two u32 outputs |
| 2 | `IOAccelSharedDestroyDeviceShmem`: selector 6, one scalar input, no output | `0x1b2fb30f4`–`0x1b2fb310c` | Kernel allocation teardown, unmap, reference accounting |
| 4 | `IOServiceOpen`, type 4 | `0x1b2fb4284` | Queue/class contract |
| 4 | Selector 1, structure input `8 + 24*N`; signed count at input+4, no outputs | `0x1b2fb4578`–`0x1b2fb45d0` | Every record's semantics, referenced commands and completion protocol |

Selector 7 is type-specific: the type1 input and type2 output are different calls. The queue constructor's asynchronous scalar registration is **not** evidence of `IOConnectMapMemory64`. Resource creation has further variable-size inputs not given invented names here.

Error paths are visible in the original constructor: selector2 failure at `0x1b2fb2558` and mandatory selector0 failure at `0x1b2fb2680` go to cleanup and return a null wrapper; selector5 failure is optional. A reply decoder is not allowed to turn those failures into success. Exported device/shared/queue release wrappers at `0x1b2fb2728`, `0x1b2fb2eb4`, and `0x1b2fb44e8` all guard null and branch to the same release thunk. This does not establish the kernel user-client destructor, queue drain, cross-process ownership or asynchronous completion behavior.

## 600-byte consumer boundary

See `docs/DUCHAMP_GRAPHICS_ABI_FIELD_MAP.md` and `research/graphics-abi-20F66/selector2-field-map.json` for the full byte partition, instruction anchors and confidence labels.

Newly verified: reply+`0x18` is passed as the symbol-name argument to **`dlsym`**, with first argument -3. The direct stub resolves to `0x1a6c2cc88` in libdyld; the symbol resolver and original bytes independently agree. The returned function pointer is saved at device-object+`0x18`, and null causes constructor failure. The declared string extent remains unknown.

The base at reply+0 is used to form addresses that the original consumer dereferences. A count of one uses the base directly; only count>=2 uses the offset table. A 600-byte zero reply, a nonzero service handle, or a syntactically valid offset list cannot establish real allocation, mapping or ownership. The 64-byte configuration query writes device-object+`0x270`; its later accessors are **not additional fields of the 600-byte reply**.

## Compatible implementation study

The pinned public Apple [IOFramebufferUserClient](https://github.com/apple-oss-distributions/IOGraphics/blob/76285384ff0ce63965a21b8023bf6d7e447fcc19/IOGraphicsFamily/IOFramebufferUserClient.cpp) was reviewed for bounds-checked dispatch, descriptor-backed mapping and termination patterns (lines 168, 242, 310). It is APSL2.0 source, retained for study only. It does not define this iOS accelerator ABI; no selectors or implementation were copied. Receipt/hash: `OUT/reference/apple-source-receipt.json`.

The retained MIT [AdrenoMetal revision](https://github.com/UniXNU/AdrenoMetal/tree/cc0a4e8e57d20f4a4698753c2530875f2b10c0ca) and [Adreno740 revision](https://github.com/UniXNU/Adreno740/tree/be70fb13ed19d5fdf139d27977da6f54078cf50a) remain useful for per-task ownership, bounded requests and real-backend completion patterns. `OriginalAcceleratorABI.h:3` explicitly targets iOS17, `OriginalGPUProviderABI.h:3` leaves opaque storage, and `NativeOfflineGPU.cpp:179` uses its own wire contract. The macOS shim and host Metal server require other runtimes. These sources do not establish 20F66's producer structure or provide a Linux software Metal executor. Exact file hashes/licenses are retained in `OUT/baseline/reference-source-receipts.json`. [UniXNU's GPU guide](https://unixnu.com/porting/gpu) also requires matching the GPU and OS ABI. No Adreno hardware, shader or firmware code was transferred to MT6897/Mali.

## Changes and tests

New `tools/duchamp_ioaccel_abi.py` safely decodes captured bytes and recognizes the verified structure-call prefix. It performs no pointer dereference, IOKit call or rendering. Unknown types, bad counts, short/oversized captures and wrapping ranges are rejected. Unknown methods are explicitly unsupported. Even positive caller-supplied ownership/mapping/synchronization assertions remain unverified and cannot enable execution. This diagnostic check is not a new authorization system or provider.

| Verification | Result | Evidence |
| --- | --- | --- |
| New offline ABI/bounds/negative-claim tests, including 1,000 deterministic randomized captures | **36/36**, exit 0 | `OUT/test-duchamp-ioaccel-abi.py.log` |
| Original code binding | **15 intervals / 29 anchors**, exit 0 | `OUT/static-verification.json` |
| Fresh original services under source-built XNU | **22/22**, exit 0 | `OUT/trial-1/service-verification.json` |
| Original IOSurface diagnostic program | **24/24**, guest exit 0 | `OUT/platform-iosurface-contract.txt` |
| Real IOKit diagnostic program | **26/26**, guest exit 0 | `OUT/platform-graphics-provider-contract.txt` |
| Correlation of original callers, task identity and real kernel returns | **PASS**, exit 0 | `OUT/correlated-verification.json` |
| Corrupted/false-success variants of the fresh IOKit log | **8/8**, exit 0 | `OUT/test-duchamp-graphics-provider-log-corrected.log` |
| Discovery / observer / RAM bounds regressions | **20/20 + 22/22 + 6/6**, exit 0 | `OUT/targeted-tests.json` |
| Frozen native/recovery artifacts | **25/25 unchanged** | `OUT/preserved-native-files.json` |

The first invocation of the IOKit log test omitted its required log argument and exited 2; it is retained in `OUT/targeted-tests.json`. The corrected invocation above uses the **fresh actual guest log** and passes. The earlier disk-failed original-service runs remain failures, not relabeled passes.

Applications35, compositor25, windows22, mouse18, Mach-O17, filesystem11 and services74 were already executed on this exact unchanged kernel in the preceding baseline. Their receipts/log hashes are revalidated as preserved evidence; they were **not rerun in this revision**, which changes only offline tooling/docs. No kernel patch or guest provider was introduced.

## Fresh execution and next required evidence

Exact source-built kernel SHA-256: `4ae22e3d38d0be2372fc66703db6b5b957803c55b743ed4190c4725a0a17cedd`, verified against its 1127 source-link inputs. Original launchd remains PID1; original BackBoard is PID25/birth90 and SpringBoard PID34/birth119, UID501. The run ended with `PLATFORM SERVICES DONE status=0`, debugger exit0, no observed panic, host duration213.897s. Source fixture hashes and all installed files agree.

The fresh original BackBoard query returns kr0 but iterator0; subsequent iteration returns service0. This is empty service matching, **not** a proven error-to-success conversion. The observed swap1 has four zero surface IDs and zero rectangles. Diagnostic IOSurface use and the custom compositor are separately attributed; neither is an authentic SpringBoard frame. Sampling limits also mean this is not a claim about every later unobserved call.

Next: recover the matching producer dispatch/mapping code for type1 selector2 and its associated shared-client allocation/destruction contract. Establish actual returned values, owner task, map/unmap lifetime, callback symbol, fence/event layout and completion ordering before implementing a provider. Current no-provider behavior and explicit unsupported returns remain correct. Do not proceed by publishing a service that merely satisfies discovery.
