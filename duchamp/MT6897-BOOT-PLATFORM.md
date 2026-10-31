# MT6897 bootstrap platform integration — 2026-10-31

This milestone connects a bounded GIC redistributor scan/wake implementation
to the existing DUCHAMP XNU boot path and generates separate saved-hardware
and QEMU ADTs. It also fixes the boot CPU driver's Qualcomm-only matching.
No phone, USB, ADB, fastboot, physical UFS or partition operation is involved.
The generated phone ADT is an offline description, not a deployable boot image.

## Captured hardware and source basis

The input FDT is the saved 485760-byte capture with SHA-256
`9c49589f70044127be8941a9ea5537977f440ccd5ac15cfd24e120c8a1181d29`.
The profile builder verifies this pin before parsing. Device dumps and generated
ADTs remain outside Git. It cross-checks `board.toml` rather than guessing
missing clock or interrupt properties.

| Selected captured fact | Offline treatment |
| --- | --- |
| GICD `0x0c400000`, size `0x40000`; GICR `0x0c440000`, size `0x200000` | Preserve for the phone profile; use QEMU's different resources for the emulator profile. |
| GIC `#interrupt-cells=4` | Parse four complete timer specifiers, including the partition cell. Reject unsupported flags/partitions. |
| Architected timer `13000000` Hz; interrupt IDs 29, 30, 27, 26 | Select virtual timer INTID 27. Runtime `CNTFRQ_EL0` and delivery on the phone are unverified. |
| CPU `reg` values `0x000` through `0x700`, four Cortex-A510 then four Cortex-A715 | Use `reg`, not the misleading node names. Emit the boot CPU only. |
| PSCI method `smc` | Record the declaration; do not call firmware or infer a working CPU_ON contract. |
| Framebuffer base `0xfcc2f000`, reserved size `0x033d0000` | Cross-check packed and split FDT tags, then bound the framebuffer extent. |

The framebuffer geometry, 1220 by 2712 pixels, stride 4992 and depth 32, comes
from the existing board record combining the saved FDT and Android display
state. The profile does not claim that the FDT alone supplies this geometry.
Nor does a framebuffer description establish Mali acceleration or display
controller initialization.

The public GIC/timer references are pinned at the captured Android kernel's
release-stamp revision
[`cf2c2dc91b9e9f016dc25cf095b1fe34cb5dfcb6`](https://github.com/aosp-mirror/kernel_common/tree/cf2c2dc91b9e9f016dc25cf095b1fe34cb5dfcb6).
`tools/duchamp_boot_profile.py` records exact Git blob IDs for:

- [irq-gic-v3.c](https://github.com/aosp-mirror/kernel_common/blob/cf2c2dc91b9e9f016dc25cf095b1fe34cb5dfcb6/drivers/irqchip/irq-gic-v3.c), particularly `gic_iterate_rdists()` and `__gic_populate_rdist()`;
- [arm-gic-v3.h](https://github.com/aosp-mirror/kernel_common/blob/cf2c2dc91b9e9f016dc25cf095b1fe34cb5dfcb6/include/linux/irqchip/arm-gic-v3.h);
- [GICv3 DT binding](https://github.com/aosp-mirror/kernel_common/blob/cf2c2dc91b9e9f016dc25cf095b1fe34cb5dfcb6/Documentation/devicetree/bindings/interrupt-controller/arm,gic-v3.yaml);
- [architected timer DT binding](https://github.com/aosp-mirror/kernel_common/blob/cf2c2dc91b9e9f016dc25cf095b1fe34cb5dfcb6/Documentation/devicetree/bindings/timer/arm,arch_timer.yaml).

The stamp correlation does not establish reproducible source/binary identity;
see [SAVED-UFS-CONTRACT.md](SAVED-UFS-CONTRACT.md).

## Executed XNU changes

`drivers/duchamp_gic_boot.h` implements normal C algorithms with explicit I/O
callbacks. `tools/stage-duchamp-gic-boot.py` installs them in the already-patched
XNU tree during the mandatory final dxb pass. Only the DUCHAMP branch changes;
other platform bodies are retained. A receipt pins all staged file hashes and
rejects partial, modified or conflicting repeat staging.

The scan validates resource extents and overlap, checks GICR_PIDR2 for GICv3/4,
then compares all MPIDR affinity levels against GICR_TYPER. It respects Last
and the 128/256 KiB frame size indicated by VLPIS, with a finite frame limit.
PIDR2 prevents an all-zero wrong region from masquerading as CPU0. These
checks cannot make inaccessible MMIO safe or establish secure ownership.

Wake performs at most one ProcessorSleep clear, preserves unrelated WAKER
bits, orders the write, and requires ProcessorSleep and ChildrenAsleep clear.
Both a nanosecond deadline and a finite read budget apply; a frozen timer or
ignored write cannot produce an infinite polling loop. Callbacks themselves
must return. Failure enters the existing kernel panic path rather than
resetting shared hardware. This patch changes no Distributor/ICC ownership
policy and adds no secure-monitor call.

`iokit/KernelConfigTables.cpp` previously matched SweetCPU only to
`qcom,kryo470`. The DUCHAMP personality now also accepts `arm,cortex-a510`,
`arm,cortex-a715` and QEMU's `arm,cortex-a76`. Its displayed name becomes
`ARM64 bootstrap CPU`. This is the existing architected IOCPU/GIC path;
it is not a port of Qualcomm power registers. The generated profiles select
one CPU. Existing QEMU SMP/PSCI code remains present, but MT6897 secondary
startup, suspend and power management are not established by this change.

The same final staging pass guards legacy informational clock ratios in
`pe_identify_machine.c`. Omitting an unknown bus clock previously divided by
zero. DUCHAMP now reports unavailable ratios with a zero numerator and a
nonzero denominator, while preserving known-clock calculations. No CPU,
bus or DDR clock is fabricated, and this does not calibrate the architected
counter. The non-DUCHAMP calculation remains unchanged.

## Separate target descriptions

| Output | Phone profile | QEMU profile |
| --- | --- | --- |
| GICD base/size | `0x0c400000 / 0x40000` | `0x08000000 / 0x10000` |
| GICR base/size | `0x0c440000 / 0x200000` | `0x080a0000 / 0x100000` |
| Counter frequency | 13 MHz, saved declaration | 62.5 MHz, emulator profile |
| Boot CPU compatible | `arm,cortex-a510` | `arm,cortex-a76` |
| Selected CPUs | 1 | 1 |

Unknown core/bus/DDR clock properties are omitted for both targets. The fixed/peripheral
frequency aliases in this legacy software ABI refer to its counter timebase;
they do not assert that every hardware peripheral bus runs at 13 MHz.
Both profiles describe the Duchamp-sized framebuffer instead of the old
template's 1080 by 2400 framebuffer at `0x9c000000`. The display canvas stays
1220 by 2712; the separate `sweet-fbcon` text viewport has height 2680
(83 full text rows). This reserves the bottom 32 pixels painted by
`sweet_early_mark()`, matching the existing early console's reservation.
Without that reservation the last normal-console row overlapped the diagnostic
band and produced two undecodable glyphs. The full mapped framebuffer extent
and boot/display geometry remain unchanged.

The source template is pinned to SHA-256
`be512dce04bf581d188440246b4e3402de057a43f4c178da7984a68ccbb9ba2f`.
The builder removes Qualcomm compatible strings and inherited storage nodes.
It retains `D22AP`, `iPhone10,3`, `xiaomi,sweet` and `AppleARM` as explicit
software identities needed by the existing platform/userland scaffold.
Those names are not claims about the physical device. The memory window
comes from `board.toml`; a generated profile is not a runtime reservation or
proof that the window remains available. Existing loader checks still apply.
Every manifest leaves phone authorization, physical providers and secondary
startup disabled/unverified.

## Reproduce offline

From the repository in WSL, choose new output directories:

```sh
python3 tools/fetch-duchamp-boot-sources.py research/boot-source-new
python3 tools/build-duchamp-boot-profile.py research/boot-profile-new \
  --fdt ../phone-fdt.bin --template work/qemu-multiproc.adt \
  --sources research/boot-source-new --target qemu
python3 tools/test-duchamp-boot-profile.py \
  --fdt ../phone-fdt.bin --template work/qemu-multiproc.adt \
  --sources research/boot-source-new
python3 tools/test-duchamp-gic-boot.py research/boot-gic-check-new
```

Use `--target phone` only to produce the separate offline description. The
builder does not create an Android boot image or execute a payload.
Full guest tests run on Linux-native storage through the Windows native-workspace
launchers; see [FAST-SYSTEM-BOOT.md](FAST-SYSTEM-BOOT.md).

## Actual evidence

- `research/mt6897-boot/check-v2/result.json`: PASS, 128 native ASan/UBSan
  checks, the same 128 ARM64 model checks, plus four actual virtual GICR
  discovery/wake checks. ELF SHA-256
  `d83344e72f0180ccc7c9d05e77dce7318171149d275dc4a2e8572e4ccd71f06e`.
- Eleven staging guard tests and 18 saved-FDT/profile tests pass.
- `clock-consumer-v1` executes the actual transformed PE function with mocked
  DT properties under ASan/UBSan. The original missing-bus case reproduces
  division by zero; the fixed unknown/zero cases and retained legacy known
  clock case pass. This is a consumer test, not hardware clock measurement.
- The staged `pe_fiq.c` and `pe_identify_machine.c` compile against real
  generated XNU headers (`compile-v3`). Local
  C++ compilation is blocked by Linux clang lacking Apple's XNU type builtins;
  `compile-v2` is a preserved failure, not a full build pass.
- Intermediate [CI 41152464883](https://github.com/Mehmed911/ios-sweet/actions/runs/41152464883)
  succeeded at `bb15237`. It predates PIDR2 and ARM CPU matching changes.
- `guest-profile-baseline-v1` failed with the new ADT and old `f6dfc1e` kernel:
  no root/PID1 success markers appeared within 180 seconds. The old CPU
  personality's incompatible match was identified from the actual source.
  This failure remains recorded; no QEMU pass is claimed for that run.
- Source `654a3c9` / CI 41153721164 was cancelled after being superseded by
  the clock fix. It is not a build pass.
- Final kernel source `ff841ef` succeeded in
  [CI 41154098870](https://github.com/Mehmed911/ios-sweet/actions/runs/41154098870).
  Artifact 13024424002 archive SHA-256 is
  `d527cafd07e02fcebefcfdb0306cdce7f936fc4a4f432cc1e611e57064375c85`;
  kernel SHA-256 is
  `a26248fa69047a6c2110f7998022d0625e8c617dd900050f098d39ed49a79232`.
  The archive digest and its internal `SHA256SUMS` both match.
- `system-final-v1` passes all 72 original Apple-service checks, six wrapper
  checks and 113 installed hashes in 86.640 host seconds, default QEMU clock.
  It uses the unchanged legacy ADT and original Apple-service RAM fixture.
- `guest-profile-final-v1` reached root/PID1 and all required read/backend
  markers in 33.430 seconds, but the report **failed** because two bottom-row
  glyphs overlapped the diagnostic band. The failed report is retained.
  `guest-profile-final-v2` with the corrected viewport passes **24/24**
  strict checks in **33.539 host seconds**, default QEMU clock, 15 sampled
  frames and zero undecodable glyphs. XNU mounts HFS+, starts diagnostic
  PID1 and passes read/write-refusal/error/backend/table checks. The backend
  receipt explicitly remains `fw_verified=0 physical=0`.
- `final-verification.json` confirms result/source/profile pins, all five saved
  phone-input hashes and preserved user changes. No QEMU process remains.

The final ADTs are `phone-profile-v4` and `qemu-profile-v4` under the ignored
evidence directory. Their SHA-256 values are respectively
`efa8ca6254a0534ebe79c0c9a38b12d07b9a468a7bf32ed30c348511553e6101` and
`5ddf0057a50d97be8fc2a08ad88e443ab3460290f6fc532f5f4dbc063562eebe`.
The QEMU UFS fixture ADT is verified as `qemu_ufs.build_tree()` applied to
that exact QEMU boot profile. No physical phone profile was executed.

To replay the strict read-only guest from Windows, with the saved kernel and
fixture already present:

```powershell
./tools/test-duchamp-ufs-native.ps1 `
  -Kernel research/mt6897-boot/kernel-final/kernel.development.sweet `
  -KernelSha256 a26248fa69047a6c2110f7998022d0625e8c617dd900050f098d39ed49a79232 `
  -Fixture research/mt6897-boot/ufs-profile-v4 `
  -Head ff841ef7728a717262c00cee96fc163e12aedf8e -Run 41154098870 `
  -Output research/ufs-guest-new -Backends
```

The next physical prerequisites remain firmware/resource ownership, runtime
timer/interrupt delivery and scheduler verification, then an authorized DMA/UFS
provider. Storage and Mali are separate uncompleted work. QEMU RAM-root and
Apple-service tests do not prove full iOS or phone boot readiness.
