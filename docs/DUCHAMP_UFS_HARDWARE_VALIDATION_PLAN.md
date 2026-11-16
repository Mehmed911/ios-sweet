# Duchamp UFS hardware validation plan

## Smallest useful physical experiment

Capture two events from **one actual Slot B boot** of the known-good
RAM-root XNU build. Observe the final BL31 release, after all LK storage
operations and BL31 callbacks. Observe bootshim-to-XNU entry in that same
session. Keep the scope to read-only observation of already available
telemetry and CPU/boot identity. Require a vendor-supported,
non-perturbing channel whose documentation identifies the source and
semantics of each measurement. If a channel cannot collect a field
without changing resources or relying on an unverified access, record
the field as unknown and end the experiment at that boundary.
[Evidence source matrix](DUCHAMP_SLOT_B_TRUSTED_HANDOFF.md#evidence-sources-and-trust)

| Observation | Producer or independent observer | Acceptance check |
| --- | --- | --- |
| Selected and resolved slot, measured LK and BL31, final FDT, boot ID/sequence and exit point | Vendor-validated measured-boot and final-exit trace from LK/BL31, after callbacks for the final-exit event | Validate a source pinned to the installed device/build, the challenge and current boot epoch, resolved B, measured bytes and event ordering. |
| XNU entry PC, boot argument/ADT identity, target image and boot identity | Supported independently captured XNU entry event, or the existing shim/kernel with a separately reviewed RAM-only correlation marker if observation without a code change is unavailable | Require the same boot challenge, exact image and expected FDT-to-ADT or boot arguments relationship. Observed identity must correspond to the execution that actually enters XNU. |
| Current reset, clocks, rail/domain, PHY and resource permissions | Existing trusted vendor telemetry from the respective owners at release | Treat device reset and HCI/UniPro reset separately. Verify clock vote and resource lifetime semantics. Require explicit scope and an enforceable owner for any grant. |
| Current queue fence, fabric drain, DMA route and cache contract | Existing firmware/controller and fabric telemetry plus DMA, IOMMU and cache owners, with evidence after the last request/remap | Require exact master and coverage, full queue/fabric accounting, mapping epoch and scope, and separate cache responsibility. A queue snapshot, CPU barrier, or HCE/reset state alone cannot prove drain. |

An authenticated vendor channel can supply measurement records tied to
the installed firmware and boot identity. An independent validation
setup may instead directly witness and log the same events under
authorized hardware observation, with source identity and a
chain of custody. A serial banner, an unsigned log from Android, or the
checksum of the bootshim record cannot supply authority. Independent
measurements establish what happened. A grant remains a separate,
verifiable statement from the resource owner.

## Component and device boundaries

- **Preferred experiment.** Use existing vendor-supported telemetry and
  a supported entry observer. Keep LK, BL31, XNU and all slots as built.
  There is no demonstrated supported Duchamp channel that supplies all
  of the required evidence today.
- **If entry correlation is missing.** The existing standalone
  `PHONE_CAPTURE` can help validate a PC/`x0`/FDT capture in its own
  approved diagnostic boot. It stops before XNU and cannot count as the
  XNU-entry event. To correlate an actual XNU boot, use vendor
  observation at that entry or review a bounded RAM-only marker in the
  existing bootshim/XNU path. The marker must preserve the calling
  convention, cache publication rules and memory reservations. No
  physical integration for such a marker was added in this phase.
- **If firmware evidence is missing.** Request an authorized final-exit
  diagnostic from the vendor and a producer for the resource attestation.
  Any required firmware instrumentation belongs in that supported build
  or in a vendor-authorized external trace. There is no need to patch
  security-controller policy or replace stock LK/BL31 for this phase.
  Without a supported channel, stop at offline validation.
- **No storage or controller operation.** The experiment has no reason
  to map the physical HCI, read the device-reset syscon, issue UFS or
  SMC commands, change clocks, PHY, reset or power, reconfigure IOMMU,
  or start DMA. Keep the existing physical gate disabled. Evidence
  collection never authorizes a block read by itself.

## Recovery and abort criteria

Before a separately approved experiment, verify the known-good Android
Slot A path and the approved recovery method. Record the existing slot
metadata and hashes of saved boot and recovery images as applicable.
Preserve both Slot A and recovery, all shared partitions and user data,
the known-good Slot B image and the original recovery toolchain. Keep a
host with the already verified recovery connection available. Prefer a
method that does not require changes to persistent boot configuration.

A failed or stalled diagnostic can leave the device on a black screen,
consume Slot B boot retries, or leave B selected. A wrong-slot test
image, a shared partition write, firmware/version mismatch, incompatible
AVB metadata, RAM corruption or a disturbed firmware power/DMA state
could also prevent Android from starting. If the trace or entry evidence
is incomplete, the device resets, or the expected screen/log does not
appear within the defined observation window, stop the run. Use the
previously verified recovery path to select the original Android A
configuration and verify Android reached userspace on A. If an approved
temporary change affected B, restore the exact saved B image/configuration
under the recovery procedure and verify it separately. Avoid writing
A, shared storage or firmware during recovery. Hold for diagnosis if
the approved recovery path is unavailable. No recovery, slot selection
or reboot is performed by this plan.

## Required checks before hardware

1. Native ASan/UBSan and ARM64 QEMU tests pass for malformed or stale
   evidence, wrong boot/slot/domain, reset mismatch, missing clock/power
   or drain, ambiguous cache ownership and revocation. Denied cases must
   refuse all physical access and produce zero virtual UFS interactions
   in the denial trace.
2. The exact capture ELF passes the static capability checks and
   bootshim/payload regressions. If a correlation marker is later added,
   verify its hashes, reserved RAM bounds, entry ABI and no-I/O behavior
   locally before considering its use.
3. Full-XNU QEMU verifies the unchanged read-only boot and denial paths.
   Preserve the CI kernel, QEMU manifests, exact command receipts and
   known-good Android images.
4. The evidence channel, trusted measurement or authorization source,
   expected userspace outcome, time limit and recovery method are
   documented for the actual device. Obtain explicit approval for the
   exact attempt. Keep physical UFS disabled even if the observation
   succeeds. A later proposal to use UFS requires independent approval
   and positive evidence under the existing read-access and DMA gates.

The requested offline tests passed as recorded in the
[trusted handoff report](DUCHAMP_SLOT_B_TRUSTED_HANDOFF.md#test-results).
The missing supported same-boot evidence channel still blocks physical
validation.
