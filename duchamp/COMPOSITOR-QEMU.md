# Duchamp QEMU compositor and framebuffer

The unchanged iOS 16.5 test root reached the service-readiness stop marker
with native SpringBoard running. In that run, `backboardd` submitted a single
empty swap while the display was on and then requested power off. A separate
synthetic client drove a valid layer through the same kernel to the framebuffer.
The native compositor still needs to produce a nonempty frame.

## Tested presentation path

`AppleCLCD::start` takes the framebuffer from `PE_current_console` and
creates a physical IOSurface. Selector 5 queues the swap, and
`AppleCLCD::vsyncFired` drains it when the display is on and the flush
interval elapses. `present` copies enabled, nonzero IOSurface layers to the
physical framebuffer. The display timer continued to tick in the native
run. The final QMP dump matched the shared RAM bytes at `0xfcc2f000`.

The local 20F66 cache's `_kern_SwapEnd` passes selector 5 and a 0x46c-byte
record starting at connection offset 0x18. `_kern_SwapSetLayer` stores
surface IDs starting at connection offset 0x6c and edits the mask at
0x11c. Subtracting 0x18 gives the kernel offsets 0x54 and 0x104.
The zero IDs were therefore observed at the offsets written by this
userland build. `_kern_RequestPowerChange` sends selector 12 with one
scalar. The trace reads the actual scalar and identifies its caller from
the current kernel thread and BSD process.

The QEMU ADT's display node describes 1125×2436, which matches the
BackBoard MIG reply in the readiness test. The AppleCLCD instance reports
1220×2712 with a 4992-byte stride, matching the injected QEMU framebuffer.
The synthetic copy used this actual geometry. The effect of the difference
on the native compositor has yet to be isolated.

## Runtime evidence

The private records are under `work/compositor-qemu-20261107`.
`verification.json` passed all six observation checks and has SHA-256
`30d16a4391704a782e89183f0ef0893d132082514fd3d4a4bebd2e824cb0a725`.
The native V3 run used the unchanged V6 root
`8029fb33aa7805e773e10848f05af0f85349a1e1c9fe1e3dcea35890f3f9c171`.
Hardware breakpoints captured the following calls from `backboardd` PID 25.

| Call | Vsync count | Observed arguments |
| --- | ---: | --- |
| Power | 6791 | Value 1 |
| SwapEnd | 8438 | ID 1, mask `0x80000007`, four zero surface IDs, zero rectangles, display on |
| Power | 8438 | Value 0 |

V3 reached `PLATFORM SERVICES DONE status=0` in 192.520 host seconds without
an observed panic. The saved driver state showed one swap, zero eligible
layer logs, power off and a dirty pending record. The retained V6 baseline
matched the same state and record. A separate run with only
`sweethidtest=7` added reached the same readiness marker in 191.264 seconds
and still ended with the same single empty swap. The test sampled the
final display state and did not prove end-to-end receipt of the Home event.

The first debugger attempt could not read a signed register as an
address. V2 fixed the conversion and captured power-on and the empty
swap. V2 continued past readiness because its stop text was incorrect,
then observed an interrupt processing timeout in QEMU. V3 used the
actual readiness marker and captured the following power-off request.

The isolated test used the previously verified 128 MiB IOSurface root
as a fixture, copied it, and replaced its test job with a new diagnostic
client. The client used the original IOSurface and IOKit libraries to
submit surface ID 2 as a 64×32 BGRA layer. It set display power to on and
the test used `sweetfb_noconsole=1` to prevent console writes over the
frame. All 2048 pixels at (521, 1801) matched the expected bytes. The
stopped driver recorded one eligible layer and cleared its dirty flag.
The test took 75.246 host seconds. The fixture stayed unchanged and
the VM used a separate writable RAM copy of the prepared input image.

## Reproduce

Run the synthetic test under WSL with
`python3 tools/test-duchamp-compositor-frame.py --output work/compositor-frame-new`.
It uses the pinned kernel, QEMU ADT, HFS helper and local IOSurface V3 fixture.
The read-only RAM analyzer accepts a stopped native run directory as its
sole argument. The debugger script can be passed to `qemu-service-ram.py`
with the unchanged V6 root, `--seconds 215` and
`--stop-on-text 'PLATFORM SERVICES DONE status=0'`.

Follow the native path from QuartzCore's
`CA::WindowServer::Display::render_display` to
`IOMobileFramebufferSwapSetLayer`. Capture whether the call receives a
non-null surface, its ID, and the next SwapEnd record. The next graphical
gate is a nonzero native layer with corresponding pixels in stopped
QEMU scanout. Phone hardware, Mali and physical UFS were outside these
tests.

The native call trace and startup experiments continue in
[QUARTZCORE-QEMU.md](QUARTZCORE-QEMU.md).
