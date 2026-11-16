# Duchamp Slot B trusted handoff evidence

## Verified sequence and limits

The audit starts from `e2876c3`. It uses the saved LK and BL31 binaries
whose hashes appear in the [shutdown analysis](DUCHAMP_UFS_LK_SHUTDOWN_ANALYSIS.md).
The retained Fastboot log reports that firmware initialized UFS and the
M-PHY. The archived Slot B XNU system reached userspace from an embedded
RAM root. The logs describe separate executions. The Android Slot A
BL31 banner supplies a version string and no authenticated byte identity
for the firmware that ran in the Slot B XNU boot.
[Saved observations](DUCHAMP_SLOT_B_UFS_HANDOFF.md#1-verified-observations)

| Boundary or resource | Verified from source or the saved bytes | Unresolved on the actual Slot B path |
| --- | --- | --- |
| LK storage cleanup | The sampled LK wrapper at partition offset `0x196b8` calls platform cleanup at `0x196e8`. UFS shutdown at `0x79e0c` writes AHIT zero, attempts START STOP UNIT PowerDown through the legacy doorbell, and writes HCE zero at `0x79e48`. The shutdown caller does not check PowerDown success, and the path has no post-store HCE or queue readback. LK is the last **identified HCI writer** in this path. | Whether PowerDown or HCE shutdown completed, the final link state and configured queue mode, subsequent writers, queue emptiness and outstanding interconnect work. |
| BL31 reset service | One LK shutdown branch asks the saved BL31 bootloader UFS service for selector 2, level 0. BL31 callsites `0x44e84` and `0x450fc` hit helper `0x44f84`. It conditionally writes bit 0 of AO syscon `0x112b8090` and reads HCI IP version at `0x112b2240`. The pinned Linux caller independently identifies selector 2 as active-low **device reset**. HCI, crypto and UniPro resets are separate. | Runtime branch selection, whether the conditional store ran, device reset level at entry, controller reset state and duration of any assertion. |
| Final BL31 exit | LK's `0x10054` callsite and `0x10cd4` trampoline implement the separate kernel-boot handoff. The BL31 descriptor at `0x65500` points to `0xb63c`. It runs the named EMI non-secure permission and SMPU callbacks after LK's cleanup and before return to the non-secure boot target. | The effective firewall permission, any later UFS/resource changes and who owns the aperture. The audited chain contains no verified UFS-specific delegation. |
| Bus clocks, reference clock, rails, domain and PHY | The saved FDT describes the relevant clocks, regulators, RTFF/MTCMOS and M-PHY v1. Pinned Xiaomi Linux code controls runtime clocks, delegates reference clock and MTCMOS operations to firmware, and distinguishes host and device resets. | Which owner controls each vote or gate at XNU entry, whether the required clocks and rails remain on, the domain and PHY state, and whether continuity can be guaranteed. |
| DMA and IOMMU | The saved Android probe reported direct DMA and no standard Linux attachment for this device. CPU barriers, a zero HCE write and a reset request do not account for posted work or other producers. | Whether any request survived cleanup, the real UFS master route, whether a domain and its translations were retained or replaced, whether old submissions are fenced, and whether the fabric completed a drain. |
| Cache | LK's CPU cache transition covers its CPU execution handoff. The saved Linux implementation supplies its own DMA API and cache policy. | Cache responsibility for descriptors and buffers, coverage of any system cache, effective coherency and who owns the lifetime of that contract across handoff. |
| Bootshim to XNU | Saved entry diagnostics corroborate `PC=0x40000000` and `x0=0x47c80000` for the recorded phone experiment. The normal shim materializes the payload and can call `duchamp_enter_xnu`. The standalone entry diagnostic halts at the bootshim. | Matching the two observations to each other and to final firmware state in one actual XNU boot. |

The reset role follows from the pinned Xiaomi selector and reset routine
together with the matching binary trace. No reset register was read or
written on the phone in this phase.
[Reset trace and source references](DUCHAMP_UFS_OWNERSHIP.md#identifying-the-always-on-syscon-bit),
[LK and BL31 audit functions](../tools/audit-duchamp-lk-handoff.py#L179),
[bootshim entry](../duchamp/bootshim/start.S#L86),
[normal XNU dispatch](../duchamp/bootshim/shim.c#L473)

## Evidence sources and trust

Measure after the last LK UFS operation and the final BL31 callbacks,
at the boundary before BL31 releases the boot CPU. Correlate with an
independent capture at XNU entry in the same execution. Missing or
inapplicable fields require explicit reason and provenance. Keep the
following assertions separate.

| Assertion | Source and check |
| --- | --- |
| Same boot and final exit | A supported firmware diagnostic or independently controlled vendor trace establishes a fresh boot identifier, sequence and final-exit marker. Its authenticated statement binds a verifier challenge plus instrumented event order and a validity window. Validate the XNU entry event separately and reject replay or mix-and-match. |
| Actual Slot B | The firmware slot-selection/verified-boot event and the measured loaded images for the **resolved** slot. Require this independently of `/chosen` hints or a host-selected request. |
| Executing firmware, bootshim and target | The vendor measurement chain for the bytes actually selected and loaded. Identify LK and BL31 separately and pin their measured values to vetted builds. Bind bootshim and XNU identities and entry targets. The checksum of a saved image or a matching banner alone does not identify the running image. |
| DTB and ADT | Measure the exact firmware-final FDT bytes before release and compare with bounded bytes at bootshim entry. If the loader transforms FDT to ADT, record the exact relationship and digests of the resulting ADT, boot arguments and XNU image at entry. A hash confirms equality of measured bytes across the two samples. It carries no authority about what the properties claim. |
| Ownership, MMIO and lifetime | The documented resource authority identifies the current owner and authorized next consumer of HCI, clocks/votes, rails, domain, PHY, resets and IRQ, with exact permission scope, effect duration and revocation. A state sample or NS access control observation alone provides no grant. |
| Positive clock, power, reset and PHY state | Authorized, passive telemetry from the appropriate clock, power, reset and PHY owners at the final boundary. Include source semantics and stable-until conditions, plus separately reported device reset and host/UniPro resets. Avoid substituting register-declaration topology or a different boot's values. |
| DMA drain and isolation | The producer and controller owners attest that each legacy or MCQ queue is accounted for and prior submissions cannot resume. An independent fabric completion or isolation acknowledgment covers transactions already admitted. Bind the relevant DMA master, descriptors, protected XNU range and completion epoch. |
| IOMMU or direct route | The platform DMA/isolation owner verifies the real stream, domain and mapping epoch, and accounts for bypass, old translations and completion of invalidation. For direct DMA, supply an independently verified protection boundary and extent. A null property or Linux attachment query supplies no runtime ownership evidence. |
| Cache responsibility | The platform owner documents which CPU and system-cache operations cover that DMA master and range. Prove that the appropriate agent finished the necessary synchronization and retains ownership of the contract for this handoff. An FDT coherency hint is only a declaration. |
| Integrity, origin and freshness | Verify against a provisioned vendor or controlled-measurement trust root. The statement covers the exact identity, scope, fact values and receipt references, with a current resource epoch and revocation status. A digest, checksum, nonce or bootshim echo alone cannot authenticate facts or grant resources. |

The saved stock firmware and retained ATF, PL/LK and pstore logs provide
no demonstrated producer for these assertions. The smallest missing
instrumentation is a supported final-exit emitter or independently
controlled trace that covers the exact handoff, plus a same-boot XNU
entry marker and an authenticated resource-authority statement.
Instrumentation may establish observations first. A subsequent grant
must come from the entity that can actually enforce ownership and
lifetime. [Hardware validation plan](DUCHAMP_UFS_HARDWARE_VALIDATION_PLAN.md)

## Offline implementation and current XNU integration

- The opt-in `PHONE_CAPTURE=1 UFS_HANDOFF_PROBE=1` collector now emits
  version 3 of its passive 88-byte RAM record. The version 2 prefix
  preserves the entry FDT length, slot hint, declared dependencies,
  blocker mask and screen fingerprint. Offsets 40 and 48 record PC and
  `x0`. Offset 56 holds the 32-byte SHA-256 digest of the FDT's bounded
  `totalsize` bytes. The existing entry/RAM bounds precede the read.
  The record reads neither ATF memory nor an untrusted second pointer.
  [Layout](../duchamp/bootshim/ufs_handoff_evidence.h),
  [bounded collector](../duchamp/bootshim/ufs_handoff_evidence.c),
  [SHA-256 specification](https://csrc.nist.gov/pubs/fips/180-4/upd1/final)
- The display keeps D0 (fingerprint), D1 (blockers) and D2 (slot hint and
  declaration bits). D3 through D6 show the digest, in byte order, when
  the FDT is valid. An `iommus` declaration or `dma-coherent` property
  records presence only and leaves the corresponding state blocked.
  Valid captures clear only the FDT-invalid bit, leaving `0xffef`.
  Invalid captures leave `0xffff` and a zero digest. The boot ID,
  firmware identity, reset, IOMMU and cache blockers are explicit.
  The image draws to the existing framebuffer, touches no UFS hardware,
  and stops before XNU. [Display and capture](../duchamp/bootshim/phone_capture.c#L374),
  [isolated build profile](../duchamp/bootshim/build.sh#L130)
- The separate test-only `DUCHUFS1` reader requires a live existing lease,
  exact boot and firmware/FDT identity, and matching DMA route. The IOMMU
  version additionally checks stream, domain and mapping epoch against
  the approved gate evidence. It requires independent provenance,
  freshness and current context on each accept, claim and recheck. The
  current sample now also independently confirms the resource
  prerequisites and cache owner, so even an authenticated test receipt
  cannot substitute for missing or changed current state. Revocation
  still prevents publishing a successful transition.
  [Validation and state transitions](../duchamp/drivers/model/duchamp_ufs_handoff_model.c),
  [production gate](../duchamp/drivers/mt6897_ufs_gate.c#L949)
- The current full-XNU comparison is emulator-only. The explicitly
  selected QEMU loader copies the fixture mailbox into the test ADT and
  its entry ID into boot arguments. The QEMU XNU backend matches those
  IDs, checks its fixture proof and can call the observer on the
  RAM-backed register bank. The physical observation record has a
  separate format with no consumer in that path. The passive diagnostic
  and test-only reader are outside production XNU staging. No physical
  provider or permission source was added.
  [QEMU loader](../duchamp/bootshim/qemu_bl31_receiver.c),
  [QEMU XNU entry](../duchamp/xnu/qemu_ufs_handoff.c#L67),
  [QEMU observer](../duchamp/xnu/qemu_ufs_observer.c#L86),
  [XNU staging](../tools/stage-duchamp-qemu-ufs.py)

## Test results

| Suite | Result |
| --- | --- |
| Passive entry diagnostic | 12 cases each on native ASan/UBSan and ARM64 bootshim QEMU. This includes missing clock/power declarations, an untrusted B hint with synthetic firmware fields, the saved Duchamp FDT, and SHA-256 padding boundaries. QEMU matches the digest against the guest FDT bytes and checks all 64 displayed hexadecimal digits. The saved FDT reports no slot hint. |
| Offline handoff lifecycle | 98 cases each on native ASan/UBSan and freestanding ARM64 QEMU. Wrong boot/domain, incomplete or stale proof, fabricated/corrupted fixtures, unverified drain, reset/clock/power disagreements, ambiguous or changed cache owner, and revocation all deny. The virtual UFS traces are empty in the model tests. |
| Observer authority | 28 cases each on native ASan/UBSan and ARM64 QEMU, including 318 denial and 318 revocation positions per environment. Four native race tests and the compile against XNU headers passed. The unrelated virtual UFS trace is empty. |
| Bootloader | Host, payload preflight, plain entry capture and UFS entry capture passed. The ELF audit confirms no payload/XNU jump, watchdog access or SMC/HVC in the isolated diagnostic. |
| Full XNU | 11 fresh QEMU runs passed using the already-built CI 43631086106 kernel. Two read-only GPT/HFS+ boots reached diagnostic PID 1. The nine stopped scenarios emitted zero virtual UFS events. |
| Static audit and staging | The repeat pinned LK/BL31 and reset selector checks, LK audit tests, and XNU stage isolation checks passed. |

Commands, exits, full-XNU kernel logs and traces are in the workspace
directory `outputs/duchamp-trusted-boot-handoff-20261116`. The phone
was not accessed. Physical UFS remains disabled.
