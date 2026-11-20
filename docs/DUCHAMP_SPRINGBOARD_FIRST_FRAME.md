# Authentic SpringBoard first-frame trace — 20F66 / QEMU

Date: 2026-11-19. Render result: **BLOCKED_BY_GRAPHICS_DEPENDENCY**.

The original BackBoard and SpringBoard reach their main entry points and pass the native-job stability/RPC checks. An authentic SpringBoard frame has **not** been verified. The first positively observed rendering failure is BackBoard's original QuartzCore path requesting a Metal device and receiving nil. This is not asserted to be the only remaining startup dependency.

Physical status remains **BLOCKED_BY_MEMORY_EVIDENCE**. No ADB/Fastboot, phone reboot, slot change, flash, physical UFS, firmware change, commit or push occurred.

## Execution identity and preservation

The exact source-built kernel is `97adb3971c14e1c8f1fd42b18623b183d32edf9d882dc99a2c216b5dc229d001`. Its receipt SHA-256 is `db250b3319dd4fc84edd930b12b4123bc7549a8111c22c7d1995dd54d2f42e54`; all 1,127 source-link object hashes were checked. No new kernel or original userspace instruction was patched during tracing.

Source baseline is `d91562d9c2bd3bc33d52550c101de1009bb41dc0`, branch `duchamp-bootstrap`, plus preserved uncommitted changes. The pre-task tracked diff, status, NOTES and runner copies are archived in `C:/Users/Mehmedamir/Documents/Codex/2026-10-23/referenced-chatgpt-conversation-this-is-an/outputs/duchamp-springboard-first-frame-20261119/baseline/`. The 25 frozen native-candidate, DTB, memory-validation and Android-recovery file hashes remain unchanged; see `C:/Users/Mehmedamir/Documents/Codex/2026-10-23/referenced-chatgpt-conversation-this-is-an/outputs/duchamp-springboard-first-frame-20261119/frozen-files.json`.

| Original executable | Local SHA-256 | Actual identity in accepted trace |
|---|---|---|
| backboardd | `686f26a6a7b749fd0ae30acca704022da8cb6f85b5c39a0e0e09e25ffd00d273` | PID 25, task-unique birth 90; UUID `E81FD7FD-034F-3195-A4F5-3C692536E5AA` |
| SpringBoard | `7926a1ba0b115cf45102b2c3d8e4eb7bc9c84bcf70b573d2a798690d9148059c` | PID 34, task-unique birth 119; UUID `40EC75F0-76C1-3DEB-85F1-39369B09E9D5` |

Both original mobile jobs run as UID/GID 501 under original launchd PID 1. Kernel-derived thread/task/process data, executable UUIDs and the actual shared-cache UUID/slide bind these observations in a controlled VM. This is not cryptographic firmware attestation. An initial hardware breakpoint can precede page fetch: unreadable text is explicitly marked `instruction_bytes_resident=false`; the tracer never forces a page fault, changes PC or fabricates an opcode read.

## Accepted run and first unresolved boundary

`C:/Users/Mehmedamir/Documents/Codex/2026-10-23/referenced-chatgpt-conversation-this-is-an/outputs/duchamp-springboard-first-frame-20261119/trial-4/` records the accepted passive trace: 162 events, 334.518 host seconds, controller status 0, no trace error, no observed kernel panic. The guest health checks and all 294 installed fixture-file hashes passed: **22/22**.

1. The original BackBoard display service gives two real BKS replies with `kr=0`, 1125×2436, scale 1; the native LaunchServices rebuild/query finds the original SpringBoard bundle.
2. BackBoard enters 3 actual `CA::Context::commit_transaction` calls. **Zero** SpringBoard context commits are observed before the controller's completion marker. SpringBoard main entry and process stability are separate verified milestones, not proof of completed application initialization.
3. The direct return from `MTLCreateSystemDefaultDevice` is captured 40 times, always `x0=0`. The matching original cache bytes and decoded stubs establish the actual call chain; see the companion render-path report. The observer logs at most 40 samples per user site/process; total breakpoint visits remain in `trace_stopped.counters`. Unlogged visits are not claimed to have all returned nil.
4. IOSurface selector 13 (limits) returns 0. There is no observed successful user surface creation, no original source-buffer snapshot, and no verified producer dimensions/format/backing interval to correlate with SpringBoard.
5. BackBoard submits Swap ID 1. The four surface IDs are `[0,0,0,0]`; layer mask is `0x80000007`; both rectangle arrays are zero. SwapEnd's method return is 0. A successful empty operation is not a rendered frame.
6. The corrected observer can record validated kernel timer/work-loop callbacks separately from userspace producer identity. Actual out-of-line presentation completions observed in this run: 0. The SwapEnd acknowledgement must not be recast as a presentation completion. A kernel callback is not assigned to SpringBoard.
7. No nonzero SpringBoard surface → presentation → raw-pixel chain exists. The final raw framebuffer and PNG are retained as **diagnostic console output**, never labelled a SpringBoard screenshot.

The final console also reports unresolved launchd lookups including `com.apple.mobilegestalt.xpc`, `com.apple.iconservices`, `com.apple.pluginkit.pkd`, `com.apple.searchd`, and additional services. Their individual criticality and synchronous wait behavior are not established. This task does not claim that supplying a Metal device alone would finish SpringBoard startup.

## Milestones kept separate

| Milestone | Result |
|---|---|
| Original SpringBoard remains running | Verified within six five-second health samples |
| BackBoard display RPC responds | Verified, two native replies |
| SpringBoard submits original CA transaction | Not observed |
| Original content-bearing surface produced | Not observed |
| BackBoard accepts display operation | Empty swap acknowledged; content acceptance not established |
| Existing compositor receives original SpringBoard pixels | Not established |
| Framebuffer change represents an original frame | Not established; captured image is console output |
| Pixels correlate to SpringBoard identity/surface/sequence | Not established |

## Captured bytes and traces

Framebuffer raw length: **13,538,304 bytes**, 1220×2712, stride 4992, QEMU guest PA `0xfcc2f000`.

- Raw SHA-256: `c77db9d4f048dd7f7578d517affbd7a31e31233ebe768ecdabfbeb42c8599809`.
- Diagnostic PNG SHA-256: `60c2db81e24a6752e947b0af7eac02c51962bab5a6f9780495229cd15be33e0e`.
- Authentic frame screenshot: **none**.

The machine-readable evidence is in `C:/Users/Mehmedamir/Documents/Codex/2026-10-23/referenced-chatgpt-conversation-this-is-an/outputs/duchamp-springboard-first-frame-20261119/pipeline-result.json` and `C:/Users/Mehmedamir/Documents/Codex/2026-10-23/referenced-chatgpt-conversation-this-is-an/outputs/duchamp-springboard-first-frame-20261119/framebuffer-output.json`.

Other retained artifacts:

- `springboard-startup.jsonl`: original executable/cache/main binding.
- `backboard-display.jsonl`: BackBoard/IOKit and presentation observations.
- `surface-creation.jsonl`: intentionally empty when no create is observed.
- `surface-queries.jsonl`: successful limits query recorded separately.
- `frame-submissions.jsonl`: CA calls, layer submissions, SwapEnd and presentation/completion records.
- `metal-context.jsonl`: direct default-device return and wrapper-return samples, with process/thread identity.
- `trial-4/render-events.jsonl`, `debugger.log`, `command.json`, `layout.json`, copied observer/config, guest logs, all 294 installed-file comparisons, and extraction command/exit receipts.
- `trace/trace-config-v4.json`: all kernel/user opcode pins, 10 actual DWARF layouts, original binary UUIDs and cache bindings.
- `regression-commands.json`, `targeted-commands.json`, `host-tool-versions.json`, `final-manifest.json`: exact commands, exit codes, tool versions and output hashes.

The complete 3 GiB final RAM root and sparse 10 GiB guest RAM remain on the native Linux filesystem in `/var/tmp/duchamp-first-frame-uig1ipa9`. Small evidence files are copied to Windows; no Apple binaries were uploaded or redistributed.

## Changes made

Added the fixed passive observer, DWARF/config preparation, conservative frame-proof prerequisites and their negative tests. Added one explicitly receipted passive mode to the large-RAM QEMU runner; the source-kernel prohibition on historical debugger/code patches remains. Added three source-profile denial cases. Original graphical binaries, kernel drivers, UFS gates and native boot layout are unchanged.

A callback with no BSD process was initially skipped by the process-identity filter. The final observer retains validated kernel-thread identity for those callbacks and records empty presentation completion without inventing a producer. This fixes an observation gap, not a renderer.

No safe minimal graphics implementation was justified from the nil-device observation alone. Returning fake success, making up a Metal device, forcing software-renderer PC/registers, or displaying the custom shell would not implement the missing interface. The old nonpassive QuartzCore debugger script was not run.

## Test results

All listed commands exited 0. Counts are separate suites and are not summed across repeated nested runs.

| Suite | Result |
|---|---|
| Passive observer, DWARF/provenance/pixel-prerequisite negative tests | 22/22 |
| Source-kernel / passive-profile rejection tests | 7/7 |
| Large-RAM layout separation/bounds | 6/6 |
| Original launchd/providers/BackBoard/SpringBoard trace fixture | 22/22; 294/294 installed hashes |
| Application lifecycle / two-contact input | 35/35 plus 14 host-input checks |
| Custom compositor | 25/25 plus 10 graphics checks |
| Custom window manager / shell | 22/22 |
| Actual virtual mouse | 18/18 plus 10 host-input checks |
| Read-only md0 + writable md1 filesystem integration | 11/11 |
| Existing Darwin launchd/services | 74/74 |
| Real dyld/dynamic and static Mach-O execution | 17/17 |
| Frozen native/recovery file preservation | 25/25 unchanged |

The source-built kernel is used in every QEMU regression. Native/custom graphics/input regression success is not evidence of original Apple graphical API completeness or physical hardware compatibility.

## Failed or limited diagnostic attempts

- Trial 1: controller completed, but observer rejected an executable header that was not mapped yet. Not an accepted rendering trace.
- Trial 2: header deferral worked, but reading the original main instruction before page fetch still stopped the observer. Not an accepted trace. Original process survival was not relabelled first-frame success.
- Trial 3: complete original service/partial rendering trace, empty Swap 1. It exposed the missing kernel-thread callback observation; retained as historical evidence.
- Trial 4: corrected observer and direct Metal return site; accepted current trace.
- The optional `ipsw dyld disass` markup path failed with a Go allocation error while parsing Objective-C metadata. A bounded cache-byte read and LLVM disassembly replaced that host diagnostic; the error was not counted as guest OOM or a rendering failure.

## Next justified implementation

Investigate an actual reusable renderer/provider contract or a verified original CPU-renderer configuration for this 20F66 QuartzCore path. Verify required operations and pixel ownership before implementation. Independently trace SpringBoard's remaining initialization/service waits until its first CA commit is observed. Then require a nonzero surface and a matching presentation sequence/raw-byte comparison. Do not weaken first-frame evidence to accept an empty swap or a custom image.
