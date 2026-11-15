# Duchamp diagnostic bootshim

This is a position-independent AArch64 Linux Image payload for local build and
inspection. It records the LK entry registers, accepts only EL1 with MMU and
caches disabled, validates the inherited FDT header in low RAM, draws a narrow
diagnostic marker on the verified Duchamp framebuffer, and stops in `WFE`.

Marker value `0x0000ff00` means the entry gate and FDT header passed. Marker
value `0x00ff0000` means the execution state was safe for physical framebuffer
access but the FDT check failed. The displayed colors depend on the inherited
pixel format. EL2 or an MMU/cache-on entry stops without touching the
framebuffer.

The image has no XNU branch, storage access, PSCI call, GIC setup, watchdog
change, boot-image wrapper, or flashing command. A successful host build is not
evidence that LK will enter it with the expected register contract.

`pack_boot.py` can wrap the diagnostic Image using the non-payload metadata from
the captured stock `boot_a`. It accepts only Android boot header v4 with an
empty ramdisk and empty boot signature, replaces only the kernel size and
payload, and omits the now-invalid stock AVB footer. The resulting small,
unsigned image is intended only for offline inspection and a later explicitly
approved `fastboot boot` capability test. It must not be flashed.

For offline diagnosis of bootloaders that require a structurally complete AVB
partition, `--preserve-avb-container` keeps the captured 64 MiB partition size,
signed vbmeta block, and AVB footer while replacing and zero-padding only the
pre-vbmeta payload region. The original hash descriptor will intentionally fail
for the changed payload. This option proves only that the image remains
parseable; it does not make the diagnostic Xiaomi-signed or authorize flashing.

The captured Duchamp stock `boot_a` kernel payload is an LZ4 legacy frame, not
a raw ARM64 Image. `--lz4-legacy` compresses the validated ARM64 input with that
same framing before updating `kernel_size`. Always decompress the resulting
payload and compare it byte-for-byte with the input during offline validation.

Run `./test.sh` on a Linux host to exercise the complete C entry gate and
marker writer against fixed, mapped stand-ins for the measured FDT and
framebuffer addresses. The test verifies that EL2 and MMU-on entry do not touch
the framebuffer, invalid FDTs draw the failure marker, a valid FDT draws the
success marker, and row padding remains untouched.

Before drawing, the shim also fills `duchamp_bootshim_diagnostic` in RAM with a
versioned magic value, the entry-gate result, marker decision, FDT header
values, the preserved entry registers, and a checksum. This record is intended
for debugger or emulator inspection only; it is not persisted across reset and
does not write to phone storage.

The 12-band marker is also a visual report. Bands 0-7 represent overall
status, EL1, MMU off, data cache off, instruction cache off, FDT range/alignment,
FDT magic, and FDT size respectively. Pass rows use `0xff00ff00`; failure rows
use `0xffff0000`. Bands 8-11 alternate `0xff00ffff` and `0xffff00ff` as a build
signature, making the structured-marker build distinguishable from the older
single-color diagnostic. Each band is 226 physical scanlines, filling the full
2712-line display so the result cannot be mistaken for the retained boot logo.
Pixel appearance still depends on the inherited framebuffer format.
The high alpha byte is deliberately `0xff`; the first wide-band hardware test
used zero alpha and successfully replaced the retained logo with black, proving
the framebuffer address while hiding the intended RGB colors.

EL2 is now an observable diagnostic case rather than an immediate black stop.
The assembly reads `SCTLR_EL2` and installs `VBAR_EL2`; when EL2 translation
and caches are off, the C gate draws a failure report with the EL row red. If
EL2 translation or caches are active, it still stops without touching the
physical framebuffer. The shim does not execute `eret` or attempt an EL2-to-EL1
transition.

For phone builds, the shim also stops the documented MediaTek watchdog only
after confirming EL1/EL2 with translation and caches off. The live DT identifies
TOPRGU at `0x1c00a000` with the `mediatek,mt6589-wdt` fallback binding; the
implementation follows Linux's `mtk_wdt_stop`: read mode offset 0, clear enable
bit 0, OR key `0x22000000`, write, barrier, and read back. The before/after mode
values are included in the RAM diagnostic record. Host/QEMU builds can define
`DUCHAMP_TEST_NO_WATCHDOG=1` because QEMU virt does not map this phone MMIO.

`test_qemu.py` boots the actual freestanding ARM64 `Image` on QEMU's virt
machine, captures the measured Duchamp framebuffer address through QMP, and
checks every diagnostic row plus the first stride-padding word. This complements
the native host harness by exercising the assembly entry and linked image.

## Dual-boot menu in QEMU

Build and exercise the menu from the repository root with fresh output paths:

```sh
out=$(realpath -m work/duchamp-menu)
BOOT_MENU=1 QEMU_ONLY=1 SHIM_OUT="$out/preview" sh duchamp/bootshim/build.sh
python3 duchamp/bootshim/test_boot_menu_qemu.py "$out/preview/Image" "$out/test"
```

The emulated PL011 maps W and S to the two volume keys and Enter to the power
key. Android (A) is initially selected and wins the 10-second timeout even
when XNU (B) has been highlighted. The harness verifies the framebuffer focus
and saves PNG captures. B ends at the shim in the preview build.

To test XNU dispatch, build with the existing QEMU SWEETXNU payload:

```sh
PAYLOAD=/path/to/payload-qemu.bin MATERIALIZE=1 READY=1 JUMP=1 \
  BOOT_MENU=1 QEMU_ONLY=1 SHIM_OUT="$out/with-xnu" sh duchamp/bootshim/build.sh
python3 duchamp/bootshim/test_boot_menu_qemu.py "$out/preview/Image" "$out/dispatch" \
  --with-xnu "$out/with-xnu/Image" --xnu-dtb /path/to/phone-fdt.bin
```

This configuration lets a confirmed B enter the existing guarded XNU loader
path. A confirmation or menu timeout requests the next slot from a simulated
firmware provider on the emulated UART. A fresh A readback is required before
issuing the QEMU PSCI reset. A wrong slot or missing readback leaves an error
on screen and halts at the shim. The harness observes the QMP guest-reset
event after a simulated A readback.

For a one-shot XNU request via ramoops, build the QEMU preview with
`BOOT_ONCE=1` and give the test the saved Duchamp DTB:

```sh
out=$(realpath -m work/duchamp-boot-once)
BOOT_ONCE=1 BOOT_MENU=1 QEMU_ONLY=1 SHIM_OUT="$out/build" sh duchamp/bootshim/build.sh
python3 duchamp/bootshim/test_boot_once_qemu.py "$out/build/Image" /path/to/phone-fdt.bin "$out/test"
```

The test models the Android writer and the slot selector. The ARM64 bootshim
reads the pmsg ring after a QEMU guest reset, consumes complete requests in
its valid data, and requests a return to A. The test compares the ring and
adjacent bytes across resets. XNU dispatch in this preview is simulated.

For a real XNU entry in the same test, build a second image with BOOT_ONCE=1,
QEMU_ONLY=1, BOOT_MENU=1, PAYLOAD set to the existing SWEETXNU payload, and
MATERIALIZE=1 READY=1 JUMP=1. Pass its Image as `--with-xnu` to the runner
above. The test verifies one kernel entry after simulated A readback, then
uses a host reset to prove that entering B again cannot replay the request.
Wrong or missing readback halts before the handoff. The QEMU request fixture
is at 0x47000000, clear of the linked image and separate from retained pmsg.

To rehearse a recovery request from Slot B in QEMU, provide the uncompressed
stock Duchamp ARM64 Linux Image and the uncompressed OrangeFox recovery cpio:

```sh
out=$(realpath -m work/duchamp-recovery-chain)
RECOVERY_CHAIN=1 BOOT_MENU=1 QEMU_ONLY=1 SHIM_OUT="$out/build" sh duchamp/bootshim/build.sh
python3 duchamp/bootshim/test_recovery_chain_qemu.py "$out/build/Image" \
  /path/to/stock.Image /path/to/orangefox-only.initramfs "$out/test"
```

The host models the firmware's slot selection and recovery request. On B the
shim jumps to the stock kernel with a QEMU virt DTB and the recovery ramdisk.
A separate PID 1 probe verifies the Linux reboot and Slot A kernel entry after
simulated A readback. The packaged OrangeFox process runs in a separate guest
without phone storage or a display backend for its UI.

The build and entry guards restrict the profile to QEMU virt. Android on
Duchamp advertises volume up through mtk-kpd, and volume down and power
through mtk-pmic-keys. The archived LK log records keypad initialization
and a PMIC volume-down press during boot.

The input decoder consumes the active-low volume-up bit from the saved keypad
mapping and decoded PMIC levels for volume down and power. It waits for all
keys to be released before accepting a single fresh press, and ignores
held-at-entry buttons, repeated samples, invalid PMIC samples and chords.
The QEMU-only preview can also read a keypad/PMIC fixture from guest RAM as
soon as the menu starts, before drawing the framebuffer or reading UART:

```sh
BOOT_MENU=1 QEMU_ONLY=1 BOOT_MENU_ENTRY_KEYS=1 SHIM_OUT="$out/entry" \
  sh duchamp/bootshim/build.sh
python3 duchamp/bootshim/test_boot_menu_qemu.py "$out/preview/Image" "$out/entry-test" \
  --entry-keys-image "$out/entry/Image"
```

The suite starts separate guests with a neutral sample, each of the three
buttons held, an incomplete sample, an invalid PMIC value and no sample.
After a held or unavailable sample, it verifies that the menu requires a
release before fresh presses can move B → A and confirm A. This exercises
the keypad decoder and menu logic with injected input.

### Android selection on Duchamp

The verified recovery path uses stock LK Fastboot to select A before Android
boots. Android exposes its Boot Control HAL once Android is running. Both
are defined by [AOSP's slot selection contract](https://source.android.com/docs/core/architecture/bootloader/updating#support-for-slots).
The reviewed stock LK Linux handoff exposes no documented next-slot operation
that the shim can call.

On Qualcomm redwood, the [HakiOS menu](https://hackios-web.vercel.app/en/docs/u-boot#installed-beside-android-a-menu-at-every-start)
marks its own slot unbootable and reboots so ABL chooses the Android slot.
This depends on redwood's ABL and updates boot metadata. Upstream
[U-Boot A/B selection](https://docs.u-boot.org/en/latest/android/ab.html)
also requires a board port with storage and boot-control metadata support.
For Duchamp, a phone provider still needs documented early keypad and PMIC
access and a verified LK-compatible next-slot operation. The QEMU provider
uses emulated input and a simulated readback.

### Volume-up press and release before XNU

`PHONE_CAPTURE=1 KPD_PROBE=1` adds an isolated keypad diagnostic to the
PC/x0 capture. It uses the saved Duchamp FDT and
[Xiaomi keypad driver](https://github.com/MiCode/MTK_kernel_device_modules/blob/bsp-duchamp-u-oss/drivers/input/keyboard/mtk-kpd.c)
for the register layout. The archived LK log records `KP_EN=1`. This shows
LK initialized the block before Fastboot. The first Slot B trial measured
`KP_EN=1` and `KP_MEM1=0xffff` at bootshim entry with the button released.

After the existing EL/MMU/cache check and exact phone PC/x0 match, the
diagnostic reads `KP_EN` once. With `KP_EN == 1`, it reads the initial
`KP_MEM1` state and shows D0=6 before starting a 12-second press window.
Confirming a press starts a separate five-second release window. It samples
at about 200 Hz and requires two consecutive samples to confirm each edge.
A button held at entry must be released before a new press can count.

| D0 | Meaning |
| --- | --- |
| 0 | Entry address or x0 mismatch |
| 1 | About to read KP_EN |
| 2 | KP_EN did not return 1 |
| 3 | About to read KP_MEM1 |
| 4 | Initial state released |
| 5 | Initial state pressed |
| 6 | Waiting for a new press |
| 7 | Press recorded, waiting for release |
| 8 | Press and release recorded |
| 9 | Press window ended without a new press |
| A | Release window ended without a confirmed release |
| B | Generic timer unavailable |

`D1` packs the raw KP_EN halfword above the last confirmed KP_MEM1 halfword.
The low 12 hex digits of `D2` show the initial, press and release snapshots
as three four-digit values. Use D0 to tell whether an edge was recorded.
`D3` shows the latest raw KP_MEM1 value. At either timeout the shim reads
it once more without treating that single sample as a confirmed edge.
The result remains on screen when the capture stops in the shim.
Volume down and power require a separate early
[PMIC provider](https://github.com/MiCode/MTK_kernel_device_modules/blob/bsp-duchamp-u-oss/drivers/input/keyboard/mtk-pmic-keys.c).
The current profile performs no PMIC access or keypad register writes.

Run the local test with an unused output directory:

```sh
sh duchamp/bootshim/test_kpd_probe_qemu.sh \
  work/lk-handoff-audit-v1/report.json work/kpd-probe-test
```

The suite checks the phone binary rejects QEMU's entry addresses. A separate
fixture binary uses RAM instead of keypad registers. The harness updates MEM1
while the ARM64 image is running to verify a release beyond the original
press deadline, a button held at entry, timeouts, a raw value distinct from
the last confirmed sample and the diagnostic framebuffer.

### PMIF status at bootshim entry

`PHONE_CAPTURE=1 PMIF_PROBE=1` adds a two-register snapshot to the isolated
PC/x0 image. The saved Duchamp DTB maps `pmif` at `0x1cc04000` and routes
MT6363 SID 4 through that bank. The
[MiCode PMIF driver](https://raw.githubusercontent.com/MiCode/MTK_kernel_device_modules/bsp-duchamp-u-oss/drivers/spmi/spmi-mtk-pmif-core.c)
selects the mt6xxx layout and SWINF2 on MT6897. The entry guard requires
the measured phone PC/x0 and the existing EL/MMU/cache checks.

`D1` packs the raw INIT_DONE word above the raw SWINF2 status word.
`D0` is 0 on a handoff mismatch, 1 before the INIT_DONE read, 2 when
initialization is unavailable, 3 before the SWINF2 read, 4 for an idle
channel snapshot, 5 for a non-idle state, or 6 for an all-ones status.
An idle snapshot establishes the visible state at that instant. PMIF
transactions remain subject to channel ownership and serialization.

The image issues only MMIO loads to PMIF. The existing backend's modeled
TOPSTATUS read separately checks the command and acknowledgement for one
byte from SID 4 at 0x001e. Button bit assignments still need validation
against physical samples, since the
[MiCode MT6363 key driver](https://github.com/MiCode/MTK_kernel_device_modules/blob/bsp-duchamp-u-oss/drivers/input/keyboard/mtk-pmic-keys.c)
uses separate press and release IRQs for its normal input path.

```sh
sh duchamp/bootshim/test_pmif_probe_qemu.sh \
  work/lk-handoff-audit-v1/report.json work/pmif-probe-test
```

`payload_preflight.c` is the next-stage no-copy/no-jump boundary. It runs the
existing FDT/payload guard and additionally requires the measured Duchamp XNU
window (`0x1c0000000` + `0x20000000`), a bounded entry/top, and 1-32 segments.
It reports entry, ADT, boot_args and top addresses but never writes the target
window. `test_payload_preflight` exercises it against captured artifacts before
it is linked into a phone diagnostic.

Set `PAYLOAD=/path/to/payload.bin` when running `build.sh` to embed that exact
payload and enable the phone-side preflight. This variant still performs no
segment copy and has no XNU branch. Bands 8-10 become preflight status,
10-segment count, and expected memory-window status; band 11 remains magenta as
the build signature. `verify_embedded.sh BUILD_DIR PAYLOAD` byte-compares the
embedded section with the source payload.

Set `MATERIALIZE=1` together with `PAYLOAD=...` to link the bounded segment
materializer. It repeats the complete guard before writing, copies only the
planned segment and ADT ranges into the measured `0x1c0000000` window, zeros
each segment tail and the boot-args page, and then stops. There is still no XNU
branch. The final materializer pattern uses green row 10 for success and cyan
row 11 as its distinct signature.

Set `READY=1` together with `MATERIALIZE=1` to add the final no-jump handoff
gate. It requires the hardware-observed EL1 and MMU/cache-off state, rechecks
entry and boot-args bounds/alignment, executes `dsb sy; ic iallu; dsb sy; isb`,
and stops. It does not install translation tables and does not branch. Magenta
row 11 identifies this ready-gate build. The exception vectors record kind,
ESR, ELR, FAR and SP in RAM and replace the display with red bands plus one
magenta band identifying the exception class.

Set `RETURN=1` to link the bounded XNU-to-bootshim diagnostic channel adapted
from the current HakiOS loader-return ABI. With `MATERIALIZE=1`, the bootshim
searches only the validated copied Mach-O segment ranges for exactly one aligned
`XNULDRST` slot and fills in the physical return-stub address, checkpoint and
physical-minus-virtual offset. Zero or multiple matches fail closed and prevent
a `READY`/`JUMP` handoff. The return record accepts ESR/ELR/FAR and at most
64 KiB of log data; oversized logs retain a bounded head and tail. Log addresses
outside the validated XNU window are never dereferenced. `RETURN_CHECKPOINT=N`
sets the optional checkpoint field. `TEST_XNU_RETURN=1 RETURN=1` builds the
QEMU-only visual return test; it is not a phone mode.

This reuses only the generic transport contract. It does not import HakiOS's
MT6768 eMMC, PMIC, clock, Mali or device-MMIO implementation; Duchamp is MT6897
with UFS and requires its own documented backends.

`JUMP=1` is a separate, opt-in build and requires `READY=1`. Only that build
links the final indirect branch. It masks interrupts, repeats the architectural
barriers, places the physical boot_args address in `x0`, and branches to the
validated physical entry. Builds without `JUMP=1` remain incapable of entering
XNU. A jump build must pass the 8 GiB QEMU/FDT end-to-end test before it can be
considered for a separately approved hardware trial.

## QEMU-only LK RAM transport integration

`LK_RAM_TRANSPORT=1 QEMU_ONLY=1 PAYLOAD=...` is a separate local proof mode.
It wraps the immutable SWEETXNU payload in the versioned `DUCHLKR1` capsule,
streams that capsule through the MT6897 LK provider into staging RAM, runs the
normal guard/materializer, and returns a checksummed report instead of entering
XNU. The build rejects `MATERIALIZE`, `READY`, `JUMP`, `RETURN`, and
`TEST_XNU_RETURN` combinations. It also omits the `duchamp_enter_xnu` branch
helper entirely.

This mode is deliberately linked for QEMU virt at `0x40200000`. Its first
assembly instructions require both that runtime address and QEMU's DTB address
`0x48000000` before clearing BSS or touching any other memory. A copy loaded by
the phone's LK therefore stops in `WFE`; the mode is not a phone payload.
The fixed link address is also required because the resident protocol uses C
callback tables whose function pointers must contain runtime addresses.

Run the complete proof from the repository root with four new paths: captured
FDT, SWEETXNU payload, captured stock boot image, and a non-existing output
directory:

```sh
sh duchamp/bootshim/test_lk_ram_bootshim.sh \
  ../phone-fdt.bin path/to/payload-phone.bin ../phone-boot/boot_a.img \
  work/validation-lk-ram-bootshim
```

The suite first proves the negative build gates, then runs the real freestanding
Image in 8 GiB QEMU RAM. It polls the checksummed completion report, verifies
the exact payload byte count, segment count, entry and boot-args address, and
requires a clear exception record. The layout verifier then checks the ELF,
capsule, full loader guard, QEMU image/DTB/staging/XNU ranges, and an LZ4 legacy
64 MiB Android boot-v4 wrapper. That wrapper is named
`qemu-only-layout-not-for-phone.img`; its preserved stock AVB descriptor has an
expected payload-hash mismatch and it must never be booted or flashed.

The QEMU image must end before the reserved DTB placement at `0x48000000`.
Consequently, a much larger payload (including the current roughly 151 MB
candidate) is rejected for this complete LK-layout proof even though the
streaming staging protocol itself has a larger capacity. This is a layout
limit, not evidence of phone compatibility.

## Fail-closed Duchamp phone-layout preflight

`PHONE_LAYOUT=1 PHONE_CONTRACT=...` is a separate offline build mode. It accepts
only the report produced by `tools/audit-duchamp-lk-handoff.py` for the pinned
LK, boot, vendor-boot, final-FDT and runtime-iomem captures. It is mutually
exclusive with `QEMU_ONLY`, `LK_RAM_TRANSPORT`, `PAYLOAD`, `MATERIALIZE`,
`READY`, `JUMP`, `RETURN` and `TEST_XNU_RETURN`.

The mode links at the captured vendor-boot Image contract `0x40000000`. Its
assembly guard requires that runtime `_head` and inherited FDT `x0` equal the
static/corroborated addresses, then always stops in `WFE` before BSS clearing or
any C call. It contains no payload, transport or XNU branch. The post-link
verifier requires zero relocations, no undefined symbols, an empty LK-capsule
section, an Image end below `0x47c80000`, and continued execution authorization
set to false.

This mode does not prove the runtime kernel PC or FDT register. LK computes both
targets dynamically and hands them to secure firmware through SMC
`0xc2000115`; those runtime values have not been numerically captured. See
`duchamp/MT6897-LK-HANDOFF-CONTRACT.md` for the exact evidence and command.

## Isolated runtime PC/x0 capture

`PHONE_CAPTURE=1 PHONE_CONTRACT=...` builds a separate position-independent
ARM64 Image for measuring the two missing runtime values. It is mutually
exclusive with the fixed phone-layout guard, QEMU-only transport, embedded
payload, materializer, ready gate, XNU jump and return channel. The build links
`phone_capture_entry.c` instead of the normal diagnostic `shim.c`, so the
result contains no FDT dereference, watchdog access, storage operation, payload
transport or branch to XNU.

Immediately after preserving the entry registers and clearing its own BSS, the
assembly uses `adr` to record the runtime address of `_head`. The isolated C
entry records that value and inherited `x0` in a checksummed 64-byte RAM record.
Only an EL1 or EL2 entry with translation and both caches disabled may write the
already measured framebuffer. It clears the visible surface and renders two
white hexadecimal lines on black: `PC=0X...` and `X0=0X...`. It never
dereferences `x0`, so an unexpected value is still observable rather than used
as a pointer.

Run the complete local proof with a new output directory:

```sh
sh duchamp/bootshim/test_phone_capture_qemu.sh \
  work/lk-handoff-audit-v1/report.json \
  work/phone-capture-qemu-v1
```

The suite checks negative build combinations, verifies the linked opcodes,
requires zero relocations and undefined symbols, boots the actual image in
QEMU, reads the RAM record through QMP, and checks representative glyph pixels.
QEMU's measured result is expected to be `_head=0x40200000` and
`x0=0x48000000`; that is an emulator result, not evidence of Duchamp's runtime
handoff.

This image is not a workaround for the phone's deployment boundary. The saved
Duchamp fastboot probe already established that its bootloader rejects the
standard RAM-only `fastboot boot` command as unknown, and the installed Android
kernel has no kexec support. Do not flash this capture image merely to obtain
the values. A separately documented RAM-only launch mechanism is still needed
before the physical capture can be run without changing a boot partition.
