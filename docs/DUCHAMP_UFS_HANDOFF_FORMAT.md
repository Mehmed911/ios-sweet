# Duchamp UFS handoff format

## Scope

`DUCHUFS1` is a proposed test-only software record for a cold-entry
ownership check. There is no matched firmware issuer or on-device
decoder. The implementation stays under `duchamp/drivers/model` and
rejects compilation without its explicit test macro. It requires a
previously issued lease from the existing MT6897 UFS gate and an
independent provenance verifier. Parsing produces a decoded view.
Validation produces status only, with no new lease, MMIO mapping,
DMA operation or UFS submission.
[Wire and session types](../duchamp/drivers/model/duchamp_ufs_handoff_model.h),
[parser and validator](../duchamp/drivers/model/duchamp_ufs_handoff_model.c)

## Wire layout

Version 1 has exactly 448 bytes. Integers are unsigned and little-endian.
The signed data is exactly bytes 0 through 383. The 64-byte provenance
proof follows at offset 384. A future producer/verifier pair must agree on
a supported authentication scheme and bind it to the trusted authority
ID, protocol and exact signed bytes. Unknown authorities, missing proof and
a bare checksum are insufficient. The format pins these regions without
choosing a firmware ABI, key or signature algorithm.

| Offset(s) | Width | Fields in order |
| --- | --- | --- |
| 0 | 8 | ASCII magic `DUCHUFS1` |
| 8, 12 | 4 each | Format version 1 and total bytes 448 |
| 16, 20, 24, 28 | 4 each | Board `0x6897` for Duchamp, actual slot B (2), final BL31 stage (1), existing gate DMA route (1 direct, 2 IOMMU) |
| 32, 36, 40 | 4 each | Ownership, prerequisite and DMA proof masks |
| 44, 48, 52, 56, 60 | 4 each | Queue mode, configured queue count (one legacy or 1–8 MCQ), busy queue bits, outstanding DMA count, stream ID. Busy bits and outstanding count must be zero with complete positive evidence. |
| 64, 72, 80, 88 | 8 each | Boot ID, current handoff sequence, issue and expiry time in a shared authenticated monotonic milliseconds domain |
| 96, 104, 112, 120, 128, 136 | 8 each | Exact HCI base and bytes, gate lease ID, evidence fingerprint, provider epoch, trusted authority ID |
| 144, 152, 160, 168, 176 | 8 each | Controller, PHY, firmware, DMA and cache owner IDs, all matched to the existing lease |
| 184, 192, 200, 208 | 8 each | Clock, power, reset and IRQ owner IDs |
| 216, 224, 232, 240, 248, 256, 264 | 8 each | Isolation epoch, IOMMU domain ID, complete queue snapshot receipt, fabric fence receipt, descriptor pool receipt, cache receipt, and isolation receipt |
| 272, 280 | 8 each | Protected XNU physical base and length, a nonempty overflow-checked interval |
| 288, 320, 352 | 32 each | SHA-256 digests for target XNU, source BL31 and live FDT |
| 384 | 64 | Opaque provenance proof checked by the authority verifier |

The exact ownership mask `0x1ff` covers exclusive HCI, clocks, power,
PHY, resets, IRQ, DMA, cache and firmware control. The exact prerequisite
mask `0x7ff` requires pinned rails, active domain, pinned bus and reference
clocks, PHY ready, reset deasserted, HCE off observed, granted non-secure
control, resource lifetime pins, cold-init permission, and read-only
policy. This is a conservative known state for version 1. Future entry
states need an explicit reviewed version or policy.

The exact direct mask `0x7f` requires completed fabric drain, complete
queue snapshot, old submissions fenced, old descriptors quarantined,
XNU memory isolated, cache synchronized and direct filtering proved.
The IOMMU mask `0x3bf` includes the same first six facts and instead
requires the old stream blocked, IOTLB invalidation completed and
endpoint translations accounted for. The direct stream/domain fields
are zero. The IOMMU domain is nonzero and the stream is independently
matched, including legal stream ID zero. An all-one stream is invalid.
Absent and unknown mask bits fail closed.

## Validation and lifecycle

1. Copy exactly 448 bytes from stable caller RAM into private session
   storage. Check size, magic and version. The parse-only API leaves
   output untouched on a malformed header and carries no authority.
2. Require the exact platform and HCI range, complete positive
   resources/DMA proof and meaningful evidence IDs. Bind the recorded
   owners, boot generation, gate evidence fingerprint and epoch to the
   caller's existing gate lease. The lease is independently revalidated
   through the unchanged gate API.
3. Require the external verifier to authenticate the exact byte copy
   and validate all referenced receipts and their still-current scope.
   Trust is supplied by the verification channel and authority policy.
   The mock uses an allow-listed fixture and carries no production key.
4. Sample trusted Slot B, boot ID, sequence, authority ID, image digests,
   route/domain/stream/epoch, range and time independently of the record.
   Require a nonzero policy freshness budget, bounded issue-to-expiry
   interval and current time in `[issue, expiry)`. An apparent clock
   regression between checks or a changed sequence fails. Time and the
   sequence are sourced externally from the same boot.
5. Atomically move `NEW → CHECKING → VALIDATED → CHECKING → CLAIMED`.
   A claimed session can pass a recheck through `CHECKING`. Each
   transition revalidates the record, provenance, current context and
   existing lease. Failed validation or explicit revocation makes the
   session terminal. Calls racing an in-progress check are refused and
   revocation wins any later publication. A check and a later I/O
   dispatch cannot share this model's status as an access grant. Any
   future integration must serialize controller lifetime and preserve
   existing per-operation authorization and hardware locks. Trusted
   intake must own one session per boot and enforce replay policy
   across sessions.

## Offline verification

- **80 cases passed** on both native ASan/UBSan and standalone ARM64 QEMU
  with identical decisions. The parser refused all 448 shorter lengths and
  an oversized record. Negative cases include wrong slot, boot or digest,
  stale sequence/time, unknown owners, altered body/proof, missing power
  or clocks, incomplete DMA proof, revocation, and a changed live stream or
  range. The virtual UFS trace contains zero register and SCSI events.
- **11/11 full-XNU QEMU regressions passed** with the existing CI
  43631086106 kernel. Cold and default-off read-only GPT/HFS+ boots reached
  diagnostic PID 1. All nine stopped cases produced zero virtual UFS
  events. The model is outside XNU staging and the kernel was reused.
- The existing bootshim host suite, all eight QEMU entry metadata cases,
  LK audit, cold-init model, gate/provider, DMA route, cache, snapshot and
  staging regressions passed. Results and exit codes are recorded in the
  [test receipt](#test-receipt).

### Test receipt

The outer workspace directory `outputs/duchamp-ufs-ownership-dma-20261115`
contains `verification.json`, `SHA256SUMS`, the root regression
`*.command.json` files, and their named logs. The new model's compiler,
native executable and QEMU commands with exit codes are under
`format-tests`. The compile-rejection check is expected to exit 1.
The rest of the verification runs exit 0.

```sh
python3 -B tools/test-duchamp-ufs-handoff-format.py /path/to/new-output
```

## Physical validation blocker

A trusted same-boot producer and a separate provenance verifier for
the installed firmware still need to be established. Obtain the final
post-BL31 record, the resource and DMA attestation and the XNU entry
identities first. The firmware/clock state, reset level, and DMA
isolation remain unmeasured on Slot B. No flash, reboot, slot change,
MMIO, DMA or partition operation occurred on the phone.
