# MT6897 RAM-only launch provider status

## Result

There is no documented LK or UEFI entry provider that can launch the Duchamp
image from RAM under the current no-partition-write rule.  The provider gate
therefore remains closed.

This is a measured limitation, not a claim that the loader or XNU payload is
invalid.  The existing `mt6897_lk_transport` safely consumes an immutable
capsule that is already in RAM, but something else must first transfer control
to that code.  It is a transport consumer, not a phone entry mechanism.

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

The comparison above was made against these saved source snapshots:

- HakiOS kernel/docs commit `2631f5d7d4f9d7322aca60991b34ba465dec343b`,
  especially `docs/u-boot.md` and `docs/uefi-boot.md`;
- HakiOS UEFI commit `687fa6c6a5a70f43184de92980e0a76eea5f2c4b`;
- HakiOS MT6768 commit `4f27037146bd147ad15d36329e307a937603cc13`,
  especially `tools/chainboot.py` and `mtkloader/build_flashed.py`.

Those revisions are reference evidence only.  None supplies an MT6897 LK or
UEFI callback contract that satisfies the conditions below.

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
