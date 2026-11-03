# MT6897 DMA/IOMMU and UFS fail-closed gate

This milestone adds a policy core and local model tests. It does **not** enable
physical UFS, execute an SMC, access MediaTek MMIO, create an IOMMU mapping, or
authorize a phone test.

## Why the gate is a lease, not a boolean

UFS activation crosses five ownership boundaries: controller/PHY resources,
firmware power control, cache maintenance, DMA translation, and any bounce or
IOMMU memory. A one-time `true` value cannot prove that those owners remain
valid while later commands run.

`drivers/mt6897_ufs_gate.[ch]` therefore uses this sequence:

1. Initialize an all-zero gate once with a nonzero boot generation.
2. Submit a complete evidence record containing the exact DTB/firmware hashes,
   controller/PHY ranges, DMA aperture, and direct-DMA or IOMMU receipts.
3. Reject incomplete or contradictory records before calling any verifier.
4. Require the external verifier to return a non-revocable, boot-bound lease
   with exact owner tokens.
5. Check the same lease before every later hardware operation.
6. Permanently fault the gate on a stale lease, altered receipt, callback
   failure, re-entry, concurrent authorization, or attempted re-authorization.

The `ARMED -> VERIFYING` transition is an atomic one-shot claim. A competing
caller atomically marks the attempt contended; it cannot invoke a second
verifier, and the caller owning the transition latches a terminal fault before
publishing a usable lease. Native pthread tests cover contention before the
verifier, while the verifier is active, and during final lease publication;
the verifier is called at most once and no contended attempt returns a usable
lease.

There is intentionally no reset, release, or rearm API. A production provider
must hold its resources until boot end. The current tree has no physical lease
provider, so it cannot authorize MT6897 UFS.

## Pinned Duchamp evidence and current decision

The saved profile is tied to:

- DTB SHA-256:
  `9c49589f70044127be8941a9ea5537977f440ccd5ac15cfd24e120c8a1181d29`
- captured ATF payload SHA-256:
  `716222a632e4a0623a2e467e17f1d36f38a37f79a1c026447fe724e75e90e07e`
- UFS HCI: `0x112b0000`, size `0x3000`
- UFS PHY: `0x112a0000`, size `0x10000`
- observed bus DMA ceiling: 36 bits (`0x0fffffffff`)
- observed Linux route: generic direct DMA, no attached IOMMU at observation
- observed device: non-coherent, with a SWIOTLB pool pointer

Those observations are useful but insufficient. The gate must deny the saved
profile for exactly these unresolved facts:

- installed-firmware runtime effect contract;
- exclusive/resource ownership;
- XNU cache-maintenance ownership;
- direct DMA address translation and firewall behavior;
- a proved bounce disposition.

The verifier is not called when those local blockers exist. A SWIOTLB pointer
is not proof that a transfer used bounce memory, and absence of a Linux IOMMU
attachment is not proof of physical identity or firewall bypass.

## Integration rule

`drivers/mt6897_ufs_provider.[ch]` is now the only lease-guarded dispatch shell
for future MT6897 UFS operations. A zero-initialized provider is disabled. It
has six explicit operation classes: power, clock, PHY, MMIO, DMA and UFS
command. Binding requires a valid lease, and every operation rechecks that
lease immediately before changing state from `CHECKING` to `DISPATCHING`.
Missing or stale leases permanently fault the provider without invoking its
callback. A concurrent fault that wins before `DISPATCHING` also prevents the
callback; once dispatch has begun, platform locking remains the responsibility
of the future physical implementation.

The gate and provider are staged into the XNU source copy. The opt-in QEMU XNU
backend test presents the current pinned Duchamp evidence, confirms the gate
denies it before the verifier callback, and then exercises all six provider
entry points. Both the zero provider and the denied binding leave the model's
hardware-access and dispatch counters at zero. This is source integration and
a RAM-only selftest, not a physical provider.

Before any future physical integration, the provider must:

- derive a fresh boot generation from the boot session;
- validate the exact saved/runtime receipts rather than set evidence bits by
  convention;
- acquire all owner tokens before returning approval;
- call `mt6897_ufs_gate_lease_check()` before power, clock, PHY, MMIO, DMA,
  IOMMU, or UFS-command callbacks;
- call `mt6897_ufs_gate_fault()` on the first provider/runtime failure;
- never route MT6897 through the legacy Qualcomm `sweet_ufs_rootdev` path.

## Local verification

Run the evidence-bound test runner with the saved DTB and three pinned reports.
It compiles and runs a receipt extractor against the actual gate helper, then
requires the embedded DTB, ATF, firmware-audit, runtime-DMA and PRDT hashes and
all HCI/PHY/DMA/service constants to match those inputs. It also executes host
sanitizers, concurrent gate and provider tests, and two ARM64 freestanding
QEMU models; it never contacts a phone. The provider model covers all six
operation classes with a valid synthetic lease, while negative tests prove
missing, stale and concurrently revoked leases produce zero denied dispatches.
The combined Duchamp offline gate also runs this component.

The 2026-11-03 v8 run passed 708 native and 708 ARM64 gate checks, 140 gate
concurrency checks, 107 native and 107 ARM64 provider checks, and 35 provider
concurrency checks. The combined 17-component gate also passed. Results are in
`work/test-mt6897-ufs-gate-20261103-v8/result.json` and
`work/offline-gate-ufs-20261103-v8/result.json`.

The result must keep all physical flags false and report the current profile
as denied. A passing local test means the policy fails closed; it does not mean
that physical UFS or full system boot is ready.
