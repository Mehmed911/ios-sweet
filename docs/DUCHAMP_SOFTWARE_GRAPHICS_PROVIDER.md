# Software graphics provider implementation decision

Date: 2026-11-20. Branch: `duchamp-bootstrap`, HEAD `d91562d9c2bd3bc33d52550c101de1009bb41dc0` plus preserved uncommitted work.

**Status: BLOCKED_BY_UNKNOWN_ABI. No IOAcceleratorES provider or Metal device was published.**

The user explicitly requires stopping provider implementation at an unknown ABI boundary. The missing type1 device descriptor, resource ownership and command/completion contracts are on the mandatory initialization/execution path. Implementing only a matching class, storing the API string, or returning invented descriptors would shift the failure while falsely advertising compatibility.

## Available reusable implementation

The existing 0BSD Darwin compositor has real surface capability import, bounded CPU BGRA compositing, alpha, Z-order, dirty rectangles, input routing, process cleanup and framebuffer presentation. It uses its own Mach protocol. Original QuartzCore/Metal does not automatically submit that protocol. Its successful test frames are not SpringBoard frames.

The existing IOSurface implementation already handles the tested allocations and same-process Mach-port aliases. Its default external-method error remains explicit. No replacement or duplicate surface allocator was added. Complete sandbox/global-ID/concurrency qualification is still separate work.

## Reference source audit

| Reference | Pinned revision / license | Reuse decision |
| --- | --- | --- |
| UniXNU AdrenoMetal | cc0a4e8e57d20f4a4698753c2530875f2b10c0ca / MIT | Study discovery, real backend operations, bounded transports and resource lifetimes |
| UniXNU Adreno740 | be70fb13ed19d5fdf139d27977da6f54078cf50a / MIT | Study publish-after-readiness; no Adreno register, firmware, memory or shader code copied |

Both local reference worktrees were checked clean; exact inspected-file and license hashes are in `reference-source-receipts.json`.

- `OriginalAcceleratorABI.h` explicitly describes an iOS17 original base. Its size assertion does not establish the complete 20F66 ABI.
- `NativeOfflineGPU.cpp` uses its own wire protocol, per-task capabilities, packet limits and a 4 KiB page-table qualification. Its selector numbers are not original IOAccelerator selector numbers and are not copied.
- `OfflineMetalFrontend.mm` proxies real work through that explicit offline protocol. `HostMetalCommandServer.mm` requires a real host Metal device and executes operations on it. Source availability alone does not provide such a backend on this Linux QEMU host.
- `IOGPUMetalDeviceShim.h` has a TARGET_OS_OSX path that supplies zero-return stubs for unimplemented selectors. That permissive path is specifically excluded by this task's no-fabricated-success rule and was not reused.
- NativeBridgeMetalFrontend / NativeMetalObjects concepts require actual resource/shader/queue implementations. They are not a ready-to-install 20F66 CPU provider.

## Safe code change

Only the offline execution verifier was generalized to follow explicitly recorded kernel-manifest, trace-config and guest-build paths. It still hashes every source-link input, binds the exact kernel hash, checks the canonical trace receipt, verifies current guest sources, validates actual task/return pairs and rejects missing evidence. It does not publish a service, alter Metal discovery, change a kernel or add an authorization grant.

Five verifier cases use explicitly labelled copies of the accepted 2026-11-19 logs: default receipt paths, explicit receipt paths, wrong kernel, non-passive config, and missing receipt. These are verifier tests, not new guest execution or graphics functionality. The failed new QEMU run is retained separately; it is not replaced by replayed evidence.

## Minimum justified next implementation

1. Qualify the entire selector2 producer/consumer contract, mapped address lifetime, bounds and synchronization using the exact 20F66 interfaces.
2. Qualify resource import/ownership across type1, type2 and type4 clients and actual queue record meanings.
3. Select or build a real CPU execution backend and a 20F66-qualified plugin/runtime. Advertise only commands it executes correctly; reject unsupported work.
4. Then publish a genuine provider and trace the original requests. Completion must follow actual execution, and a surface must be presented with its owning task and transaction intact.

No provisional compatible interface, fake feature table, zeroed descriptor, Apple/Adreno command stream interpretation or immediate fake completion was implemented.

Code: [receipt-bound verifier](C:/Users/Mehmedamir/Documents/Codex/2026-10-23/referenced-chatgpt-conversation-this-is-an/work/ios-sweet-duchamp/tools/verify-duchamp-provider-run.py). Test receipt: [five labelled replay cases](C:/Users/Mehmedamir/Documents/Codex/2026-10-23/referenced-chatgpt-conversation-this-is-an/outputs/duchamp-ioacceleratores-abi-20261120/receipt-path-tests.json). Physical status remains BLOCKED_BY_MEMORY_EVIDENCE. No phone, slot, UFS, firmware, commit or push operation occurred.
