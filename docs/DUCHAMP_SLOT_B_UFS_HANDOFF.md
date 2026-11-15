# Duchamp Slot B UFS handoff

## 1. Verified observations

- The November 15 ADB receipt identifies Duchamp/MT6897 with Android boot
  completed on Slot A. Boot identity matched before and after capture. Linux
  reported both `ufshcd-mtk` and `ufs_mtk_phy` as runtime-active. The ATF
  snapshot and bounded raw export reported BL31
  `lts-v2.8.6(release):2fbca47`; neither, the PL/LK export, nor the two pstore
  entries contained a correlated Slot B XNU handoff, read grant, or resource
  pin marker in the bytes inspected. The published export copies debug RAM.
  [MiCode ATF reader](https://github.com/MiCode/MTK_kernel_device_modules/blob/3c4ccd07d5624879555ec710c11bb8818e5cb5c6/drivers/misc/mediatek/atf/tfa_debug.c#L175-L227)
- The retained PL/LK log from the earlier Fastboot session with B selected
  reports `ufshcd_init OK`, `ufs init OK` and M-PHY initialization activity.
  It establishes that firmware reported initialization in that session.
  Its boot path reaches Fastboot and supplies no correlated XNU-entry record.
- The archived November 11 Slot B trial reached XNU services with the
  embedded 32 MiB RAM root. The image audit identifies `rd=md0` and found
  no UFS ADT node, firmware handoff property, or UFS handoff receiver in that
  image. The later XNU and Android observations have distinct provenance.
- The saved FDT (SHA-256
  `9c49589f70044127be8941a9ea5537977f440ccd5ac15cfd24e120c8a1181d29`)
  describes `/soc/ufshci@112b0000` at `0x112b0000` for `0x3000` bytes and
  a PHY at `/soc/ufsphy@112a0000` with `mphy-ver=1`. The HCI declares 12
  clocks, including UFS selection, UniPro and HCI clocks. Providers include
  clock syscons `0x112b8000` and `0x112bb000`. The node also describes the
  reset controller, `vcc`, `vccq`, `dvfsrc-vcore` and the
  `mediatek,ufs-rtff-mtcmos` policy. It contains no `power-domains` property
  at that node. The DTB declares dependencies and addresses.
  [Duchamp hardware inventory](../devices/duchamp/hardware.json)
- The exact saved LK and BL31 samples passed the offline digest and entry
  audit. LK's final platform cleanup reaches the UFS shutdown routine
  (partition offset `0x79e0c`), tries a power-off notification, and writes
  zero to HCE at `0x79e48`. That path lacks HCE readback and its caller
  does not check the notification result. The saved BL31 kernel-boot
  handler runs `sip_emi_set_nsr_permission` and
  `spm_smpu_hre_first_bk` before the final handoff. The callbacks do
  not constitute a verified grant for the UFS aperture.
  [LK handoff contract](../duchamp/MT6897-LK-HANDOFF-CONTRACT.md)

The supporting workspace receipts are under `outputs/`, in
`duchamp-slot-b-ufs-read-authority-20261115`,
`duchamp-slot-b-live-lk-log-20261111`,
`duchamp-slot-b-handoff-audit-20261111` and
`duchamp-slot-b-trial-20261111`. The new
`duchamp-slot-b-ufs-handoff-passive-20261115/lk-bl31-handoff-audit.json`
records the reproduced static audit and both binary hashes. The retained
Fastboot PL/LK export is 197,219 bytes with SHA-256
`bee2a8bd4a06b44fdb8b88b8d6957e30721ab52051da91425b72684a1c3aa18d`.

## 2. Unverified at Slot B XNU entry

| Question | Finding |
| --- | --- |
| Does firmware initialize UFS? | The retained Fastboot log reports success earlier in firmware startup. The final Slot B XNU entry state remains unsampled. |
| Does the power domain stay on? | Unproven. The Android driver explicitly controls RTFF/MTCMOS across suspend and resume. |
| Do the required bus clocks stay on? | Unproven. The driver has clock setup and ref-clock request/acknowledgment paths. The FDT clock references describe topology. |
| Does the UFS PHY remain initialized? | Unproven. The retained log records earlier M-PHY activity and the Android driver tracks PHY power and runtime PM. |
| Are resources transferred without reset or power loss? | Unproven. The LK shutdown attempt changes controller state, and the BL31 callbacks run later. No same-boot record establishes final resource state, reset state, or lifetime. |
| Are the intended non-secure HCI reads permitted and non-destructive? | Unproven. The LK mapping and XNU page-protection test establish software address translations. Neither observes the aperture's access controls or read behavior on the phone. |
| Is the archived BL31 byte-identical to the installed build? | Unproven. The reported Android banner is version evidence. The offline byte audit applies to the saved sample. |

[MiCode UFS initialization](https://github.com/MiCode/MTK_kernel_device_modules/blob/3c4ccd07d5624879555ec710c11bb8818e5cb5c6/drivers/ufs/ufs-mediatek.c#L1524-L1625)
and [MiCode UFS runtime PM](https://github.com/MiCode/MTK_kernel_device_modules/blob/3c4ccd07d5624879555ec710c11bb8818e5cb5c6/drivers/ufs/ufs-mediatek.c#L3244-L3315).

## 3. Required evidence and existing verifier

A trusted platform authority must establish the current device, actual
Slot B, and fresh boot identity independently of the record it validates.
Its grant must match the XNU entry for that boot and the exact MT6897 HCI
window. The existing observer requires:

- Version `1`, rights exactly `MUO_REQUIRED` (`0x3f`), a nonzero matching
  boot ID, nonzero grant ID, owner ID and resource epoch, the fixed
  `0x112b0000` / `0x3000` aperture, and zero reserved data.
- All six rights. The window is readable, power is pinned, bus clocks
  are pinned, non-secure reads are permitted, access and resource pins
  last until reset, and the selected reads are non-destructive.
- Successful validation by the trusted authority before mapping, before
  each load, and before publication. Revocation prevents new dispatches.
  An already authorized callback may finish under the resource pins.
  Failed or revoked captures leave the caller's output unchanged.

The observer maps Device memory permanently with `VM_PROT_READ`.
A physical authority must prove the runtime access and lifetime before
that mapping. The gate for commands additionally requires queue state,
controller ownership, DMA mapping and cache-maintenance evidence. A
successful passive snapshot supplies queue observations only.

## 4. Source locations

| Source | Role |
| --- | --- |
| [`tools/audit-duchamp-lk-handoff.py`](../tools/audit-duchamp-lk-handoff.py) | Hash-pinned LK entry and secure handoff audit. `inspect_lk()` and `inspect_bl31_handoff()` establish static call paths and record the limits of the evidence. |
| [`duchamp/bootshim/start.S`](../duchamp/bootshim/start.S) and [`phone_capture_entry.c`](../duchamp/bootshim/phone_capture_entry.c) | Existing isolated bootshim entry, CPU state capture and framebuffer report. |
| [`duchamp/bootshim/ufs_handoff_evidence.c`](../duchamp/bootshim/ufs_handoff_evidence.c) | Bounded FDT capture from entry RAM. No hardware or grant interface. |
| [`duchamp/drivers/mt6897_ufs_observer.c`](../duchamp/drivers/mt6897_ufs_observer.c) and [`mt6897_ufs_observer.h`](../duchamp/drivers/mt6897_ufs_observer.h) | Existing grant checks, atomic dispatch and revocation policy. |
| [`duchamp/xnu/mt6897_ufs_observer_xnu.c`](../duchamp/xnu/mt6897_ufs_observer_xnu.c) and [`qemu_ufs_observer.c`](../duchamp/xnu/qemu_ufs_observer.c) | Read-only XNU mapper and the only XNU caller, an emulator integration test. |
| [`duchamp/MT6897-UFS-FAIL-CLOSED.md`](../duchamp/MT6897-UFS-FAIL-CLOSED.md) | Separate physical command and storage prerequisites. |

## 5. Changes implemented

The opt-in, isolated `PHONE_CAPTURE=1 UFS_HANDOFF_PROBE=1` mode retains
its PC, `x0`, exception level and SCTLR capture. It stops in the existing
diagnostic path before XNU. It reads the incoming FDT from the same bounded
RAM window and publishes a version 2 record. The screen shows `D0` (FDT
fingerprint), `D1` (blockers), and `D2` (slot hint in the upper 32 bits,
declared dependencies in the lower 32 bits).

Slot values are unknown (0), A (1), B (2), or invalid/conflicting (3).
The collector recognizes exact `androidboot.slot_suffix` tokens in
`/chosen/bootargs` and `bootargs_ext`. The saved Duchamp FDT yields unknown.
The record does not inspect Android bootconfig or claim a trusted slot.
The dependency bitmap records declarations for the expected HCI register
tuple, clocks, PHY, power domains, RTFF/MTCMOS, resets, VCC and VCCQ.
The collector does not dereference phandles or the HCI aperture. It clears
only the FDT-invalid bit after a valid metadata capture. All remaining
blockers stay set (`0x7ef`), including unverified slot, owner, power,
clocks, PHY and MMIO. The FDT fingerprint is for correlating the display
and RAM record.

The mock authority fixture tests two wrong-slot cases and a stale resource
epoch in addition to the existing mismatched boot ID and six individual
missing-right cases. Its entry slot is independent of the evidence claim.
The runtime verifier, firmware configurations, identity mapping, and XNU
production boot path retain their existing behavior.

## 6. Offline test results

| Suite | Observed result |
| --- | --- |
| Entry evidence | Eight native ASan/UBSan and ARM64 bootshim QEMU cases each. Cases cover B, A, missing/invalid/conflicting slot hints, absent clock and power declarations, and the original saved Duchamp FDT. Native malformed-buffer checks also pass. All captured FDT inputs are unchanged. |
| Bootshim compatibility | Plain and UFS-probe QEMU PC/x0 and framebuffer captures pass. Static checks confirm the probe links no payload jump, SMC, HVC, or watchdog access. |
| UFS read-only observer | 28 cases each on host ASan/UBSan and ARM64 QEMU. The valid fixture performs 316 reads from a RAM-backed bank. Missing or stale authority, Slot A or a mismatched record slot, and absent clock or power rights fail before mapping. All 318 denial and 318 revocation positions and four native races pass. Separate virtual UFS trace size is zero. Both observer sources compile with the XNU BSD headers. |
| Full-XNU QEMU regression | Four fresh runs with the previously built XNU kernel from CI 43631086106. The valid fixture read the RAM-backed bank 316 times and reached read-only GPT/HFS+ PID 1 in 33.953 s. Missing power, missing clocks and revocation before mapping each produced zero maps, zero reads and an empty virtual UFS trace. The new slot/epoch cases ran in the standalone suite. |
| Existing UFS regressions | Register snapshot suite passes 30 cases, 316 read faults and 316 revocations. The synthetic BL31-handoff suite denies 20 cases and performs one verified virtual read. Nine audit, staging and profile suites pass 82 checks. The standard bootshim host suite also passes. |
| Exact artifact audit | The saved LK, BL31, stock boot header and FDT satisfy their pinned signatures and layout checks. Disposition remains execution blocked. |

Reproduce the entry suite with local firmware receipts and a new output
directory. The script runs only host tests and QEMU.

```sh
python3 -B duchamp/bootshim/test_ufs_handoff_qemu.py /path/to/new-output \
  --contract /path/to/lk-handoff-audit.json \
  --saved-duchamp-fdt /path/to/phone-fdt.bin
```

## 7. Remaining blockers

Physical UFS queue inspection is disabled. We need a vendor-supported
record or verified initialization at the final handoff for the exact Slot B
configuration. It must establish register read permission and side effects,
reset and PHY state, and ownership of the power domain and the relevant
clocks. The current mapper requires continuity through reset. No current
producer satisfies that contract. Physical storage commands remain blocked
independently.

## 8. Safe next hardware validation procedure

1. Obtain the supported LK/BL31 trace or handoff specification for this
   Duchamp firmware. Verify its origin and observation point after the
   last storage operation and BL31 boot callbacks.
2. For a separately approved diagnostic boot, preserve the known-good
   Android Slot A path and use a verified recovery route. Collect the
   existing entry CPU/FDT record and actual Slot B identity through a
   supported channel with no HCI mapping or controller access. The
   isolated diagnostic stops before XNU.
3. Obtain a correlated final-boundary record and actual XNU entry marker
   from one boot of the reviewed XNU candidate. Match the device, slot, fresh
   boot ID, firmware identity and loaded image. Independently verify the
   grant, power and clock lifetime, PHY/reset state, and read semantics.
   Any absent or mismatched field leaves mapping disabled.
4. After that evidence is reviewed and physical access is separately
   approved, map only the proved read-only window and collect one bounded
   queue snapshot. Use the existing per-read checks. Leave the controller
   untouched and stop on inherited activity, revocation, or inconsistent
   samples. Evaluate storage commands under their separate gate.

This update used local artifacts and QEMU. It issued no phone commands,
reboot, slot change, flash, partition write, or physical HCI access.
