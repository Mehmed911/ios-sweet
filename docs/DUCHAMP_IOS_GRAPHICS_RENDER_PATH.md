# 20F66 original graphics render path in the source-built QEMU kernel

Scope: 2026-11-19, `duchamp-bootstrap`, uncommitted working tree based on `d91562d9c2bd3bc33d52550c101de1009bb41dc0`. Physical MT6897 status remains **BLOCKED_BY_MEMORY_EVIDENCE**. This report describes a QEMU compatibility environment, not native Mali or iOS hardware support.

## Bound implementation

The executed kernel is `97adb3971c14e1c8f1fd42b18623b183d32edf9d882dc99a2c216b5dc229d001`, selected through its full source-link receipt, SHA-256 `db250b3319dd4fc84edd930b12b4123bc7549a8111c22c7d1995dd54d2f42e54`. All 1,127 input object hashes were revalidated. No archived CI kernel was substituted or instruction-patched.

The original 20F66 binaries and intact cache execute in a separate, copied 3 GiB writable RAM filesystem on the host's native Linux filesystem. The 43 cache components total 2,722,512,896 bytes; cache UUID is `E5420DB3-30D0-33AA-8B7E-05B5038BB46D`. This large diagnostic layout is distinct from the frozen native 32+4 MiB candidate and the small dual-RAMDisk regression layout. The large test uses no block/UFS backend.

The local executable receipts establish which files were tested. They do not independently authenticate Apple's distribution chain, confer redistribution permission, or prove firmware ownership.

## Existing components and observed boundaries

| Boundary | Actual implementation | Evidence and limitation |
|---|---|---|
| Original SpringBoard executable | Original main executable plus original SpringBoard framework in the intact cache; original launchd mobile job | Mach-O UUID, actual kernel task/PID/birth, main entry, health checks. Application initialization and a SpringBoard CA transaction are not established. |
| CoreAnimation | Original QuartzCore cache image | BackBoard enters `CA::Transaction::commit()` and `CA::Context::commit_transaction()`. BackBoard transactions alone are not SpringBoard content. |
| Metal device acquisition | Original `CAMetalContextCreate` calls original Metal `MTLCreateSystemDefaultDevice` | A breakpoint immediately after the normal call observes nil. The old trace label `metal_device_result` is the wrapper RET, not this direct-return site. |
| IOSurface backing | Port-specific `SweetSurface` / `IOSurfaceRootUserClient` | Selector 13 limits query succeeds. No successful selector 0 creation by the original graphical processes is observed. |
| BackBoard display RPC | Original service plus native read-only BKS probe | Two actual replies return `kr=0`, 1125×2436, scale 1. Active endpoints and replies do not prove display rendering. |
| Frame submission | Original IOMobileFramebuffer library into port-specific `IOMobileFramebufferUserClient` | SwapBegin/SwapEnd are observed; Swap 1 contains four zero surface IDs and zero rectangles. Method success is not pixel presentation. |
| Pixel copy/presentation | `AppleCLCD::swap`, timer callback, `AppleCLCD::present` | Latest-record storage and a bounded CPU-copy path; not an Apple GPU command processor. Empty submissions have no source pixels. |
| Scanout | Shared QEMU guest RAM at `0xfcc2f000`, host snapshot helper | 1220×2712, row pitch 4992, 13,538,304 raw bytes. Captured console pixels have no SpringBoard attribution. |
| Custom Darwin compositor/WM | Separate launchd-managed services from earlier work | Regression-tested independently. They are not substituted into the original CA/BackBoard render chain. |
| Input | Existing virtual input test services/driver | Regression-tested VirtIO events and custom-shell routing. This is not evidence of original BackBoard HID acceptance. |

The display probe's 1125×2436 logical response and the framebuffer structure's later 1220×2712 logical/physical values are recorded separately. No coordinate equivalence is assumed or silently corrected.

## Exact source locations

The kernel's actual linked source snapshot is `/var/tmp/duchamp-clang.zZKCR0J4/kernel-workspace/dxb/xnu/` in Ubuntu. Relevant source files were copied to `C:/Users/Mehmedamir/Documents/Codex/2026-10-23/referenced-chatgpt-conversation-this-is-an/outputs/duchamp-springboard-first-frame-20261119/linked-source/` and matched to the object receipt's source hashes:

- `iokit/Kernel/arm/SweetSurface.cpp`: `kernelAddress` at line 93; client task retention at 447; per-task data/state mappings at 507–531; output layout at 623; create at 650; selector dispatch at 725.
- `iokit/Kernel/arm/SweetFramebuffer.cpp`: default surface and driver registration around 160–203; timer/dirty-record drain at 245–256; `swap` at 300; `present` at 312; source-buffer bounds/copy at 350–400; owning task at 410; SwapEnd at 494–502.
- The five linked DWARF inputs and their hashes are in `C:/Users/Mehmedamir/Documents/Codex/2026-10-23/referenced-chatgpt-conversation-this-is-an/outputs/duchamp-springboard-first-frame-20261119/trace/trace-config-v4.json`: `sleh.o`, `kern_proc.o`, `sys_generic.o`, `SweetSurface.cpo`, `SweetFramebuffer.cpo`. This avoids guessed C++/kernel structure offsets.

Working-tree tooling:

- [Passive observer](C:/Users/Mehmedamir/Documents/Codex/2026-10-23/referenced-chatgpt-conversation-this-is-an/work/ios-sweet-duchamp/tools/duchamp-render-passive.gdb): hardware breakpoints and reads only; no guest function calls, register assignment or guest-memory writes.
- [Trace preparation](C:/Users/Mehmedamir/Documents/Codex/2026-10-23/referenced-chatgpt-conversation-this-is-an/work/ios-sweet-duchamp/tools/prepare-duchamp-render-trace.py): source receipt, actual DWARF, kernel symbol/opcode lookup, original cache VA-to-file mapping, executable UUIDs.
- [DWARF parser](C:/Users/Mehmedamir/Documents/Codex/2026-10-23/referenced-chatgpt-conversation-this-is-an/work/ios-sweet-duchamp/tools/duchamp_dwarf_layout.py): rejects absent/ambiguous types, nonconstant member offsets and out-of-record fields. Readers additionally validate field width; bitfields are not guessed.
- [QEMU runner](C:/Users/Mehmedamir/Documents/Codex/2026-10-23/referenced-chatgpt-conversation-this-is-an/work/ios-sweet-duchamp/tools/qemu-service-ram.py): separate fixed passive-observer option; original prohibition on instruction patches/arbitrary legacy debugger scripts remains for source-linked kernels.
- [Conservative pixel prerequisites](C:/Users/Mehmedamir/Documents/Codex/2026-10-23/referenced-chatgpt-conversation-this-is-an/work/ios-sweet-duchamp/tools/duchamp_render_proof.py) and [negative tests](C:/Users/Mehmedamir/Documents/Codex/2026-10-23/referenced-chatgpt-conversation-this-is-an/work/ios-sweet-duchamp/tools/test-duchamp-render-trace.py): PID/birth/UUID/task correlation, strict BGRA bounds/copy comparisons. These helpers are not a complete first-frame acceptance engine.
- [Source-profile denials](C:/Users/Mehmedamir/Documents/Codex/2026-10-23/referenced-chatgpt-conversation-this-is-an/work/ios-sweet-duchamp/tools/test-duchamp-source-large-profile.py): original four denials plus nonpassive, wrong-kernel and wrong-observer denials.

## Surface and buffer safety limits

Existing surface references/maps are per client task; creator PID plus task-unique birth is recorded on successful create. A lookup reference, global surface ID, Mach port or matching pixels alone does not prove who produced the content. The existing global ID lookup and no-op ownership/notification selectors are not a complete security or private-ABI implementation. No permissive selector behavior was added in this task.

The source caps dimensions, properties and buffer sizes and checks copy bounds. The trace additionally bounds reads to 32 MiB, source snapshots to eight surfaces, and exact framebuffer dimensions/stride. Unsupported formats, short buffers, bad pitch/offset, wrong binary UUID, reused PID births, wrong client tasks and mismatching pixels are rejected by the proof-prerequisite tests. The helpers deliberately require BGRA; no broader conversion is claimed.

The observer now records timer/work-loop presentation even when the validated kernel thread has no BSD process. Such a callback is labelled `<kernel-thread>` and never assigned a fabricated userspace owner. Empty SwapEnd/present completion is distinguished from content-bearing presentation.

## Original cache call-chain evidence

The bounded decode of the matching QuartzCore bytes establishes:

1. `CAMetalContextCreate` at unslid `0x18837b718` pushes an autorelease pool.
2. Its call at `0x18837b73c` reaches stub `0x18dbb87c0`.
3. The actual ADRP/ADD/BR stub targets `0x181a34b3c`, symbolicated in the same cache as `_MTLCreateSystemDefaultDevice`.
4. The direct-return site `0x18837b740` is `mov x20,x0`; this site records the returned device before it is moved.
5. The normal path preserves that result through pool pop and returns it at `0x18837b758`.

The byte records, mapping, bounded LLVM decode, stub decode and symbolication are retained in `metal-device.bin`, `metal-device-bounded-llvm.txt`, `metal-context-callees.json` and `metal-context-stubs.json` under `C:/Users/Mehmedamir/Documents/Codex/2026-10-23/referenced-chatgpt-conversation-this-is-an/outputs/duchamp-springboard-first-frame-20261119`. No guessed pointer-authentication mask or patched renderer branch was used.

Apple documents the default device as the starting point for Metal objects: [Getting the default GPU](https://developer.apple.com/documentation/metal/getting-the-default-gpu). This API documentation explains the interface; the nil result in this particular environment comes from the actual trace.

## First-frame acceptance still required

An authentic frame requires an original SpringBoard transaction plus producer identity or a demonstrated cross-process render transfer, a real nonzero backing surface, accepted BackBoard operation, a bounded compositor copy/presentation completion, and a contemporaneous raw framebuffer comparison tied to the same surface and sequence. Hashes alone, an empty swap acknowledgement, console changes, default surface 1, BackBoard-only transactions, or a custom test pattern do not satisfy this chain.

There is no verified original CPU-renderer selection mechanism in this task. The old QuartzCore debugger script contains register/PC forcing and CI-era addresses and was not executed. Neither it nor a fake Metal object/reply is an acceptable compatibility fix. A real renderer/provider implementation or a verified original CPU configuration must be investigated before a first-frame claim. Missing launchd services and display-coordinate consistency remain separate follow-up checks.
