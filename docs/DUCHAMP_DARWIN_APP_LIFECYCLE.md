# Darwin application lifecycle in QEMU

2026-11-18. `duchamp-bootstrap`, HEAD `d91562d9c2bd3bc33d52550c101de1009bb41dc0` plus preserved uncommitted work. Physical readiness remains **BLOCKED_BY_MEMORY_EVIDENCE**. This stage performs no phone operations and no commit or push.

## Architecture and actual execution

The existing compositor and window manager remain separate native Darwin processes. This stage adds an application-management process and two fixed application executable paths. All are ARM64 Mach-O programs loaded through the existing Darwin runtime and managed by the original launchd as PID 1.

```text
shell toolbar -> audited AP Mach service -> application manager
                   -> launchctl kickstart -> launchd -> app-red / app-blue
                   -> audited GW lifecycle request -> window manager
                       -> app's registered inbox -> graceful exit / test abort
app exit -> Mach dead-name notification -> window/surface cleanup -> focus restoration
```

The red and blue programs use the same original test-program implementation, installed at distinct paths and executed as distinct guest processes. They are not two painted surfaces masquerading as application processes. Per-PID guest logs and launchd exit receipts establish their execution. This is a fixed two-application test catalog, not LaunchServices or SpringBoard compatibility.

## Source map

| Files | Responsibility |
| --- | --- |
| `tools/duchamp-app-wire.h` | AP request/reply ABI, fixed catalog IDs and application states |
| `tools/duchamp-app-service.inc` | Native application manager, asynchronous launch, lifecycle validation |
| `tools/duchamp-darwin-gui.c` | Existing WM/shell/client integration, audited senders, private inbox events |
| `tools/duchamp-gui-wire.h` | Extended GW operations and separate identity reply, preserving the old result ABI |
| `tools/duchamp-window-core.[ch]` | Visibility, focus restoration, ownership, per-contact capture and geometry |
| `tools/duchamp-app-observer.inc` | Native lifecycle observer, actual launchd exit receipts and stale-owner tests |
| `tools/duchamp-gui-control.h` | Explicit application test mode and normal interactive mode |
| `tools/test-duchamp-readonly-var.py` | Installation of executable copies, launchd jobs and RAM-root integration |
| `tools/duchamp_app_touch_oracle.py` | Independent expected framebuffer bytes for twelve lifecycle states |
| `tools/test-duchamp-darwin-gui.py` | Source-built XNU test orchestration and native/pixel verification |
| `tools/verify-duchamp-app-session.py` | Native postflight of a normal session without the lifecycle observer |
| `tools/test-duchamp-app-touch-browser.py` | Automated browser interaction through the actual virtual input device |

## Identity and process boundaries

The application manager accepts only kernel-audited shell or diagnostic-observer callers. The window manager recognizes the application manager separately from ordinary application clients. Each lifecycle action is bound to the current PID **and PID version**; PID reuse alone cannot authorize an operation. Application identities are exposed through a separate `GW_INFO` reply so the existing compositor/window reply layout stays intact.

The WM registers a send right to each application's inbox and requests a kernel dead-name notification. Applications accept lifecycle events only from the audited WM and touch events only through their registered delivery channel. A close request exits the target process normally. The explicit test crash calls `abort()` in that process. The service never accepts an arbitrary PID, executable path or shell command from a client.

Old process handles are rejected after restart. When a process exits, its windows and compositor layers are removed and captured contacts are detached. A later release of an old contact is not retargeted to the replacement process. Foreground/background retains the same live process identity; background hides the window and cancels its captures, and focus returns to the highest visible eligible window.

These are prototype root-service boundaries based on the existing audited Mach facilities and fixed executable paths. They do not implement a general multi-user application sandbox, entitlements policy or production application installer. The current control mechanism supports cooperating applications; it is not a force-kill service for a completely unresponsive application.

## Asynchronous launch and truthful readiness

`AP_QUERY`, `AP_LAUNCH`, `AP_FOREGROUND`, `AP_BACKGROUND`, `AP_TERMINATE`, `AP_CRASH` and `AP_RESTART` operate only on IDs 2 and 3. States are STOPPED, BACKGROUND, FOREGROUND, PENDING, FAILED and STOPPING.

Launching forks a bounded, tracked `launchctl` utility. The manager periodically reaps it and checks the actual WM-owned PID/version. It reports PENDING while launchd schedules the job and emits READY only after that process creates its window. Restart waits for the old owner to disappear before queuing a replacement. Duplicate pending launch requests coalesce. Input handling acknowledges the request without waiting for launchd's throttling interval; diagnostic callers may explicitly wait for readiness.

This fixes an observed bug: the earlier synchronous helper killed a utility after four seconds and could report failure even though launchd subsequently created the application. Pixel checks alone missed that discrepancy. Native postflight now requires distinct process identities, asynchronous queued/READY receipts, no failed launch reply and no input reconnection caused by launch latency. The launchd throttling policy was not disabled. Its behavior is documented in Apple's [launchd.plist manual](https://github.com/apple-oss-distributions/launchd/blob/main/man/launchd.plist.5).

## Interactive shell

Normal `--applications` mode starts eight jobs, with no synthetic lifecycle observer. The 160×96 test canvas has primitive, original toolbar buttons:

| Horizontal interval | Action |
| --- | --- |
| 12–38 | Launch/foreground red |
| 48–74 | Launch/foreground blue |
| 86–104 | Background focused application |
| 108–126 | Close focused application |
| 130–150 | Restart focused application, or launch it if stopped |

Title strips move windows, lower-right corners resize them, and independent contacts capture independent targets. The shell preserves the existing VirtIO mouse mode. See `DUCHAMP_QEMU_MULTITOUCH.md` for the new device path and its cancellation limits.

## Build and execution evidence

All outputs are outside the source tree under `../../outputs/duchamp-app-multitouch-20261118/`. Exact commands, exit codes and log SHA-256 values are retained in the command receipts and final manifest. The kernel is freshly source-linked, not a modified prebuilt binary:

- `kernel-2/kernel.development.sweet`: 19,543,912 bytes.
- SHA-256: `97adb3971c14e1c8f1fd42b18623b183d32edf9d882dc99a2c216b5dc229d001`.
- `kernel-2/build-manifest.json`: 1,127 verified source link inputs, including the compiled input driver and source registration hook.
- Kernel compiler: isolated patched Clang 24; native/userspace compiler and linker: LLVM 21.1.8; installed QEMU: 10.2.1.
- md0: 32 MiB HFS+, read-only. md1: 4 MiB writable HFS+ at `/private/var`; `/var` resolves there. Both are QEMU RAM images.

The native app suite boots that exact kernel and requires actual guest process logs, launchd exit receipts, twelve complete byte-exact framebuffer comparisons, two simultaneous device-origin contacts, focus restoration, cleanup and fresh PID/version identities. Graceful blue termination reports exit code 0. Deliberate red failure reports `Abort trap: 6`. The replacement red receives two fresh events, and receives no old contact release.

Final accepted queue-backpressure runs:

| Evidence | Result |
| --- | --- |
| `attempt-7/verification.json` | **35/35**, twelve full observed framebuffer comparisons |
| `attempt-7/host-input/verification.json` | **14/14**, actual VirtIO device path and twelve expected states |
| `browser-5/verification.json` | **18/18**, twelve browser framebuffer crops, normal interactive session |
| `browser-5/native-postflight/verification.json` | **15/15**, real guest lifecycle, input and filesystem evidence |

The normal guest red app is PID 32/version 76. Blue app instances are PID 34/version 81, PID 37/version 88 and PID 40/version 95. All have PPID 1; these are recorded guest identities, not promised identifiers for future runs. The normal session has no lifecycle observer or synthetic WM input. Root remains byte-identical, writable var changes, root writes return EROFS, and the var capacity test returns ENOSPC. `attempt-5` and `browser-3` retain the preceding successful asynchronous-launch results. Unsuccessful intermediate receipts remain preserved rather than being relabelled.

Existing suites on the exact new kernel: GUI **22/22**, VirtIO mouse **18/18**, browser mouse **16/16**, compositor **25/25**, graphics **10/10**, filesystems **11/11**, services **74/74**, and real dynamic/static Mach-O **17/17**. Native ASan/UBSan assertions: application/touch ownership **42**, touch parser **71**, existing window manager **53**, pointer parser **33**. Individual suites overlap; these counts should not be summed into a claim of independent tests.

## Reproduce

From the WSL repository directory, with the preserved local toolchain/runtime dependencies:

```sh
OUT=../../outputs/duchamp-app-multitouch-20261118
python3 -B tools/build-duchamp-qemu-pointer-kernel.py "$OUT/kernel-rebuild" \
  --baseline-build ../../outputs/duchamp-patched-clang-20261117
python3 -B tools/test-duchamp-darwin-gui.py "$OUT/new-app-test" \
  --kernel "$OUT/kernel-2/kernel.development.sweet" \
  --kernel-manifest "$OUT/kernel-2/build-manifest.json" \
  --mkfs ../../outputs/duchamp-readonly-var-20261116/formatter/unpacked/usr/sbin/mkfs.hfsplus \
  --app-touch
python3 -B tools/run-duchamp-live-input.py --help
python3 -B tools/run-duchamp-live-input.py "$OUT/manual-session" \
  --artifacts "$OUT/attempt-7" --applications \
  --kernel-manifest "$OUT/kernel-2/build-manifest.json" \
  --mkfs ../../outputs/duchamp-readonly-var-20261116/formatter/unpacked/usr/sbin/mkfs.hfsplus \
  --seconds 3600
```

Use a new output directory for each run. The normal launcher accepts `--applications`, the accepted test artifacts and the kernel build manifest; it prints a localhost viewer URL with a session token. Its complete invocation is retained in the normal browser command receipt. The runner requires the locally available matching runtime files; this stage does not redistribute them or establish their license.

## Remaining work

The test catalog has two applications and a single window per application; arbitrary installation, richer application metadata and multi-window applications are future work. Services are root-only prototypes and do not replace Apple graphical services. The retained QEMU RAM queue uses coherent virtual memory, not a verified MT6897 DMA route. No touchscreen, Mali, native firmware ownership or physical memory evidence was established. Android/recovery files and the native candidate remain unchanged.
