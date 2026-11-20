# SpringBoard rendering progress and validation

Date: 2026-11-20. Branch: `duchamp-bootstrap`, HEAD `d91562d9c2bd3bc33d52550c101de1009bb41dc0` plus preserved uncommitted work.

**Highest supported status: BLOCKED_BY_UNKNOWN_ABI.**

No new IOAcceleratorES provider was installed or discovered. No GPU connection, original graphics selector execution, resource binding, rendered SpringBoard pixels, or first authentic frame is claimed. Static call-site decoding must not be relabelled as an observed successful BackBoard request.

## Preserved source-built baseline

The exact source-built kernel remains SHA-256 `4ae22e3d38d0be2372fc66703db6b5b957803c55b743ed4190c4725a0a17cedd`, 1127 verified source-link inputs. No kernel or boot payload change was necessary for this ABI audit. The previously accepted original-service 22/22, IOSurface24/24 and IOKit26/26 records remain archived, with their source/artifact hashes rechecked. Diagnostic surface IDs and custom-compositor images remain separate from original SpringBoard rendering.

## Fresh completed regressions

| Test on the exact unchanged source-built kernel | Result |
| --- | --- |
| Application lifecycle / multitouch | 35/35 |
| Compositor | 25/25 |
| GUI / window management | 22/22 |
| Live virtual mouse | 18/18 |
| Dynamic / static Mach-O | 17/17 |
| Nested graphics / dual RAMDisk / Darwin services | 10/10, 11/11, 74/74 |
| Native ASan/UBSan argument contract / failure transport | 14/14 + 14/14 |
| Discovery / observer / source profile / large RAM bounds | 20/20, 22/22, 7/7, 6/6 |
| Explicitly labelled verifier replay and rejection cases | 5/5 |

All five fresh regression commands exited 0. The existing negative cases cover null/dead handles, malformed pointer/count pairs, unsupported selectors, short buffers, null surface capabilities, foreign compositor ownership, invalid dirty rectangles, replay/stale epochs and cleanup after process termination. These are tests of the existing interfaces; no claim of testing an unimplemented accelerator's ownership/security is made.

## Fresh original-services attempt and host limitation

A separate fresh original BackBoard/SpringBoard run was started with the same pinned kernel, binaries and fixture. It reached the original services but terminated with SIGBUS / exit135; C was subsequently measured at 0.89 GiB free and WSL instance creation temporarily failed. Its trace is truncated during the IOSurface diagnostic. **It is not counted as a fresh 22/24/26 pass.** The partial trace, command, layout and logs are retained in `trial-1-host-storage-failure` and `host-storage-failure.json`.

A current-run duplicate rebuild payload was removed after recording its size and SHA-256. Nine additional current-run payload copies were archived to reproducible-payload-copies.zip, independently decompressed/hash-verified, and only then removed from their original temporary locations. Their paths, lengths and SHA-256 values are recorded in archived-payload-copies.json. Failed-run disposable virtual RAM files were removed after their logs were saved. Source files, known-good kernels, old accepted runs and native/recovery candidates were preserved. A filesystem trim was attempted; it did not establish enough host space for unrestricted testing. No explicit WSL shutdown/restart command or phone operation was performed.

A second attempt reused the verified input root without another 3 GiB copy. When host free space again fell below 768 MiB, the confirmed current-run QEMU/debugger/runner were stopped before another storage fault. Its partial trace and cancellation record are in retry-storage-cancelled. It is also incomplete, and is not counted as a fresh 22/24/26 pass. No further large VM was attempted without sufficient host capacity. After the scoped archive/cleanup, Windows reported about 2.16 GiB free; large VM testing still needs more headroom.

## Frame acceptance still required

Original SpringBoard task → genuine qualified device/plugin → owned surface and command → executed pixels → same surface ID/transaction accepted by BackBoard → SwapSetLayer/SwapEnd/present → byte-matched framebuffer dump. Empty swaps, a nonzero matching handle, diagnostic frames or custom GUI frames do not meet this chain.

Evidence directory: `C:/Users/Mehmedamir/Documents/Codex/2026-10-23/referenced-chatgpt-conversation-this-is-an/outputs/duchamp-ioacceleratores-abi-20261120`. See [fresh regression commands](C:/Users/Mehmedamir/Documents/Codex/2026-10-23/referenced-chatgpt-conversation-this-is-an/outputs/duchamp-ioacceleratores-abi-20261120/regression-commands.json), [targeted tests](C:/Users/Mehmedamir/Documents/Codex/2026-10-23/referenced-chatgpt-conversation-this-is-an/outputs/duchamp-ioacceleratores-abi-20261120/targeted-commands.json), [ABI findings](C:/Users/Mehmedamir/Documents/Codex/2026-10-23/referenced-chatgpt-conversation-this-is-an/work/ios-sweet-duchamp/docs/DUCHAMP_IOACCELERATORES_ABI.md) and [implementation boundary](C:/Users/Mehmedamir/Documents/Codex/2026-10-23/referenced-chatgpt-conversation-this-is-an/work/ios-sweet-duchamp/docs/DUCHAMP_SOFTWARE_GRAPHICS_PROVIDER.md).

Physical status stays **BLOCKED_BY_MEMORY_EVIDENCE**. No physical flashing, reboot, slot change, UFS access, firmware change, commit or push occurred.
