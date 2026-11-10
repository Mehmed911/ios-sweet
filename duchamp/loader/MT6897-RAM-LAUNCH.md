# MT6897 RAM-only launch provider status

## Result

There is no documented LK or UEFI entry provider that can launch the Duchamp
image from RAM under a no-partition-write rule. The provider gate
therefore remains closed.

This is a measured limitation, not a claim that the loader or XNU payload is
invalid.  The existing `mt6897_lk_transport` safely consumes an immutable
capsule that is already in RAM, but something else must first transfer control
to that code.  It is a transport consumer, not a phone entry mechanism.

## Later approved boot-partition diagnostic

On 2026-11-06 the user authorized an isolated `boot_a` diagnostic followed by
exact stock restoration, then explicitly requested a repeat to read the
numbers. The repeat photo measured runtime Android Image `_head=0x40000000`
and inherited `x0=0x47c80000`. Android and the original live `boot_a` hash were
verified after restoration. See
[PHONE-PC-X0-FLASH-TRIAL.md](../PHONE-PC-X0-FLASH-TRIAL.md).

That approved route can deploy controlled diagnostics through a boot-partition
write. It supplies the two missing numeric entry observations for that route.
It does not provide a no-write RAM launch command or prove capsule placement,
cache ownership, or physical UFS readiness.

## Exact LK command audit

`tools/audit-duchamp-lk-ram-launch.py` accepts only the saved 16 MiB `lk_a`
sample with SHA-256:

```text
f85373d3b4cdf3c959e38bbbfe198a2857e03a5266c6f2a40c319549a5ba957a
```

The audit decodes AArch64 branches to LK's command-registration function at
`0xffff00005070705c`.  It recovers all 14 direct registration call sites and
the 22-entry OEM table traversed by one of those calls.  The resulting 35
registered Fastboot commands include:

- `download:`, `flash:`, `erase:` and the ultra-flash commands;
- reboot, continue, slot selection and power-off commands;
- 22 OEM diagnostic, lock-state, dump and policy commands.

The binary contains one standalone `boot` string at partition offset
`0xa7633`, but no recovered registry entry binds `boot`, `run`, `execute`,
`jump`, `go`, `start` or `chainload` to a handler.  A string in the image is
not a command registration.  Downloading bytes therefore does not establish a
documented way to execute them.

Run the offline audit with a new output path:

```sh
python3 tools/audit-duchamp-lk-ram-launch.py \
  --lk ../phone-firmware/lk_a.bin \
  --output work/lk-ram-launch-audit-v1/report.json
```

Use `--require-provider` as a fail-closed build gate.  It exits nonzero for the
current LK because no eligible RAM launch provider was proved.

## Active phone verification

On 2026-11-09 a read-only ADB check confirmed that Android had booted on
Duchamp/MT6897, slot `_a`. The active `lk_a` SHA-256 matched the sample above.
The running kernel configuration had both
`CONFIG_KEXEC` and `CONFIG_KEXEC_FILE` disabled.

The binary audit also followed the registered `continue` callback. It sends
`OKAY`, sets the Fastboot return state and signals LK's Linux boot event.
The waiter on that same event calls `boot_linux_from_storage`. `download:`
has a separate callback. The audited path therefore resumes storage boot.
[AOSP Fastboot protocol](https://android.googlesource.com/platform/system/core/+/refs/heads/main/fastboot/README.md)

The MediaTek V6 route documented in MTKClient invokes `boot_to` after an
accepted download agent stage one, as part of loading stage two. An
authenticated Duchamp entry that hands control to the diagnostic with a
verified PC, FDT and CPU state remains unproven.
[MTKClient V6 implementation](https://github.com/bkerler/mtkclient/blob/118a000a83ea31c4f427fe5225abfe964546e05e/mtkclient/Library/DA/xmlflash/xml_lib.py)

The existing entry diagnostic was rebuilt and passed the AArch64 QEMU
record and framebuffer checks. The guest reported PC `0x40200000`,
`x0=0x48000000` and EL1, and the test verified the SCTLR MMU and cache bits
required by the diagnostic. No phone boot or partition modification was
performed for this check.

## MediaTek V6 candidate check

On 2026-11-10 the published `DA_DUCHAMP_OS1.0.12.0.bin` candidate
reported hardware code `0x1203`, subcode `0x8a00` and hardware version
`0xca00`. Its SHA-256 is
`b37df080ce20e073b295717bf379e0ae58ff44bfe8f0e9a52b641b087ba33969`.
Those fields identify the candidate's target family. Admission on the
connected Duchamp firmware remains unverified.
[Pinned candidate](https://github.com/k4lp/mt6897-unlock-attempt/blob/152fabe7eab3e370cf4c16e039ae6c462e914b1f/security/DAA/working/candidates/DA_DUCHAMP_OS1.0.12.0.bin)

The candidate's `BOOT-TO` handler computes a 32-byte digest and compares it
against the SHA-256 of the bundled DA2 body, excluding its signature tail.
The comparison takes the error branch on a mismatch. The PC/x0 diagnostic
has a different digest.

The isolated QEMU test ran the 52 comparison bytes from the exact DA1.
It matched the bundled DA2 and took the mismatch branch for the diagnostic
and for DA2 with one byte changed. The first harness run hit an alignment
exception and the aligned replay passed all three checks. The test used
host-computed digests and covered the comparison branch only. The complete
USB command, device admission and firmware handoff remain untested. The
RAM-only launch gate stays closed. The QEMU result and reproduction script
are under `work/ram-provider-sources-20261109-v1`.

## Why the other paths do not qualify

| Path | What is established | Why it is not the Duchamp RAM provider |
| --- | --- | --- |
| Stock MT6897 LK Linux handoff | The exact LK has an internal SMC `0xc2000115` handoff to a runtime kernel and FDT target. | It is internal control flow, not a documented callback ABI that remains callable after handoff. |
| HakiOS Qualcomm UEFI/U-Boot | Qualcomm ABL uses `fastboot boot`, then U-Boot/UEFI loads the XNU loader. | Duchamp LK does not register `fastboot boot`; Qualcomm USB/UEFI drivers and Adreno assumptions are not portable to MT6897/Mali. |
| HakiOS MT6768 | A bare-metal loader is prepended to the Android kernel and chain-booted from `boot_a`. | It requires a boot-slot image; it is not a no-write RAM entry path. |
| Existing Duchamp LK capsule transport | Strict, bounded, immutable RAM source validated in QEMU. | It begins only after the loader is already executing. |
| Android kexec | No usable installed-kernel entry was established. | It cannot supply the missing caller. |

The `oem uefilog` command recovered from the OEM table is a log command.  Its
name does not prove that a UEFI boot-services environment or a callable UEFI
image loader is installed.

## Diagnostic channel review, 2026-11-11

The opt-in `--diagnostic-channels` audit now follows the registered
`oem uefilog` handler in the exact saved LK. The handler gets a retained
buffer and its header, computes a length from the header, copies the buffer,
and sends it through the existing response routine. Its own log label reads
`pllk  log`. The checked file offsets are the handler at `0x9234`, buffer
getters at `0x141ac` and `0x141b8`, copy at `0x92b8`, and label at
`0xb1a1f`. This static evidence identifies the sender's source. Availability
on a running phone, an XNU handoff snapshot and a resource grant remain
unverified. The audit executes no OEM command.

The MediaTek kernel reference at the pinned `a805f95d61dbf0b2959c9262acc626893114321d`
revision implements two log consumers. `/proc/pl_lk` returns the saved PL/LK
buffer. The ATF logger consumes an existing ring and advances its shared
read index. The raw ATF view maintains a separate reader offset. The ordinary
ATF file's open routine calls `nonseekable_open` and performs no SMC. Time
synchronization occurs during driver probe and resume, while its write
routine has a separate debug SMC. These source-level observations have not
been matched to the running logger's binary. Reading those views does not
ask the firmware to sample UFS at a new execution boundary.
[ATF log consumer](https://github.com/mt6897-devs/android_kernel_device_modules_6.1/blob/a805f95d61dbf0b2959c9262acc626893114321d/drivers/misc/mediatek/atf/atf_log.c)
[PL/LK log consumer](https://github.com/mt6897-devs/android_kernel_device_modules_6.1/blob/a805f95d61dbf0b2959c9262acc626893114321d/drivers/misc/mediatek/log_store/log_store.c)

Upstream TF-A documents a DebugFS service selected through build options,
with shared-buffer setup and an SMC conduit. Its presence and exported
files on Duchamp have not been established. MediaTek's public UART boot-log
instructions describe Genio evaluation boards. A verified Duchamp UART
connection and firmware trace containing the required UFS fields remain
missing. [TF-A v2.8 DebugFS](https://trustedfirmware-a.readthedocs.io/en/v2.8/components/debugfs-design.html)
[MediaTek Genio communication guide](https://genio.mediatek.com/doc/android/sw/android/get-started/communication.html)

The reviewed Xiaomi kernel branch and module tree provide Android source,
while a matching LK/BL31 diagnostic contract remains unverified. The first
recursive kernel inventory was truncated. A separate complete
`drivers`-subtree query closed the inventory gap for the logger filenames.
The source receipts and 25 local audit/ownership test results are under
`outputs/duchamp-diagnostic-channels-20261111`. The hardware acquisition
requirements remain in [MT6897-LK-HANDOFF-CONTRACT.md](../MT6897-LK-HANDOFF-CONTRACT.md#ufs-evidence-at-the-bl31-exit-boundary).

Reproduce the extended static audit with a new output path.

```sh
python3 tools/audit-duchamp-lk-ram-launch.py \
  --lk ../phone-firmware/lk_a.bin --diagnostic-channels \
  --require-provider --output work/lk-diagnostic-channels-NEW.json
```

For the saved LK, the report is written and the provider requirement exits
with status 1. This preserves the existing launch gate.

The comparison above was made against these saved source snapshots:

- HakiOS kernel/docs commit `2631f5d7d4f9d7322aca60991b34ba465dec343b`,
  especially `docs/u-boot.md` and `docs/uefi-boot.md`;
- HakiOS UEFI commit `687fa6c6a5a70f43184de92980e0a76eea5f2c4b`;
- HakiOS MT6768 commit `4f27037146bd147ad15d36329e307a937603cc13`,
  especially `tools/chainboot.py` and `mtkloader/build_flashed.py`.

Those revisions are reference evidence only.  None supplies an MT6897 LK or
UEFI callback contract that satisfies the conditions below.

The current UniXNU core and two real MediaTek ports were also inspected.  The
generic BootShim/UEFI/DarwinBoot chain still requires the stock bootloader to
enter BootShim.  Ruby/MT6877 flashes `boot_a`, while Merlinx/MT6768 flashes its
p33/boot partition because its bootloader also rejects `fastboot boot`.
Neither is a no-write provider for Duchamp.  The pinned source comparison,
device-address matrix and offline audit are recorded in
[UNIXNU-MEDIATEK-REUSE.md](../UNIXNU-MEDIATEK-REUSE.md).

## Conditions for opening the gate

A future provider is eligible only when all of these are backed by a saved,
reproducible artifact or vendor source:

1. A RAM-only caller transfers control to a stated entry address without
   writing a partition.
2. The caller's `x0`/FDT value, exception level, MMU and cache state are
   measured at the entry point.
3. The capsule address, size, lifetime and ownership are fixed and cannot
   overlap LK, FDT, framebuffer, reserved memory, loader scratch or XNU output.
4. Cache maintenance and barriers are documented for that ownership transfer.
5. Failure and recovery return to a known bootloader or normal Android boot.

Until then, no phone build may turn the QEMU-only LK transport into a jump,
call LK USB functions by offset, invoke the internal SMC out of context, or
substitute a Qualcomm UEFI implementation.  The safe next source of evidence
is vendor LK source or a vendor-supported RAM execution command—not a guessed
address.
