# Duchamp authentic SpringBoard frame status

Date: 2026-11-19. Branch: `duchamp-bootstrap`; HEAD: `d91562d9c2bd3bc33d52550c101de1009bb41dc0` plus preserved uncommitted work.

**BLOCKED_BY_UNIMPLEMENTED_GRAPHICS_API**

**FIRST_SPRINGBOARD_FRAME_VERIFIED = false.**

The exact new source-linked kernel boots original launchd PID 1, BackBoard PID 25 and SpringBoard PID 34. All 22 original service checks pass. The independent original IOSurface diagnostic (PID 37) passes 24/24, and the new original-IOKit contract diagnostic (PID 38) passes 26/26; both exit 0. These diagnostics are not original SpringBoard rendering.

BackBoard's opcode-bound matching chain (trace sequences 526, 528, 529, 530, 531) reports no IOAcceleratorES service. Forty sampled original default-Metal-device returns are nil. A BackBoard swap is recorded with swap ID 1, surface IDs `[0,0,0,0]`, zero rectangles, mask `0x80000007`. No original BackBoard/SpringBoard surface-create selector 0 or completed present event is recorded in this run. SpringBoard's unrelated IOKit opens must not be relabelled as GPU opens. The passively observed generic Metal/IOKit sites have explicit observation caps; absence after a cap is not proof of no later call.

Surface 2 belongs to diagnostic PID 37, not SpringBoard. Its real CPU-written BGRA bytes and Mach port `0x1e03` prove the diagnostic path only. The native CPU-compositor regression frames likewise remain test-client images. No screenshot or altered framebuffer is offered as an authentic SpringBoard frame.

## Acceptance chain still required

1. Original service selects a genuine functional graphics provider/plugin.
2. A real user-client request creates owned resources and successfully executes its advertised work.
3. Original SpringBoard-owned IOSurface is correlated with its task, port and CoreAnimation transaction.
4. Supported rendering produces actual bytes in that surface.
5. The same surface ID reaches BackBoard acceptance, SwapSetLayer, SwapEnd, present and framebuffer copy.
6. A framebuffer dump matches those source bytes and the transaction, with no diagnostic substitution.

Only then may a first-frame status replace the current blocker. This work establishes neither complete Metal nor Mali hardware compatibility.

Evidence directory: `C:/Users/Mehmedamir/Documents/Codex/2026-10-23/referenced-chatgpt-conversation-this-is-an/outputs/duchamp-ioacceleratores-20261119`. The exact new source-linked kernel is `C:/Users/Mehmedamir/Documents/Codex/2026-10-23/referenced-chatgpt-conversation-this-is-an/outputs/duchamp-ioacceleratores-20261119/kernel/kernel.development.sweet`, SHA-256 `4ae22e3d38d0be2372fc66703db6b5b957803c55b743ed4190c4725a0a17cedd`. Its receipt verifies all 1127 object inputs. The prior kernel `97adb397…` remains unchanged. This is a full relink with a newly compiled source object, not a prebuilt-kernel binary patch.

## Test evidence

- `trial-1/service-verification.json`: original service checks and 296 installed-file hash comparisons.
- `platform-iosurface-contract.txt`: original IOSurface 24/24 and exit recorded by the controller.
- `platform-graphics-provider-contract.txt`, `provider-verification.json`: original-library 26/26 with actual return codes, registry identity and owned client.
- `kernel-provider-methods.json`: task-bound kernel entry/return confirmation, including the corrected unsupported-selector error.
- `metal-discovery-result.json`, `original-graphics-events.json`, `trial-1/render-events.jsonl`: exact original-process discovery and empty-swap evidence; zero trace errors.
- `regression-commands.json`: fresh full-source-kernel compositor, GUI, application/multitouch, live-input and Mach-O executions. Detailed test counts are in each verification.json and the final manifest.
- `targeted-commands.json`, `targeted-corrections.json`: ASan/UBSan contract/transport tests plus observer, discovery, profile, bounds and log-integrity cases. The first observer invocation had the wrong filename, and the first profile invocation omitted its required receipt argument; both exited 2 and were corrected separately. An initial host compile included incompatible host stdio/guest fflush declarations; the unnecessary host stdio include was removed before the passing sanitizer run.

The known-good baseline, native 32+4 MiB candidate and Android recovery images remain separate and preserved. Physical status remains **BLOCKED_BY_MEMORY_EVIDENCE**. No flash, reboot, slot change, physical UFS access, firmware modification, commit or push was performed.

## Completed regression results

| Test | Actual result |
| --- | --- |
| Application lifecycle / multitouch | 35/35, exit 0 |
| CPU compositor | 25/25, exit 0 |
| GUI / window manager | 22/22, exit 0 |
| Live virtual mouse | 18/18, exit 0 |
| Dynamic/static Mach-O | 17/17, exit 0 |
| Nested graphics / dual RAMDisk / Darwin services | 10/10, 11/11, 74/74 |
| Native ASan/UBSan input-contract / failure transport | 14/14 + 14/14 |
| Discovery / observer / source profile / large RAM bounds | 20/20, 22/22, 7/7, 6/6 |
| Corrupted-log and false-success rejection | 8/8 |

All five fresh QEMU regression commands exited 0 using the new `4ae22e3d…` kernel. Native/recovery preservation checked 25 file hashes. No hardware validation is inferred.
