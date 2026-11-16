# Duchamp final BL31 to XNU handoff

## Status

Baseline `7ba1a6c` provides a passive bootshim diagnostic and fail-closed
UFS checks. This phase pins the previously booted Slot B images and adds
an offline verifier for a future supported capture. No reviewed channel
produces the final BL31 and XNU entry observations for the same physical
Slot B boot. Physical UFS stays disabled.
[Prior audit](DUCHAMP_SLOT_B_TRUSTED_HANDOFF.md),
[authorization checks](../duchamp/drivers/mt6897_ufs_gate.c#L949)

## Firmware behavior and trace channels

In the saved LK image, the wrapper at partition offset `0x196b8` reaches
UFS shutdown at `0x79e0c`. It clears AHIT, attempts START STOP UNIT
PowerDown, and writes zero to HCE at `0x79e48`, the last identified HCI
write. The caller does not check the PowerDown result or confirm the queues
after the HCE write. LK can request active-low device reset through BL31.
The saved helper at `0x44f84` can change bit 0 of AO syscon `0x112b8090`
or skip the store. Device reset is separate from HCI and UniPro reset.
The final reset level, queues and DMA drain remain unmeasured.
[LK shutdown](DUCHAMP_UFS_LK_SHUTDOWN_ANALYSIS.md),
[reset source and binary match](DUCHAMP_UFS_OWNERSHIP.md#identifying-the-always-on-syscon-bit)

The saved BL31 kernel-boot descriptor at `0x65500` dispatches to
`0xb63c`. On the first-entry path, `0xb6c4` runs callback group 5
through `0x28d98`, including EMI permissions and SMPU work. The call at
`0xb6c8` runs helper `0x27f54` before ordinary return at `0xb6dc`.
The firmware observation belongs at the actual final non-secure release
after all platform work. The LK jump banner and blackbox record precede
cleanup. [Static auditor](../tools/audit-duchamp-lk-handoff.py#L261)

| Channel | Verified scope |
| --- | --- |
| BL31 hooks and secure-monitor interfaces | The sampled kernel-boot service dispatches callbacks. No reviewed descriptor establishes a passive final-exit UFS export or grant. Generic TF-A PMF may expose timestamps if enabled by the platform. No enabled Duchamp trace or UFS measurements were demonstrated. [TF-A runtime instrumentation](https://trustedfirmware-a.readthedocs.io/en/lts-v2.14.10/perf/psci-performance-instr.html) |
| Android firmware debug logging | The Android A raw dump reported a BL31 build banner. MiCode's drivers export bytes from reserved ATF log RAM. The dump supplies no correlated Slot B XNU event or byte identity for that boot. [ATF log reader](https://github.com/MiCode/MTK_kernel_device_modules/blob/3c4ccd07d5624879555ec710c11bb8818e5cb5c6/drivers/misc/mediatek/atf/atf_log.c), [debug buffer reader](https://github.com/MiCode/MTK_kernel_device_modules/blob/3c4ccd07d5624879555ec710c11bb8818e5cb5c6/drivers/misc/mediatek/atf/tfa_debug.c#L175-L227) |
| LK trace and boot phase | The historical PL/LK export returned 197,219 bytes and reported earlier UFS/M-PHY initialization on a Fastboot path. The published log-store driver tracks boot phases but supplied no authenticated XNU identity. [MiCode log store](https://github.com/MiCode/MTK_kernel_device_modules/blob/3c4ccd07d5624879555ec710c11bb8818e5cb5c6/drivers/misc/mediatek/log_store/log_store.c), [saved trace inventory](../duchamp/MT6897-LK-HANDOFF-CONTRACT.md#live-retained-lk-log-on-slot-b) |
| Fastboot and pstore | The saved LK audit found 35 command registrations with no documented ATF upload/fetch. The historical staged-data query returned unknown-command and zero bytes. The separate `lkmsg` and `lpmsg` pstore exports yielded no attributable XNU trace. |
| Independent observation | Arm documents non-invasive instruction trace where the requisite CoreSight features are implemented and accessible. The reviewed material did not establish an approved secure/non-secure trace and entry register/memory capture for this retail handset. Instruction flow alone cannot establish XNU arguments or UFS state. [Arm CoreSight](https://developer.arm.com/community/arm-community-blogs/b/architectures-and-processors-blog/posts/how-to-debug-coresight-basics-part-1) |

Actual firmware identity, slot and entry correlation, reset state, power
and clock continuity, PHY readiness, MMIO rights and resource lifetime,
queue fencing, fabric drain, IOMMU domain ownership and system-cache
responsibility remain unresolved. Slot A Linux DMA observations and
FDT declarations describe other evidence. [DMA requirements](DUCHAMP_UFS_DMA_SAFETY.md)

## Capture contract

Use a documented vendor final-exit channel and an independently
controlled XNU-entry witness. An authorized external platform observer
could supply the equivalent observations if approved for both boundaries.
Any needed instrumentation or diagnostic access must come from the
platform owner. Each witness signs only what it has verified.

| Fields | Trusted source |
| --- | --- |
| Device, challenge, boot ID, resolved Slot B, selected images and sequence | Measured-boot authority and the independent witness bind both events to one fresh attempt and one ordered event stream. Measure the executing LK and BL31, selected B triplet and XNU payload. The entry witness checks loaded XNU code against the measured payload. |
| Final return PC, incoming `x0`, actual XNU PC and `x0` | The final-exit producer observes the non-secure target and FDT pointer. The second witness independently observes bootshim arrival and the execution of XNU's first instruction with its boot argument. Match both to the reviewed artifact. |
| DTB and ADT | Compare the exact firmware-final FDT `totalsize` bytes with the bootshim's incoming bytes. Independently capture the ADT at XNU entry and compare to the exact payload. The existing v3 standalone diagnostic records PC, `x0`, and DTB SHA-256 but stops before XNU. [Passive probe](../duchamp/bootshim/ufs_handoff_evidence.c#L267), [XNU dispatch](../duchamp/bootshim/shim.c#L514), [ADT copy](../duchamp/loader/materialize.c#L113) |
| `queues`, `reset`, `clocks_power_phy`, `resource_access` | LK/UFS, BL31 reset, clock/power/PHY, and resource owners provide the final measurements or a last valid sample with a documented no-change guarantee. Include HCE, the configured legacy or MCQ queues, both device and host reset states, clock votes, rails, domain and PHY, plus explicit resource authority and lifetime. |
| `dma_drain_isolation`, `iommu_route` | The fabric and routing authorities establish completion for admitted work, no-resume and isolation of the exact protected range. Verify DMA master and direct route or stream/domain/mapping epoch, including retired translations and invalidation completion. |
| `cache` | The platform cache owner identifies responsibility, actual coherency and maintenance coverage, including the system cache and the completed synchronization for that DMA master and range. |

The new [host verifier](../tools/verify-duchamp-final-handoff.py) implements
a proposed normalized export. Each `final-bl31` and `xnu-entry` record has
`.json`, detached 64-byte Ed25519 `.sig`, and DER public key `.der` files.
The host verifies exact signed bytes against two independent fingerprints
in an out-of-band trusted profile. The signatures require a documented
producer. Test keys use a scope rejected by the physical-input CLI.
The verifier reads bounded files and has no device or grant interface.
[OpenSSL pkeyutl](https://docs.openssl.org/3.0/man1/openssl-pkeyutl/)

| Field | Encoding and check |
| --- | --- |
| Common JSON fields | `format=duchamp-final-handoff-v1`, `scope=duchamp-physical-slot-b`, `board=duchamp/mt6897`, `slot=b`, `device` and `challenge` as 64 lowercase hex digits, `boot_id` as 32 lowercase hex digits, and positive `sequence`. `images` maps `lk`, `bl31`, `boot_b`, `vendor_boot_b`, `init_boot_b` and `xnu_payload` to SHA-256 values. Both records pin `fdt_sha256`. |
| Final record | `stage=final-bl31-exit`, `ns_pc`, `fdt_pa`, and `observations`. A claimed class references `<name>.bin` with its source label and SHA-256. The exact labels are in the verifier's `SOURCES` mapping. Preserve the owner record and chain of custody. |
| Entry record | `stage=actual-xnu-entry`, `shim_pc`, `fdt_pa`, `xnu_pc`, `xnu_argument`, `adt_sha256`, and `bl31_record_sha256` of the exact final-exit JSON. Require the same boot ID and a greater sequence. `incoming.dtb` and `entry.adt` supply the measured bytes. Addresses are integer JSON values. |
| Trusted profile | All six image digests, `adt_sha256`, `shim_pc`, `fdt_pa`, `xnu_pc`, `xnu_argument`, `bl31_key_sha256`, `entry_key_sha256`, `device`, `challenge`, and Unix-second `not_before` and `not_after` on the trusted host. Provision the pins outside the capture. Use a new 32-byte random challenge per attempt and a verification window of at most 15 minutes. |

The verifier can confirm record correlation with missing owner
observations and lists those gaps. A claimed but absent or corrupted
receipt rejects the pair. Source labels and hashes bind exported bytes,
with resource semantics left to the named owners and independent review.
Successful correlation keeps `physical_ufs_authorized=false` and
`resource_ownership_validated=false`. The project has no vendor keys or
verified physical producer. Rechecking a saved challenge is the same attempt.

```sh
python3 -B tools/verify-duchamp-final-handoff.py CAPTURE_DIR \
  --trusted-profile TRUSTED_PROFILE.json
```

## Exact proposed artifacts and backups

Reuse the November 11 RAM-root XNU services build only if B already
contains this exact triplet. The saved files match the historical
installed-image receipts. The development boot image fails the stock
locked AVB chain. Stop for review if the current B setup cannot use
the exact images through the established boot and recovery path.
This experiment uses the existing images and AVB policy.

| Saved artifact relative to the workspace | SHA-256 |
| --- | --- |
| `outputs/duchamp-slot-b-candidate-20261111/boot_b.img` | `545112503a5e9052db709572cc840758619f2b7e27c9aa58c0af2a3924a8f6a8` |
| `outputs/duchamp-slot-b-candidate-20261111/vendor_boot_b.img` | `d1d1887eba4f7b4920fc4292de5cf4e9aa6e7ce474a6b45ffeb4141434743e49` |
| `outputs/duchamp-slot-b-candidate-20261111/ota-init/init_boot-OS1.0.17.0.UNLMIXM.img` | `00476196f020c0e01aa1661ac731970c2e8a5bbbc262ec04627fc9a5b87f2d78` |

The image uses `rd=md0` and a 32 MiB RAM root, and the archived ADT lacks
a UFS node and handoff receiver. Historical firmware expectations are
bootshim `PC=0x40000000` and FDT pointer `0x47c80000`. The payload plan
sets XNU `PC=0x1c1480488` and `x0=0x1c456c000`. The v3 standalone probe
is a separate image. Artifact and profile digest pins are in
`outputs/duchamp-final-bl31-xnu-20261116/artifact-verification.json`.

The three historical B originals in
`outputs/duchamp-slot-b-trial-20261111/backups` match their saved hashes.
The original `boot_b` and `vendor_boot_b` are zero-filled 64 MiB backups
of the historical pre-trial state. Preserve and verify the actual B
pre-attempt baseline before any later maintenance. A current recovery
procedure must use backups for the actual pre-attempt state.

Require a verified Android A recovery set matching the installed build,
including `boot_a`, `vendor_boot_a` and its recovery fragment,
`init_boot_a`, DTBO and AVB metadata. The saved `boot_a`, `vendor_boot_a`,
`dtbo_a`, `vbmeta_a` and `lk_a` match the historical receipt. The available
`init_boot_a.stock-duchamp.img` hashes to
`951235278eb5d4912961abbec156e7350a1648d5ec4e202b47fed0a16305055f`,
while the historical A baseline recorded
`dec6f1f7d785db8f78735fbe18046e16d09ec8dc7655b9ec8f50a2f83cd40cb2`.
Resolve the discrepancy against a read-only current baseline. Current
phone hashes and A recovery boot remain unverified.

## One-boot experiment, pending prerequisites and approval

1. Obtain a verified vendor or authorized independent channel covering
   both boundaries. Provision the trusted profile from exact artifacts
   and approved keys. Confirm the observations and export are passive
   with respect to UFS and its resources, and can be retained through
   host export. Stop preparation if either source is unavailable.
2. Resolve the `init_boot_a` discrepancy and verify A and the recovery
   set. Confirm bootloader Fastboot access over USB using the established
   hardware-key route. Record original slot metadata and B retry state.
   Verify the exact B triplet is already installed and A remains the
   recovery path. Slot selection updates boot metadata even with
   no boot image change. [Android A/B boot control](https://source.android.com/docs/core/ota/ab/ab_implement)
3. After explicit approval, arm the witnesses and use the established
   B selection/boot path for **one** attempt. Expect final BL31 exit,
   bootshim entry, then actual XNU entry, followed by the existing
   RAM-root markers `NOTIFYD CONTROL PASS` and `SYSLOGD CONTROL PASS`.
   Use a 120-second screen/entry deadline for this proposed run,
   confirmed with the platform observer before approval. A photo
   corroborates arrival. Collect both original signed events, incoming
   DTB, entry ADT, owner receipts or explicit absences, and the raw
   witness trace before another boot can replace them.
4. Abort on wrong slot or target, an incomplete event pair, trust or
   hash mismatch, observer loss, unexpected controller activity, an AVB
   screen, reset loop, or deadline expiry. Missing owner evidence leaves
   that state unknown. Keep UFS disabled and preserve the evidence from
   the one attempt rather than repeating it.
5. Return to the original Android A boot selection through the approved
   Fastboot recovery path. Verify Android reached userspace on A and
   record the final metadata. Since the proposal reuses installed B,
   it requires no partition restoration. If Fastboot or A is unavailable,
   stop and use the separately reviewed stock recovery for that build.
   Preserve A, LK, BL31, AVB and shared data throughout.

## Offline verification

| Check | Result |
| --- | --- |
| Host correlator | 44 cases passed, including signature tampering, wrong boot/slot/order, stale profile, substituted artifact or DTB/ADT, missing or mismatched observation, and rejection of signed test scope by the physical-input CLI. Accepted fixtures leave physical UFS unauthorized. |
| Passive and gate regressions | 12 passive entry and 98 handoff-model cases per environment passed in native ASan/UBSan and ARM64 QEMU. The model's UFS trace is empty. Bootshim host, ordinary and probe entry, staging and payload preflight passed. |
| Exact proposed B artifact | The decompressed retained Image reached the XNU framebuffer entry marker in 7 GiB QEMU. The exact embedded payload passed host preflight with 11 segments. |
| Existing full XNU | 11/11 fresh QEMU cases passed with the existing CI 43631086106 kernel. Two read-only boots reached PID 1, and nine blocked cases emitted zero virtual UFS events. |
| Firmware and archived images | Pinned LK/BL31 and reset audits passed. The proposed B triplet and historical B rollback hashes matched. The saved A init-boot discrepancy remains open. |

The workspace directory `outputs/duchamp-final-bl31-xnu-20261116`
contains command receipts, logs, traces and file digests. The physical
experiment was not executed. A supported same-boot producer and the
matching Slot A recovery baseline remain prerequisites.
