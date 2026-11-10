# UniXNU MediaTek reuse assessment

## Result

UniXNU supplies a useful board-neutral loader architecture, but none of the
reviewed MediaTek ports supplies the missing no-write RAM entry for Duchamp.
The current phone-entry gate therefore remains closed.

This conclusion comes from the actual source snapshots, not only the device
catalog:

- UniXNU core `e2fdae4312d0acc3d8a52bc457101e7918095e6a`;
- DarwinBoot `3c75734014cdab0acd9541e88057b7606ee7ae08`;
- Ruby/MT6877 `f92f29031e971f257196e19562243411302ea87c`;
- Merlinx/MT6768 `c6b28c4ffda1ed62ef75c2580980d6387d7eb67c`.

The review and tests are offline. No phone, fastboot command, boot image, MMIO,
UFS command or partition was accessed.

## Boot-entry finding

The generic UniXNU sequence is:

```text
Android bootloader -> BootShim -> board UEFI -> UniXNU -> DarwinBoot -> XNU
```

This is reusable only after the Android bootloader has entered BootShim. The
official guide requires a bootloader that accepts `fastboot boot`. The exact
Duchamp LK audit found no registered `boot`, `run`, `execute`, `jump`, `go`,
`start` or `chainload` command.

The two inspected MediaTek examples do not close that gap:

| Port | Entry actually used | Compatibility with the no-write rule |
| --- | --- | --- |
| Ruby, MT6877 | Stock LK reads a full Android v2 image from `boot_a` and enters the raw shim at `0x40080000`; the project states that every experiment is flashed to `boot_a`. | Not eligible. |
| Merlinx, MT6768 | Mu-Silicium UEFI and UniXNU are packaged for the p33/boot partition because its bootloader rejects `fastboot boot`. | Not eligible. |

UEFI does not itself create an entry mechanism. A Duchamp UEFI port would
still need LK to start its BootShim from RAM, or it would require a partition
write that is outside the current policy.

## Reuse matrix

| Component | Decision | Reason |
| --- | --- | --- |
| UniXNU loader protocol | Reuse after a real UEFI entry exists | The request interface for kernel path, boot arguments, DT and ramdisk is board-neutral. It does not call LK or create the missing caller. |
| DarwinBoot Mach-O, ADT and trust-cache validation | Adapt/reference | The bounded validation and placement design is useful. Current DarwinBoot uses a Darwin 23 `boot_args` layout of `0x480` bytes with a 1024-byte command line; this project targets XNU 8796 and uses 736 bytes with a 608-byte command line. It is not a drop-in loader. |
| DarwinBoot final EL1 handoff | Adapt/reference | It cleans the owned window, invalidates instructions, disables MMU/data/instruction caches and branches at EL1. The order is useful evidence, but its ownership comes from UEFI allocation and cannot be assumed for LK RAM. |
| Ruby early shim | Concepts only | Saving `x0`, measuring `CurrentEL`, installing vectors and parsing the inherited FDT are portable ideas. Its watchdog, memory and framebuffer constants are MT6877-specific. |
| Ruby GIC/timer | Algorithms only | Both devices declare 13 MHz, but Ruby uses GICD `0x0c000000` and GICR `0x0c040000`; Duchamp's captured FDT uses `0x0c400000` and `0x0c440000`. |
| Ruby framebuffer | Software drawing only | Ruby's visible LK layer is `0x7cdfc000` and its early shim used `0x7ba10000`. Duchamp uses `0xfcc2f000`, stride 4992, 1220 by 2712. |
| Ruby UFS probe and XNU patch | Do not reuse on the phone | It targets UFSHCI `0x11270000`, assumes LK left the MT6877 host and PHY running, uses pointers directly as DMA addresses and has no explicit data-cache/IOMMU ownership contract. Duchamp UFS is `0x112b0000` and remains fail closed. |
| Ruby/Merlinx image packers | Reference only | They preserve device-specific Android image layouts but produce images intended for a boot partition. They are not a RAM launcher. |

No Qualcomm, Adreno, MT6877 or MT6768 register constant is imported into the
MT6897 backend.

## Static verification

`tools/audit-unixnu-mediatek-reuse.py` verifies the exact revisions and source
markers above, extracts the compared addresses and emits a machine-readable
report. It deliberately fails if an upstream change invalidates a conclusion.

```powershell
python tools/audit-unixnu-mediatek-reuse.py `
  --ruby ../references/unixnu-ruby `
  --unixnu ../references/unixnu-core `
  --merlinx ../references/unixnu-merlinx `
  --output work/unixnu-mediatek-audit-v1.json
```

`--require-ram-provider` is the build gate. It exits nonzero for these sources,
because no eligible provider exists.

The unit tests use synthetic source fixtures and check the fail-closed cases:

```powershell
python tools/test-audit-unixnu-mediatek-reuse.py
```

## Safe staged integration

1. Keep the current Duchamp LK capsule transport and phone jump disabled.
2. Use the UniXNU loader protocol and DarwinBoot validators as QEMU/host design
   references; preserve the XNU 8796 `boot_args` ABI already proved by this
   project.
3. Accept a phone entry provider only when a saved vendor artifact or source
   proves a no-write RAM caller, entry address, `x0`, EL, MMU/cache state,
   ownership lifetime, cache handoff and recovery path.
4. Keep the MT6897 physical UFS backend disabled until its independent
   firmware, firewall, DMA, cache and resource-ownership gates pass. Ruby's
   inherited-host shortcut is not evidence for Duchamp.

The closest immediately testable milestone remains a QEMU-only loader
validation. UniXNU does not change the current requirement for an MT6897/LK
RAM entry provider before another no-write phone trial.

## Updated UniXNU and HakiOS review, 2026-11-11

The UniXNU guide still enters BootShim through a device that accepts
`fastboot boot`. The current device catalog, at
`3fd6a3cf0e6f2eba5d3de3a4d1912e2db23a0fc4`, identifies the Lenovo TB375FC as
its MT6897 entry. A fresh audit of the saved Duchamp LK still rejects
`--require-provider`. No reviewed port documents a compatible no-write
Duchamp entry. [UniXNU boot guide](https://unixnu.com/guide/boot)
[Pinned catalog](https://github.com/UniXNU/UniXNU/blob/3fd6a3cf0e6f2eba5d3de3a4d1912e2db23a0fc4/devices.toml)

| Port | Boot and diagnostic evidence |
| --- | --- |
| Lenovo TB375FC, MT6897 | The port documents UEFI handoff on its own hardware and restoration of `boot_a` and `misc`. Its persistent diagnostic recorder uses UFS writes to reserved mrdump slots. [Lenovo diagnostics](https://github.com/billyham07/UniXNU-tb375fc/blob/cc4da0eabe4a27825253e6332f33ca4760ebb359/package/Tb375fcDiag.md) |
| Dandelion, MT6765 | The port flashes its boot image and records persistent diagnostic output through an eMMC writer. [Dandelion handoff](https://github.com/licg89/UniXNU-dandelion/blob/b74625d907696e2e340006998b20f1fd28db68bf/HANDOFF.md) |
| Merlinx, MT6768 | The port writes the boot partition. Its USB log client requires a running XNU MUSB endpoint. The saved Duchamp FDT declares MTU3. [Merlinx boot notes](https://github.com/Dracen-W/UniXNU-merlinx/blob/b0563d97b47c674741112bfb3db439fe4fc63883/docs/devices/merlinx.md) |
| Dali, MT6991 | The port describes ramoops with a fresh test token and a restore step for `boot_b`. The complete unattended cycle is still under qualification. [Dali reset qualification](https://github.com/localhosts-A/UniXNU-Dali/blob/1a9738d2ee37dbe1b73f1b2ff3134426a89d82f9/docs/unattended-cycle.md) |
| HakiOS X6826B, MT6768 | The loader enters through `boot_a` and uses ramoops to pass early console text to Android. [HakiOS boot path](https://github.com/oosexgang/hakios-mt6768/blob/ad65e1f4b3ba479e9d7ada98f17398b83cc6f285/README.md) |

**Ramoops is a candidate diagnostic output for Duchamp after entry.** The
saved Duchamp FDT reserves `0x48090000 + 0xe0000` as `mediatek,pstore`. An
earlier Android panic produced `console-ramoops-0`. After the local test, a
read-only ADB query confirmed the live ramoops parameters: console
`0x40000`, pmsg `0x10000`, ftrace and record `0x1000` each, ECC zero, and
memory type zero. The pinned GKI zone order gives a calculated console
start of `0x4811f000`. [Earlier phone result](diagnostics/dma-iommu-probe/PHONE-TEST-2026-11-01.md)
[GKI ramoops layout](https://github.com/aosp-mirror/kernel_common/blob/cf2c2dc91b9e9f016dc25cf095b1fe34cb5dfcb6/fs/pstore/ram.c)

The QEMU test compiled only the upstream HakiOS console-ring writer with
the modeled console address. ARM64 guest code wrote a short record and a
wrapped ring into private QEMU RAM. Both matched byte for byte after a
paused QMP system reset and an independent host decoder recovered the
expected payload using the GKI header and ring order. The test verified
adjacent bytes and rejected an oversized header. It did not boot Android
or verify physical retention of a record written by XNU. No code or
diagnostic record was installed on the phone. [HakiOS writer](https://github.com/oosexgang/hakios-mt6768/blob/ad65e1f4b3ba479e9d7ada98f17398b83cc6f285/mtkloader/mtkdbg.h)
[GKI ring reader](https://github.com/aosp-mirror/kernel_common/blob/cf2c2dc91b9e9f016dc25cf095b1fe34cb5dfcb6/fs/pstore/ram_core.c)

The replay script, pinned source receipts, results and Android parameter
receipt are in `outputs/duchamp-mediatek-upstream-20261111`. Use a fresh
output directory when repeating the replay. Any later integration still
requires a supported Duchamp entry and an owned console range. Ramoops can
carry a record from the receiving loader; the UFS state and resource grant
must still come from firmware at the handoff boundary.
