# 20F66 selector2: evidence-backed byte map

**Incomplete consumer-side analysis; not an Apple C structure or a provider contract.** No successful original 600-byte GPU reply was captured. Unknown fields, unknown ownership and unknown synchronization remain unknown. Status: **BLOCKED_BY_UNKNOWN_ABI**.

Machine-readable map: `research/graphics-abi-20F66/selector2-field-map.json`.

Original evidence: `C:/Users/Mehmedamir/Documents/Codex/2026-10-23/referenced-chatgpt-conversation-this-is-an/outputs/duchamp-abi-repair-20261120/descriptor-consumer-original.json`, `descriptor-symbol-resolver.json`, and `static-verification.json`. All15 inspected code intervals match the actual original cache bytes; all29 anchors redecoded correctly. Cache UUID `E5420DB3-30D0-33AA-8B7E-05B5038BB46D`, IOAccelerator UUID `432C7305-2785-3EA6-90D1-F6F951A61657`.

## Request and alignment

`IOAccelDeviceCreateWithAPIProperty` uses type1 selector2, with no input and requested structure-output capacity `0x258` (600). The caller zeros the buffer, uses stack address `sp+0x30` for output, and stores the requested capacity at `sp+0x20` (`0x1b2fb2534`–`0x1b2fb2554`). Kernel error causes cleanup; success alone is not usable memory proof.

The caller's stack is16-byte aligned; buffer+0 is therefore16-byte aligned. This establishes an observed caller layout, **not a required wire-structure alignment**. All data is decoded using little-endian byte operations, including unaligned host captures. No host C pointer is cast into the input.

## Full 600-byte analysis partition

The last two rows partition the remaining captured bytes for bounded inspection. They do not prove the producer declared arrays of those exact lengths. **Runtime values are UNKNOWN for every row** because discovery never reached a successful GPU reply.

| Byte offset | Width / relative alignment | Actual consumer access | Meaning and confidence | Exact original instructions |
| --- | --- | --- | --- | --- |
| `0x000` | 8 bytes; offset divisible by8 | `ldr x21,[sp,#0x30]`, store object+`0x20`; used in address arithmetic | **Direct** base operand. Whether it names shared/client-mapped memory, its owner, bounds and lifetime: **UNKNOWN** | `0x1b2fb2598`, `0x1b2fb25c8`, `0x1b2fb25e4`, `0x1b2fb2620` |
| `0x008` | 8 bytes; offset divisible by8 | `ldr d0,[sp,#0x38]`, copy to object+`0x34` | **Direct access only. UNKNOWN** interpretation. Not classified as pointer, flags, size, or a pair of fields | `0x1b2fb2634`, `0x1b2fb2638` |
| `0x010` | 4 bytes; offset divisible by4 | `ldr w8,[sp,#0x40]`, copy to object+`0x3c` | **Direct access only. UNKNOWN** semantic label | `0x1b2fb263c`, `0x1b2fb2640` |
| `0x014` | 4 bytes; offset divisible by4 | `ldr w20,[sp,#0x44]`, signed compare and signed loop bound | **Direct** consumer count. Valid producer range and relation to resources: **UNKNOWN** | `0x1b2fb25a4`, `0x1b2fb25ac`, `0x1b2fb2604`, `0x1b2fb2614` |
| `0x018` to `0x057` | 64-byte bounded inspection span; start divisible by8 | Pass address of+`0x18` as symbol-name argument to `dlsym(-3, name)` | **Direct** text start and consumer. **Inferred** inspection extent, not a proved64-byte field. Symbol name/value and declared capacity: **UNKNOWN** | `0x1b2fb2648`, `0x1b2fb264c`, `0x1b2fb2650`; stub→`0x1a6c2cc88:_dlsym` |
| `0x058` to `0x257` | 512 bytes; u32 accesses at4-byte steps | If count>=2, first offset at+`0x58`, then count-1 offsets at+`0x5c+4*i` | **Direct** conditional offset accesses. 128 available u32 slots is arithmetic capacity of this capture, **not a proven producer limit**. Unused bytes remain **UNKNOWN**, not reserved pointers | `0x1b2fb25c4`, `0x1b2fb25d8`, `0x1b2fb25dc` |

Producer write rules and required alignment are **UNKNOWN** for all rows. Static output direction establishes kernel-to-caller reply intent, not how the producer initializes or validates each byte. The offset table is conditional; remaining bytes are intentionally preserved as uninterpreted hex.

## Count and dereference behavior

- Count<1 skips the later u32 dereference loop in the inspected consumer.
- Count==1 uses the base directly and does **not** consume the offset table.
- Count>=2 constructs the first address from base+u32 at+`0x58`, then the rest from+`0x5c+4*i`.
- Each resulting address is dereferenced for a u32 at `0x1b2fb2620`; copied results start at device-object+`0x44`.
- The offline decoder rejects negative counts, counts exceeding the available capture, address-addition overflow and a wrapping4-byte load. These are conservative inspection rules, not claims that the original producer uses these exact validation rules.

The original function-pointer return from `dlsym` is stored at device-object+`0x18`; a null return takes the cleanup path. A NUL found within our64-byte inspection window is only bounded text evidence. It establishes neither the producer's declared capacity nor a callable, compatible symbol.

## Related replies must remain separate

Type1 selector0 requests64bytes into **device-object+`0x270`**, not into the600-byte reply. `device-config64.json` loads object+`0x270/0x274/0x278/0x280/0x288`; `device-shared-size.json` reads+`0x290`; `device-max-resource.json` reads+`0x298`. Those offsets are relative to the wrapper object and cannot be transplanted into this descriptor.

Type2 `IOAccelSharedCreateDeviceShmem` separately requests16 output bytes: a u64 at reply+0 and two u32 at+8/+12 are copied to caller outputs. The corresponding destroy wrapper searches an optional userspace tracking list by a u32 and sends scalar selector6. This does not prove the output address's mapping, memory type, kernel-side lifetime or synchronization rules. Raw code is retained in `shared-create-devshmem.json` and the complete exported `shared-destroy-devshmem.json` interval.

## Offline harness and limits

`tools/duchamp_ioaccel_abi.py` supports exact-size decoding, byte-safe unaligned captures and structure-call shape inspection. It does not resolve descriptor addresses, look up symbols from the input, open IOUserClients, allocate GPU resources or send commands. The separate negative-claim checks never convert caller assertions into trusted ownership.

`python3 tools/test-duchamp-ioaccel-abi.py`: **36/36 passed**, including truncated/oversized input, noncontiguous buffers, count1 semantics, count128 capture bounds, negative/large counts, wrapping addresses, unterminated text, type-specific selectors, malformed queue frames, stale/foreign handles and unknown mapping/synchronization. The1,000 randomized decoder cases are synthetic tests; they are not original Apple replies.

Required next evidence: matching producer dispatch code and allocation/mapping/unmap logic; an actual reply attributable to an original caller; allowed sizes/counts and exact symbol; task ownership; fence/event memory; destruction and completion ordering. Until established, unsupported graphics operations remain unsupported and no compatible provider is published.
