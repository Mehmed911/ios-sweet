MT6897 boot platform — active source integration (2026-10-31):
Baseline5834326, duchamp-bootstrap. No phone/USB/ADB/fastboot/partition access.
Captured FDT timer13MHz, virtual PPI11=>INTID27, GIC four-cell interrupt
specifiers; GICD0x0c400000/0x40000, GICR0x0c440000/0x200000.
CPU reg IDs0x000..0x700,4 Cortex-A510 +4 Cortex-A715; use reg, not node names.
PSCI method smc is a saved declaration, not firmware authorization.
New duchamp_gic_boot.h fixes full MPIDR Aff3:Aff0 matching, VLPIS-aware
128/256-KiB redistributor scan, full extent/overlap validation and bounded wake.
One ProcessorSleep clear preserves other bits, then requires both sleep bits
clear; frozen timer/ignored write/failed callbacks cannot loop indefinitely.
No Distributor or ICC ownership policy changes; no SMC or physical provider.
stage-duchamp-gic-boot.py patches only DUCHAMP branch of existing pe_fiq.c,
retains non-Duchamp bodies, rejects changed/partial staging via source receipt.
Mandatory final dxb staging and CI header comparison added.
bb15237 CI41152464883 SUCCESS (intermediate scan/wake version only).
Latest check-v2 PASS:128 native ASan/UBSan and128 ARM64 model checks,
plus4 actual QEMU GICR checks; added PIDR2 validation before TYPER scan.
ELF SHA d83344e72f0180ccc7c9d05e77dce7318171149d275dc4a2e8572e4ccd71f06e.
11 staging guards and18 saved-FDT/profile tests PASS. pe_fiq.c cross-compiles
against real generated XNU headers. Local C++ compile-v2 is BLOCKED by Linux
clang lacking Apple's __builtin_xnu_type_summary/signature, not a compile pass;
Full Apple-toolchain CI41154098870 now SUCCESS at ff841ef7728a717262c00cee96fc163e12aedf8e.
New separate phone/QEMU ADTs derive saved-FDT GIC/timer/CPU facts, preserve
template software identities, omit unknown phone clocks and enable one CPU only.
Public GIC/timer source blobs pinned at kernel_common cf2c2dc91b9e9f016dc25cf095b1fe34cb5dfcb6.
New QEMU-profile baseline FAILED on old f6dfc1e kernel (no BSD/root/PID1);
SweetCPU only matched qcom,kryo470. Added DUCHAMP-only ARM A510/A715/A76
bindings and neutral CPU name; final new-kernel guest tests PASS below.
Clock consumer audit found undefined division with missing bus-frequency.
DUCHAMP-only ratio guards retain unknown clocks as zero and use nonzero
ratio denominators. clock-consumer-v1 executes the real transformed function:
baseline UBSan division-by-zero reproduced; unknown/zero and legacy known
clock cases PASS after change. compile-v3 cross-compiles both pe_fiq.c and
pe_identify_machine.c against generated XNU headers. No synthetic clock added.
654a3c9 CI41153721164 cancelled after superseding it with the clock fix.
Final kernel artifact13024424002 archive SHA d527cafd07e02fcebefcfdb0306cdce7f936fc4a4f432cc1e611e57064375c85;
kernel SHA a26248fa69047a6c2110f7998022d0625e8c617dd900050f098d39ed49a79232.
Verified API archive digest and internal SHA256SUMS; final kernel has ARM
CPU binding/name and bounded-GIC scan/wake markers.
guest-profile-final-v1 reached root/PID1 but FAILED strict decoding:2 glyphs
overlapped the last32-pixel diagnostic band. Corrected ADT sweet-fbcon text
viewport to2680px/83rows, retaining actual1220x2712 canvas/full mapping.
guest-profile-final-v2 PASS:24/24,33.539hostsec,15frames,0unknown glyphs,
defaultclock; HFS+ root,PID1,readonly/error paths,backend/table RAM checks.
Uses qemu-profile-v4 (ARM A76,unknown core/bus/DDR clocks omitted), not phone MMIO.
system-final-v1 PASS:72/72 original Apple service checks+6 wrapper checks,
113 installed hashes,86.640hostsec,defaultclock;unchanged legacy ADT/root.
Final profiles phone SHA efa8ca6254a0534ebe79c0c9a38b12d07b9a468a7bf32ed30c348511553e6101;
QEMU SHA 5ddf0057a50d97be8fc2a08ad88e443ab3460290f6fc532f5f4dbc063562eebe.
tools/test-duchamp-ufs-native.ps1 reproduces strict24 checks on Linux ext4
via Windows UNC, verifies source/fixture/kernel preservation; no /mnt/c VM trace.
research/mt6897-boot/final-verification.json PASS:all report/source/profile
pins,5 saved phone input hashes,user edits unchanged;no remaining QEMU process.
See duchamp/MT6897-BOOT-PLATFORM.md for reproduction and limitations.
VLPIS behavior on the actual phone is not captured or asserted by these tests.
Physical GIC/timer/scheduler/firmware readiness still unverified; no phone image
or test was deployed. Preserve1689 old notes,7 qemu classifier lines and loader edits.
End of MT6897 boot-platform handoff.

Fast system bootstrap — verified local milestone (2026-10-31):
Baseline1dae03f, duchamp-bootstrap. Host/QEMU/RAM only; no phone/USB/partitions.
New tools/test-duchamp-system-boot.py reuses the unchanged proven RAM fixture
with an explicit kernel pin; Windows test-duchamp-system-native.ps1 copies via
UNC and performs all high-frequency VM trace/snapshot/HFS work on Linux ext4.
No Apple executables/libraries modified or added to Git; copied evidence retained.
Kernel remains f6dfc1e CI41147308270, SHA
f86bd430b9fdb58d93c0f38d2009b71a7d1b5f15107ea9656c045c5a2eea99ca.
Reference RAM root89388d378c8d2fc66cf942d3c60647ad0579ebb29df629903a7bad0c44469a21.
research/fast-boot/system-native-unc-v1:72/72 actual service checks+6 wrapper
checks PASS;113 installed hashes;86.819hostsec,17frames,default QEMU clock.
Original launchd PID1/notifyd/cfprefsd/Foundation clients;4 ordered phases,
10 native launchctl calls and daemon/reader restart recovery observed.
Kernel/root/reference/sources unchanged; no complete iOS or physical device claim.
Prior same-root/probe run1691.019s used old kernel/different host workload;
about19.5x historical comparison, not controlled hardware timing/speed guarantee.
Short UFS diagnostics:default20/20 at77.515s;icount0 same fixture20/20 at32.237s;
icount4 backend fixture24/24 at39.414s. Clock selection optional/default unchanged.
Broader /mnt/c experiments interrupted during p9_client_rpc stalls, NOT passes.
User explicitly approved Ubuntu/WSL restart; shutdown/start completed, no old
QEMU processes remain and repo filesystem access recovered. Saved evidence intact.
All4 Python execution/preservation guards+2 native launcher guards/parser PASS.
Linux Python --native-workspace replay after restart:system-native-python-v2
72/72 service checks+6 wrapper checks,113 hashes,86.674sec,default clock PASS.
research/fast-boot/final-verification.json PASS:all5 positive reports/current
source closures,5 saved boot/FDT/firmware hashes,user1689+7 edits preserved;
no QEMU process left. Interrupted experiments retained, not counted as passes.
Docs duchamp/FAST-SYSTEM-BOOT.md; physical GIC/timer/scheduler, firmware/DMA/UFS,
Mali/input and SpringBoard still require separate actual validation/development.
Keep prior1689-line notes tail,7-line qemu classifier edit and loader/user files.
End of fast-system boot handoff.

Bounded UFS waits / saved boot policy — verified milestone (2026-10-31):
Baseline 50f15c39241565cdb4a87921b0fe949af2f8f4d7, duchamp-bootstrap.
No phone/USB/ADB/fastboot/partition access. Existing user changes preserved.
Fixed unbounded frozen-clock UFS waits with a mandatory finite, operation-wide
poll budget. Timeout poisons the host without reset/rebind or DMA reclamation;
deadline versus budget exhaustion is exposed to XNU diagnostics.
research/mt6897-policy/poll-v1/result.json PASS:67 native ASan/UBSan checks
and the same67 on ARM64 in QEMU (register/DMA fixture model).
transport-v1/result.json PASS:142 actual QEMU UFS/qtest host-core checks,
including a frozen timer above4GiB;78 native sanitizer guards also pass.
compile-v1/result.json:both changed C TUs compile with real XNU generated
headers, new timeout-cause core definition resolves the adapter import.
Production core commit f6dfc1e077bd196288d99d2250adfbd0b313e7b0 pushed.
Full XNU CI41147308270 SUCCESS at f6dfc1e; artifact13022331159, archive SHA
e980cee5e4e240e8595320757b6799a5be72375b6512ecf0110ccac431606c91.
Kernel SHA f86bd430b9fdb58d93c0f38d2009b71a7d1b5f15107ea9656c045c5a2eea99ca.
NEW guest-backends-v1/verification.json24/24 and guest-baseline-v1/verification.json
20/20 PASS with this exact kernel; both exit0,81.805/81.815sec,16frames each.
Actual virtual UFS/HFS+ root -> diagnostic PID1 reads/EROFS/heartbeat observed;
no sampled panic,0 unknown glyphs. No RAMDisk; both root images unchanged.
In-kernel backend/table selftest remains RAM models with fw_verified=0/physical=0.
Stopped rootPA0x1c2820000 aligned64KiB and below35bits; pool0x1c2830000/data0x1c2834000.
final-verification.json passes source closures,7 fresh public blobs and5 original
saved image hashes. All user pre-existing1689-line notes/loader/QEMU changes preserved.
Boot-policy tools/docs committed01aa3148328119598bcc6f6ba929469fbadb1b92.
New boot-policy auditor pins7 public files to the saved GKI stamp. audit-v2
finds swiotlb=noforce disables DEFAULT SWIOTLB init, disable_dma32=on disables
that zone, ufshcd_core_init is requested blacklisted. Built-in protected KVM
is only a request, not runtime proof. EXTEND command line needs951/2048 bytes;
saved vendor-boot bootconfig section is empty, bootloader-generated one unknown.
check-v2 PASS:50 native ASan/UBSan +50 ARM64 QEMU checks of3 unchanged Linux
parameter bodies with fixture capabilities; no Linux/pKVM/SWIOTLB initialization.
All9 auditor guards pass (one initial boundary-test expectation corrected).
Fresh public fetch verifies all7 exact Git blobs. Full bootargs never exported.
This refines previous default-bounce assumptions; vendor overrides remain open.
See duchamp/UFS-BOUNDS-POLICY.md. These Linux policies do not authorize XNU DMA.
Physical firmware identity/effects, DMA ownership and effective masks remain
unverified. No physical MT6897 backend enabled by these local tests.
Next: close those actual firmware/DMA evidence gaps before physical UFS use;
do not infer them from Linux policy, source replay, QEMU or a successful CI.
End of bounded-UFS handoff.

Saved-UFS firmware/DMA contract — verified local milestone (2026-10-31):
Baseline cb57481f071b3d94f0a21433e0f56dbc243638d2, duchamp-bootstrap.
No phone, USB, ADB, fastboot, module loading or partition action. Inputs preserved.
New tools audit-duchamp-saved-ufs.py / duchamp_saved_ufs.py verify saved boot-v4,
vendor-boot-v4, captured FDT, LK/preloader and 13 exact public source blobs.
Public fetch-duchamp-contract-sources.py reproduces downloads without replacing
differing files; extracted modules/fragments/images stay outside Git.
boot_a SHA1b972f4f1c98428f2fca1e7c1c8cf463e0122a70a290e482be3230c7838e3e12;
vendor_boot_a SHAd1d1887eba4f7b4920fc4292de5cf4e9aa6e7ce474a6b45ffeb4141434743e49.
Captured release6.1.57-android14-11-gcf2c2dc91b9e-ab11782407 resolves to public
GKI cf2c2dc91b9e9f016dc25cf095b1fe34cb5dfcb6. Stamp correlation only, not
byte-identical rebuild/current running state. Modules say maybe-dirty, no srcversion.
Saved IKCONFIG: IOMMU_DMA/default DMA strict=y, passthrough=n, SWIOTLB=y,
XEN=n, standard ARM_SMMU/ARM_SMMU_V3=n, ARM64 4K/PA48. modules.load requests
all six inspected UFS/PHY/IOMMU modules; load intent is not runtime evidence.
UFS module SHA7043e1109b4c356a914fdc92ffbe463c0c43cb27342f6ccce1517a2086b02493.
Binary ufshcd_init has 64->32 streaming-mask fallback; coherent setter's return
is ignored. Captured live HCCAP/effective post-quirk caps/masks are still absent.
No UFS iommus/iommu-map on saved ancestry; /soc DMA window remains64GiB.
Candidate: direct DMA, possibly SWIOTLB; inherited dma_ops/fwspec/vendor/secure
overrides still need proof. NULL IOMMU does not clear inherited dma_ops.
ARM_V7S display-table OAS35 is NOT the UFS mask or its IOMMU route.
Saved SMC fragments confirm client x0=c2000276, selector512(op0/1), selector8
(off/on,PRE/POST). Actual BL31 effects/return semantics remain unverified.
LK/preloader have BL31 loader/reservation strings; these are not monitor identity.
research/mt6897-contract/audit-v3/result.json: audit complete, all physical flags false.
check-v4/result.json PASS, exit0:216 source ASan/UBSan checks; same216 on ARM64;
244 saved DMA instruction checks +96 saved SMC instruction/policy checks.
12 actual SMC calls to a QEMU-only EL3 monitor, not installed MT6897 firmware.
Fifteen unchanged source function bodies; allocations/kernel DMA/SWIOTLB/cache
callbacks are fixture models. Saved .text fragments have relocated external
calls/exit branches and synthetic frames. Original MMIO/registration is not run.
guards-v2.log:8 guard tests PASS. Final ELF SHA256
7663c6219f988f3af04fbcf0d70df81cbc6385a6e93c0c170e6aa04d7146d1ea.
QEMU10.2.1 Debian1:10.2.1+ds-1ubuntu3.3. Sources/module hashes unchanged.
No production XNU backend modified; no new full-kernel CI/boot in this milestone.
Earlier XNU24/20 results belong to the previous d51e7db kernel, not this fixture.
See duchamp/SAVED-UFS-CONTRACT.md for exact scope, pins, replays and remaining gaps.
Next physical authorization needs matched monitor/build/effect and secure ownership
plus runtime ops/fwspec/domain/SWIOTLB, HCCAP and both effective masks. None can
be inferred from the saved files/QEMU results, so physical providers stay closed.
End of saved-UFS contract handoff.

XNU backend/table integration — active work (2026-10-31):
Baseline 116fef581bb1d756d82604029309580f56ab4b8b, duchamp-bootstrap.
No phone/USB/ADB/fastboot/partition commands. Preserve all existing files.
New offline 4-KiB ARM_V7S table builder: IAS34/OAS35, NS/NO_PERMS/MTK_EXT/
MTK_TTBR_EXT, finite caller-owned L2 pool, whole-operation preflight,
nonidentity CPU/physical addresses, sealed immutable tables and cache-sync
failure poisoning. No live unmap or UFS stream-routing assumption.
Pinned Android source commit 498f91c17b0822a09aede17d26a63bf8c6813725,
drivers/iommu/io-pgtable-arm-v7s.c blob08ec39111e608f6405a5777889d6ac2eda561506.
research/mt6897-xnu/tables-v2/result.json PASS:11476 ASan/UBSan checks
against six unchanged upstream encoding/decode/install function bodies,
with allocator/cache/atomic fixture helpers; no hardware table walk.
tables-v1 extractor regex failed before any C test; failure retained.
research/mt6897-xnu/compile-v3:9 C TUs compiled against real generated XNU
headers; staging-v1 has6 checks, idempotence/change rejection and all imports
resolved against the prior kernel plus the new objects. All8 staging unit
tests pass, including changed-file/partial-stage rejection and ownership.

tools/stage-duchamp-qemu-backends.py stages eight cores and one XNU adapter.
Only rd=qufs0 calls the new adapter; boot argument sweet-qemu-backends=1 and
exact QEMU firmware/ADT+Cortex-A76 gate required. No flag returns without work.
The opt-in kernel selftest uses real XNU contiguous allocation, PA validation,
cache cleaning, clocks, mutexes and read-only /dev/mbtest diagnostic output.
Peripheral callbacks are private RAM models only. Actual UFS remains QEMU PCI
read-only through the established driver. Unknown firmware contract and UFS
IOMMU selection are required to fail closed. No physical SMC is wired.
Integration 0a947b6: run41140465715 built successfully, artifact13019651368,
ZIP SHA d82a04411baafd27230be3fabc45f15726271da2449e2cd32fea401ddebc811b;
kernel fd75b80bfcef016eb37cd52b285be3b577bbff018911b517f2fb928883baf2f3.
guest-ci107-v1 FAILED before tables marker, EIO5. Read-only monitor replay
guest-ci107-diagnostic confirmed root VA0xfffffe78672a0000, physical
PA0x1c281c000 (low16bits0xc000), while table context remained fresh.
Source review found kmem_alloc_contig's VA mask does not constrain physical
alignment. Follow-up explicitly supplies a page-number mask and a 35-bit PA
limit, with PA alignment/range readback checks. Compile-v3 PASS for all9 TUs.
Fix d51e7db compiled all9 TUs locally. Parallel CI41142122133 on temporary
branch codex/mt6897-xnu-tables-d51e7db SUCCEEDED (avoided cancelling CI107).
Active branch remains duchamp-bootstrap; corrected guest results follow.
Artifact13019712695 ZIP SHA256
4dfb5b7194e18c3e2f4185e91ed5457a44c071cf09ede0eaf53c609367a8ac80 verified.
Extracted kernel matches SHA256SUMS:
fdbbca3def13fddcbef77d01504aeaabe41bfb3a7b7df94b4d7fd03fd015b92d.
guest-backends-v1/verification.json PASS24/24, exit0, 81.580s,16frames.
guest-baseline-v1/verification.json PASS20/20, exit0, 81.570s,16frames.
All backend checkpoint groups observed. PID1 exact /dev/mbtest receipt, EOF,
EROFS, root identity, raw UFS/offset/EFAULT/HFS bytes and heartbeat passed.
Read-only stopped-guest physical monitor confirmed root PA0x1c2830000,
pool PA0x1c2840000, data PA0x1c2844000; root64KiB alignment/range PASS.
Both runs zero unknown glyphs/no observed panic/unchanged images and sources,
read-only/no RAMDisk. Sampling limits and existing local runner classifier
are recorded in duchamp/XNU-TABLES-QEMU.md. All old failures retained.
Offline contract-v2 audit matched three exact GKI Git blobs, captured DTB and
saved LK/preloader hashes. UFS direct/bus-window DMA is a conditional source
candidate only; no installed BL31 contract or actual DMA route verified.
Three deliberately mutated source copies were refused by exact blob pins.
Next: resolve matching installed GKI/runtime fwspec/vendor overrides, actual
controller DMA mask/cache/ownership and matched BL31 effect semantics before
binding physical providers. No display/MDP IOMMU assignment to UFS.
End of active XNU-table handoff.

MT6897 PMIF/PMIC, SMC and partial IOMMU register backends — local milestone (2026-10-31):
Baseline f323908cbe1173c6241cf6b3ff47761d96327559; branch duchamp-bootstrap.
No phone/USB/ADB/fastboot/partition command. All previous files preserved.
New code is NOT linked into XNU or bound to phone MMIO; physical UFS remains
disabled. No installed firmware compatibility or physical regulator/IOMMU test.

duchamp/drivers/mt6897_pmif.c: matched mt6xxx SWINF2 command/data programmer,
1-4 bytes, SIDs4/8 only, 16-bit register bounds, explicit little endian,
initialized controller and route mask0 guard, finite idle/valid polling,
no stolen inherited reply, no auto retry after a transport fault.
PMIF idle is NOT PMIC ACK/NACK proof; physical error IRQ handling is absent.
mt6897_pmic.c: VEMC SID4 exact voltage table/trap-selected nibble, TMA
unlock/write/relock, factory trim preserved, enable bit only/680us delay;
SID8 vbuck3 uses matched mt6315_8-regulator ABI, selector and SET enable,
256us delay. No disable/global shutdown/mode/guessed voltage target.
Matched n_voltages=0xbf means selector191/1193750uV refused, even though
DTB and linear endpoint include it; max accepted selector190/1187500uV.
Relock is attempted even after a partial failure. Poisoned bus may prevent
it: failure remains latched, not claimed recovered. Readback is programmed
bits only, not actual measured rail voltage or PHY readiness.

mt6897_smc.S: raw SMCCC SMC#0, x0-x7 input/x0-x3 output, no default binding.
mt6897_firmware.c: whitelisted UFS requests, per-call authorization and
mandatory matched-firmware reply verification; unknown zero results refused.
Separate reference ATF f3083e2e6c508d58f9bce1b2fce5eeb0903a4c6d UFS handler
returns zero when CONFIG_MTK_MTCMOS handling is compiled out. This is NOT
installed MT6897 firmware identity. Existing LK evidence also does not prove
the installed UFS SiP effect/return contract.

mt6897_iommu.c: actual TTBR write/readback and GEN2 full/range TLB register
programming for source-defined display/MDP banks, 34-bit address encoding,
fresh-status and TLB_SYNC guards, finite CPE wait, failures pin state/tables.
Requires a preconfigured powered exclusive domain and externally built/
synchronized encoded ARM_V7S/MTK_TTBR_EXT tables. Table allocation/encoding,
SMI/stream routing, shared-domain coordination and full HW init are NOT done.
UFS client unconditionally refused before any authorization or register I/O.
No documented UFS-to-IOMMU route was found in source/inspected DTB ancestry.

research/mt6897-backends/check-v2/result.json: PASS, exit0:
105 PMIF +193 PMIC +39 firmware +87 IOMMU =424 native ASan/UBSan model checks.
SAME424 checks passed during actual ARM64 CPU execution of models in QEMU.
12 additional checks of TWO actual SMC calls from NS EL1 into a QEMU EL3 test
monitor passed, then MT6897 ARM64 MODEL PASS and semihost exit0.
This is no MT6897 peripheral/secure-firmware or XNU execution.
Freestanding ARM64 compilation of four C backends +raw SMC object passed;
all five normal-RAM objects have no undefined imports. Secure fixture uses
strict alignment, explicit byte-wise runtime, MMU/cache off.
ELF SHA256 8dba37ef2d3ca4c44c559623fe86be0346b6e79b048e36ffca28fea763fd607d.
Seven source files matched exact vendor Git blobs at commit
a805f95d61dbf0b2959c9262acc626893114321d; source catalog
duchamp/drivers/mt6897-backend-sources.json. Sources stay ignored.
Saved DTB SHA256 9c49589f70044127be8941a9ea5537977f440ccd5ac15cfd24e120c8a1181d29
matched before resolving rails/PMIC IDs/SPMI offsets/IOMMU nodes.
All11 selected production/test input hashes unchanged during run and staging.
QEMU10.2.1 Debian1:10.2.1+ds-1ubuntu3.3; version log and exact commands local.
check-v1 is an earlier passing subset; check-v2 adds protected-write
enforcement and every fallible PMIF-write/PMIC transaction point.
No new XNU kernel/CI or phone image was built in this milestone.
Reference/replay: duchamp/MT6897-BACKENDS.md, tools/test-mt6897-backends.py.

Next: match installed firmware identity/SiP semantics/effects and delegated PHY
ownership; supply trusted XNU MMIO/cache/locking and regulator-vote/resource
adapters, PMIF error IRQ handling and controller quiescence/recovery.
A full IOMMU driver still needs matching table builder and actual client
routing; do not wire UFS to display/MDP/APU IOMMU based on guessed stream IDs.
End of MT6897 backend handoff.

MT6897 power/PHY policy and DMA ownership — verified local milestone (2026-10-31):
Baseline a15c2e59f212e530c600201034db6450eaa5a336; branch duchamp-bootstrap.
Source-pinned subset: duchamp/drivers/mt6897_ufs_platform.c/.h and
mt6897_ufs_dma.c/.h. Neither linked into XNU nor bound to physical callbacks.
No phone/USB/ADB/fastboot/boot-partition commands; old files preserved.
Captured DTB SHA256 9c49589f70044127be8941a9ea5537977f440ccd5ac15cfd24e120c8a1181d29.
The PHY has mphy-ver=1: vendor phy_power_on/off returns without old ver=0
register programming. The new subset deliberately has no PHY MMIO callbacks.
Captured policy: RTFF enabled, no VA09 flag, IDs UniPro0/crypto1/HCI2.
Implements guarded SiP request encoding (no SMC instruction/provider),
RTFF restore/on, reference-clock PRE/request/ACK/32us/POST, bounded 3000us
and 32-poll timeout, explicit source-defined timeout notification, host-reset
order with 100us delay and captured masked-register descriptors.
Prerequisites require exclusive ownership, stable rails and all correct
parent/leaf clocks, matched SiP/PHY firmware, link off and DMA quiescence.
These are caller attestations, NOT firmware verification or physical readiness.
DMA API separates CPU VA/PA/device IOVA, refuses unknown routing, validates
alignment/aperture/overflow/mask, synchronizes private full-pool ownership
through callbacks, refuses completion/unmap while active and pins poisoned
allocations. No IOMMU table/stream-ID or bypass/coherency guess.
Saved /soc dma-ranges declares a zero-to-zero 64-GiB window; no inspected
UFS ancestor iommus/iommu-map/dma-coherent. Actual route/mask stays unknown.

research/mt6897-platform/check-v6/result.json: PASS, exit 0.
176 power-sequence + 149 DMA-ownership checks under native ASan/UBSan.
SAME 325 checks passed during actual ARM64 QEMU CPU execution of models;
MT6897 ARM64 MODEL PASS + semihost exit 0. No MediaTek peripheral or XNU run.
ARM model MMU/cache off, strict-alignment build, explicit byte-wise runtime.
Normal-RAM production objects compiled freestanding ARM64, general registers
only, no undefined imports. They use default alignment flags separately.
ARM model ELF SHA256 3788be0f0ab3f952abf38de62f00bfbb75714a5a9b262f37518a146bead8d378.
Six downloaded vendor files verified against exact upstream Git blob IDs.
Pinned vendor a805f95d61dbf0b2959c9262acc626893114321d; Linux v6.1 commit
830b3c68c1fb1e9176028d02ef86f3cf76aa2476. Source catalog in
duchamp/drivers/mt6897-platform-sources.json; sources/dumps stay ignored.
Report includes source/object hashes, selected DTB facts and upstream receipts.
Test sources still match report hashes at staging time.

Preserved failures: check-v3 timeout; check-v4 diagnosed unaligned model
pbarrier trace-store (ESR 0x96000061, ELR 0x4020486c, FAR 0x40246fcc) with
MMU-off memory attributes. Fixture now compiles strict-alignment code.
check-v5 exposed memcpy lowering with strict-alignment code; final harness
checks normal-RAM standalone objects separately and supplies an explicit
runtime for its ARM fixture. These failures are not counted as passes.
Reference/replay: duchamp/MT6897-PLATFORM.md, tools/test-mt6897-platform.py.
No new full XNU CI/kernel/phone image was required or built in this milestone.
Physical PMIC/topckgen/masked-reset providers, matched SiP return/authorization,
delegated PHY ownership, effective DMA mask/domain/stream/cache and hardware
quiescence/recovery remain unimplemented/unverified. MT6897 root stays disabled.
Next: establish those provider contracts before physical transport integration;
GPU/Mali/CSF remains separate. Do not turn model success into a phone-ready claim.
End of MT6897 platform handoff.

# DUCHAMP update — 2026-10-22

QEMU UFS / XNU integration — verified milestone (2026-10-31):
Baseline HEAD 62c91492b0bda5a764f202349b5e2141a5ee48ec.
Source adapter duchamp/xnu/qemu_ufs.c stages with the unchanged portable core
via tools/stage-duchamp-qemu-ufs.py after the existing BSD checkpoints.
Opt-in root qufs0; separate virtual firmware/ADT profile, Cortex-A76 gate,
PCI ECAM 0x3f000000/slot4, BAR 0x10000000; physical MT6897 remains unsupported.
BSD strategy has bounds, read-only policy, serialized bounce reads, residuals
and biodone completion. DMA allocation is permanent; callbacks clean/flush
physical cache lines and preserve poisoned/in-flight memory ownership.
Local Actions-104-generated-header compilation passed for both C TUs;
all their imports resolve against the baseline kernel/each other.
Local IOKit C++ compile cannot validate Apple XNU compiler builtins on Linux;
its failure is retained in research/xnu-ufs/compile/IOKitBSDInit.log.
First full Xcode CI succeeded, but guest-v1 is a FAILED runtime test: UFS
root mounted and PID1 entered, then raw character read panicked at memmove
+0x48 / qu_strategy+0x1c0, FAR=user stack. physio/buf_map returned a user VA
that plain memcpy cannot access with PAN enabled. Its failed outputs remain.
Fix now uses uiomove from a private CPU buffer outside the controller lock;
B_PHYS strategy requests are rejected. Both C TUs recompiled successfully.
Full Xcode fix CI succeeded; exact new kernel passed both guest tests below.
CI source commit 51bd2ca39c97d441df912a9a12e31cf24ea7a601; run 41131664525.
PAN fix commit 9a10068375fa1320d802e3d30fe951f8b1a07f4f; run 41133993461.
Kernel artifact ID 13015622163, ZIP SHA256
cb11ed54942844c14f12346a1c3c8121d90777a9038896442e4c1be5181c668f,
matched GitHub digest. research/xnu-ufs/kernel-fix-ci/kernel.development.sweet
SHA256 c40bebddeaea04c11ca8f4812de8160490ba8933ee68bc63a9481ed257d82109,
matched artifact SHA256SUMS. No kernel stubs/rebuild after download.
research/xnu-ufs/guest-v2/verification.json: PASS 20/20, exit 0,
80.493 host seconds, 16 sampled frames. Real XNU HFS+ mount/rootvnode via
qufs0 (no ADT RAMDisk), PID1, root st_dev matches qufs0 st_rdev with valid
inode types, raw header and offset reads, invalid user pointer returns
EFAULT without panic, write-open returns EROFS, exact 1024 file bytes,
and later heartbeat. Zero unknown glyphs/no observed panic. Read-only host
image unchanged, kernel pin and all five test-source hashes preserved.
Early QUFS printf/IOLog is not framebuffer-visible; stat64 device identity
and no-RAMDisk gates establish the root source. The legacy marker
QEMU RAM ROOT MOUNTED alone does not establish its source.
Fixture research/xnu-ufs/fixture-v4 root SHA256
5f4f6b5c5a7947dcab9e2c56f668b719053b89a5f07dc256f255e11fdbec3440.
research/xnu-ufs/md0-regression-v1/verification.json: PASS 10/10, exit 0,
89.932 host seconds, 18 sampled frames. SAME new kernel, old RAM root/static
PID1 and later heartbeat, no UFS-image option, zero unknown glyphs/no observed
panic, kernel/root unchanged. Base HFS+ SHA256
e5b5c1b68c00db65ae31d8d29baef6ab88c8131e29940d8ce7b810536726414a.
These sampled short boots are not long-term stress or phone tests.
The existing 7-line uncommitted qemu-sweet MEMORY READY diagnostic remains;
its classification branch was not exercised. Exact working hashes are in report.
The new qu_read/qu_error bodies passed 18 ASan/UBSan control-flow model checks
in research/xnu-ufs/uio-model-v1. This is not XNU VM/PAN execution proof.
Virtual-UFS fixture prepared with no fallback ADT RAMDisk;
tools/test-qemu-ufs-profile.py passed 19 rejection tests.
Six MT6897 AO/PDN clock leaves implemented separately, not linked to a phone
backend; 123 ASan/UBSan model checks and ARM64 compile passed in
research/xnu-ufs/clocks-v2, including captured-FDT ID/provider matching.
Baseline tree ZIP SHA256 b2cf5bc24205c978858eb8667d7a9c65dfe66a87d1d56399efda9c34c76da333.
Native WSL build cache path is in research/xnu-ufs/base104-tree-path.txt.
No phone/USB/UFS hardware/boot-partition command. Preserve all previous files.
Reference/replay: duchamp/QEMU-UFS-XNU.md; scripts refuse output overwrite.
No complete physical power/PHY/reset/SiP, topckgen mux, DMA/IOMMU backend or
Mali CSF acceleration. Six model-tested clock leaves do not power on UFS.
Next: match firmware ownership/SiP/PHY/reset and DMA mapping/cache contracts
before connecting physical MT6897 transport; identify selected Mali DDK/CSF
firmware and design MMU/queue/fence/power backend independently of Adreno.
End of active XNU-UFS handoff.

Portable storage/software-graphics cores (2026-10-31; this commit):
Baseline HEAD 6b93481421300eeebc124813a2998bed140fda5f; branch duchamp-bootstrap.
No phone/USB/UFS hardware or boot-partition command. No new XNU build or CI.

Implemented independent portable C UFSHCI read transport and raw 32-bit
software framebuffer fill/blit, with offline hardware-dependency extraction.
These cores are NOT yet linked into XNU. MT6897 root selection stays
kIOReturnUnsupported; there is no physical MediaTek power/DMA/MMIO backend.
No complete iOS, accelerated GPU, DSI scanout or phone-UFS claim.

Actual tests: research/mt6897-drivers/core-v6/result.json, exit 0,
108/108 checks. Real QEMU UFS emulation/DMA via qtest, guest CPU stopped.
Three cases: generated 16-MiB read-only disk at DMA 0x100000 and
0x100100000, then existing 32-MiB HFS+ root at above-4GB DMA. Five exact
byte-comparison reads per case, including 256 KiB and the last block.
All images unchanged; HFS+ source SHA256
491aa78408c423c50e8b59644e416e94b643ed3eb119158d52684af4176c8b3f.
This is transport evidence, not an XNU UFS mount. Controller version 0x400.
Injected task-tag and completion-mask faults are separately identified.
No arbitrary CDB/SCSI WRITE API; only NOP, fDeviceInit queries and SCSI reads.
Cold-device UNIT ATTENTION retry is bounded to three valid sense responses.
Timeout/error poisons the host; API blocks rebind/resubmit. DMA storage stays
reserved until a real platform proves quiescence; no automatic reset/abort.
Readiness flag is a caller precondition, not proof of firmware compatibility.

Same run: 78 native guard checks under ASan/UBSan, exit 0; freestanding
AArch64 compile of both C cores passed, llvm-nm undefined imports empty.
research/mt6897-drivers/framebuffer-arm-v2/result.json: 3/3 checks, exit 0.
Actual ARM64 raster code ran at EL1, MMU/cache off, in ordinary guest RAM
at Duchamp framebuffer address/geometry (1220x2712, stride 4992).
Every pixel, row padding and outside guard matched; capture SHA256
2be9fd76292a0edafb0fc52d54f2d3bf029911cfb6674554659d9a55df3ec3ac.
No hardware GPU, framebuffer mapping/cache-on, vsync or scanout test.
tools/test-inspect-duchamp-hardware.py: 20 tests, exit 0; actual phone DTB
inspection succeeded; captured DTB SHA256
9c49589f70044127be8941a9ea5537977f440ccd5ac15cfd24e120c8a1181d29.

DTB facts: UFS 0x112b0000+0x3000, compatible mediatek,mt8183-ufshci;
PHY 0x112a0000+0x10000; 12 named clocks, 3 resets, 9 four-cell IRQ tuples;
Mali 0x13000000+0x480000, five named IRQs and memory-provider references.
Absent iommus/dma-coherent is NOT proof of bypass/coherency. The inspector
resolves variable provider cells and bus translations without bootargs/serials.
Selected report research/mt6897-drivers/hardware-v1.json remains local.

Read pinned MediaTek device modules a805f95d61dbf0b2959c9262acc626893114321d
and vendor modules 6bceb1b8e3444dd6caf80ad7470c9e57bbdcd1ab. UFS variant
needs PHY, clock/reset, power and SiP/RTFF-MTCMOS sequencing. GPU source
has CSF/firmware/MMU requirements; installed phone DDK/firmware ABI remains
unidentified. Independent implementations only; external sources stay ignored.
QEMU reference source 7f36b1fbeb1f6f070cd5f8eddb3edbcafac15440 differs
from tested installed QEMU 10.2.1; no firmware behavior equivalence claim.

Failures retained: core-v1 wrong test PCI BAR-width assumption; core-v2
unhandled cold UNIT ATTENTION. ARM-v1 overlapped the default QEMU DTB;
ARM-v2 relocates its ELF. Later passing runs have exact input/object hashes.
Replay/scope/pinned source links: duchamp/DRIVER-CORES.md.
Next concrete work: XNU read/completion adapter in separate QEMU storage
configuration while retaining md0; separately derive the MT6897 PHY/clock/
reset/SiP and DMA/cache ownership sequence from matching firmware evidence.
Physical backend stays disabled; Mali needs its own CSF/MMU/fence/power ABI.
All pre-existing edits, untracked trees and 1689 old NOTES additions preserved.

Grouped live-preferences/restart milestone (2026-10-30; this commit):
Baseline HEAD 8e7565855a862b5018c337d032f28dddedcd2e90. QEMU/RAM only.
No phone, USB, UFS or boot-partition command; no new kernel build or CI run.

Successful run: work/launchctl-cfprefs-batch-v2, exit 0, 72/72 checks.
All 113 file hashes matched; unchanged Actions 104 kernel and original
Apple launchd/xpcproxy/cfprefsd/notifyd/frameworks. Runtime audit: 92 binaries.
1691.019 host seconds, 70 sampled frames, no visible panic,
zero unknown glyphs, stopped on the second-heartbeat text (>=2 beats).
Writer PID 7, first reader1 PID 5, new reader1 PID 16,
reader2 PID 6. Original cfprefsd changed from PID 9 to 13,
runs=2. Original notifyd stayed PID 8, runs=1.
All ten real CLI calls exited 0. Writer and reader2 runs=1, reader1 runs=2,
all normal exits=0 and reaped; old daemon was forcibly restarted, not graceful.

Four ordered phases: set/read generation 1; live update to generation 2;
after daemon restart plus orderly stop/restart of reader1, read generation 2
without setters; then write/read generation 3 through the existing writer.
Reader2 remained alive across all four phases. Both clients acknowledged
every applicable phase. All four probe instances entered an empty chroot
after independent-domain warmup; direct preference paths stayed ENOENT.
Saved final plist exactly device=DUCHAMP-RECOVERED, integer soc=6897,
boolean enabled=true, integer generation=3. Chroot directory stayed empty.
Signals were explicit program posts through native notifyd after synchronize;
notification state/control files carried only step numbers, never values.
No automatic NSUserDefaultsDidChangeNotification or FSEvents delivery claim.

First attempt work/launchctl-cfprefs-batch remains a failure: two live-update
phases passed, then the test checked PID 13 while it was still xpcproxy.
Bounded executable-transition waiting fixes this harness race. Its 113 file
hashes matched; intermediate phase2.json proves actual saved false/generation 2.
Sources/headers are frozen in each run's test-sources/ with input hashes.
Basic writer, reader and controller rebuilt byte-identically to v5 in
work/cfprefs-basic-build-check-v2/comparison.json; no baseline VM rerun.

Parallel review: hakios-metal commit 54a46fadec5bd9684ebd77f3a0834c84b5eb01a6.
make test CXX=clang++ passed 21 tests, 0 failed checks on Linux FakeGpu.
Checkout clean, MIT, no iOS build or device GPU run. Parser/state semantics
are useful references; actual transport/PM4 are Adreno-specific and the
repo's shader pipeline is unfinished. See HAKIOS-METAL-REUSE.md.

Initial root SHA256 89388d378c8d2fc66cf942d3c60647ad0579ebb29df629903a7bad0c44469a21.
Payload 8c1c249fd0940b03bfca7ac7781d721e328230a680bb59427e93545177b08635.
Saved root 03532c1d4e832f36ca6d3f992e1df619239afb364aa4b3ff5c9af9723658ed58.
Full report: work/launchctl-cfprefs-batch-v2/run/verification.json; guest/ logs.
Docs: duchamp/CFPREFS-BATCH-QEMU.md and HAKIOS-METAL-REUSE.md.
Remaining: MediaTek platform/storage/graphics contracts and device tests.
MT6897 root selection still returns kIOReturnUnsupported; RAM tests prove
no UFS driver compatibility, phone full-boot or complete iOS readiness.
All earlier local edits and 1689 old NOTES lines remain unstaged.

Original cfprefsd / isolated NSUserDefaults milestone (2026-10-30; this commit):
QEMU/RAM only. Baseline HEAD bea1e346cbd0ec005a5fc63dbd05cb504d90916e.
No phone, USB, UFS, fastboot or boot partition command was run.
No new kernel build or Actions run. The Actions 104 kernel is unchanged.

Successful run: work/launchctl-cfprefs-v5, exit 0, 49/49 checks passed.
112 file hashes matched: 110 installed files plus original launchd/xpcproxy.
978.85 host seconds, 75 sampled frames, zero unknown glyphs, no visible panic;
stopped on the second success heartbeat before the 1500-second limit.
Observer PID 3; writer PID 5; separate reader runs PIDs 12 and 15.
Original regular cfprefsd PID 7 stayed running, runs=1, same PID before/after.
The separate system-session job stayed unstarted, runs=0; not exercised.
Ten real Procursus launchctl invocations exited 0. All three probes exited 0,
were reaped and stayed stopped for two heartbeats. Daemon shutdown not tested.

Every probe warms only org.sweet.qemu.runtime-warmup (unset key, no setters),
then enters an empty chroot and changes cwd to /. The actual fixture suite
org.sweet.qemu.preferences is first accessed after isolation. Direct creation
and later direct reading at all three standard preferences paths return ENOENT.
Writer sets device=DUCHAMP, integer soc=6897, boolean enabled=true. Both fresh
isolated readers obtain all three values without setters. The saved real-root
plist contains exactly those values/types. The saved chroot directory is empty.
Regular outside descriptors carry only console/log/PID/release data, not values.
No injected library, fabricated XPC reply or per-message trace is claimed.

Pinned original cfprefsd: 05e6c217284c2e4f669243fe24296f3ba9abb53a750c9d3860348b0b43c978e2.
Runtime: research/cfprefs-runtime-20F66-v2/runtime-root, 92 audited binaries,
107016192 bytes plus seven existing Foundation resources. Apple files local only.
The first 85-file image crashed: CF dlopen of MobileCoreServices was missing.
Debug PC=0/LR=0x100e22fd0 matched CF file offset 0xfafd0 (FSEventStreamCreate
indirect call). Adding the original MobileCoreServices/CoreServices closure
fixed this daemon crash. See duchamp/CFPREFS-QEMU.md for pins and exact replay.
Attempts v1-v4 remain preserved and are failures, not successes. Interpose
hooks never ran; that method was removed. Chroot-before-runtime-init also
crashed; independent-domain warmup before chroot is verified in v5.
The later chroot failure was FAR=8/nonzero ELR; its exact function is unknown.
The periodic-frame debug observer caught a normal pause, not a null fault.

Root SHA256: 14dde88259e13d1f5c352d7eee4ec1c7c02afd74305180626db54e119f86abba.
Payload: 33579779ba49f0fb307bf9a0e7e5eee47c6f0fc7f70aec58f58234be1f399f68.
Saved root: a648ed135606d03c51dcc1f838ce0310d936ea95b5c72ab78eabdac1bc2173f7.
Full report: work/launchctl-cfprefs-v5/run/verification.json; guest logs in guest/.
Next: live preference updates/notification invalidation between clients.
FSEvents change delivery, reboot persistence, sandboxed app domains, UI and
MT6897 hardware support are outside this test. No complete iOS claim.
Pre-existing unrelated local edits and 1689 added NOTES lines stay unstaged.

Original notifyd integration milestone (2026-10-30, QEMU/RAM only; this commit):
Original iOS notifyd now runs beside original syslogd, with two-process
notification state/post/cancel and notifyd-controlled ASL remote filters.
Baseline HEAD: 263e74fdd5d061528c2d5d9e75bf1799f9dd89c4.
No phone, USB, UFS or boot partition command was run.

Successful run: work/launchctl-notifyd-v3, exit 0, 74/74 checks passed.
51 installed file hashes and original launchd/xpcproxy/syslogd/notifyd
hashes matched. 536.613 host seconds, 42 sampled frames, zero unknown
glyphs, no visible panic. Stopped on second heartbeat before 1500 sec.
Observer PID 3, syslogd PID 4, probes PIDs 5/6, notifyd PID 7.
All six real CLI print processes exited 0. Both daemon before/after
prints matched: same PID, running, runs=1. Both probes returned 0,
were reaped, runs=1, no restart through two heartbeats. Both daemons
were alive at the stopped guest snapshot; graceful shutdown not tested.

Both probes registered plain IPC tokens for the same non-self name.
Initial state=0, initial changed=1 then quiet=0 were proven. Probe 1 set
and posted 0x1020304050607001; both probes received the exact state.
Probe 1 cancelled its check token (valid=0/check status=2), then set
and posted 0x1020304050607002. Only probe 2 received it; the cancelled
token stayed invalid. Remaining tokens were cancelled. The synchronization
files carried only done tokens, not notification state. Daemon debug
confirmed the name and cancellation calls; the real resolved name_id
was 1, distinct from the internal IPC-version name.

The observer set com.apple.system.syslog.master to 0x300ff, read it back,
then posted com.apple.asl.remote. ASL probes used options 0x20000000
(NO_REMOTE clear, SHIM_NO_TRACE retained). All six runtime evaluations
were 0x00230005 with TUNNEL set, and six exact raw records reached the
original syslogd file with expected root sender identities. The master
state was restored to zero and its token cancelled. Modern os_log/logd
and arbitrary credential-forgery behavior were not tested.

Native source: research/notifyd-20F66/apple-extracted, selected from
20F66 system-image member 096-04088-077.dmg with existing APFS range-cache
helper/7z. Extraction exit 0: 2 files / 129501 bytes. notifyd is 128704
bytes, plain arm64, iOS 16.5, libSystem/libbsm, dyld. Original job 797 bytes,
MachServices com.apple.system.notification_center and PublishesEvents
com.apple.notifyd.matching retained in the copied job. Test adds root/
System, RunAtLoad=true/KeepAlive=false and -d/-log_file/-shm_pages 0.
Original executable/library bytes are unchanged. Partial APFS cache is
not a complete-image digest or independent Apple signature verification.

Actual binary LC_SOURCE_VERSION/library PROJECT string identify 312.
Matched Apple Libnotify-312 source commit:
885677be0379101ccf37b46f8da81dbc17d6d301 (not exact build equivalence).
The first two attempts, work/launchctl-notifyd and -v2, FAILED after
298.05 and 297.615 sec. First combined assertion hid the native result;
the second separately logged registration 0/token 2 and get_state 0 with
0x0000000700000003. Server log showed get_state_2 name_id=0.
Matched 312 source explains zero-page register_check delegates to plain
without filling name_id, leaving zero; the client then reads IPC version
(PID<<32|3). Final fixture uses notify_register_plain/NID_UNSET, preserving
the exact-state assertions. No binary patch and no claim register_check/
get_state works with zero shared pages. Failure diagnostics sync before
FAIL to preserve newly created HFS entries; first attempt had missing
new log entries despite visible console execution. All attempts retained.

Runtime: research/notifyd-runtime-20F66-v2/runtime-root.
42 binaries / 11006176 bytes, no missing strong dependencies.
Replay: tools/test-sweet-launchctl.sh with original Actions 104 kernel,
qemu-multiproc.adt, launchd-final/root.hfs, new runtime, HFS tool, fresh
output, 1500 and notifyd. Details: duchamp/NOTIFYD-QEMU.md.
Report: work/launchctl-notifyd-v3/run/verification.json; raw files in guest/.
Old syslogd saved guest recheck passed 43/43 with final verifier:
work/syslogd-notify-final-recheck.json; original report preserved.
10 observer modes/probe compile checks, Python/shell checks passed.
No kernel change or new CI. Pre-existing dirty files/NOTES edits preserved.

SHA-256:
notifyd 819c8ec6b3bee5cd2f1dcbe0b2b698418c411b4c126f2f97cbdae932c1972907
notifyd original plist 627b24feb59a493a50f488bc62ec9e878c333757d4ddb7786a977650ed9b1a05
probe1 d75e313663319e78e301954ece5698e8fc2c4f7527b8324494a9c82ff0003267
probe2 4c75ae7555275a5cc7a906c408cb6944451979aafab3bdd56f62f0ef38555f7f
observer f364f0dee8bef980589bdff407e35d7bb77e134248234967f9c7519513d23b28
input root 3e800f071990192fefd69684477618532c85ab85accbd74f750a51c2f70e6baf
payload eacdc56581aa13cc14c0fd36feb8041a1e71b0aacb14715793d4ece58e8a676e
exported root e942200c5f595f8918aa7e39935d2e39bc4aea0999af57eac19d7f442e5b9583
raw ASL log f41a71dafad74ffd53ecc98175fcf71957487dc4423cbe4010140f77f3c17bce
Rehashed unchanged kernel/base:
kernel 82fc8fe1391bea90bcce9ed2d4e8a2ff8204667f6785857873717564ec9331c9
base 491aa78408c423c50e8b59644e416e94b643ed3eb119158d52684af4176c8b3f

Coverage: plain/check polling over IPC, state and cancellation, and ASL
remote-filter integration. Shared memory, dispatch callbacks, daemon
restart recovery, UIKit, SpringBoard/full iOS and MT6897 drivers remain
unproven. No VM is left running for this completed fixture.

Original syslogd milestone (2026-10-30, QEMU/RAM only; this commit):
Unmodified Apple iOS 16.5 restore syslogd now receives legacy ASL messages
from two C programs and writes six real raw records to its own log file.
Baseline commit: 9f101800fbbcf958c511ab7350d3853cd99aa374.
No phone, USB, UFS or boot partition command was run.

Actual result: work/launchctl-syslogd, exit 0, 43/43 checks passed,
49 installed file hashes and original launchd/xpcproxy/syslogd hashes
matched. 397.172 host seconds, 31 sampled frames, zero unknown glyphs,
no visible panic; stopped on second observer heartbeat before 1200 sec.
Observer PID 3; original syslogd PID 4; probe PIDs 5 and 6, root children
of original launchd PID 1. All four CLI print processes exited 0.
Server before/after prints were identical: running, PID 4, runs=1.
Both probes sent three messages, returned 0, were reaped and stayed
stopped. The original daemon remained alive through final heartbeats;
the fixture does not test its graceful shutdown.

Inspection: original syslogd is plain arm64, iOS 16.5, 166848 bytes,
direct imports libbsm.0.dylib and libSystem.B.dylib; dyld /usr/lib/dyld.
Original 347-byte job is Disabled=true, KeepAlive=true, MachServices
com.apple.system.logger, daemon environment ASL_DISABLE=1.
The RAM copy enables the job, disables KeepAlive, adds root/System
identity, diagnostics and module flags; executable bytes are unchanged.
Daemon ASL_DISABLE=1 is retained to avoid self-logging. Probe jobs set
ASL_DISABLE=0 and open ASL with NO_REMOTE|SHIM_NO_TRACE=0x20000004.
Actual runtime eval for all six messages: 0x00030005, SEND_ASL set,
TRACE/local-file bits clear. No probe opens the daemon output path.

Native daemon debug receipts contain all six tokens at
__asl_server_message. Independent host parsing of sweet-asl.log verified
exactly six records with expected Message/Sender/Facility/Level/custom
fields and matching PID/UID/GID. This verifies expected root senders;
forged credential fields and unprivileged senders were not tested.
Readiness, begin/exit gates and actual job exit/PID files were checked.
launchd still logged persona lookup and legacy launch(3) activation
warnings; they did not prevent the observed legacy ASL path.

Local runtime: research/syslogd-runtime-20F66/runtime-root.
Preparer: tools/prepare-syslogd-runtime.py; 41 binaries / 10877472 bytes,
no missing strong dependencies. Original extraction:
research/syslogd-20F66/apple-extracted, from the pinned restore.apfs.
Reference Apple syslog source commit 69d8586e9a599c304e1b702a9c2830e2f78126d5
was read for flags/config/ABI, not claimed to exactly match this build.
Required exports were separately checked in the real pinned library.
Nine observer modes and the C probe passed arm64 checks with -Werror;
shell/Python checks passed. One VM run, no kernel change or new CI.

Replay: tools/test-sweet-launchctl.sh with Actions 104 kernel, existing
qemu-multiproc.adt, original launchd-final/root.hfs, the new runtime,
HFS tool, fresh output path, 1200 and syslogd.
Details/replay: duchamp/SYSLOGD-QEMU.md.
Report: work/launchctl-syslogd/run/verification.json.
Raw log, daemon debug, CLI and extracted files: its guest/ directory.

SHA-256:
syslogd 86838d9149bb898e3d39266fea884c6c92eeac1e6486c072b135a879c9eeaabe
original plist 86ce6512803e6a20c04834f155a38e1b1a24ff66c9452a57850f65bf2056d5fe
probe1 81d467a90d7b76a5427b3c62832ec9589c9b6d8fa16e84a80726310ef813f6b8
probe2 6b4b55dce920698153bbf6e56b09cff5c95890ae05a064c4f5d7b02279adf305
observer b8731a57adffe79f10ddea2cffbb321635da1d3844659ba3e697d4ea1571ae26
input root 24a366af70ac1e3d30cda31e6cad4708c80f47bb899f8278cd194f3df159cc7d
payload 16c324fe03a318c8b2031e89c4f2407be0f2787ed64dab7eab7b1244b4b2bfee
exported root bdf674d4e60e53d321aa98e38c39306846d323f2500cf67d7604c35d4ed056eb
raw ASL log 1e4be882410f11880afc0e9821d7e55c51ce35eb1ecdd8ba0ded54103ffdb65a
Rehashed unchanged kernel/base:
kernel 82fc8fe1391bea90bcce9ed2d4e8a2ff8204667f6785857873717564ec9331c9
base 491aa78408c423c50e8b59644e416e94b643ed3eb119158d52684af4176c8b3f

Coverage is the original daemon's legacy ASL receive/file path. Modern
os_log/logd, notifyd, rotation, arbitrary input, UIKit, SpringBoard,
full iOS and MT6897 hardware compatibility remain unproven.

Foundation/XPC batch milestone (2026-10-30, QEMU/RAM only; this commit):
Two live clients now exercise two on-demand server generations and six
representative malformed-request cases in one grouped QEMU boot.
Baseline commit: a4b9d8956aed9683fad4ea01d987b56ee1bb6af9.
No phone, USB, UFS or boot partition command was run.

Actual result: work/launchctl-foundation-xpc-batch, exit 0, 83/83 checks
passed. All 96 installed file hashes and the original launchd/xpcproxy
hashes matched. 916.589 host seconds, 69 sampled frames, zero unknown
glyphs, no visible panic; stopped on the second observer heartbeat,
before the 1500-second limit. The user interrupted the conversation
during the boot; the existing run finished in the background. Its
completed report and raw logs were reviewed on resume; no second boot.

Observer PID 3 and client PIDs 4/5 were root children of original launchd.
Server PID 7 initially activated from native traffic, returned 0 after
SIGTERM and was reaped. Clients stayed alive and reopened connections;
native traffic activated server PID 11. Prints showed runs=0 initially,
runs=1 after first activation/exit and runs=2 after the second.
All nine real CLI processes exited 0. The observer issued print and kill
only, with no kickstart/bootstrap/start. Both server instances and both
client jobs finished with last exit code=0 and stayed stopped through
two heartbeats. The MachServices name remained registered.

Each server held two live connections; every one of the 36 data replies
reported active=2. Per-peer handlers share one private serial dispatch
queue, so this is concurrent live clients with serialized processing,
not proof of parallel Foundation callbacks. Four hellos and four closes
were recorded. Each client/generation sent three valid JSON requests
and six rejected cases: syntax, wrong XPC type, missing data, 4097-byte
payload, wrong JSON field type, and an envelope PID differing from the
actual XPC peer. Exact statuses 1..6 were returned on the same connection.
Valid requests after errors succeeded; totals: 12 accepted, 24 rejected.
All 36 saved JSON files independently decoded correctly; all 12
server/client reply pairs were byte-identical. Valid per-operation pool
drains appeared in order. No runtime exception or diagnostic failure.

Replay: tools/test-sweet-launchctl.sh with the previous kernel/ADT/base,
research/foundation-runtime-20F66-v2/runtime-root and HFS tool, a fresh
output directory, 1500 and foundation-xpc-batch.
Details: duchamp/XPC-BATCH-QEMU.md.
Report: work/launchctl-foundation-xpc-batch/run/verification.json.
Raw CLI outputs, logs, JSON and extracted installed files: its guest/.
Eight observer modes and the two new Objective-C peers passed arm64
syntax checks with -Werror; shell/Python checks passed. Required new
XPC/dispatch exports were verified in the pinned runtime before boot.
An initial Objective-C identifier conflict was corrected before boot;
there was only one VM run. Earlier scenarios/images remain preserved.

SHA-256:
server 90894c0b02d38a112c4976cb6d6142859fc5f37e937a81f20873d6a108b61e22
client 1543a5c511277b84f5f9daea8d3b898a2b246b5594edc17c70c4169bd4b749bd
observer 44ca3b85ed2605305ee9bf277dd497333fb12119f6a75f6157ba7651a22d9458
input root 62671e29f50f6fd4d97df7a05b2f0d0cbc0d92cca133e011598f9043e41815cd
payload ca55c15c2f94de7a0b25dedfbf29d6c583522abe0d9a3f7e03f0e7c83b9d531e
exported root 125024bf1c51cd7bf03d262cecb06eeacf8f77c3da33826c55e7e771502d8206
Rehashed unchanged kernel and original base:
kernel 82fc8fe1391bea90bcce9ed2d4e8a2ff8204667f6785857873717564ec9331c9
base 491aa78408c423c50e8b59644e416e94b643ed3eb119158d52684af4176c8b3f

This is a bounded fixture, not a fuzzer or a production IPC server.
Arbitrary malformed traffic, stress, NSXPCConnection, UIKit, SpringBoard,
full iOS and MT6897 storage/drivers remain unproven.
Next useful system step: inspect an original system daemon and its
runtime/job dependencies before adding a QEMU-only service test.

Foundation/XPC integration milestone (2026-10-30, QEMU/RAM only; this commit):
Original Apple Foundation now processes JSON in both native libxpc peers,
with on-demand launchd MachServices activation and orderly exits.
Baseline commit: 97d940bb47a0a3ce62fa62fc3aaea615eee3d3d7.
No phone, USB, UFS or boot partition command was run.

Actual result: work/launchctl-foundation-xpc, exit 0, 56/56 checks passed,
95 installed file hashes plus original launchd/xpcproxy checks passed.
531.312 host seconds, 40 sampled frames, zero unknown glyphs, no visible
panic; stopped on second observer heartbeat before the 900-second limit.
Observer PID 3, client PID 4, server PID 6, root children of launchd PID 1.
Initial server print had runs=0 and no PID with its Mach name registered.
Only after that print did the observer release the client; native XPC
traffic activated the server without any manual start command.

Both peers are Objective-C/MRC with blocks and exceptions. Three JSON
requests passed through NSDictionary/NSJSONSerialization/NSData into
native XPC data. Server checked received classes/fields against the
integer envelope, uppercased duchamp to DUCHAMP, added fixture soc=6897
and XOR-transformed values. Client parsed and validated every reply.
Each request was 46 bytes, each reply 58 bytes. Nine atomically saved
JSON files independently decoded correctly on the host; all three
server/client reply pairs were byte-identical. All nine per-operation
autorelease-pool drains appeared in order, including worker callbacks.

Six launchctl commands exited 0. Client cancelled its connection and
returned 0; server saw connection invalidation, handled SIGTERM,
cancelled peer/listener and returned 0. Final prints: not running,
runs=1, last exit code=0. Both PIDs reaped and stayed stopped through
two heartbeats. The MachServices entry remained registered.
Original Apple libraries, launchd and xpcproxy remained byte-identical.
CLI remains pinned Procursus FOSS launchctl 1:1.1.1, not Apple's CLI.

Replay: tools/test-sweet-launchctl.sh with the prior six inputs,
research/foundation-runtime-20F66-v2/runtime-root, fresh output directory,
900 and foundation-xpc. The copied HFS root is 128 MiB in RAM.
Details/replay: duchamp/FOUNDATION-XPC-QEMU.md.
Report: work/launchctl-foundation-xpc/run/verification.json.
Raw logs, nine JSON files and file extractions are under its guest/.
Earlier native-XPC saved guest recheck passed using a separate report
work/xpc-integration-tools-recheck.json; original report preserved.
Seven controller modes, both integrated Objective-C peers, old C XPC
peers and standalone Foundation compile checks passed with -Werror.
Python/shell checks passed. No kernel change or new Actions build.

SHA-256:
server 2a72fb59c4baa0228cd578639aedb851f131d05dccf057b2f6f1036200749926
client ef5647df2d8ae691da4158ee99e6880fa7a65a5f5cec7fbcf031dab3bcb56870
observer 3085749319a68c6865efc78da4fb9683808284776300a2d696eae38f37cfb694
input root 236b7ff7bf6d753f9d70fd97c98f530198035b92da6f47d477ee7ac484ebd628
payload a04f5a411feb1fc09183f9c315f0d6c89396d62b9c0892a097b4f5ab9d66c5b0
exported root e44eddb4efe8a04e0bd9bfd1d91aa67fd8a7997251e6c503842c369d598d8032
Rehashed unchanged kernel and original base:
kernel 82fc8fe1391bea90bcce9ed2d4e8a2ff8204667f6785857873717564ec9331c9
base 491aa78408c423c50e8b59644e416e94b643ed3eb119158d52684af4176c8b3f

Coverage: one activation, one client, three valid Foundation JSON
exchanges and graceful exits. This uses C libxpc data, not high-level
NSXPCConnection. Malformed inputs, concurrent clients and repeated
activation remain useful next grouped tests. UIKit, SpringBoard,
full iOS and MT6897 storage/driver work remain unproven.

Foundation milestone (2026-10-30, QEMU/RAM only; this commit):
An Objective-C program now executes selected APIs in the original Apple
iOS 16.5 Foundation/CoreFoundation and matching libobjc/Swift closure.
Baseline commit: 2409971aaf221e6a2984392b0836d9c9ced9e9b2.
No phone, USB, UFS or boot partition command was run.

Actual result: work/launchctl-foundation, exit 0, 26/26 checks passed,
94 installed/original file byte checks passed, 315.692 host seconds,
23 sampled frames, zero unknown glyphs, no visible panic. Stopped on
second observer heartbeat before the 900-second limit.
Program PID 4, observer PID 3; root children of original launchd PID 1.
Ordered proof: NSAutoreleasePool creation; uppercase DUCHAMP; Arabic
UTF-8 round trip with five UTF-16 units; NSDictionary/NSNumber with
device and soc; JSON encode/decode; atomic NSData write/read; named
SweetProbe NSException throw/catch; pool drain; readiness; normal exit.
The saved 31-byte JSON independently decoded as device=DUCHAMP,soc=6897.
Both launchctl commands exited 0. Final print: not running, runs=1,
last exit code=0. PID 4 reaped; later heartbeats confirmed no restart.
The observer sent no signal or start command to the target.

Runtime preparation: tools/prepare-foundation-runtime.py.
Successful output: research/foundation-runtime-20F66-v2/runtime-root.
82 plain-arm64 binaries / 100,424,416 bytes, seven framework resources,
no missing strong dependencies. Source APFS hash and all file/resource
hashes recorded in its parent source.json. The first preparation output
was retained after rewriting identical read-only base files failed;
the preparer now skips matching existing bytes. Broad 7z extraction
rejected one unneeded libextension symlink; it was not reconstructed.
Replay can exclude it with -xr!libextension.dylib (list exclusion checked).

Replay tools/test-sweet-launchctl.sh with the prior six inputs, replacing
the runtime with the new one, then 900 and foundation. Objective-C uses manual reference counting
and exceptions; observer uses SWEET_FOUNDATION_TEST=1.
Builder copies/grows only the new RAM root from 32 to 128 MiB, verifies
its HFS header/length, creates only missing framework directories and
re-extracts every installed file. Target plist stays unchanged.
RAMDisk: 0x1c24d8000 + 0x08000000, inside the 512 MiB payload window.
Details/replay: duchamp/FOUNDATION-QEMU.md.
Report: work/launchctl-foundation/run/verification.json.
Raw logs, JSON and file extractions: work/launchctl-foundation/guest/.

SHA-256:
program eb121f6730f9bd198b1631bea0ebffaa349893379d3927c894ed88724ba7f1a6
observer 88424f24048eb5334b14c8beaa8e8b88ca74fb7985c3028f19068adf0b2890c8
input root ee2c72087cec9fe87500253c0c583ca7f55aa4d78d5e4cc097bc29bd3df5c040
payload 1ecf5feaf7f16ef85392c0abf9a9a29bb3c7c58e3e0c68a0799db7a86736b81e
exported root 096c443f4ab67987ad55f287b256cc88e662aa5c204db204c681bf798f84b271
Foundation 182a6fb6d6c51e8e1a70e9152c84cd9d1bd65d2a1f0bda21a4ebe1be446021f2
CoreFoundation 1bc84069d4292467b750c7aafb4c3114092cb9b5fa906d9c40e61504dc883878
Rehashed unchanged Actions 104 kernel and original base:
kernel 82fc8fe1391bea90bcce9ed2d4e8a2ff8204667f6785857873717564ec9331c9
base 491aa78408c423c50e8b59644e416e94b643ed3eb119158d52684af4176c8b3f

All six controller modes and the Objective-C program pass arm64 checks
with warnings as errors; shell/Python checks pass. No kernel change or
new CI build. Earlier images/results and Apple sources remain local.
Coverage is selected Foundation APIs, not Foundation/XPC integration,
network services, UIKit, SpringBoard, full iOS or MT6897 UFS.

Native XPC milestone (2026-10-30, QEMU/RAM only; this commit):
One combined fixture now proves launchd MachServices registration,
on-demand server activation, native Apple libxpc dictionary request/reply,
and orderly exits. Original Apple launchd/xpcproxy/libxpc are unchanged;
observer CLI remains pinned Procursus FOSS launchctl 1:1.1.1.
Baseline commit: 8c6172eeb6b159bb0f64724bfece43f771d10dc8.
No phone, USB, UFS or boot partition command was run.

Actual result: work/launchctl-xpc, exit 0, 43/43 checks passed,
449.402 host seconds, 35 sampled frames, zero unknown glyphs, no visible
panic. Stopped on second observer heartbeat before 720 seconds.
Observer PID 3, client PID 4, server PID 6; all root children of PID 1.
The initial server print had no PID, runs=0 and its registered Mach name.
Only after that print did the observer release the client's begin gate.
Native XPC traffic caused launchd to start PID 6 without a start command.
Both endpoints verified xpc_connection_get_pid and executable paths.
Three independent dictionary exchanges matched the expected payloads:
0x10203001 -> 0x4a7a6a5b, 0x10203002 -> 0x4a7a6a58,
0x10203003 -> 0x4a7a6a59. All eight integer fields are compared.
Client cancelled its connection and returned 0; server recorded native
XPC connection invalidation, handled SIGTERM, cancelled listener/peer
and returned 0. Final prints: not running, runs=1, last exit code=0.
Both PIDs reaped; Mach service registration remained in the final print.
All six CLI processes exited 0; final heartbeats confirmed stopped state.

Replay tools/test-sweet-launchctl.sh with prior six inputs, 720, then xpc.
Server plist: RunAtLoad=false, KeepAlive=false, MachServices containing
org.sweet.qemu.mach-service. Client/observer: RunAtLoad=true, no service.
Native programs use -fblocks; observer selects SWEET_XPC_TEST=1.
The same 39-file / 10,551,232-byte runtime suffices; no new kernel CI.
Public libxpc prototypes/ownership/queue rules checked in Apple docs;
listener flag bit 0 also checked in the pinned libxpc disassembly.
Sync replies occur on client main, outside its event-handler queue.
The API has no per-request timeout here; whole-VM limit bounds the run.
Details/replay: duchamp/XPC-QEMU.md.
Report: work/launchctl-xpc/run/verification.json.
Raw peer logs, CLI files and listings: work/launchctl-xpc/guest/.

SHA-256:
server bfb60c484b8878d658cad3182256d0b768e5273240dd7dfd4fd11b379a1c936a
client e321ce84071a0c6c5d01188fca0782c5435d811e753cf65506cf55543a6bec55
observer 0ac3063243d8d2a62928e12d31ebcdff3dfa8d5de53f798827afc431f3a45170
input root 7dba76a3799e87d7b8443f23d6eaf391ab23cb51c31246aa24641f219077dbe3
payload 28c415f14ee8ab3c2ab7927e95cdd3197fe63f465418dd3c29d96ac9b9d465cb
exported root a90255ffc4b32bfa2fbbc6dc7798c949145537610223b0d6026356ded7aa7af1
server plist e32f6c8940f7005aa3347ec2f2663dbf5c4a86c9405d4b9c7be6dad7f8f81275
Rehashed unchanged Actions 104 kernel and original base:
kernel 82fc8fe1391bea90bcce9ed2d4e8a2ff8204667f6785857873717564ec9331c9
base 491aa78408c423c50e8b59644e416e94b643ed3eb119158d52684af4176c8b3f

Five controller modes and both XPC programs passed arm64 -Wall -Wextra
-Werror checks; shell/Python checks passed. Old Unix guest recheck passed
39 checks with the split launch-policy validation. Its original 38-check
report was saved/restored; verification-xpc-tools-recheck.json records
the recheck. Prior images and results remain intact.

Coverage is one native XPC connection, three replies and one on-demand
activation. Repeated activation, concurrent clients, Foundation/system
services, full iOS and MT6897 UFS remain unproven and separate work.

Two-service IPC milestone (2026-10-30, QEMU/RAM only; this commit):
A separate Unix-domain socket server and client now exchange validated
messages as root children of unchanged Apple launchd PID 1. A third
observer uses pinned Procursus FOSS launchctl 1:1.1.1 for state/stop checks.
Baseline commit: de31099d57f8b4dfa162ada21049fbbeec504206.
No phone, USB, UFS or boot partition command was run.

Actual result: work/launchctl-ipc, exit 0, 38/38 checks passed,
428.675 host seconds, 33 sampled frames, zero unknown glyphs, no visible
panic. Stopped on SWEET launchctl: heartbeat=2 before 720-second limit.
Observer PID 3, server PID 4, client PID 5; all root children of PID 1.
Both socket endpoints verified LOCAL_PEERPID and the peer executable path.
Three 32-byte request/reply frames carried matching PIDs, sequence,
version, payload and XOR checksum. Both independent saved logs matched:
seq 1: 0x10203001 -> 0x4a7a6a5b
seq 2: 0x10203002 -> 0x4a7a6a58
seq 3: 0x10203003 -> 0x4a7a6a59
The client closed its socket; the server observed EOF.
The observer released the client via a RAM file; its main returned 0.
It sent SIGTERM to the idle server; the handler only set a flag, then
normal execution closed the listener, unlinked the socket and returned 0.
Both PIDs were reaped. Final launchctl prints: not running, runs=1,
last exit code=0. No signal death. Socket absent from saved RAM root.
All five CLI children exited 0; later observer heartbeats confirmed
both services stayed stopped. No kickstart/bootstrap/direct service exec.

Replay tools/test-sweet-launchctl.sh with the prior six inputs, 720,
then ipc. It builds sweet-ipc-server.c at the existing C-service path,
adds sweet-ipc-client and its job, and selects SWEET_IPC_TEST=1 for the
observer. All three jobs RunAtLoad=true / KeepAlive=false. The server
job's plist stays byte-identical to the base. Fixture executables are
new in this scenario; prior scenarios retain their original C target.
ABI declarations checked against local XNU 22.6 CI source headers and
uipc_usrreq.c. This is AF_UNIX SOCK_STREAM, not an XPC/Mach service test.
Details/replay: duchamp/IPC-QEMU.md.
Report: work/launchctl-ipc/run/verification.json.
Raw peer logs, CLI stdout/stderr and listings: work/launchctl-ipc/guest/.

SHA-256:
server f89ef4d320f554bf13f5e284efb6f4ba4d61235c6d6cf5140fe91edc04f88972
client fc9b79e2d48729ff45b6abe6909325b69a499e7660aabe821af5d1e605cf866f
observer 2bc3845ccdfa148c36411c271046816ded93a732c1ae3b0844308dae41fc30f2
input root aa4e450a621daa745ed915bc97fe3ce3dd605b7e25e5f4fa2bf9d3bbec8c53f0
payload 55a093b2d3b86c5850bdad77a1d28d8eb0e024d326687d6ce409d7b493a034bf
exported root 47800e98c2f14a64e2c8b5ee7a28164b370d5fc1afc4cb8575458e10237de9f7
Original Apple launchd/xpcproxy and pinned CLI hashes passed.
Rehashed unchanged Actions 104 kernel and initial base:
kernel 82fc8fe1391bea90bcce9ed2d4e8a2ff8204667f6785857873717564ec9331c9
base root 491aa78408c423c50e8b59644e416e94b643ed3eb119158d52684af4176c8b3f
No new kernel CI build. Server/client and all four controller modes
passed arm64 C checks with warnings as errors; shell/Python checks pass.
The prior saved KeepAlive run still passes its 33 checks.

Coverage: one connection and three request/reply pairs; normal client
exit; SIGTERM cleanup of an idle server after peer EOF. Active-request
cancellation, concurrent clients and XPC remain separate coverage.
Full iOS and MT6897 UFS are not proven. Preserve all prior roots/results.

KeepAlive milestone (2026-10-30, QEMU/RAM only; this commit):
Unchanged Apple launchd/xpcproxy automatically restarted the diagnostic
C service twice with KeepAlive=true, using pinned Procursus FOSS
launchctl 1:1.1.1 only to print and send SIGTERM / SIGKILL.
Baseline commit: 9653af572059e49531a7eb43638aa2e02c5daef2.
No phone, USB, UFS or boot partition command was run.

Actual result: work/launchctl-keepalive, exit 0, 33/33 checks passed,
450.716 host seconds, 35 sampled frames, zero unknown glyphs, no visible
panic. Stopped on SWEET launchctl: heartbeat=2 before the 720-second limit.
Controller PID 3 is a root child of original PID 1 /sbin/launchd.
All five CLI processes exited 0:
print-before: PID 4 running, runs=1.
kill SIGTERM: PID 4 reaped / ESRCH; launchd respawned PID 7 automatically.
print-auto-1: PID 7 running, runs=2, last terminating signal=15.
kill SIGKILL: PID 7 reaped / ESRCH; launchd respawned PID 10 automatically.
print-after: PID 10 running, runs=3, last terminating signal=9.
No kickstart/bootstrap/direct exec of the target was used by the controller.
All three target instances passed readiness checks; PID 10 and controller
continued heartbeats. The saved readiness file contained 10.

Replay tools/test-sweet-launchctl.sh with the prior six inputs, 720, and
keepalive as eighth argument. Only controller gets SWEET_KEEPALIVE_TEST=1.
The copied target plist changes only KeepAlive false -> true; base stays
unchanged and controller KeepAlive stays false. The target C binary is
byte-identical to the prior tests. Builder records base/installed plist
hashes and base properties. Verifier checks three distinct PIDs, ordered
autorestarts, run count 1/2/3, signals, raw CLI files and final heartbeats.
Details/replay: duchamp/KEEPALIVE-QEMU.md.
Report: work/launchctl-keepalive/run/verification.json.
Raw trace and CLI outputs: work/launchctl-keepalive/guest/.

SHA-256:
target 465d9bed7e2d6765c121d4cb5f330cd123b48ab9f387c3a5feaceb171bd4677f
controller ca5fcabfe9da5ab23768841986ab9e0eada43674c2a32524ef0b7fc05cf30bb8
input root 9ef39b5556b5d4416a89aa58e21eafd0bd0038c9f468359ba61cb6a33720a03f
payload d7b6d4d88ee53ec67473bf21ebea8e2fdde545b172b5a7665e3ce16aabfbaba6
exported root 85b2e3958900f668387963f0fea647bc1a20f88aa83b58f30aec72a0d104de30
KeepAlive plist 7e33d9a92afeca768a5aacd4fb95ff171355444bee1c24099a6dfa136cc8f808
base plist 004e41dbd0bc0d0f1ef88a7ee73c6ae228c55a5e7d8728704289dc244380083c
Rehashed unchanged Actions 104 kernel and initial base:
kernel 82fc8fe1391bea90bcce9ed2d4e8a2ff8204667f6785857873717564ec9331c9
base root 491aa78408c423c50e8b59644e416e94b643ed3eb119158d52684af4176c8b3f
No new kernel CI build. Original launchd/xpcproxy/CLI hashes passed.
Three C controller modes passed arm64 -Wall -Wextra -Werror checks;
shell syntax and Python compile checks passed. Updated verifier still
accepts prior saved guests: 22 stop/restart and 27 bootout/bootstrap checks.

This tests unconditional KeepAlive after signal termination in QEMU.
Normal exit, conditional KeepAlive dictionaries and custom shutdown
handlers remain separate coverage. Full iOS and MT6897 UFS are not proven.
Keep all successful roots and prior failed probes for comparison.

bootout/bootstrap milestone (2026-10-30, QEMU/RAM only; this commit):
The pinned Procursus FOSS launchctl 1:1.1.1 successfully removed and
reloaded org.sweet.qemu.c-service under unchanged Apple launchd/xpcproxy.
Prior lifecycle commit: 5343d416b2d83ad71f37357d7321065172aa62d8.
No phone, USB, UFS or boot partition command was run.

Actual result: work/launchctl-bootstrap, exit 0, 27/27 checks passed,
399.932 host seconds, 31 sampled frames, zero unknown glyphs, no visible
panic. Stop marker: SWEET launchctl: heartbeat=2 .
Controller PID 3 is a root child of PID 1 /sbin/launchd.
print-before: exit 0, target PID 4 running.
bootout system/org.sweet.qemu.c-service: exit 0, PID 4 reaped / ESRCH.
After five seconds, print returned ENOSERVICE=113 (wait status 0x7100):
Could not find service "org.sweet.qemu.c-service" in domain for system
The plist remained readable and byte-identical to the base image.
bootstrap system /System/Library/LaunchDaemons/org.sweet.qemu.c-service.plist:
exit 0; readiness file became 9; print-after: exit 0, PID 9 running.
Both target and controller continued heartbeats. This proves removal of
registration and reloading, beyond the earlier stopped-but-registered test.

Replay tools/test-sweet-launchctl.sh with the same six inputs, 720, then
bootout-bootstrap as its eighth argument. Omitting the mode retains the
SIGTERM/kickstart scenario. Only the controller gets SWEET_BOOTSTRAP_TEST=1.
Verifier requires the exact missing-service status/text and checks the
saved guest plist, original executables, PID transition and heartbeats.
Details and replay: duchamp/BOOTSTRAP-QEMU.md.
Raw trace/CLI files: work/launchctl-bootstrap/guest/.
Report: work/launchctl-bootstrap/run/verification.json.

SHA-256:
target 465d9bed7e2d6765c121d4cb5f330cd123b48ab9f387c3a5feaceb171bd4677f
controller ef31d135fdf0120e930b77f7c34724a5cb44589ce8bed7b75d8194ee2f3c0bd8
input root 949814247b6e88a4d466518d0dc88bdce01cd13066e9fb7120590afc87585b58
payload fe12ca6fd72cf90be45a82a9f807bc4147c46115e9a996ccaa761b9bb575d38b
exported root d2bbb6a6910f100fac9bff93a7c1f646f27fe0c63451ba8fa3d2a8cd951b51e4
target plist 004e41dbd0bc0d0f1ef88a7ee73c6ae228c55a5e7d8728704289dc244380083c
The unchanged Actions 104 kernel and initial base root were rehashed:
kernel 82fc8fe1391bea90bcce9ed2d4e8a2ff8204667f6785857873717564ec9331c9
base 491aa78408c423c50e8b59644e416e94b643ed3eb119158d52684af4176c8b3f
No new kernel CI build. Both controller modes pass arm64 C checks with
-Wall -Wextra -Werror; Python compile and shell syntax checks pass.
The updated verifier accepts the prior lifecycle run (22 checks) and
rejects the earlier SIGTERM-ignored run despite its no-panic result.

This milestone covers one diagnostic service in QEMU's development
kernel. It does not establish full iOS or a working MT6897 storage backend.
Keep the existing successful roots and failed probes. Further work should
select a separately scoped userland test; phone storage remains outside it.

launchctl lifecycle milestone (2026-10-30, QEMU/RAM only; this commit):
Apple's unchanged launchd/xpcproxy now successfully serve print, SIGTERM
stop, stopped-state print, kickstart -p, and running-state print through
pinned Procursus FOSS launchctl 1:1.1.1. This is not an Apple-supplied
launchctl binary. Restore/update/system image file lists contained none.
The CLI SHA-256 is
11527b7bb1027f10a7d994815efbe81df3b692ca9df8b172b6a1f656c6cc028d;
libiosexec.1.dylib is
9d8f0b10be02f9829854e11dc4a86f70dbfd0f0322f3a3a996716e4d38214391.
prepare-launchctl-runtime.py pins official package URLs/SHA-256 values and
copies the existing restore runtime. LC_RPATH resolution was added to the
dependency audit; the closure is 39 files / 10,551,232 bytes. No global
package installation, Apple binary patch, or kernel modification was used.

Final complete wrapper run: work/launchctl-signals, exit 0, 22/22 checks
passed, 412.973 host seconds, 32 sampled frames, zero unknown glyphs, and
no visible panic. The 720-second maximum was cut short by the second
controller heartbeat after CONTROL PASS. The root/System controller PID 3
is a child of original /sbin/launchd PID 1. Target PID 4 was running,
terminated by SIGTERM, reaped (ESRCH), and remained absent during the
stopped check after at least five seconds. kickstart printed 9; the new
target published PID 9 and print-after showed it running. All five CLIs
exited 0. Both target and controller continued heartbeats.

The target now publishes a PID readiness file after its identity/file checks
and explicitly sets/read-backs SIGTERM=SIG_DFL with an empty mask. Both
instances logged inherited SIGTERM=ignored, mask=0. Before that fix the
CLI request succeeded and launchd logged signal 0xf, but the target kept
running; work/launchctl-final correctly failed after 60 reap polls.
The first probe (work/launchctl-probe-1) failed from O_WRONLY capture
readback / EBADF; O_RDWR fixed the controller. That failed VM was stopped
early with its RAM root exported. All attempts and raw outputs are kept.
The strict verifier rejects the earlier no-panic / successful-CLI failure.
This tests default SIGTERM termination, not custom signal-handler cleanup.

--save-ramdisk validates the ADT RAMDisk physical range and exports it after
stopping the VM. The verifier extracts all five actual stdout/stderr files,
the controller trace, readiness PID, and original executable bytes from the
saved HFS image. It checks ordered CLI statuses, old/new process state,
signal normalization, both target instances and continuing heartbeats.
Evidence: work/launchctl-signals/guest/ and run/verification.json.

Final target SHA-256
465d9bed7e2d6765c121d4cb5f330cd123b48ab9f387c3a5feaceb171bd4677f;
controller 2425fbdf5d19ce32eaf90bf6b3bc967afec5bcd57aa7fed011e8c508958b3001;
input root 6304a5a91fd1b6cf223912f710139df443d2de3bb1fc5934ad926a301d419e3d;
payload e4ac257dacec131822e5d864dc232046028f52ba0b25f73d6075d573c916def6;
exported root 072372b543a717b9c06ca0e4bdee7ed634a9a87f43efa53be92e6e64bba08071.
Actions 104 / 40939563499 kernel is unchanged:
82fc8fe1391bea90bcce9ed2d4e8a2ff8204667f6785857873717564ec9331c9.
The previous launchd input root remains
491aa78408c423c50e8b59644e416e94b643ed3eb119158d52684af4176c8b3f.
The full public system DMG was also fetched during asset investigation:
research/launchctl-20F66/096-04088-077.dmg, ZIP CRC32 028fc181 verified.
It is not needed to replay this test. Apple/third-party files stay ignored.
No helper/QEMU download processes remained after completion.

Next QEMU step: bootstrap/bootout of the target job and verify removal and
re-registration. Full iOS, SpringBoard, production signing, and MT6897 UFS/
hardware remain unfinished. Phone/USB/boot partitions were not accessed.
Previous commit: b52fd2a. Reproduction: duchamp/LAUNCHCTL-QEMU.md.

Original launchd milestone (2026-10-30, QEMU/RAM only; this commit):
Original, unmodified iOS 16.5 restore launchd now runs as PID 1 and launches
one persistent dynamically linked C system service via original xpcproxy.
The static /usr/appleinternal/sbin/launchd.sweet entry is selected with the
existing DEVELOPMENT launchdsuffix=sweet path, checks PID 1, opens console
fds and execs /sbin/launchd without forking or starting the service itself.
The C service reports PID 3, PPID 1, real/effective UID 0, and verifies that
proc_pidpath(1) is /sbin/launchd. Its RAM-file roundtrip and continuing
numbered heartbeats passed. Only one process identity was observed.
Job: org.sweet.qemu.c-service, UserName=root, GroupName=wheel,
LimitLoadToSessionType=System, RunAtLoad=true, KeepAlive=false.

Final unchanged wrapper run in work/launchd-final completed for 180 host
seconds with exit 0, all 15 checks true, 14 sampled frames, zero unknown
glyphs, and no visible panic. run/verification.json records hashes/checks;
run/frames and run/fb.txt contain sampled circular framebuffer logs.
Original launchd SHA-256
4c61512d19b9a55a6ddad27e23b88fc5008fbf77d0c0b5e6bdd7c7d90cef3e06;
xpcproxy 2d1f607a248961d6a8612aca68a42c57069fa9cf3f5afbee448cf3e70eeb315f.
Bootstrap fca4093be866f706e4a693f7f79bcfd2239ea144ccdb14dd2bbeb215719f441f;
C service 6adbe9d1fb35a1833b273507aeb2b0e9c75450d73274a3410937aa0c495d24de;
root 491aa78408c423c50e8b59644e416e94b643ed3eb119158d52684af4176c8b3f;
payload 42f784c42bbf31745502f5e11b2727f8cc2b4365f3b42c2cbaf004c7ffa781a8.
Kernel unchanged from Actions 104 / 40939563499, SHA-256
82fc8fe1391bea90bcce9ed2d4e8a2ff8204667f6785857873717564ec9331c9.

Probe 1 reached Apple launchd but panicked because the root-only fixture
could not resolve mobile (errno 114). The builder now preserves the restore
image's account IDs/groups and locks password fields. Probe 2 panicked in
the interrupt-duration watchdog while a separate observer dumped live RAM.
The new optional QEMU snapshots stop virtual time before pmemsave and
resume afterward; the runner also reaps the VM on capture/decoding errors.
Probe 3 then passed 12 earlier checks and ran the service in user/501.
launchd rejected DYLD_SHARED_REGION in that job. The final job removes that
variable and explicitly selects a root/System service. The strict verifier
also rejects the failed first probe. No watchdog or kernel check was disabled.

prepare-darwin-runtime.py now extracts launchd/xpcproxy and account inputs
alongside the 37-file runtime closure; tested using the pinned restore disk
into research/darwin-launchd-20F66. All Apple inputs stay ignored/local.
Each installed regular file is re-extracted and byte-compared; the HFS job
directory is checked for exactly one job. The original dynamic RAM-root
SHA-256 stays 750fc8ec3e2452a708da00aa078a8f6b65d7f27333c18cba17add0899ea67c91.
launchd retains embedded __TEXT,__config; no binary or global config patch.
Nonfatal logs include missing MRM cache, jetsam EINVAL and persona lookup
failures. This proves one service, not complete launchd/iOS compatibility.
Next concrete QEMU work: original launchctl status and controlled service
stop/restart. GUI, hardware drivers and MT6897 UFS remain unfinished.
Phone/USB/UFS/boot partitions were not accessed. Previous commit: 3a9bc41.
Reproduction: duchamp/LAUNCHD-QEMU.md.

Dynamic C runtime milestone (2026-10-29, QEMU/RAM only; this commit):
Fetched only Apple's 20F66 iPhone X restore disk 096-03566-084.dmg using
remotezip; pinned SHA-256
8223b75c9399dfc8cf0971374527d710b69e29e8ef69722b98a82902199fcff5.
It is an unencrypted IM4P/APFS container, not a decrypted system image.
prepare-darwin-runtime.py was also tested against the local pinned member.
Its real plain-arm64 dyld/libSystem dependency closure has 37 files,
10,401,536 bytes, all kept locally under ignored research/.

A separate C executable links to /usr/lib/dyld and libSystem with LC_MAIN
and explicit ld64.lld -adhoc_codesign. It uses real printf, dyld image
enumeration, file create/write/close/reopen/read/EOF, libc fork, and waitpid.
A static diagnostic PID 1 forks/execs it, requires exit 0, then heartbeats.
The 32 MiB HFS root is a fresh baseline copy; all 39 installed files were
extracted and byte-compared using libdmg-hfsplus at pinned commit
7ac55ec64c96f7800d9818ce64c79670e7f02b67. The baseline SHA-256 remains
e5b5c1b68c00db65ae31d8d29baef6ab88c8131e29940d8ce7b810536726414a.

Final complete wrapper run: work/userland-dynamic-final, 90 seconds, exit 0,
all 15 semantic/metadata checks passed. C main reported PID 2 and 37 images;
child PID 3 exited 42, parent verified waitpid, C exited 0, PID 1 continued.
Zero unknown glyphs and no visible panic. An initial 45-second probe had not
reached C main. The first 90-second binary ran successfully but had no
LC_CODE_SIGNATURE; the validator rejected it. Explicit -adhoc_codesign
fixed that build issue and the final untouched wrapper passed. Signature
command presence/execution under a development policy does not prove
production trust or entitlement enforcement.

Kernel unchanged from Actions 104 / 40939563499, SHA-256
82fc8fe1391bea90bcce9ed2d4e8a2ff8204667f6785857873717564ec9331c9.
Final init 2c2892d85895afefc8bd62ef620ac7081f81cdc6bbeb22935fdd4759dfd6d663;
C program 8a8427fc901b7d4041079e80e6965253ddb15a031918fcd04d2b5476f6a8953f;
root 750fc8ec3e2452a708da00aa078a8f6b65d7f27333c18cba17add0899ea67c91;
payload 422bd7cb12fd82d502cde09070d06822b417ec4f9e9137d23ed0665d7ddd0e05.
Reports: work/userland-dynamic-final/run/{fb.txt,verification.json}.
Reproduction and launchd inspection: duchamp/DYNAMIC-USERLAND.md.

Original restore launchd and xpcproxy were extracted for metadata/import
inspection only. Both are arm64/iOS and directly require libSystem/libobjc,
already in the tested closure. xpcproxy has a weak cryptex trampoline import.
Their private spawn, Mach/dispatch, host ports, sandbox/csops behavior is not
verified. The five supplied daemon plists include iPhone restore services.
Next: isolated QEMU root with actual launchd as PID 1, xpcproxy, writable
private/var directories, console/null nodes, and one controlled C service;
trace errors before adding more jobs. No original launchd was executed yet.
Full iOS and MT6897 hardware support remain unfinished. Phone/UFS/boot
partitions were not accessed. Previous milestone commit: 053964a.
The runner's long-path QMP socket fix is included: transient socket in /tmp,
removed on completion. Other pending checkpoint/loader changes stay separate.

Signal/service-control milestone (2026-10-29, QEMU/RAM only; this commit):
After the intentional exit-42/restart, PID 1 sends SIGSTOP (17) to the positive
worker PID and polls wait4(WNOHANG|WUNTRACED) for status 0000117f. It holds the
worker stopped for at least five seconds, sends SIGCONT (19), requires
WCONTINUED status 0000137f, and allows ten seconds for renewed heartbeat output.
It then sends SIGTERM (15), requires termination status 0000000f, reaps the
worker, checks kill(pid, 0) returns ESRCH, and starts a third persistent worker.
Each wait event has at most 50 polls with 100ms pauses. Worker SIGTERM is
explicitly SIG_DFL with an empty signal mask; select retries EINTR. This tests
default actions, not a custom signal handler or graceful cleanup routine.

The complete 90-second wrapper run in work/userland-signals-verified exited 0.
All 27 semantic checks passed, including ordered signal events, no worker
heartbeat during the stopped interval, fresh heartbeat after continuation,
termination/reaping, final restart, and all three workers' file/IPC tests.
No visible panic and zero unknown glyphs were observed. The earlier run in
work/userland-signals-final also passed guest checks but its host wrapper
reported a trailing syntax error after its comment was edited mid-execution;
the untouched rerun passed end to end. The verifier rejected an IPC-only
result copied to work/userland-signals-negative. Previous milestone: ef86078.

Kernel unchanged from Actions 104 / 40939563499, SHA-256
82fc8fe1391bea90bcce9ed2d4e8a2ff8204667f6785857873717564ec9331c9.
Final init 10256d2be047a950c2b920670e69806814089b37ae6ef19ce8c44a2e65df2c1c;
worker 595827b44de924f7316a2befbe6ef641ac897b7a0cd25e14bd68f5fd52dbdcb1;
root ccc0ecc271447f104854eabaea6b5cbdaf9c56e9a5706d93a9282f5bb20c17c1;
payload 19dd823926c2fe1971bcd3dfbeff1c8a3510742d0be60f103d8c96c9bf083df9.
The repeated build produced identical input hashes. Artifacts and report:
work/userland-signals-verified/run/{fb.txt,verification.json}. Documentation:
duchamp/USERLAND-QEMU.md. Phone/UFS/boot partitions were not accessed.
Richer userspace and the MT6897 hardware backend remain unfinished.

IPC and RAM-file milestone (2026-10-29, QEMU only; this commit):
PID 1 now creates a fresh pipe before each fork, closes its writer, and checks
the exec'd worker's exact READYv1 message followed by EOF. The child uses dup2
to inherit the writer on fd 3 and closes unused endpoints. On each exec the
worker creates /sbin/worker-data, writes 18 known bytes, closes and reopens it,
compares every byte, checks EOF, then sends its pipe message and closes fd 3.
Both transfer loops handle short reads/writes and reject premature EOF.

The existing kernel from Actions 104 / 40939563499 was reused. The single
test-sweet-userland.sh run in work/userland-ipc-final completed for 90 seconds
with no_panic_observed, zero unknown glyphs, and all 17 semantic checks true.
The intentional exit 42, wait4 status 00002a00, restart, and continued
heartbeats still passed. Both workers completed the RAM-file and IPC checks.
The updated verifier rejected a copied exec-only result in
work/userland-ipc-negative, proving that old milestones alone do not pass.

Final hashes: init
b519aa9d6c849949ca73c70e99b6ef56dfe5111ca5aa270771fd3f679ad0138d;
worker a5a310483d999a5038da85b08184f2ec3c80ec3b3546d02dae27b5dc439f5abd;
root b1e19227f8f004c41b44a470f79d7750827df376d9f0c30c1c2363d6df067363;
payload 42a402a2c38e030c7d207e83b9f43d08901d0b6630ed7a4c5e7724f509dc6e9b.
See run/verification.json and run/fb.txt under that directory. Previous
exec-only milestone: 039b4a1. No new kernel build or phone access was needed.
Remaining work includes signals/service control, richer userland, and the
separate MT6897 hardware backend. These are RAM-root observations in QEMU.

Diagnostic exec/supervision milestone (2026-10-29, QEMU/RAM only; this
commit): tools/build-sweet-userland.sh builds separate signed arm64 init and
worker executables. PID 1 creates /sbin/worker on the writable RAM HFS root,
forks and execs it with argv once, then uses wait4(WNOHANG) to reap its deliberate
exit 42 (raw status 00002a00). It requires that status before restarting the
worker with argv stay; unexpected exits stop with TEST FAILED. Worker entry
also checks argc and a PID greater than 1. No kernel change was required:
Actions run 104 / 40939563499 at 4ada6fda3a7b6bd6b3c880698b35c0bc30ebbf8e
provided the reused kernel. Final 90-second QEMU run completed with
no_panic_observed and zero unknown glyphs; every semantic check passed,
including two exec entries, wait status, restart, and continued parent/worker
heartbeats. The verifier correctly rejected the earlier failed compact-worker
run despite its no_panic_observed snapshot.

Artifacts: work/userland-exec-final/{launchd,sweet-worker.macho,root.hfs,
payload.bin,run/fb.txt,run/verification.json}. Reproduce with the single command
documented in duchamp/USERLAND-QEMU.md. Kernel SHA-256:
82fc8fe1391bea90bcce9ed2d4e8a2ff8204667f6785857873717564ec9331c9;
init cba363ff31a227b0ca4aa410196148f0abcb7146a0a885455e993625a931da73;
worker 2918b89ab249a0f54f2e63a89355e746669dcd3cb6f6b315581838391bd8a64a;
root 0a19b8c12959f48d292bedd8a018a461de832dd043cd9932747677f8766ac34f;
payload 30bfd3b0b46aabb1b673cff58165ba5fa0b84281260d25d07d154c399e54ecde.

Failed experiments retained: the compact worker used an invalid 4K file offset
for this 16K arm64 loader; it has been replaced with the standard Mach-O layout.
An earlier unsuccessful writable hpmount attempt altered work/root-multiproc.hfs;
do not reuse it. All final images use the unchanged original HFS baseline
work/qemu-rootvnode-98/root-with-launchd.hfs (e5b5c1b6...36726414a).
Phone, UFS, and boot partitions were not accessed. Next work can add IPC and
file-service tests in QEMU; a dynamic userland and MT6897 storage remain
separate unfinished work. This milestone is a diagnostic userspace, not iOS.

Direct device read (2026-10-24): ADB/root reports Linux
`6.1.57-android14-11` on aarch64 and the expected ARM feature set. Android's
`dmesg` exposes no usable EL or PSCI diagnostic, so the current EL cannot be
confirmed from userspace. Do not add a guessed SMC path; the handoff backend
must remain rejected until EL/firmware entry state is measured or documented.

Live platform contract (2026-10-24): the decompiled live FDT declares
`arm,psci-1.0` with `method = "smc"`, CPU nodes with `enable-method =
"psci"`, `arm,gic-v3`, and an ARMv8 timer plus MediaTek MT6897 system-timer
nodes. This is concrete platform data for the future backend; it does not
prove that an arbitrary loader may invoke PSCI from its current exception
level, so no SMC or hardware handoff was attempted.

DTB memory comparison (2026-10-24): `vendor_boot`'s embedded DTB describes
only `0x40000000`..`0x80000000` (1 GiB), while the live FDT describes RAM up to
`0x300000000` and includes the high range used by the payload at
`0x1c0000000`. The guard accepts the live FDT and rejects the embedded DTB as
`payload window is outside live RAM`. This rejection is now documented as a
required safety property for future loader tests.

Vendor DT table extraction (2026-10-24): `vendor_boot_a` contains an Android
DT table with magic `0xd7b7ab1e`, total size `396071`, one entry, and entry
DTB size `396007` at table offset `64`. The extracted embedded DTB has SHA256
`8aeadd5306b84193384c0f14dea51c1ba23afd7419c7150c1ea1eb2566c49022`, which
differs from the live `/sys/firmware/fdt` SHA256
`9c49589f70044127be8941a9ea5537977f440ccd5ac15cfd24e120c8a1181d29`.
Running the guard against the embedded DTB rejects the current payload as
`payload window is outside live RAM`; the live FDT remains authoritative for
the current boot. This demonstrates that boot-time DT selection/overlay or
memory description changes the handoff contract; no image was modified.

Handoff bounds hardening (2026-10-24): `mt6897_handoff_run` now checks
window-end overflow and requires the complete 0x4000-byte boot-args page to
fit inside the validated window, not merely its starting address. Mock success
and translation-failure tests still pass (`MDTIX` and `MDT`); object size is
372 bytes.

Read-only MT6897 boot-chain observations (2026-10-24): the live device is
`duchamp`, `mt6897`, slot `_a`, with root through Magisk. The by-name links
resolve to `boot_a -> sdc38`, `vendor_boot_a -> sdc39`, and `dtbo_a -> sdc41`.
`/proc/cmdline` identifies the MediaTek Android boot path and `hwid.project_name`
is `duchamp`. `/proc/iomem` reports system RAM beginning at `0x40000000` and a
high range beginning at `0x1c0000000`; it also reports the reserved framebuffer
range `0xfcc2f000-0x100000000`, matching the loader framebuffer base
`0xfcc2f000`. These observations do not prove that XNU can reuse Android's
memory map or that a handoff is safe; no partition was read or written.

MT6897 handoff contract (2026-10-24): added `duchamp/loader/mt6897_handoff.c`
and `.h`. It validates aligned in-window entry/boot-args and enforces the
order disable-MMU, clean data cache, install translation, invalidate I-cache,
then enter-XNU through explicit callbacks. Freestanding Clang compilation
passed; object size is 348 bytes. This is a guarded contract/mock boundary,
not a register-level MT6897 backend: no hardware callback or physical handoff
was executed.

MT6897 local loader wrapper (2026-10-24): added `duchamp/loader/mt6897_loader.c`
and `.h`. The wrapper calls the existing bounded materializer and emits a
small handoff manifest with entry, boot-args, memory window, and Duchamp
framebuffer geometry. WSL Clang build passed; the wrapper object is 161 bytes.
With the extracted phone FDT and verified Duchamp payload, the harness returned
`mt6897_prepare=0`, 10 segments, entry `0x1c1480488`, boot args
`0x1c24dc000`, framebuffer `0xfcc2f000` at `1220x2712`. A `0x1000` window was
rejected with result 4. This remains a local bounded-memory test: no physical
RAM mapping, MediaTek DRAM/MMU/cache setup, exception-level change, or XNU
branch exists, and no phone boot was attempted.

QEMU handoff check (2026-10-23): the C materializer output was compared with
`tools/qemu-sweet.py`'s host image using the same payload and Duchamp profile.
Both images were 38,666,240 bytes with SHA256
`098ba6d9bcc62ec3cd437713a416ef17fd53d145b907c1b0cae035696505b62b` and zero
byte differences; entry `0x1c1480488` and boot_args `0x1c24dc000` also matched.
The subsequent QEMU run was not completed in this Windows environment:
Unix QMP sockets are unavailable, and the TCP fallback is blocked by
`WinError 10013` before QMP can connect. The QEMU command was also made
`-nodefaults` so it does not request unrelated `efi-virtio.rom` firmware. This
is an environment limitation, not evidence of an XNU or payload failure.

QEMU controlled jump completed (2026-10-23): the local QEMU process was
allowed to bind its monitoring endpoint and `qemu-sweet.py --framebuffer
duchamp` ran the verified payload for 10 seconds. The framebuffer decoder showed
every marker from `SWEET EARLY 1` through `SWEET EARLY 15`, followed by
`DUCHAMP XNU MEMORY READY`; no panic text appeared and QEMU produced a register
snapshot. The decoder still reports 3 unknown cells from the intentional bottom
stage band, so the status is `incomplete_decode`/snapshot-only rather than a
clean decode. This is a QEMU `virt` result, not MT6897 hardware validation.

Bounded materialization (2026-10-23): added `duchamp/loader/materialize.c` and
`materialize.h`. This stage applies the validated dry-run plan only to a
caller-provided byte window: it copies 10 payload segments, zero-fills their
tails, places the ADT, and creates revision-2 `boot_args`. It contains no raw
physical-memory access, cache/MMU transition, or XNU branch. Strict bare-AArch64
compilation and execution under Unicorn passed. The first segment and ADT were
byte-identical to the payload, boot args reported revision/version 2/2,
physBase `0x1c0000000`, top `0x1c24e0000`, and the exact Duchamp framebuffer.
Reducing the required `0x24e0000`-byte window by one byte returned
`DUCHAMP_GUARD_PLATFORM`, left the destination marker unchanged, and zeroed the
result plan before any copy.

Dry-run loader plan (2026-10-23): added `duchamp/loader/plan.c` and `plan.h`.
After the guard succeeds, this freestanding layer emits the segment source
offsets, physical destinations, copy/zero lengths, ADT placement, revision-2
boot-args values, entry address, and Duchamp framebuffer contract. It contains
no destination-memory writes and no branch to XNU. Strict bare-AArch64
compilation passed. The actual ARM64 function was executed under Unicorn with
the captured MT6897 FDT and verified payload: it returned 10 segments, entry
`0x1c1480488`, ADT `0x1c24d8000`, boot_args `0x1c24dc000`, framebuffer
`0xfcc2f000`/4992/1220x2712x32, and the expected virtual ADT address. A bad
framebuffer stride returned `DUCHAMP_GUARD_PLATFORM` and a fully zeroed plan.

Freestanding loader guard (2026-10-23): added `duchamp/loader/guard.c` and
`guard.h`. The allocation-free ARM64 core validates SWEETXNU v1 payload bounds,
entry placement, a version-17 MT6897 FDT, live RAM containment, fixed and dynamic
reservations, and caller-supplied occupied ranges. It only returns a placement
plan; it contains no payload copy, cache/MMU transition, exception-level change,
or jump to XNU. It compiled with strict freestanding AArch64 warnings enabled and
was executed under Unicorn against the captured MT6897 FDT and real payload.
The valid case returned physical base `0x1c0000000`, entry `0x1c1480488`, ADT
`0x1c24d8000`, boot_args `0x1c24dc000`, and top `0x1c24e0000`. Negative cases
rejected an occupied-range collision, bad payload magic, and truncated FDT, and
left the output plan zeroed. This is host/emulator validation only.

QEMU framebuffer harness update (2026-10-23): `tools/qemu-sweet.py` now accepts
`--framebuffer duchamp`. It consistently uses base 0xfcc2f000, 1220x2712 and
stride 4992 in XNU boot_args, framebuffer capture, PNG conversion and console
decoding. The old hard-coded Sweet geometry remains the default. This repairs
the host harness mismatch only; it does not validate the MT6897 display path.

Full DUCHAMP kernel/QEMU verification (2026-10-23): GitHub Actions run
`39830616234` completed successfully at `9939a0e`; the downloaded artifact ZIP
matched GitHub SHA256 `5cb02f0323e17679ab47a431e039a07a29143d2de45cb12c22ff57f375195f53`,
and `kernel.development.sweet` matched its included SHA256
`4ce45cc4ec6fb7bd6f7db075fffca90816b586022b1f3e00d937a3dedc9116c6`.
An isolated QEMU `virt` run used the 0x1c0000000 + 512 MiB high-memory window,
the minimal one-CPU QEMU ADT, and the Duchamp framebuffer geometry. The screen
reached `arm_vm_init returned` followed by the intentional
`DUCHAMP XNU MEMORY READY` stop, with no panic. The decoder reported three
unknown glyph cells because its final sampled text row overlaps the deliberate
64x32 Stage-0 color band at the physical bottom of the screen; visual inspection
confirmed the text itself is intact. This proves the compiled early-memory path
in QEMU only, not MT6897 hardware execution or display-controller compatibility.

Loader planning guard (2026-10-23): added `tools/duchamp-loader-guard.py`. It
parses a version-17 MT6897 FDT and SWEETXNU v1 payload, requires 2/2 address
cells and identity-mapped reserved-memory, checks the payload window is inside
live RAM, rejects fixed reservations and every overlapping dynamic
`alloc-ranges`, validates all Mach-O payload segment/file bounds and the entry,
and rejects caller-supplied loader/DTB/stack/source ranges. It emits addresses
only and never copies or jumps. Against the captured FDT and verified kernel it
accepted the high-window plan (`phys_base=0x1c0000000`, entry `0x1c1480488`,
ADT `0x1c24d8000`, boot_args `0x1c24dc000`) after checking 52 fixed, four
dynamic and three occupied ranges. Negative checks rejected an occupied-range
collision, bad magic, bad version and a truncated FDT. This remains an offline
snapshot check; a future loader must invoke equivalent checks on the FDT from
the same boot.

Build dispatched: https://github.com/Mehmed911/ios-sweet/actions/runs/39828208185 at source f22878076d156c246bd0605e173e181b0982ddcc. GitHub currently reports queued (no runner/steps started yet); do not claim a linked kernel or a phone XNU boot. Patch commit: 1cadc81582597a05a49d03d219b23a3c2504f5a5. Expected compile-time stop: DUCHAMP XNU MEMORY READY after arm_vm_init.

The low RAM candidate in the previous handoff is superseded. The captured FDT contains dynamic allocation requests whose allowed ranges overlap low RAM. The revised planner excludes each entire alloc-ranges region as well as 52 fixed reservations and nested iomem exclusions. New hardware candidate: physical 0x1c0000000 + 0x20000000 (512 MiB). It has no fixed or dynamic conflicts in that captured tree. It remains a candidate: a loader must repeat checks on the actual boot FDT and check overlap with its Image, DTB, payload and framebuffer before any writes.

Minimal ADTs for one CPU pass serialization/contract tests and reject Qualcomm UFS, wrong timer/GIC and unsafe memory. Candidate hardware timebase is 13MHz and virtual timer INTID 27. QEMU control tests use QEMU GIC addresses/timebase, not MTK emulation. The earlier reference kernel reached arm_vm_init return at both low RAM and the new high RAM base in QEMU, then hit the expected missing DUCHAMPBOOT platform driver panic later in IOKit. That later panic is NOT a successful boot, and the new compile-time stop precedes it. The geometry/stop-patched kernel still needs successful CI and its own QEMU test.

No phone changes in this phase. The POCO still has restored Android; only the standalone 16KB MMU diagnostic has run on its hardware.

---

# DUCHAMP bootstrap handoff — 2026-10-21

This branch is a POCO X6 Pro (MT6897) early-memory experiment, separate from the Redmi/SWEET results below. Patch 0082 replaces bootstrap framebuffer geometry and forces the SWEET build to define DUCHAMP. It deliberately halts after arm_vm_init, before serial_init, PE_init_platform(TRUE), IOKit and BSD. Expected marker: DUCHAMP XNU MEMORY READY.

Physical POCO evidence so far: standalone diagnostic entered EL1, CNTFRQ=13000000, reported TGran16 support, then passed ten actual 16KB alias read/write checks with MMU enabled and restored it off. Android boot_a was restored and independently hash-verified after that trial. XNU and iOS have NOT executed on this POCO.

Local checks: all four changed XNU source files compile individually for SWEET and DUCHAMP (eight objects); geometry and clean patch application checks pass. A minimal single-CPU ADT candidate uses MT6897 GICD 0x0c400000, GICR 0x0c440000, virtual timer INTID 27, and no Qualcomm storage/input/USB nodes. Candidate RAM 0xa0000000..0xbe000000 comes only from a captured map; a future loader must validate the live FDT and every reserved range before writing it. No device dumps or Apple artifacts are committed.

Kernel CI on this branch is the next validation. Even a successful build is not a phone boot image: it still needs QEMU validation and an MT6897 loader with live memory-range checks. Preserve Android and the original boot image.

---

# iOS 16 on sweet (Redmi Note 10 Pro, SM7150) - working notes

## Agent handoff / active work (2026-10-15, latest)

### >>> UPDATE 2026-10-18 (read first, then the 10-17 handoff below) <<<

**STATE at end of 2026-10-18 (evening):**
- On the phone: userdata = **image v15** (`/run/media/dipa/android/ios-sweet-ipsw/ios16-root-20H392-v15.img/.simg`; = v14 + `/private/var/preferences/SystemConfiguration/preferences.plist` with one network service "USB Ethernet": Interface DeviceName ue0 Type Ethernet, IPv4 Manual 192.168.7.2/24 router 192.168.7.1, DNS 1.1.1.1 8.8.8.8, set "Automatic" as CurrentSet). Fallback image v14 (v12/v13 deleted).
- Kernels: **0078** = all 8 cores (`cpus=8`, cpu6/7 = A76, homogeneous SMP; mkadt now emits 8 CPU nodes; ADT `shim/out/sweet-0078hi.adt`); **0079** = display off/on via IOMFB selector 12 kern_RequestPowerChange(state) (fade over 6 vsyncs, then black; verified: power button gives "SWEET FB: display off/on"); **0080** = `SWEET NET: <proc> route add/delete/change ...` and `... add/delete address ...` trace (built, `shim/out/shim-boot-0080s.img`, NOT booted yet).
- **Internet over USB: not working yet.** Host side is ready (temporary iptables: FORWARD accept for 192.168.7.0/24 + MASQUERADE, comment "ios-sweet"; lost on host reboot). With v15 the phone sent no DNS and no outbound traffic (only mDNS/ARP) -> configd probably did not apply the service (or did, without default route/DNS). Next: boot 0080s on v15, watch `SWEET NET` lines (does configd add 192.168.7.2 / default route on ue0?). If configd ignores ue0 (not an IOKit IONetworkInterface; configd 1241.140.6 source in `research/configd-1241`, SCNetworkInterface createInterface needs IONetworkInterface -> controller (IOMACAddress, SelfNamed) -> bus), add IOKit stand-ins and/or rename the ifnet to en*.
- Live log listener (`nc -ukl 5140`) may still be running, writing `logs/live-0078s.txt`.

**LIVE LOG over USB (0077, boot 0077s): no more recovery round-trips.** Boot an image with `sweetusb=2`, run `tools/sweet-usbnet.sh logs/live-NAME.txt` on the PC: it waits for the phone's CDC-ECM interface, sets 192.168.7.1/24 (sudo) and prints/saves the kernel console the phone streams every 100 ms as UDP to 192.168.7.1:5140 (starts with the last 64 KiB). `ping 192.168.7.2` checks the link. Current image: `shim/out/shim-boot-0077s.img` (kernel 0077, ADT sweet-0069hi, cpus=6, sweetfb_noconsole=1, sweetfb_hz=30, sweetusb=2). The recovery pull (`tools/sweet-log-pull.sh`) is still the way after a panic/hang before USB comes up.

**🎉 USB networking works (boot 0076s, 18:24 local): `ping 192.168.7.2` from the PC answers in ~1 ms, 0 % loss (200-packet burst, 1500-byte frames, 512/1024-byte frames).** 0075: CDC-ECM function (bulk 0x81/0x01, interrupt 0x82 NETWORK_CONNECTION; host MAC 02:00:5e:77:ee:01) + kernel ethernet ifnet `ue0` (legacy output, header strip like if_fake) with 192.168.7.2/24 set from the kernel (proto_plumb + SIOCAIFADDR on an in-kernel socket). 0076: received frames into one cluster mbuf (mbuf_allocpacket gave a first mbuf of length 0 -> panic "Failed mbuf validity check: len -14"). Host side (Linux cdc_ether, interface `enp0s20f0u3u1`): `nmcli dev set IF managed no; sudo ip addr add 192.168.7.1/24 dev IF; sudo ip link set IF up`. Boot image `shim/out/shim-boot-0076s.img` (`sweetusb=2`). iOS itself does not see ue0 yet (configd needs an IONetworkInterface in IOKit).

**USB device mode works (boot 0074s, 17:45 local): the host enumerates the phone at high speed as `1209:0001 ios-sweet "Sweet iOS (USB bring-up)"`.** 0072 read-only probe: ABL leaves the USB30_PRIM GDSC and all 7 USB clocks on, DWC3 v3.20a (GSNPSID 0x5533320a) in device mode (GCTL 0x00112000), halted (DCTL RUN_STOP 0, DSTS 0x00d3de04), event buffer still at ABL's 0xfdfc8000, QUSB2 PHY alive. 0073 (`sweetusb=2`): DCTL soft reset, own event buffer (polled, interrupt masked), ep0 DEPSTARTCFG/SETEPCONFIG/SETTRANSFRESOURCE, setup TRB, RUN_STOP; control-transfer state machine as Linux ep0.c; descriptors: vendor class, no data endpoints. It ran but no event came: **0074** forces the VBUS session in the Qualcomm wrapper (QSCRATCH 0xa6f8800: HS_PHY_CTRL |= UTMI_OTG_VBUS_VALID(20)|SW_SESSVLD_SEL(28), SS_PHY_CTRL |= LANE0_PWR_PRESENT(24), as Linux dwc3_qcom_vbus_override_enable) -> connect + enumeration. Image `shim/out/shim-boot-0074s.img`. Black Phone app: main thread waits in -[VMVoicemailManager fetchAccounts] (sync XPC; voicemail needs the modem).

**Navigation works (boot 0071s on v14, log `logs/boot-0071s.txt`):** swipe up from the bottom edge returns to the home screen; app switcher works. Two fixes: **0070** pid_hibernate (syscall 435 was nosys on the macOS config -> SIGSYS killed SpringBoard in -[SBToAppsWorkspaceTransaction _didComplete] when an app left the foreground; the only CONFIG_EMBEDDED-only entry in syscalls.master); **0071** touches starting within 48 px of an edge carry kIOHIDDigitizerEventFromEdgeTip (UIKit `_UIEventHIDTouchEdgeTypeForHIDEvent` reads the digitizer EventMask 0xb0007 bits 0x800/0x1000/0x2000/0x40000). Diagnosed, not fixed: Settings (Preferences) SIGTRAP in PodcastsUI func_1cdc47c58: force-unwrap of `URL.volumeTotalCapacity` (nil on our HFS+ root). Phone/Photos/Messages show black (MobilePhone launches, no crash) - next: stack samples via boot-arg `sweetsample=MobilePhone,MobileSlideShow,MobileSMS,SpringBoard` (image `shim/out/shim-boot-0071s.img`).

**🎉🎉 MILESTONE 2026-10-18 ~15:30 local: iOS 16.7 SPRINGBOARD HOME SCREEN ON THE PHONE** (boot `shim/out/shim-boot-0069s.img` = kernel 0069 + ADT `shim/out/sweet-0069hi.adt`, image **v14**; log `logs/boot-0069s-v14-HOMESCREEN.txt`). Home screen with a few apps, Settings opens, Control Center / lock screen / notification center work, touch + buttons work, 6 A55 cores (`cpus=6`), `sweetfb_noconsole=1 sweetfb_hz=30`. Known issue: cannot leave Settings (home gesture / AssistiveTouch home do nothing) - to investigate.
What it took today (in order): 0058 HID services (Apple IOHIDFamily-1915 user client), 0059 iPhone X identity (hw.product etc.), 0060 SPMI keys + GENI touch, 0061 1125x2436 presented display, 0062 RPMh L11C touch power + IOPMPowerSource battery, 0063 GENI FIFO packing (Goodix GT9896), 0064 PRIV_WORK_INTERVAL grant (SpringBoard "Failed to create work interval"), 0065 SMP via PSCI (6 A55), 0066 crash map regions, 0067 console mute without cons_ops write, 0068 IOSurface lookup of an already-mapped surface returns base -1 (backboardd snapshot crash), 0069 UFS log flush 10 s. Image v13: CommCenter removed from launchd.plist, BKNoWatchdogs. **Image v14** = v13 + Setup skipped (`/var/mobile/Library/Preferences/com.apple.purplebuddy.plist` SetupDone/SetupFinishedAllSteps true, SetupVersion 11, daemonizeNeedsToRun false; purplebuddy.notbackedup mini-buddy flags false; managedconfiguration.notbackedup LockdownActivationIndicatesCloudConfigurationAvailable false; springboard MCForceShowCloudConfigurationUI false) + mobileactivationd data ark seeded (`/private/var/containers/Data/System/D90C94C4-F94E-4FCF-8A28-A93BE3846D8E/Library/internal/data_ark.plist`, -ActivationState Activated etc.) + MediaToolbox D22/D221/Default SubServerConfiguration StartRecorderServer=false (mediaserverd crash loop: portrait-filter prewarm called NULL GL). **Activation:** ADT /chosen certificate-production-status 0, effective-production-status-ap 0, certificate-security-mode 1, effective-security-mode-sep 1 -> mobileactivationd's native Hactivation branch (Codex `codex/activation/report.md`; alternative 4-byte daemon patch documented there). Fallback image v13; v12 deleted.

**🎉 TOUCH WORKS (boot 0063u on image v13, 2026-10-18 ~13:15 local):** tapping (i) on Setup's Hello opens the device-info sheet; swipe-up is recognised (spinner, then back to Hello - under investigation). Chain: RPMh L11C vote (0062, `bsd/dev/sweet_rpmh.c`) -> GT9896 @0x5d on GENI SE7 (0063 fixed FIFO packing: register address went out byte-swapped) -> sweet_hid_touch -> SweetHIDTouch -> backboardd. Battery icon OK (0062 SweetBattery IOPMPowerSource, static 100 %). **Image v13** (= v12 + CommCenter jobs removed from launchd.plist + `BKNoWatchdogs`=true and `FBLaunchWatchdogExceptions{com.apple.purplebuddy:100}` in /var/mobile/Library/Preferences/com.apple.springboard.plist): Setup no longer killed by the scene-create watchdog (it blocked in CoreTelephony getSubscriptionInfo -> CommCenter, Codex `codex/setup/report.md`; that report also lists how to skip Setup: SetupDone/SetupFinishedAllSteps/SetupVersion=11 in com.apple.purplebuddy.plist + activation check). v9 deleted, fallback = v12. Input latency ~1 min with 1 CPU -> Codex task 11 = SMP via PSCI (`codex/smp/`).

**INPUT WORKS (boot 0060u on a freshly flashed v12, log `logs/boot-0060u.txt`):** power, volume up, volume down reach iOS (PMIC -> sweet_keys.c -> SweetHIDButtons -> backboardd). Power locks/unlocks (screen "off" shows the kernel console because the panel never really turns off). **Device identity fixed: iPhone X** (home indicator, Face-ID-style Setup). Earlier test (0059u, `sweethidtest=15` fake Home presses) advanced Setup from Hello to the language list.
- **0058** HID: `iokit/Kernel/arm/hid/`: IOHIDEventServiceUserClient + IOHIDEventServiceQueue + IOHIDEvent compiled UNCHANGED from Apple IOHIDFamily-1915.140.3 (= exact version of the iOS 16.7 IOHIDLib, clone in `research/iohid-1915`) over our minimal IOHIDEventService (SweetHID.cpp: SweetHIDButtons consumer page 0x0C power 0x30 / vol 0xE9/0xEA / menu 0x40; SweetHIDTouch digitizer collections). C hooks `sweet_hid_key(key, down)` (0 power, 1 vol+, 2 vol-, 3 home) and `sweet_hid_touch(finger, down, x, y)`. HID logs go to IOLog. Boot-arg `sweethidtest=N` = fake Home press every N s.
- **0059** identity: hw.machine/hw.model/hw.target/hw.product from the ADT (macOS-config kernel used to answer "iPad8,6"/"Redmi Note 10 Pro"). mkadt: root compatible `D22AP|iPhone10,3|xiaomi,sweet|...`, model iPhone10,3, target-type D22, `/product` copied from the real D22AP device tree (`research/ipsw-x/d22ap.adt`, extracted from the IPSW, NOT in git), `/buttons home-button-type 2`. Codex report `codex/mg/report.md`: MG ProductType = sysctl **hw.product** (unrecognized -> iPod), HWModelStr = hw.target, HomeButtonType = `/buttons/home-button-type`; disk cache `/private/var/containers/Shared/SystemGroup/systemgroup.com.apple.mobilegestaltcache/Library/Caches/com.apple.MobileGestalt.plist` (keyed by build + UUID only -> stale iPod answers survived; reflashed clean v12 to clear it).
- **0060** drivers by Codex (`codex/input/hw-report.md`): `bsd/dev/sweet_keys.c` (SPMI arbiter v5 observer reads, PON 0x810 bits KPDPWR/RESIN SID0, PM6150L GPIO2 SID4 0xc110; works), `bsd/dev/sweet_touch.c` (GENI SE7 I2C @0xa84000, starts 45 s after boot). Touch result: SE7 fw ok (proto 3) but **0x5d and 0x38 both time out -> touch IC unpowered** (L11C LDO needs an RPMh vote). Codex task 8 = RPMh client (`codex/rpmh/`), task 7 = battery (`codex/battery/`).
- **0061** (CI 39117078444): red status bar "rdar:45025538" = UIKit "No status bar visual provider for screen" (360x800 pt is no real iPhone). AppleCLCD now presents **1125x2436** (iPhone X) and shows the centered 1080x2400; touch mapped the same; ADT canvas 1125x2436. `sweetfb_native=1` reverts.
- Images: `shim/out/shim-boot-0060b.img` (0060 + /buttons ADT `sweet-0060hi.adt`). Next: 0061 image with ADT from current mkadt.

### >>> HANDOFF 2026-10-17 late (read this first) <<<

**STATE: iOS 16.7 Setup.app "Hello" screen is ON THE PHONE** (boot `shim/out/shim-boot-0057u.img` on image v12). Photo `/run/media/dipa/android/ios-sweet-work/MILESTONE-setup-hello-2026-10-17.jpg`. SpringBoard + backboardd + Setup run; nothing crashes in the GUI path. Remaining crash/relaunch loops: installcoordinationd (should be fixed by 0057, unverified), mediaserverd (VirtualAudio removed in v12, unverified), mobileactivationd (~100/boot, not analysed), bluetoothd + fairplayd.H2 relaunch constantly (no hardware).

**What is on the phone now:** userdata = image **v12** (`/run/media/dipa/android/ios-sweet-ipsw/ios16-root-20H392-v12.img` + `.simg` + `.sha256`; v9 kept as fallback, v8/v10/v11 deleted or superseded). Kernel **0057** (`xnu/out-0057`, CI `39067532732`). ADT **`shim/out/sweet-0057hi.adt`** (QEMU twin `research/q0057-hi.adt`). Boot image **`shim/out/shim-boot-0057u.img`**. Boot args: `debug=0xc serial=3 cpus=1 keepsyms=1 -enable_kprintf_spam -noprogress rd=ufsroot0 unentitled_ios_sim_launch=1 ignition_level=1 wdt_test=no_user_checkin ufsrw=1 rootrw=1 launchd_unsecure_cache=1 wdt=-1`.

**Build a phone image** (kernel K, ADT A): `python3 tools/mkpayload.py $K $A shim/out/payload-X.bin --cmdline "$B" && (cd shim && ./build.sh ../shim/out/payload-X.bin && cp out/shim-boot.img out/shim-boot-X.img)` then check `python3 tools/unpack_bootv2.py shim/out/shim-boot-X.img shim/out/check-X && cmp shim/out/check-X/ramdisk shim/out/payload-X.bin`. QEMU smoke test: `python3 tools/mkpayload.py $K research/q0057-hi.adt $S/csq/payloadX.bin --ramdisk $S/csq/root-fork.img --cmdline "debug=0xc serial=3 cpus=1 keepsyms=1 -enable_kprintf_spam -noprogress rd=md0"` + `PATH=~/swift/usr/bin:$PATH python3 tools/qemu-sweet.py ... --secs 40 --kernel $K --fail-on-panic` (S = scratchpad; root-fork.img lives in the session scratchpad csq/ dir and may be gone in a new session).

**Kernel workflow:** edit `research/bt28/xnu/...` (keep the pre-edit copy in `research/preNNNN/`), syntax check `python3 tools/xnu-cc.py research/run28.log research/bt28 <file>`, make `xnu/patches/NNNN-*.patch` with `diff -u pre bt28 | sed` path rewrite, add new/changed files to `research/check-patch-order.py` list, run it (must say applied + MATCH), commit + push -> GitHub Actions `xnu` builds (~8 min) -> `gh run download <id> -R dipa-studio/ios-sweet -n xnu-kernel -D xnu/out-NNNN`. **Repo is PUBLIC since 2026-10-17** (private macOS runner minutes ran out: "recent account payments have failed"); public = free runners. Commit trailer: only `Co-Authored-By: dipa-studio <183933817+dipa-studio@users.noreply.github.com>`.

**Phone workflow (user does buttons, Claude runs commands):**
- Boot test kernel: phone in fastboot -> `fastboot boot shim/out/shim-boot-X.img`. NEVER `fastboot getvar`.
- **Read logs WITHOUT filming:** after a test the user holds Power+VolDown -> fastboot -> `fastboot boot recovery/recovery.img` (OrangeFox, temp) -> wait for `adb shell true` -> `tools/sweet-log-pull.sh /run/media/dipa/android/ios-sweet-work/logs/<name>.txt` (reads the 4 MiB console ring the kernel keeps in the last 1025 blocks of userdata; patch 0047). Then `adb reboot bootloader` brings the phone back to fastboot without the user.
- **Flash a root image:** `fastboot flash -S 512M userdata <img>.simg` (7 min, 25 chunks). After a big flash the Xiaomi ABL fastboot hangs: next `fastboot boot` stalls at "Sending" -> the USER must re-enter fastboot by hand (Power+VolDown). Do not retry commands against the hung ABL. A flash right after `adb reboot bootloader` once failed on chunk 1 (USB protocol error): just retry. User must NOT unplug during flash (once interrupted at 25/25 -> reflash).
- **Edit the phone root without reflashing (same-length only):** find the file's raw offset in the local image (it is one extent; search the image for its first 4 KiB), compare with `adb exec-out dd if=/dev/block/sda34 ...`, then `adb push` changed 4 KiB blocks and `dd of=/dev/block/sda34 seek=... conv=notrunc,fsync`, read back. Recovery kernel has no hfsplus.
- **Pull the whole phone root** (12 min): `adb exec-out "dd if=/dev/block/sda34 bs=1048576 count=16384" > img`; mount ro with udisksctl or `sudo mount -t hfsplus -o loop,ro`. To write into a pulled image: `sudo fsck.hfsplus -fy` first (volume is never cleanly unmounted -> Linux mounts ro even with -o force), then `sudo mount -t hfsplus -o loop,force`.
- Making images: copy latest img with `cp --sparse=always`, mount rw with force, change, `sync; umount`, `sha256sum`, `img2simg`. Keep only the latest image + one fallback on the SSD (/home is ~98% full; big work files live in `/run/media/dipa/android/ios-sweet-work/`, old kernels/images archived in `.../ios-sweet-work/archive/`).

**Diagnostics built into the kernel (all SWEET-only):** persistent console log (0047, boot-arg sweetlog=0 off; flush every ~1 s); `|name| text` copies of /dev/null writes for processes in `sweetnull` (default backboardd,SpringBoard; 0048); `IOK name:` IOKit lookup/open trace for `sweetiolog` (default backboardd,SpringBoard; 0049/0054, 400 lines max); `SWEET Sandbox: proc op N` (0050); `STR ...` heap text dump on SIGABRT/SIGTRAP for `sweetscan` (default backboardd,SpringBoard; 0051/0053) - this is how NSException/BSAssert reasons were found; `SMP name tN pc .. bt ..` user stack sampler for `sweetsample` (default SpringBoard,backboardd; first at 90 s then every 120 s, 40 samples, 16 frames; 0054/0055); `SWEET FB: N swaps` every 1000 swaps; `CRASH name ...` crash reports (0043/0044). Symbolicate cache addresses with `ipsw dyld a2s research/dsc/dyld_shared_cache_arm64 <addr - slide>`; main-binary addresses: addr - mh + 0x100000000.

**Patches added today (0046-0057, all CI-built):** 0046 IOSurface (IOCoreSurfaceRoot) + IOMobileFramebuffer (AppleCLCD on /arm-io/disp0) + arm-io nubs; 0047 persistent log; 0048 /dev/null tee; 0049 IOKit trace; 0050 permissive "Sandbox" MAC policy; 0051/0053 heap text on crash; 0052 RENAME_SWAP via exchangedata on HFS; 0054/0055 sampler, swap counter, AKS selectors 35 (extended device state = 17) and 101; 0056 panel copy from the vsync timer at 10 Hz (sweetfb_hz) instead of every swap; 0057 no config_ext_resolver (ACL group entries resolve without memberd). ADT (tools/mkadt.py): /arm-io/disp0, /chosen/display-scale 3, /chosen/unique-chip-id (synthetic 0x5357454554000001) + chip-id 0x8015 -> IOPlatformUUID A9683613-3704-53F2-95D0-98A8FB574E78. Image v9-v12: /private/var/containers/{Bundle,Data/System,Shared/SystemGroup,Temp}; launchd.plist StandardOut/ErrorPath renamed to ...PatX (pointing jobs at /dev/console stops them launching: EACCES); v12: LastSystemVersion=20H392 in plain /var/mobile/Library/Preferences/com.apple.migration.plist (stops the 1-hour data migration that ran every boot), VirtualAudio.plugin moved to /Library/Audio/Plug-Ins/HAL.disabled/.

**Codex helper** (`codex exec --skip-git-repo-check -m gpt-6.1-sol -c model_reasoning_effort=high -s workspace-write -C /run/media/dipa/android/ios-sweet-work/codex -o OUT "$(cat task.md)" < /dev/null`, run detached with setsid nohup; config already defaults to gpt-6.1-sol high). Reports in `/run/media/dipa/android/ios-sweet-work/codex/`: mediaserverd-report.md, installcoordinationd-report.md (-> 0057), ufs-performance.md (ranked UFS speed plan), **ufs/0058-sweet-ufs-faster.patch** (READY, not yet applied: ufslogsecs default 10 s log flush batching, optional ufscache=1 directional cache ops, optional ufswait=1 spin-then-sleep; syntax-checked, host-stub verified; see ufs/README.md). Apply it as patch 0058 after review.

**Claude safety-classifier note:** several messages about QuartzCore renderer selection / writing an HFS reader tool were cut off by an automatic classifier (false positives, user agrees). Keep those topics short or let them be; they are not blockers now (rendering already works).

**NEXT STEPS (in order):**
1. **Input** (Setup stuck on Hello): touch + power + volume as IOHIDEventService/IOHIDDevice services backboardd matches (log shows backboardd matching IOHIDDevice with DeviceUsagePairs and IOService with HIDServiceSupport=true). Phone hardware: Goodix/Focaltech touch over I2C/SPI (check live DT `dtb/`), buttons via PMIC (pon) and GPIO keys. Start with a fake HID service (e.g. power button via a timer or boot-arg) to learn the ABI, then real drivers.
2. **Device identity**: MobileGestalt reports iPod + Home button. Add /product node / product-type (iPhone10,3, D22AP), device class iPhone, home-button-less (Face ID) properties in mkadt; find exact MG keys (MGIOMFBSupport.c, `IODeviceTree:/product` lookups seen in backboardd trace).
3. **Battery**: AppleSmartBattery/IOPMPowerSource style service (status bar shows empty red battery).
4. Apply Codex 0058 (UFS speed), consider cpus>1, check whether installcoordinationd/mediaserverd loops are gone, analyse mobileactivationd.
5. Hide kernel console over the GUI when not debugging: boot-arg sweetfb_noconsole=1 (but then panics are not on screen).

- **🎉 MILESTONE: iOS GUI ON THE PHONE - Setup.app "Hello" screen (2026-10-17 ~21:30 UTC, boot 0057u on image v12).** Photo: `/run/media/dipa/android/ios-sweet-work/MILESTONE-setup-hello-2026-10-17.jpg` (animated "dobar d(an)" hello lettering, status bar "iPod" + battery icon, bottom "Pritisnite Home za otvaranje" = "Press Home to open" (locale hr), (i) button). Rendered by iOS 16.7 SpringBoard/Setup through CoreAnimation -> backboardd -> kernel IOSurface (IOCoreSurfaceRoot) -> kernel AppleCLCD swaps -> ABL panel memory. What made it: data migration finally skipped (v12: `LastSystemVersion` 20H392 in the plain `/var/mobile/Library/Preferences/com.apple.migration.plist`; ADT `/chosen/unique-chip-id` + `chip-id` for IOPlatformUUID), 0057 (no ext resolver -> ACL containers work), plus everything before (0046 display/IOSurface, 0050 Sandbox policy, display-scale 3, containers dirs, RENAME_SWAP, AKS 35/101, 10 Hz present).
  **Missing (next work, in rough order):**
  - **Input: no touch, no power button, no volume buttons** (no HID drivers; backboardd looks for IOHIDDevice / HIDServiceSupport services). Setup is stuck on "Hello".
  - **Device identity: it thinks it is an iPod with a Home button** (status bar "iPod", "Press Home to open"): MobileGestalt has no product/model identity (no /product node, product-type, etc.) - give it iPhone10,3 / home-button-less (Face ID class) identity.
  - **No battery detection** (no battery/charger/PMIC service; status bar battery shows empty/red).
  - Locale came up Croatian (hr) - harmless.
  - Performance: cpus=1, polled UFS (Codex UFS patch in progress: `codex/ufs/`), backboardd presents at 60 Hz.
- **README refreshed (2026-10-17):** read the full notes and updated the public overview through patch 0045, v7 hardware observations and prepared v8 diagnostics. Documents real Apple userspace, the missing display/IOSurface GUI work, limited security services, highmem, persistent userdata root, current tooling and build examples. Documentation only; no kernel build, tests, flashing or phone boot performed.

- **v11 still migrated (boot 0056u, 20:32 UTC, `logs/boot-0056u-v11.txt`).** On iOS kCFPreferencesCurrentHost lands in the plain plist: all DMEnvironment setters (setLastBuildVersionPref, setUserDataDispositionPref, ...) use CurrentHost and the phone's `/var/mobile/Library/Preferences/com.apple.migration.plist` holds DMUserDataDisposition; datamigrator's XPC service runs with `_RoleAccount: mobile`. **Image v12** = v11 + `LastSystemVersion` = 20H392 added to that plain `com.apple.migration.plist` (keeps DMUserDataDisposition, 501:501 0600) + `/Library/Audio/Plug-Ins/HAL/VirtualAudio.plugin` moved to `/Library/Audio/Plug-Ins/HAL.disabled/` (Codex: stops the mediaserverd SIGSEGV loop; untested). **installcoordinationd loop explained (Codex `codex/installcoordinationd-report.md`):** os_crash "Failed to create data directory" EACCES for `/private/var/containers/Shared/SystemGroup/systemgroup.com.apple.installcoordinationd/Library/InstallCoordination`: `Library`/`Library/Caches` in the container are ACL-only (uid/gid 0xfffffffe, mode 0000, ACE for group GUID ...012B = gid 299 systemusers); with `config_ext_resolver` the kernel asks an identity resolver (memberd/opendirectoryd) that iOS does not run -> EWOULDBLOCK -> ACE skipped -> EACCES. **Patch 0057**: drop config_ext_resolver from FILESYS_BASE (compatibility UID/GID<->GUID mapping is used instead), likely fixes other ACL-protected containers too. Codex task 3: UFS driver performance design (`codex/ufs-performance.md`).
- **mediaserverd SIGSEGV loop explained (Codex report `/run/media/dipa/android/ios-sweet-work/codex/mediaserverd-report.md`):** the fault (FAR 0x390) is in the HAL plug-in `/Library/Audio/Plug-Ins/HAL/VirtualAudio.plugin/VirtualAudio` (ApplyBeamFormerPreference <- VirtualAudio_PlugIn::SetPropertyData <- HALS_AHPPlugIn::ObjectSetPropertyData <- AudioObjectSetPropertyData <- MediaExperience vaemVADSerializationListener): the default virtual audio device ('vdef', VirtualAudioDevice_Default) does not exist (no audio hardware/driver, no /product/audio). Proposed workaround for GUI bring-up: move VirtualAudio.plugin out of /Library/Audio/Plug-Ins/HAL/ in the next root image (untested). v11 reflashed OK after an interrupted flash (USB unplugged at chunk 25/25). Codex task 2: installcoordinationd crash loop.
- **ROOT CAUSE of the endless migration: no IOPlatformUUID (2026-10-17).** datamigrator's `-[DMMigrator isMigrationNeededWithBuildVersion:lastBuildVersion:clientPID:]` gets lastBuildVersion from `-[DMEnvironment lastBuildVersionPref]` = `CFPreferencesCopyValue("LastSystemVersion", "com.apple.migration", kCFPreferencesCurrentUser, kCFPreferencesCurrentHost)` -> a ByHost file. The phone had `/var/mobile/Library/Preferences/com.apple.migration.plist` (only DMUserDataDisposition) and NO `Preferences/ByHost` directory at all. On arm XNU publishes IOPlatformUUID (gethostuuid) only from `/chosen/unique-chip-id` (8 bytes) + `/chosen/chip-id` (4 bytes) (IOPlatformExpertDevice::generatePlatformUUID, called from IOPlatformExpert::start); the SWEET ADT had neither, so every CurrentHost preference write failed. Fix: mkadt adds `unique-chip-id` = 0x5357454554000001 (synthetic) and `chip-id` = 0x8015 -> UUID `A9683613-3704-53F2-95D0-98A8FB574E78` (same SHA1 namespace computation as the kernel). ADT `shim/out/sweet-0057hi.adt`, boot image `shim/out/shim-boot-0056u.img` (0056 kernel + 0057hi ADT, QEMU OK). **Image v11** = v10 + `Preferences/ByHost/com.apple.migration.<UUID upper and lower>.plist` {LastSystemVersion: 20H392} (501:501, dir 0755 files 0600). Flashing v11 2026-10-17 ~20:10 UTC. Codex (gpt-6.1-sol high) analysing the mediaserverd SIGSEGV loop in `/run/media/dipa/android/ios-sweet-work/codex/` (report `mediaserverd-report.md`).
- **v10 did NOT stop the migration (boot 0056n on v10, 19:18 UTC, `logs/boot-0056n-v10.txt`):** datamigrator + migrationpluginwrapper ran again, backboardd drew the progress UI (13000+ swaps in ~5 min). So `com.apple.DataMigration.plist`/LastSystemVersion is not the deciding input. What is known about the decision (datamigrator XPC service `DataMigration.framework/XPCServices/com.apple.datamigrator.xpc/com.apple.datamigrator`, strings): `Migration sentinel present. Migration necessary.` (sentinel `/private/var/datamigrator/migrate`, created and removed by datamigrator itself; absent in v10), `System build version changed from %@ to %@. Migration necessary.` / `...unchanged... not necessary`, `Disposition dictionary with build version %@ is out of date relative to current build version %@`, `SyntheticDidUpgrade`, DMUserDataDispositionManager; previous build source not found yet (not in the binary's plain strings; likely in DataMigration.framework's DMUserDataDispositionManager / preferences domain `com.apple.migration`). backboardd calls `DMPerformMigrationIfNeeded` and holds SpringBoard in `checkInAndWaitForDataMigration` until it returns. NEXT: find where the previous build version / disposition dictionary is stored (disassemble DataMigration.framework DMUserDataDispositionManager + datamigrator's isMigrationNeeded path), write it into the image; or get datamigrator's os_log out (OS_ACTIVITY_DT_MODE needs a launchd env change).
- **Data migration never records completion -> skip it (image v10, 2026-10-17).** Boot 0056n (18:16 UTC, `logs/boot-0056n.txt`, 30 min): 10 Hz panel copies, backboardd still presents at ~60 Hz (107k swaps), SpringBoard still in `BKSSystemShellService _checkIn` at sample 14. Every migration run takes 1+ hour on cpus=1 and repeats each boot. DataMigration decides from `/var/mobile/Library/Preferences/com.apple.DataMigration.plist` key `LastSystemVersion` (vs ProductBuildVersion 20H392); the pulled phone root (21:01 local) had NO such file. **v10** = that pulled phone state + fsck.hfsplus -fy (volume was marked not cleanly unmounted -> Linux mounts it read-only even with -o force; fsck found only hard-link counts + minor volume header, repaired) + `com.apple.DataMigration.plist` {LastSystemVersion: 20H392} (501:501 0600). `/run/media/dipa/android/ios-sweet-ipsw/ios16-root-20H392-v10.img` (+ .sha256, .simg); v8 files deleted, v9 kept as fallback.
- **Repo made PUBLIC (2026-10-17, user request) so GitHub-hosted macOS runners are free:** the 0056 CI run was refused ("recent account payments have failed or your spending limit needs to be increased"). Checked before: no device dumps, serials, IMEI or Apple binaries in the history (.gitignore keeps backup/, dtb/, recovery/, research/ out); commit author emails are public now. 0056 rerun `39056660104` passed -> `xnu/out-0056`, QEMU OK, image `shim/out/shim-boot-0056n.img` booted 18:16 UTC.
- **Boot 0055n (17:16 UTC, ~65 min, `logs/boot-0055n.txt`): migration bar reached 99% in ~30 min (was ~60), then crawled.** Root cause of the slowness: backboardd presents the progress UI at ~58 Hz (**167,000 swaps in ~48 min**) and AppleCLCD copied the full 10 MB frame into the panel on every swap -> ~600 MB/s memcpy on the single CPU (cpus=1), starving everything (polled UFS I/O too). Sampler (16 frames): **SpringBoard waits in `-[BKSSystemShellService _checkIn]`** (synchronous BSXPC call to backboardd, from FBSystemShellInitialize <- SBSystemAppMain) - backboardd holds the system shell check-in until the data migration ends, so the migration is the gate to SpringBoard UI. **Patch 0056**: swap only records the latest swap record; the vsync timer copies it to the panel every 60/sweetfb_hz ticks (default 10 Hz); `SWEET FB: N swaps` every 1000.
- **Boot 0054n (16:53 UTC, ~12 min, `logs/boot-0054n.txt`, patch 0054 sampler):** the data migration runs AGAIN on every boot (it completed once in the 0053s run) - completion is not being recorded. backboardd keeps swapping the progress UI (3700+ swaps in ~10 min, `SWEET FB: N swaps`). Sample during migration: SpringBoard main thread blocked in a synchronous XPC call (`mach_msg2_trap <- dispatch_mach_send_and_wait_for_reply <- xpc_connection_send_message_with_reply_sync <- -[BSXPCServiceConnectionMessage _sendSynchronously:] <- BSXPCServiceConnectionProxy ...`). Unsupported AKS selectors seen: 101 `aks_assert_consume`, 93 `aks_get_internal_info`, 34 `_aks_stash_load` (datamigrator), **35 `aks_get_extended_device_state`** (SpringBoard, chronod, remindd, searchd, symptomsd...). **Patch 0055**: AKS 35 answered like 17 (same DER device state), 101 succeeds; sampler backtraces 16 frames, 40 samples (~80 min).
- **MILESTONE: FIRST iOS PIXELS ON THE PANEL (boot 0053s long run, 15:33 UTC, ~60 min; photos IMG_20261017_183029/183222/183419; log `/run/media/dipa/android/ios-sweet-work/logs/boot-0053s-long.txt`, 407 KB, 1428 flushes).** The iOS data-migration boot screen (Apple logo + progress bar) was shown and the bar advanced to full in ~60 minutes. It is drawn by **backboardd through our kernel display path**: `SWEET SURF: backboardd create id 2/3 1080x2400 fmt 0x42475241 (BGRA) bpe 4 bpr 4352 size 10452992 keys 11`, IOSurface sels 9, 27, 5, 34 and traps 2/3 (lock/unlock), IOMFB SwapBegin (4) / SwapEnd (5, 1132-byte struct) / GetLayerDefaultSurface (3) / 68 / 55, then `SWEET FB: swap N layer 0 surface 2|3 1080x2400 ... a 0,0 1080x2400 b 0,0 1080x2400` alternating (double buffering; only the first 16 swaps are logged). Triggered by `com.apple.datamigrator` (AKS sels 101/93/34 return unsupported) and `com.apple.migrationpluginwrapper`. Probably ProgressUI-style CoreGraphics drawing into IOSurfaces (no GPU used). After the migration: SpringBoard and backboardd stay up (exec once each, no crash), nothing new drawn; crash loops only for mediaserverd, installcoordinationd, mobileactivationd (~108 each in the hour); bluetoothd and fairplayd.H2 relaunch constantly (no hardware). Kernel console text overlays the image (sweetfb_noconsole=1 would hide it).
- **MILESTONE: SpringBoard and backboardd both stay up (boot 0053s on v9, 15:29 UTC, `logs/boot-0053s.txt`).** With /chosen/display-scale = 3: `exec SpringBoard` once, `exec backboardd` once, no CRASH for either; MobileGestaltHelper reads IOMFB size/dot pitch; backboardd opens AppleCLCD (sels 57,15,22,29,33,79,74 as before). No IOSurface creates and no swaps: backboardd keeps polling `IOProviderClass IOAcceleratorES` (-> 0 found) and AGXAccelerator/IOAcceleratorESLegacy - no GPU, so no CoreAnimation renderer yet. Log goes quiet after ~47 s (only 47 flushes): the system idles. NEXT WALL: CoreAnimation rendering without a GPU (CPU path) so the window server produces frames.
- **SpringBoard's invalid mode = scale 0 (boot 0053n, 15:19 UTC, `logs/boot-0053n.txt`, heap scan):** `FBSDisplayMode cannot be configured as requested : <FBSDisplayMode: ...; infxinf@0x (1080x2400/0) 60Hz sRGB SDR>` - pixel size and 60 Hz are fine, scale is 0. libMobileGestalt (MGIOMFBSupport.c, sub_19c560a54) reads `display-scale` (u32, default 0) and `display-rotation` from **IODeviceTree:/chosen**, pixel size via IOMobileFramebufferGetDisplaySize (MobileGestaltHelper sel 8/28 in the log). mkadt now adds `/chosen/display-scale` = 3 (1080x2400 @3x = 360x800 pt). ADT `shim/out/sweet-0054hi.adt` (QEMU `research/q0054-hi.adt`), image `shim/out/shim-boot-0053s.img` = 0053 kernel + 0054hi ADT. Possible catch: MobileGestalt may have cached scale 0 in `/private/var/containers/Shared/SystemGroup/systemgroup.com.apple.mobilegestaltcache/...`.
- **MILESTONE: backboardd survives and opens the display (boot 0052n on v9, 15:07 UTC, `logs/boot-0052n.txt`).** No `CRASH backboardd`. It walks `IODeviceTree:/arm-io` children, matches IOMobileFramebuffer, `open AppleCLCD type 0 -> 0x0`, calls IOMFB selectors 57, 15, 22, 29, 33, 79 (GetBlock, out 1580/40), 74 (SupportedFrameInfo), 12, 6, 27, 17, 84, 50; opens IOCoreSurfaceRoot (sel 13); looks for AGXAccelerator / IOAcceleratorES / IOAcceleratorESLegacy (none, repeatedly), `IODeviceTree:/product` (none, repeatedly), `/buttons`, aop-smart-cover, IOPMrootDomain. No swaps yet. **SpringBoard now gets past display discovery** and dies (sig 5) in `-[FBSDisplayMode _initWithWidth:height:preferredScale:scaleOverride:refreshRate:gamut:hdr:rotation:virtual:validityCheck:]+580` <- `_initWithCADisplayMode:scale:rotation:` <- `FBSDisplayConfiguration _initWithImmutableDisplay:` <- `FBSDisplaySource initWithDisplay:` <- `FBSDisplayMonitor` (slide 0x14504000): "FBSDisplayMode cannot be configured as requested". Checks: width/height >= 2, preferredScale > 0, scaleOverride >= 0, refreshRate non-zero, valid gamut/HDR/rotation. Suspects: refresh rate 0 (IOMFB timing blocks answered with zeros) and/or scale 0 (MobileGestalt main-screen-scale; no /product node in the ADT). **Patch 0053**: heap text scan also on SIGTRAP and for SpringBoard (default sweetscan list backboardd,SpringBoard) to read the exact mode description.
- **Image v9 (2026-10-17) = v8 + `/private/var/containers/{Bundle,Data/System,Shared/SystemGroup,Temp}` (root:wheel 0755; on iOS these live on the data volume, absent from the rootfs) + launchd.plist with StandardOutPath/StandardErrorPath renamed to ...PatX (the in-place phone fix; daemons' stdout reaches the log via the 0048 /dev/null tee).** `/run/media/dipa/android/ios-sweet-ipsw/ios16-root-20H392-v9.img` SHA256 aa9f9139...6e67, `.simg` 12,145,303,864 bytes; written through `sudo mount -t hfsplus -o loop,force`. **Patch 0052** (`xnu/patches/0052-sweet-hfs-rename-swap.patch`, CI `39042761826` -> `xnu/out-0052`, QEMU OK, image `shim/out/shim-boot-0052n.img`): vn_rename falls back to VNOP_EXCHANGE when VNOP_RENAMEX(RENAME_SWAP) returns ENOTSUP for two regular files on one volume (HFS exchange swaps data and cnode descriptors = swap semantics). Flashing v9 started 2026-10-17 ~15:00 UTC.
- **backboardd EXCEPTION FOUND (boot 0051n, 14:41 UTC, `logs/boot-0051n.txt`, patch 0051 heap scan):** `*** Terminating app due to uncaught exception 'NSInvalidArgumentException', reason: '*** -[NSURL initFileURLWithPath:]: nil string parameter'`. First-throw stack (slide 0x337f0000): `+[NSURL fileURLWithPath:]` <- `-[BSSystemContainerForCurrentProcessPathProvider libraryPath]` <- `cachesPath` <- backboardd main+0x1d858 (StartWindowServer, shader cache path). BaseBoard: libraryPath = `BSSystemSharedResourcesDirectoryForIdentifier` = `BSSystemSharedDirectoryForIdentifier(id)` + "/Library"; that calls `container_system_path_for_identifier` (libsystem_containermanager -> `_container_legacy_lookup` -> containermanagerd XPC), which returned NULL (BaseBoard logs "Error getting shared system container ..."). With 0050 the sandbox denials are gone. containermanagerd.log.0 in the pulled (pre-0050) image: "Did not receive any persona attributes", "Expected to find at least one persona", notify_register_dispatch failed 9; `/private/var/containers` does NOT exist in the root image (on iOS it lives on the data volume). usermanagerd does create kernel personas 99/199/1000, but fails to save `/private/var/keybags/usersession.kb` and `persona.kb`: "Failed to atomically swap writing file: Operation not supported (45)" (HFS has no RENAME_SWAP). NEXT: create `/private/var/containers` (and check what containermanagerd needs for system group containers), fix or emulate RENAME_SWAP on HFS, then re-check backboardd.
- **Disk housekeeping (2026-10-17):** /home was at 4 GiB free. Moved (not deleted) `xnu/out-0010..0044` and old `shim/out/*.img`/`payload-*.bin` (everything before 0046) to `/run/media/dipa/android/ios-sweet-work/archive/{xnu,shim-out}` (6.3 GiB); /home now 8.7 GiB free. Large work files (phone-root.img 16 GiB, logs, tracev3 dumps) live in `/run/media/dipa/android/ios-sweet-work/`. **Patch 0051** (`xnu/patches/0051-sweet-crash-heap-strings.patch`, CI `39041440935`): on SIGABRT of a process in boot-arg `sweetscan` (default backboardd) the crash log prints heap text runs as `STR ...` (to find the NSException reason). Boot 0051n 14:41 UTC.
- **Boot 0049n (14:11 UTC, `logs/boot-0049n.txt`, patch 0049 trace): backboardd's IOKit lookups before it dies** (each run): `IODeviceTree:/arm-io/pearl-sep` -> none, matching ApplePearlSEPDriver -> none, `IOService:/IOResources/AppleKeyStore` open OK, matching IOHIDDevice (DeviceUsagePairs) / `HIDServiceSupport` notifications, `usb-drd,t8027` notification; **never any IOMobileFramebuffer / display lookup** - the exception happens before display detection. launchd (tracev3) shows backboardd's mach lookups denied with `error = 159: Sandbox restriction`: com.apple.mobilegestalt.xpc, com.apple.iohideventsystem, com.apple.system.notification_center, com.apple.logd, containermanagerd, ACCHWComponentAuthService, oscard. libsystem_sandbox uses `__mac_syscall("Sandbox", op, arg)` (ops: 1 init, 2 check, 3 note, 4 container path, 5/6/7/8 extensions, 0x15 check_bulk, ...); with no policy named "Sandbox" every call gets ENOPOLICY. **Patch 0050** (`xnu/patches/0050-sweet-sandbox-policy.patch`): built-in permissive MAC policy "Sandbox" in sweet_amfi.c (mpo_policy_syscall returns 0, container/extension ops ENOENT; logs first use of each op as `SWEET Sandbox: proc op N`).
- **Phone root pulled (16 GiB, 12 min, `adb exec-out dd if=/dev/block/sda34`) to `/run/media/dipa/android/ios-sweet-work/phone-root.img` (loop-mounted ro at /run/media/dipa/iOSRoot).** No .ips crash reports. logd tracev3 (Persist, LZ4 `bv41` blocks, decompressed strings in `ios-sweet-work/tracev3/all.txt`): /private/var/db/uuidtext is EMPTY so only launchd's own messages are readable. Findings: v8 launch failure = `Service could not initialize: posix_spawn(/usr/libexec/backboardd), error 0xd - Permission denied` (xpcproxy exit 78) - /dev/console not openable for the mobile user; backboardd[98] spawned `com.apple.MTLCompilerService` before SIGABRT; **launchd denies many mach lookups with `error = 159: Sandbox restriction`** (mediaserverd -> com.apple.backboard.display.services, remoted, mobiletimerd -> sleepd, identityservicesd -> apsd) and **tccd exits OS_REASON_SANDBOX "profile not found"** - no Sandbox kext/profiles on SWEET; likely cause of many daemon crash loops (next wall after the display). CF's uncaught-exception text never reaches stderr for daemons (no CF handler; libc++abi prints only the type). **Patch 0049** (`xnu/patches/0049-sweet-iokit-trace.patch`): `IOK name: ...` console lines for registry path lookups, child iterators, matching (with result count/class), matching notifications and IOServiceOpen of the processes in boot-arg `sweetiolog` (default backboardd), max 400 lines.
- **CONFIRMED: launchd StandardOut/ErrorPath=/dev/console stops backboardd from launching.** After the in-place rename (boot 0047n-b, log `logs/boot-0047n-b.txt`) backboardd launches again and dies as on v7: sig 6, `___pthread_kill <- abort <- demangling_terminate_handler <- _objc_terminate <- std::terminate <- _dispatch_client_callout <- _dispatch_once_callout <- main+0x9334` (window-server dispatch_once). It never opened AppleCLCD or IOCoreSurfaceRoot (no `SWEET FB/SURF: backboardd` lines) -> throws before/at display detection. **Patch 0048** (`xnu/patches/0048-sweet-devnull-tee.patch`, CI `39037749668` -> `xnu/out-0048`, image `shim/out/shim-boot-0048n.img`): writes to /dev/null by processes named in boot-arg `sweetnull` (default `backboardd,SpringBoard`) are printed as `|name| text`. Boot 0048n (13:48 UTC, log `logs/boot-0048n.txt`): only `|backboardd| libc++abi: terminating due to uncaught exception of type NSException` (CF's reason line goes to os_log, not stderr, despite CFLOG_FORCE_STDERR/OS_ACTIVITY_DT_MODE). Next: pull the whole 16 GiB root from recovery (`adb exec-out dd if=/dev/block/sda34`) to `/run/media/dipa/android/ios-sweet-work/phone-root.img` and read ReportCrash .ips files / logd tracev3 for the exception reason.
- **Persistent log WORKS (boot 0047n on v8, 13:31 UTC; pulled from OrangeFox: 70 KB, 111 flushes, `/run/media/dipa/android/ios-sweet-work/logs/boot-0047n.txt`).** In 3 min **backboardd was never exec'd** (v7 ran it), ~70 bare `exec xpcproxy`, SpringBoard loops on FBSDisplayMonitor (no display), mediaserverd sig 11 loop, locationd, lockdownd sig 5. Suspect the v8 plist (StandardOut/ErrorPath=/dev/console on backboardd). **In-place plist edit from recovery (no reflash):** launchd.plist is one extent at image/partition byte offset 0x1e025f000 (195 blocks; verified bytes identical on phone vs local v8 mount); renamed StandardOutPath->StandardOutPatX and StandardErrorPath->StandardErrorPatX (same length, both jobs) in blocks 68 and 105 via `adb push` + `dd of=/dev/block/sda34 seek=... conv=notrunc,fsync`, read back VERIFIED. Phone now differs from local v8 image in those 2 blocks (files in `/run/media/dipa/android/ios-sweet-work/`). Test boot 0047n 13:38:42 UTC. Recovery kernel has no hfsplus (raw block edits only).
- **Patch 0047: persistent console log (CI `39036478663` -> `xnu/out-0047`, QEMU no panic; phone image `shim/out/shim-boot-0047n.img` = 0047 + sweet-0046hi.adt + 0045n cmdline).** `_cnputs` (all console output: kernel printf + daemons' /dev/console) also appends to a 4 MiB ring in sweet_ufs.c; after the UFS partition is ready and writable (ufsrw=1) a thread writes new ring blocks + header to the LAST 1025 blocks (4 KiB) of userdata every ~1 s and SYNCHRONIZE CACHE (prints `SWEET LOG: console log to the last 4100 KiB ...`). Read: phone to fastboot -> `fastboot boot recovery/recovery.img` (OrangeFox) -> `tools/sweet-log-pull.sh OUT.txt` (adb dd of that area + `tools/sweet-log.py`). Not yet verified on the phone. Panics after the last flush are not in it (screen still shows them). 2x font attempt reverted: XNU's v_scale only scales the progress icon.
- **Boot 0046n on v8 (13:05 UTC, VID_20261017_150522_HSR_120):** phone prints `SWEET SURF: IOCoreSurfaceRoot registered` and `SWEET FB: AppleCLCD 1080x2400 stride 4320 at 0x9c000000, default surface 1` (nubs + match work on hardware). Visible userspace: early boot tasks, launchd_cache_loader, `exec SpringBoard`; no `exec backboardd` / `SWEET FB: backboardd` line seen in the readable frames (video blurry). Frame 00:47: lower half of the screen shows OLDER console text (16:01:12) below newer lines -> unconfirmed hint that a swap copied an old snapshot of the panel (CA reads the default/displayed surface = panel memory). SpringBoard still dies in `-[FBSDisplayMonitor _initWithBookendObserver:transformer:]+1160` (sig 5, slide 0x30960000). **Shim: 2x console font** (`shim/loader.c` Video.v_depth scale field = 1) so phone videos are readable; image `shim/out/shim-boot-0046b.img` = 0046n + 2x font.
- **Patch 0046: built-in IOSurface + IOMobileFramebuffer (2026-10-17, offline, NOT phone-tested).** `xnu/patches/0046-sweet-iosurface-iomfb.patch`: new `iokit/Kernel/arm/SweetSurface.{h,cpp}` (IOCoreSurfaceRoot + IOSurfaceRootUserClient: sel 13/0/4/34/35, traps 0-5, wired buffers mapped into the caller, per-client refs) and `SweetFramebuffer.cpp` (AppleCLCD : IOMobileFramebuffer on /arm-io/disp0: sizes, swap = CPU copy of enabled layers into the ABL panel memory, 60 Hz vsync via sendAsyncResult64WithOptions(CanDrop), panel memory published as the default IOSurface, kernel text console paused on the first swap only with `sweetfb_noconsole=1` (default keeps the console: pausing switches it to serial and would hide panics)); SweetPlatformExpert creates nubs for /arm-io children (not gic) attached to the platform expert (IOPlatformDevice::compareName casts its provider to IOPlatformExpert, so nubs under the arm-io nub never matched - first CI build showed that in QEMU). mkadt: /arm-io/disp0 {device_type display-subsystem, compatible sweet,display, canvas-width 1080, canvas-height 2400}. CI `39021572169` -> `xnu/out-0046`. **QEMU** (`research/q0046-hi.adt`, RAM disk init, msgbuf): `SWEET SURF: IOCoreSurfaceRoot registered`, `SWEET FB: AppleCLCD 1080x2400 stride 4320 at 0x9c000000, default surface 1`, init alive, no panic. Phone image **`shim/out/shim-boot-0046n.img`** (SHA256 9c4d2fe9..., CI `39024108588` with the review fixes: swap bounds check, zeroed 64-bit async ref, port release, 1.5 GiB wired budget, ref leak/race fixes; QEMU re-checked) = 0046 kernel + `shim/out/sweet-0046hi.adt` + the 0045n cmdline; boot it on image v8 (backboardd/SpringBoard log to console) and film. Expected new console lines: `SWEET SURF: <proc> create id ...`, `SWEET FB: backboardd sel N ...`, `SWEET FB: swap ...`. Open question for the next wall: QuartzCore's IOMFB server builds its renderer from Metal first (`CAMetalContextCreate`), GLES only when enabled; how the CPU renderer gets selected on a device without a GPU is not yet established.
- **IOSurface values ABI (offline RE, `/run/media/dipa/android/ios-sweet-work/iosurface-values.md`) - TODO in SweetSurface (0046 only accepts and drops values, so IOSurfaceCopyValue always returns NULL):** sel 9 SetValue in = {u32 id, u32 pad, IOCFSerialize([value, key]) or ([dict] = merge)}, sel 0xb RemoveValue in = {u32 id, u32 pad, key\0} (empty key = remove all); both out 4 bytes = new generation, client accepts only (gen+2)|1. Kernel after each change: gen = (gen+2)|1 (odd, never 0) -> state+0x20, serialized size (>=1) -> state+0x28. sel 0xa in {u32 id, u32 0, u8 0}, out {u32 ?, u32 gen, serialized non-bulk dict}; too small -> 0xe00002db + needed size (client retries x16). sel 0x1b in 0x88: bulk struct 0x70 @0, u64 valid size @0x70, u64 changed mask @0x78, u32 id @0x80 -> copy masked fields into state+0x30 (bit0 32B @0, bit1 16B @0x20, bit2 8B @0x30, bits3-10 1B @0x38..0x3f, bits11-14 24B @0x40/4B @0x58/8B @0x5c/1B @0x64).
- **IOMFB display matching confirmed (offline RE, `/run/media/dipa/android/ios-sweet-work/iomfb-match.md`):** the framework never matches on "AppleCLCD"; any registered IOMobileFramebuffer subclass works. `iomfb_match_callback` reads only `dfr`/`AppleTV`/`external` (CFBoolean, service itself, no parents); internal main display = all absent/false (type 0, name "primary"). Display count = /arm-io children whose device_type starts with "display-subsystem" (count 0 -> CreateDisplayList returns NULL; more nodes than services -> 30 s wait). IOMobileFramebufferOpen fails only on IOServiceOpen failure; canvas-width/height read as 4-byte CFData from the IOService-plane parent (optional). CopyProperty = IORegistryEntrySearchCFProperty on the service only. Patch 0046 (disp0 node, `external`=false, AppleCLCD : IOMobileFramebuffer) fits all of this.
- **IOMobileFramebuffer swap + notification ABI (2026-10-17, offline).** Swap record = fb+0x18, **0x46c bytes**, zeroed by SwapBegin and sent whole by `kern_SwapEnd` = IOConnectCallStructMethod(sel 5, rec, 0x46c, no output). **SwapBegin** = sel 4, no input, 1 scalar out = swap id (stored at rec+0x50). `kern_SwapSetLayer(fb, layer<4, IOSurfaceRef, CGRect a, CGRect b, flags)`: rec+0x54+4*layer = **IOSurface id**; rec+0x104 bit layer = layer enabled (rec+0x108 bit cleared); rect a (int x,y,w,h, scaled) at rec+0x64+16*layer, rect b at rec+0xc4+16*layer; rec+0x114+4*layer = transform from flags&0xf; flag bits 5/31/6/7/8/9 set bytes rec+0x2ca/0x2cc/0x2e3/0x2e5/0x2e6/0x467+layer. A NULL surface only sets the enable bit with zero id. SwapWait = sel 6 scalars [swap id, timeout, 0].
  - **Notifications**: `IOMobileFramebufferScheduleWithDispatchQueue`/`GetRunLoopSource` create an IONotificationPort and `IOConnectSetNotificationPort(conn, type, port, 0)` (kernel `registerNotificationPort`). `kern_EnableNotifications(fb, type, cb, ctx)` = **sel 72 scalars [NotifyCallbackFuncs[type], fb, type, 0]** -> the kernel keeps an async reference {port, func, refcon=fb} per type and fires it with `sendAsyncResult64`. Types: 0 HotPlug, 1 Power, 3 FrameInfo (args[0] = mask of 31-bit keys, args[1] u32, then values), 4 CRC, **5 Vsync**: 6 args, each a 32-bit half in a u64 slot: (ts lo, ts hi), (t2 lo, hi) passed through the time-ingest helper, (t3 lo, hi); the framework then calls the client's vsync callback(fb, ts, t2', t3, ctx). Vsync callbacks are dropped while the notification port has queued messages.

- **IOSurface.framework user-client ABI reversed (2026-10-17, offline, step 2 of the GUI plan).** `ipsw dyld disass research/dsc/dyld_shared_cache_arm64 --image IOSurface` (selector scan script: scratchpad `selscan.py`).
  - Connect (`_iosConnectInitalize`, pthread_once): `IOServiceGetMatchingService(IOServiceNameMatching("IOCoreSurfaceRoot"))`, retried with sleep(1) up to 241 times (a missing service stalls every client ~4 min, no crash); `IOServiceOpen(type 0)`; then **sel 13** (no inputs, struct out 0x18 bytes = `_ioSurfaceLimits`) and requires u16 at out+0x16 == 1 (ABI version); out+0 = offset/plane-base alignment mask, out+4 = bytes-per-row alignment mask (used as (x+m)&~m), +0..+0x14 also copied into IOSurface remote-method init, otherwise logs and closes the connection.
  - **Create = sel 0**: scalar in [parent id or 0], struct in = `IOCFSerialize(props, kIOCFSerializeToBinary)` (OSUnserializeBinary format; keys IOSurfaceWidth/Height/BytesPerRow/BytesPerElement/PixelFormat/AllocSize/PlaneInfo/CacheMode/IsGlobal/...), struct out **0xa68 bytes** ("lock result"). **Lookup = sel 4**: scalar in [id], same struct out. LookupFromMachPort = sel 0x22 (scalar in [port name]); CreateMachPort = sel 0x23 (scalar in [id, options], scalar out [port name]).
  - Lock result (copied to client+0x68, size 0x68 + planes*0x80, min 0xe8): 0x00 u64 base address **mapped in the caller's task**; 0x08 u64 task VA of a per-surface shared state page (+0 u64 registry id, +8/+0xa u16 bound accel ids, +0xc u32 seed, +0x14 u8 tiled, +0x20 u32 value generation, +0x24 YCbCr matrix, +0x28 u32 non-bulk values size, +0x2d u8 displayable, +0x2e u8 sysmem-only, +0x30 0x70 bytes bulk attachments); 0x10 u64 task VA of timestamp page (4 u64 indexed timestamps, +0x20 detach code); 0x18 u32 surface id; 0x1c u32 alloc size; 0x20 width; 0x24 height; 0x28 bytes per row; 0x2c buffer offset; 0x30 pixel format; 0x34 u32 (dcache flush length); 0x38 plane count; 0x40 u16 bytes/element; 0x42 u8 element width; 0x43 u8 element height; 0x44 cache mode; 0x4c u8 subsampling; 0x4d u8 prohibit-use count; 0x50 parent id; 0x54 slice count; 0x58 u64 trace id; 0x60 u64 protection options; planes[n] at 0x68+n*0x80 (+0 width, +4 height, +8 bytes/row, +0xc offset, +0x14 size, +0x18 u16 bpe, +0x1a/+0x1b u8 element w/h, +0x1c u8 component count, +0x1d address format, +0x54 u8 compression type (non-zero -> no CPU base address)).
  - **Traps** (IOConnectTrapN -> `IOUserClient::getTargetAndTrapForIndex`): 0 IncrementUseCount(id, category), 1 DecrementUseCount(id, category), 2 **Lock**(id, options, &seed_out), 3 **Unlock**(id, options, &seed_out), 4 Release(id), 5 Release after a failed create/lookup setup (id).
  - Other selectors: 5 SetYCbCrMatrix, 6 WrapClientImage, 7 WrapClientMemory, 9 SetValue (serialized), 0xa UpdateNonBulkValueCache (struct in 9), 0xb RemoveValue, 0xc BindAccel, 0x11 SetSurfaceNotify (async), 0x12 RemoveSurfaceNotify, 0x13 Log, 0x14 SetPurgeable, 0x15 SetOwnership, 0x16 SetTiled, 0x18 SetTimestamp, 0x19 GetTileFormat, 0x1a CopyDataValueBytes, 0x1b SetBulkAttachments (struct 0x88), 0x1e/0x2e-0x31 (via outlined helpers), 0x1f SetCompressedTileDataRegionMemoryUsed, 0x20 GetGraphicsCommPageAddress, 0x21 SetIndexedTimestamp, 0x24-0x26/0x2d IOSurfaceAccelerator, 0x27-0x29 shared events, 0x2a SignalEvent, 0x2b Set/InitDetachModeCode, 0x2c SetOwnershipIdentity, 0x32-0x34 data properties.
  - => SWEET kernel service: class/name **IOCoreSurfaceRoot** + IOSurfaceRootUserClient; minimum = sel 13, 0, 4, 9/0xa/0xb (values), traps 0-5, 0x22/0x23 later for cross-process surfaces (CA sends surfaces to backboardd by mach port). Memory: IOBufferMemoryDescriptor per surface, mapped into each task with createMappingInTask; ids from a global table.

- **Image v8: daemon logs on the console.** `tools/patch-launchd-plist.py IN OUT LABEL...` rewrites launchd.plist (binary, plistlib): renames every `_PanicOnCrash` to `_PanicOnCrasX` and gives the listed jobs `StandardOutPath`/`StandardErrorPath` `/dev/console` (devfs console is 0622, writable by mobile) plus `OS_ACTIVITY_DT_MODE=YES` (os_log mirrored to stderr) and `CFLOG_FORCE_STDERR=1`. v8 = v7 + that plist for com.apple.backboardd and com.apple.SpringBoard, written through the mount (796310 bytes, root:80 0644), SHA256 in `ios16-root-20H392-v8.img.sha256`, `.simg` ready; boot with `shim/out/shim-boot-0045n.img`. Goal: see backboardd's uncaught exception text and the window server's display probing. ODDITY (unresolved): the v5 raw-image rename at offset 0x1e025f000 is present in the v5-v7 image bytes, but the plist read through a Linux mount of v7 still had the original `_PanicOnCrash` keys; filefrag shows the file as one extent. Never patch file contents through raw offsets again; write through the mount.
- **IOMobileFramebuffer.framework reversed (step 1 of the GUI plan).** `ipsw dyld disass research/dsc/dyld_shared_cache_arm64 --image IOMobileFramebuffer`.
  - Display discovery (`IOMobileFramebufferCreateDisplayList` -> `getDisplayListNumber`): iterates children of `IODeviceTree:/arm-io`, counts nodes whose `device_type` is "display-subsystem" or "ext-display-subsystem" (or `compatible` "paravirtualizedgraphics,gpu"); then `iomfb_populate_display_infos` adds an IOServiceAddMatchingNotification(IOServiceFirstMatch, **IOServiceMatching("IOMobileFramebuffer")**) and runs the run loop up to 30 s until that many services matched. `iomfb_match_callback` reads service properties `dfr`, `AppleTV`, `external` (CFBoolean) and names displays (external ones "%s-%d").
  - `IOMobileFramebufferOpen(service, task, type, &fb)`: `__ioMobileFramebufferAlloc` (CFPreferences com.apple.iokit.IOMobileGraphicsFamily: canvas_width/height, override_display_width/height, override_panel_width/height, benchmark, enable_ktrace), `IOServiceOpen(service, task, type)` (GetMainDisplay passes type 0), `getEDTProperty` reads `canvas-width`/`canvas-height` from the service's IODeviceTree parent, then fills a table of `kern_*` function pointers.
  - User client selectors (`kern_*` -> IOConnectCall*): 3 _kern_GetLayerDefaultSurface[ScalarMethod_stub]; 4 _kern_SwapBegin[ScalarMethod_stub]; 5 _kern_SwapEnd[StructMethod_stub]; 6 _kern_SwapWaitWithTimeout[ScalarMethod_stub] _kern_SwapWait[ScalarMethod_stub]; 7 _kern_GetID[ScalarMethod_stub]; 8 _kern_GetDisplaySize[ScalarMethod_stub]; 10 _kern_SetTVOutMode[ScalarMethod_stub]; 11 _kern_SetWSSInfo[ScalarMethod_stub]; 12 _kern_RequestPowerChange[ScalarMethod_stub]; 13 _kern_EnableStatistics[ScalarMethod_stub]; 14 _kern_SetFlags[ScalarMethod_stub]; 15 _kern_SetDebugFlags[ScalarMethod_stub]; 16 _kern_SetTVOutSignalType[ScalarMethod_stub]; 17 _kern_SetGammaTable[StructMethod_stub]; 18 _IOMobileFramebufferIsMainDisplay[ScalarMethod_stub]; 19 _kern_SetWhiteOnBlackMode[ScalarMethod_stub]; 20 _kern_SwapSignal[ScalarMethod_stub]; 22 _kern_SetDisplayDevice[ScalarMethod_stub]; 23 _kern_SetDigitalOutMode[ScalarMethod_stub]; 24 _kern_GetHDCPDownstreamState[StructMethod_stub]; 25 _kern_GetDigitalOutState[ScalarMethod_stub]; 26 _kern_printDisplayRegs[ScalarMethod_stub]; 27 _kern_GetGammaTable[StructMethod_stub]; 28 _kern_GetDotPitch[ScalarMethod_stub]; 29 _kern_GetDisplayArea[StructMethod_stub]; 30 _kern_EnableDisableDithering[ScalarMethod_stub]; 31 _kern_SetUnderrunColor[ScalarMethod_stub]; 33 _kern_EnableDisableVideoPowerSavings[ScalarMethod_stub]; 34 _kern_SetVideoDACGain[ScalarMethod_stub]; 35 _kern_SetLine21Data[ScalarMethod_stub]; 41 _IOMobileFramebufferEnableMirroring[ScalarMethod_stub]; 42 _IOMobileFrameBufferGetMirroringCapability[StructMethod_stub]; 43 _IOMobileFramebufferSetRenderingAngle[StructMethod_stub]; 44 _IOMobileFramebufferSetMirrorContentRegion[StructMethod_stub]; 47 _kern_HDCPSendRequest[ScalarMethod_stub]; 48 _kern_HDCPGetReply[ScalarMethod_stub]; 49 _kern_SurfaceIsReplaceable[ScalarMethod_stub]; 50 _kern_SetBrightnessCorrection[ScalarMethod_stub]; 51 _kern_SetColorRemapMode[ScalarMethod_stub]; 52 _kern_SwapCancel[ScalarMethod_stub]; 53 _IOMobileFramebufferSetCanvasSize[ScalarMethod_stub]; 54 _IOMobileFramebufferGetMatrix[Method_stub]; 55 _IOMobileFramebufferSetMatrix[Method_stub]; 56 _IOMobileFramebufferKernelTests[StructMethod_stub]; 57 _kern_GetColorRemapMode[ScalarMethod_stub]; 66 _kern_SPLCSetBrightness[ScalarMethod_stub]; 67 _kern_SPLCGetBrightness[ScalarMethod_stub]; 68 _kern_SetParameter[Method_stub]; 69 _kern_SwapSetColorMatrix[StructMethod_stub]; 72 _kern_DisableNotifications[ScalarMethod_stub] _kern_EnableNotifications[ScalarMethod_stub]; 73 _kern_ChangeFrameInfo[ScalarMethod_stub]; 74 _kern_SupportedFrameInfo[Method_stub]; 75 _kern_FactoryPortal[StructMethod_stub]; 77 _kern_GetCurrentAbsoluteTime[ScalarMethod_stub]; 78 _kern_SetBlock[Method_stub]; 79 _kern_GetBlock[Method_stub]; 80 _kern_GetLinkQuality[ScalarMethod_stub]; 81 _kern_SwapCancelAll[ScalarMethod_stub]; 82 _kern_GetProtectionOptions[ScalarMethod_stub]; 83 _kern_CopyLayerDisplayedSurface[ScalarMethod_stub]; 84 _kern_SetContrast[StructMethod_stub]; 85 _kern_GetBufBlock[Method_stub]; 86 _IOMFBGainEncoderFinishEncoding[Method_stub]; UNKNOWN {}
  - => Kernel needs: an `/arm-io` child node with device_type "display-subsystem" (+ canvas-width/height) and an IOService of class **IOMobileFramebuffer** (subclass name match) attached under it, opened with type 0, implementing at least GetDisplaySize(8), IsMainDisplay(18), GetID(7), GetLayerDefaultSurface(3), SwapBegin(4)/SwapEnd(5 struct)/SwapWait(6), Enable/DisableNotifications(72), frame info(73/74), CopyLayerDisplayedSurface(83), plus IOSurface for the swapped buffers. NEXT: CoreAnimation's AppleDisplay/IOMFBDisplay usage of these (constructor, first swap, vsync), then IOSurface.framework's IOSurfaceRoot selectors.
- **GUI PLAN (decided 2026-10-16): CPU rendering + kernel IOMobileFramebuffer.** User: CPU rendering is fine for now (goal = prove the GUI runs), may later research an Apple-style GPU driver for the Adreno 618 -> keep display output and renderer separable. QuartzCore findings (symbols from the cache's .symbols subcache: `ipsw dyld symaddr research/dsc/dyld_shared_cache_arm64 --image QuartzCore`; strings: `ipsw dyld macho ... QuartzCore --strings`):
  - Renderers: `sw_new_context` (CA::OGL::SWContext, full CPU renderer incl. blur, images, IOSurface-backed surfaces, make_buffer_current(WindowServer::Surface)), `gles_new_context`, `metal_new_context`, `new_null_context`. Env knobs include CA_ENABLE_OGL, CA_DISPLAY_TYPE, CA_FORCE_LOCAL_SERVER, CA_FORCE_TIMER, CA_CANVAS_WIDTH/HEIGHT, CA_MAIN_DISPLAY_SCALE/ORIENTATION, CA_DISABLE_RENDER, CA_ALWAYS_RENDER (selection logic not traced yet).
  - `-[CAWindowServer _detectDisplays]` (0x1884e3150) iterates static tables `open_funcs`/`count_funcs` = AppleCLCDDisplay, AppleRGBOutDisplay, AppleWirelessDisplay only; each `count()` = `display_count_of_type(IOMFBDisplayType)` over **`IOMobileFramebufferCreateDisplayList()`**, `open(i)` = `create_display_of_type` -> `CA::WindowServer::AppleDisplay(CFString name, ..., IOMFBDisplayType)` (an IOMFBDisplay driven by IOMFBServer: vsync_callback, frame_info_callback, swaps). `CA::WindowServer::VirtualDisplay` exists but is never auto-detected (explicit API only). => the main display MUST come from an IOMobileFramebuffer kernel service.
  - NEXT: reverse IOMobileFramebuffer.framework: IOMobileFramebufferCreateDisplayList / IOMobileFramebufferOpen (service matching, display type property), the user-client selectors used by IOMFBServer (display size/modes, swap begin/set-layer/end with IOSurface ids, vsync notifications), then the IOSurface kernel side (IOSurfaceRoot user client: create/lookup/lock, memory mapping) that both IOMFB swaps and CA surfaces need. Kernel: SWEET IOMobileFramebuffer service that copies the swapped IOSurface to the 1080x2400 framebuffer at 0x9c000000.
- **logd fixed; backboardd = DISPLAY WALL (boot 0045n on v7, 21:08:57 UTC, frames VID_20261016_230850 00:55-01:28, slide 0x4c3ec000, `research/crash-0045n-v7.txt`).** No `CRASH logd` any more; new daemons run (runningboardd, WirelessRadioManagerd, networkserviceproxy, dasd, cloudpaird, magicswitchd, atc, askpermissiond, ManagedSettingsAgent, containermanagerd uses AKS 0/17). New: locationd sig 11 at CFRunLoopAddSource+132 (NULL source) from its main+0x2af138 in a dispatch_once. **backboardd** sig 6: abort <- std::terminate <- _objc_terminate <- dispatch_once <- main+0x9334 = the "start %{public}@..." wrapper (0x100009264) for **"window server"** (block 0x10000a770 -> dispatch_once body 0x10001d7f0 = StartWindowServer): MTLSetShaderCachePath, `[CAWindowServer serverWithOptions:@{kCAWindowServerDisableUpdatesOnMainDisplay: @YES}]`, `setRendererFlags:`, **`mainDisplay`** -> `displayId` -> `[CADisplay displayWithDisplayId:]`, setWindowServerDisplay:, bounds, pointScale, currentMode, preferredScale, nativeOrientation, touchScales... With no display, mainDisplay is nil and it throws. (HID system and GS start fine before it.) SpringBoard dies on the same missing display (FBSDisplayMonitor). QuartzCore display backends (from the cache's .symbols subcache, `ipsw dyld str`): `CA::WindowServer::AppleCLCDDisplay` (IOMobileFramebuffer hardware) and **`CA::WindowServer::VirtualDisplay`** (open(), new_server, clone_update). `CA_DISPLAY_TYPE` and `CA_FORCE_LOCAL_SERVER` strings exist in QuartzCore but have no direct xref (likely read via a table of CA_* env names). NEXT: find how CA::WindowServer::Server enumerates displays (IOMobileFramebuffer services vs VirtualDisplay / CA_DISPLAY_TYPE) and choose: (a) kernel IOMobileFramebuffer service + IOSurface, or (b) a VirtualDisplay rendered by CA's CPU path (CA::OGL::SW) and copied to the framebuffer.
- **watchdogd + CommCenter + identityservicesd fixed (boot 0045n on v6, 20:41:30 UTC, frames VID_20261016_224133 00:39-01:13, slide 0x20fec000).** `SWEET WDT: watchdogd sel 0 in 0/0 out 1/0 -> ok`, no watchdogd/CommCenter/identityservicesd crashes (CommCenter/identityservicesd now call AKS 0/17/7). usermanagerd boot task runs (UMD_INIT creates primary session uid 501 "mobile", personas 99 System and 199 Default registered with the kernel); `Failed to atomically swap writing file /private/var//keybags/usersession.kb: Operation not supported (45)` (HFS lacks the atomic swap rename; non-fatal so far). Remaining: SpringBoard (FBSDisplayMonitor, no display), backboardd (uncaught exception), mediaserverd, lockdownd (crash inside obfuscated code, main+0x4c1b4?), logd. **logd**: main+0x18160 = `BUG IN LIBTRACE: Failed to migrate directory` from 0x10001801c(dir 0): 0x100016538 requires the dir to exist with uid/gid/mode from the table at 0x10002df14 (0: /private/var/db/diagnostics 272:272 0751, 1: /private/var/db/uuidtext 272:272 0755, 2: /private/var/db/diagnostics/timesync 272:272 0755) plus a `.migrated` file, else XPC "operation 6" to a helper and crash. **Image v7** = v6 + those dirs/markers (also in mkiosroot.sh), SHA256 in `ios16-root-20H392-v7.img.sha256`, `.simg` ready. Boot with `shim/out/shim-boot-0045n.img`.
- **Exit-reason text works (boot 0044n, frames VID_20261016_221726 00:32-00:53, slide 0x22d5c000).** CommCenter/identityservicesd: `couldn't dlopen libobjc-trampolines.dylib: dlopen(/usr/lib/libobjc-trampolines.dylib, 0x0106): tried: '/usr/lib/libobjc-trampolines.dylib' (no such file, not in dyld cache)`: the file only exists in the OS cryptex and dyld does not search cryptexes at ignition_level=1. 19 cryptex files have no root counterpart (OS: DriverKit dyld cache + .symbols, VisualTestKit, libffi-trampolines, libobjc-trampolines, libstdc++ 6.0.9 + 2 symlinks; App: SafariSupport.bundle, AuthenticationServicesAgent, com.apple.Safari.History, passwordbreachd, safarifetcherd, webbookmarksd, webinspectord, webpushd) -> hard-linked (symlinks copied: Linux hfsplus cannot hard-link symlinks); `tools/mkiosroot.sh` does it generically. watchdogd still crashed: the `-wdt_no_pmu` / `/arm-io/wdt no-pmu` check (0x10000a01c) only runs when os_variant_has_internal_diagnostics; otherwise 0x100009b18 looks up IOServiceMatching("IOService") + IOPropertyMatch {IOPMUPrimary: 1} (NSConstantDictionary) and crashes if absent, then IORegistryEntrySetCFProperty(boot stage 0xff) (failure only logged). Patch **0045**: IOWatchdog sets IOPMUPrimary = 1 and accepts setProperties; CI `38961814194` -> `xnu/out-0045`. **Image v6** = v5 + the 19 cryptex links, SHA256 7c610c6a...297a, `ios16-root-20H392-v6.simg` (full flash needed). Boot image `shim/out/shim-boot-0045n.img` (0045 + sweet-0044hi.adt). Still open: SpringBoard (no display), backboardd (uncaught exception, reason none), mediaserverd (Fig NULL dict), logd (main+0x18160), lockdownd (main+0x4c1b4).
- **System survives daemon crashes (boot 0043p, video frames VID_20261016_215006 00:25/00:42/00:54).** With the v5 plist patch no panic: launchd keeps launching (runningboardd, powerd, tccd, healthd, peopled, cryptexd, routined, aksd, mediaremoted, familynotificationd, nanoprefsyncd, navd, cloudpaird, passd, amsaccountsd, accessoryupdaterd, wcd ...). Shared cache slide that boot 0x406b4000 (`research/crash-0043p.txt`). watchdogd still crashed at main+0xb82c from the PMU step: `-wdt_no_pmu` is only honored when os_variant_has_internal_diagnostics; customer builds read `no-pmu` from IODeviceTree:/arm-io/wdt (IORegistryEntrySearchCFProperty) -> mkadt adds /arm-io/wdt {no-pmu}. **cryptexd** sig 6: abort_with_payload <- os_crash_fmt <- `__darwin_arm_secure_boot_chip.cold.7` ("panic: failed to get crypto algorithm") <- `_img4_chip_select_personalized_ap`: reads /chosen use-ddi-secure-boot, allow-ecid-mismatch, crypto-hash-method ("sha1" | "sha2-384"), /chosen/asmb lp-smb0/1 -> mkadt adds crypto-hash-method "sha2-384". **identityservicesd** sig 6 = same `_objc_fatal` in imp_implementationWithBlock as CommCenter (block trampolines; message needed). lockdownd sig 5 at main+0x4c1b4. Patch **0044**: crash report adds `CRASH name reason ns N code X: text` (exit reason description = abort_with_payload text). CI `38959096811` -> `xnu/out-0044`, QEMU OK. Image `shim/out/shim-boot-0044n.img` = 0044 + `shim/out/sweet-0044hi.adt` (wdt no-pmu, crypto-hash-method) + cmdline (wdt=-1, no -wdt_no_pmu).
- **First symbolicated daemon crashes (boot 0043u on journaled v4, 19:38:53 UTC; video frame chat image 36; transcribed in `research/crash-0043u.txt`; shared cache slide 0x40d60000 for every process).** (Gemini's video transcription invented values, use frames only.) `tools/sweet-crash.py research/dsc/dyld_shared_cache_arm64 x research/crash-0043u.txt`:
  - **watchdogd** pc main+0xb82c (`_os_crash` trap helper) from 0x100009bb0 = set PMU boot stage via IORegistry (no PMU) -> fix: boot-args `wdt=-1 -wdt_no_pmu` (Apple's own test mode writes "%s wdt=-1 -wdt_no_pmu"; watchdogd logs "skipping setting PMU boot stage because -wdt_no_pmu found in boot-args or no-pmu found in EDT"). Kernel effect of wdt=-1: sched hygiene debug off, zone_exhausted_timeout -1 (harmless).
  - **SpringBoard** sig 5 in `-[FBSDisplayMonitor _initWithBookendObserver:transformer:]+1160` <- `+[FBDisplayManager sharedInstance]` <- `FBSystemShellInitialize` <- `SBSystemAppMain`: no main display. GUI WALL: display service (IOMobileFramebuffer / CoreAnimation display).
  - **backboardd** sig 6: abort <- std::terminate <- _objc_terminate (uncaught exception; message not shown).
  - **CommCenter** sig 6: `_objc_fatal` in `imp_implementationWithBlock` (from `+[_PFRoutines initialize]`, CoreData): objc block trampolines cannot be allocated -> likely kernel gap (trampoline page remap); will hit many processes.
  - **mediaserverd** sig 11: CFDictionaryGetValue(NULL) in FigNotificationListenerStartNotifications (routing session manager).
  - **logd** sig 5 at its main+0x18160 (bt main+0x9dfc); lockdownd sig 5 (not yet symbolicated).
  - Image v5 = v4 + launchd.plist (`/System/Library/xpc/launchd.plist`, contiguous at image offset 0x1e025f000, 1456980 bytes) with the 7 `_PanicOnCrash` keys renamed `_PanicOnCrasX` in place (raw image patch, no metadata change) -> `diff-v4-v5.simg` = 7 blocks; v5 SHA256 78f96974...185a. Boot image `shim/out/shim-boot-0043p.img` = 0043 + `wdt=-1 -wdt_no_pmu`.
- **0043 console crash reports (QEMU verified); image `shim/out/shim-boot-0043u.img`; NEXT: flash v4 + boot 0043u.** Boot 0042u (video photo IMG_20261016_211646): short exec lines work; watchdogd crashes with NO `SWEET WDT:` line (fails before its first IOWatchdog call: lookup or IOServiceOpen, or elsewhere); lockdownd, SpringBoard, mediaserverd, CommCenter, identityservicesd, backboardd, watchdogd all crash repeatedly ("Too many corpses being created" = corpse limit, no crash reports). AKS callers: lockdownd (0, 7), imagent/sleepd (0, 17, 7), backboardd (0, 17), UserEventAgent (0, 7, 102, 103 -> unsupported). Patch **0043**: `sweet_crash_log` (osfmk/kern/exception.c, called from proc_prepareexit for crash exits on the current proc) prints `CRASH name[pid] sig S code (exc<<32|code) sub X slide SR mh MH`, `CRASH name pc lr sp fp far`, `CRASH name bt` (10 fp frames); AKS sel 103 notify_state_is_set -> 0. CI `38954520419` -> `xnu/out-0043`. QEMU test: init forks, child `brk #1`: `CRASH launchd[2] sig 5 code 0x600000001 sub 0x1000004f0 slide 0x0`, pc correct, parent keeps running (pid 1 crashes panic before proc_prepareexit, so test with a child). `tools/sweet-crash.py CACHE ROOT [report]` symbolicates typed-in CRASH lines (`ipsw dyld a2s` with addr - slide; main binary offsets = addr - mh + 0x100000000).
- **v3 reflashed 18:50-18:55 UTC (`research/flash-userdata-v3b.log`, 24/24 OKAY); 0042u booted 19:01:17 UTC on the clean disk (`research/boot0042u-2.log`), SLOW MO VID pending (watchdogd failure reason).** ABL hangs on the first `fastboot boot` after every big flash; user re-enters fastboot. User gave standing approval to reflash/boot without asking (memory standing-flash-approval). Commits now end with `Co-Authored-By: dipa-studio <183933817+dipa-studio@users.noreply.github.com>` (user request; never a Claude trailer).
  - watchdogd flow: connect_to_kext (0x100005408): IOServiceGetMatchingService("IOWatchdog") fails -> "failed to discover" + _os_crash; IOServiceOpen(type 1) fails -> "IOServiceOpen failed with error : 0x%x" + _os_crash. Then sel 0 (out 1 scalar): 0 -> "userspace monitoring disabled", 0x100009bb0, sleep 2, exit(0); nonzero -> "userspace monitoring enabled", normal operation.
  - **Image v4 (JOURNALED):** `tools/mkiosroot.sh` now does `mkfs.hfsplus -J`, mounts with `-o loop,force`, adds the /System/Library/Caches/com.apple.dyld hard links (44) and /private/var/keybags/systembag.kb (0700/0600 root). Built from the IPSW dmgs (OS 087-86698-044, SystemOS 087-86593-047, AppOS 087-86715-047) -> `/run/media/dipa/android/ios-sweet-ipsw/ios16-root-20H392-v4.img` SHA256 fba4aeae...ec0f9 + `.simg`. Header: attr 0x80002100 (unmounted, journaled), journal info block 129, journal 8 MiB at 532480 flagged need-init. Linux `fsck.hfsplus -n` reports "Volume header needs minor repair" on any fresh journaled volume even after -y (quirk). QEMU: 64 MB journaled test root (`rd=md0 rootrw=1`, 0042 kernel): `hfs: Initializing the journal (joffset 0x3000 sz 0x80000)` -> mounted -> init runs, no panic. NEXT: flash v4 (full), boot 0042u.
- **SPRINGBOARD STARTS (boot 0041u 18:39:53 UTC, photo IMG_20261016_204142).** backboardd, bluetoothd, fairplayd.H2, SpringBoard (pid 111, crashed: "Too many corpses"), xpcproxy run; `SWEET AKS: backboardd sel 0 -> 0`, `sel 17 in 1/0 out 0/4096 -> 0`. Panic: watchdogd[113] exited, namespace 2 subcode 5 (SIGTRAP = its _os_crash): watchdogd crashes on purpose when IOServiceGetMatchingService("IOWatchdog") fails ("connect_to_kext() unexpectedly failed") or IOServiceOpen(type 1) fails ("IOServiceOpen failed with error"); IOWatchdog DOES register (QEMU msgbuf: `SWEET WDT: IOWatchdog registered`), cause not on screen yet -> need video. Note `wdt_test=no_user_checkin` makes watchdogd log "detected testing boot-args to not run, exiting" (path not reached here?). **HFS CORRUPTION:** `hfs_swap_BTNode: offset #0 invalid (0xBC1D) (blockSize 0x2000 numRecords 81)`, `node=19677 fileID=4` (catalog), `hfs_mark_inconsistent` repeated. Likely cause: non-journaled HFS + unclean panics while writing (0038e wrote a 2.7 GB core then panicked; every boot since ends in panic). Plan: reflash v3 (clean), longer term HFS journaling. Patch **0042**: one short `exec NAME` console line instead of the 3-line "Allowing spawn of iOS binary" notice; CI `38949451276` -> `xnu/out-0042`; image `shim/out/shim-boot-0042u.img` (same cmdline as 0041u).
- **LAUNCHD DAEMONS RUN (boot 0039u, 18:29:13 UTC, photo IMG_20261016_203052).** With `launchd_unsecure_cache=1` all boot tasks pass and launchd starts LaunchDaemons (pids > 100: identityservicesd 114 and lockdownd 106 crash, "Too many corpses being created"). Fatal: `watchdogd: ERROR: failed to discover watchdog KEXT service` -> exit (namespace 2 = signal, subcode 5) -> `_PanicOnCrash` panic. watchdogd: IOServiceMatching("IOWatchdog"), IOServiceOpen type 1, IOConnectCallScalarMethod sel 0/1 (check in)/3/4 (disable/enable userspace monitoring)/5, IOConnectCallStructMethod sel 2 (1 KiB in) and 9 (small out); VM path ("detected virtual machine environment and no watchdog KEXT found, exiting...") only when it detects a VM. Console also flooded with `hfs: set hardlink bit on vol=iOSRoot cnid=321318` (Linux-made hard links lack kHFSHasLinkChainBit; repaired only in memory on each lookup). Patches **0040** (`iokit/Kernel/arm/SweetWatchdog.cpp`: IOWatchdog + IOWatchdogUserClient, all selectors succeed with zeroed outputs, each logged once as `SWEET WDT: ...`) and **0041** (sweet_hfs hfs_catalog.c: the three link-repair printfs limited to 8 per boot); CI `38948245372` PASSED -> `xnu/out-0041` (QEMU regression OK). Image `shim/out/shim-boot-0041u.img` (0041 + sweet-0038hi.adt + ufsrw rootrw + launchd_unsecure_cache=1) booted 18:39:53 UTC (`research/boot0041u.log`), photo pending.
- **v3 FLASHED + keybag passes; next wall AMFI (launchd_cache_loader).** User said "flash, nothing to lose": `fastboot -S 512M flash userdata ios16-root-20H392-v3.simg` 17:51:52-17:57:01 UTC, 24/24 chunks OKAY (`research/flash-userdata-v3.log`). userdata = v3 (SHA256 fa84274c...22df) until the next rw boot. ABL fastboot then hung ("Sending" forever, `reboot bootloader` timed out) until the user re-entered fastboot by hand (common Xiaomi ABL crash). Boot 0038e 18:06:15 UTC (`research/boot0038e-3.log`), photos IMG_20261016_200812/200838: keybag OK, then boot tasks tzinit (`Bad zoneinfo link`, resets to system partition, OK), finish-restore, finish-demo-restore, sysstatuscheck, prng_seedctl (`failed to load kernel prng seed`, `failed to load virtual random (-147)`, AllowCrash), auearlyboot, then **launchd_cache_loader: `abort: Unable to find AMFI`** -> 2.7 GB core written to /cores in 91 s -> launchd panic `launchd_cache_loader[22] exited -- exit reason namespace 7 subcode 0x1`. launchd_cache_loader: SecStaticCodeCheckValidity of /System/Library/xpc/launchd.plist with detached .sig, then IOServiceMatching("AppleMobileFileIntegrity") + IOServiceOpen type 0 + IOConnectCallMethod sel 6 (1 scalar = 1, struct in = cdhash) = trust the cdhash, then sends the cache to launchd. Boot-arg `launchd_unsecure_cache=1` skips signature + AMFI ("Using unsecure cache"); the value is parsed with strtoul base 10 (helper 0x100002da8), so a path = 0 = off: boot 0039w (18:17:13 UTC, `=/System/Library/xpc/launchd.plist`, photo IMG_20261016_202008) still aborted `Unable to find AMFI` (core dump now skipped: `Failed to generate core file ... error 14`, so 0039 works). Image `shim/out/shim-boot-0039u.img` uses `launchd_unsecure_cache=1`. Patch **0039**: do_coredump = 0 on SWEET (kern.coredump sysctl still works); CI `38945267341` -> `xnu/out-0039` (_do_coredump now in __common). Image `shim/out/shim-boot-0039w.img` = 0039 + sweet-0038hi.adt + ufsrw rootrw + `launchd_unsecure_cache=/System/Library/xpc/launchd.plist`. TODO later: real AppleMobileFileIntegrity IOService (sel 6 trust cdhash etc.).
- **Image v3 ready, awaiting user "flash".** Boot 0038w 17:38:10 UTC, photo (chat image 30): `SWEET AKS: keybagd sel 0 -> 0x0`, `sel 14 out 1/0 -> 0x0` (x2), `MKB_INIT: mount is with NO CPROTECT ... does not support Data Protection`, `System Keybag loaded`; then keybagd still opens /private/var/keybags/systembag.kb (0x100012d3c, for BackupKeyBagKeys) -> ENOENT, `no-effaceable-storage` not set -> `Can't load the keybag. tears in rain... Time to die` -> `FATAL KEYBAG ERROR: kb_load` -> reboot -> Halt/Restart Timed Out panic. Fix: ADT `/defaults/no-effaceable-storage` (mkadt.py; `shim/out/sweet-0038hi.adt`, `research/q0038-hi.adt`, QEMU OK) + file `/private/var/keybags/systembag.kb` (0600 root, dir 0700; XML plist {KeyBagKeys: data}). **v3 image** `/run/media/dipa/android/ios-sweet-ipsw/ios16-root-20H392-v3.img` = v2 + that file, fsck OK, SHA256 fa84274c...22df; `ios16-root-20H392-v3.simg` (img2simg: zero blocks become FILL chunks, so a full flash overwrites every block the rw boots changed). Flash: `fastboot -S 512M flash userdata ios16-root-20H392-v3.simg`, then boot `shim/out/shim-boot-0038e.img` (0038 + sweet-0038hi.adt + ufsrw=1 rootrw=1).
- **0038 AppleKeyStore (CI 38938744130 PASSED -> `xnu/out-0038`; QEMU msgbuf: `SWEET AKS: AppleKeyStore registered (no passcode, unlocked)`; phone image `shim/out/shim-boot-0038w.img` booted 17:38:10 UTC, `research/boot0038w.log`, photo pending).** QEMU full kernel log trick (fb.txt is only the last screen): `llvm-nm KERNEL | grep _msgbufp` -> `--hmp "x /1gx ADDR"` gives struct msgbuf address (static, 0xfffffe0007b56678 on 0038) -> `--hmp "x /3gx STRUCT"` gives bufc (3rd quad) -> `--hmp "memsave BUFC 0x20000 \"FILE\""` (quote the file name), `tr -d "\0" < FILE`. Same inputs give the same addresses. Boot 0037w 17:08:35 UTC, photo IMG_20261016_191052: bindfs fixed mount; mount-phase-1/2 pass; `cc_fips_test` boot task: all corecrypto FIPS POST tests PASSED in userspace; then keybag boot task `keybagd --init`: `MKB_INIT: FATAL KEYBAG ERROR: failed to load system bag`, `Could not get options entry from the device tree` (x2, IODeviceTree:/options = NVRAM, non-fatal), `REBOOTING INTO RECOVERY MODE` -> reboot -> panic `Halt/Restart Timed Out @IOPlatformExpert.cpp:884` (no restart path on SWEET).
  - keybagd (static libaks): load_devicebag (0x100012c30) calls aks_get_system (sel 14, 0-1 scalar in, 1 out) and loads /private/var/keybags/systembag.kb only if the result is 0xe00002f0 (NotFound); any other error -> fatal; SUCCESS -> skip the file (userspace-reboot path). systembag.kb is a plist {KeyBagKeys}; decrypted with effaceable storage unless IODeviceTree:/defaults has `no-effaceable-storage`. Image has no /private/var/keybags. has_data_protection: statfs of /private/var; no cprotect on our HFS -> device-bag volume mapping skipped.
  - libaks connection: IORegistryEntryFromPath / IOServiceMatching("AppleKeyStore"), IOServiceOpen type 0, then selector 0 (no args) must succeed.
  - **AppleKeyStore selector map (iOS 16.7 AppleKeyStore.framework, via `ipsw dyld disass`):** 0 open, 2 create_bag, 3 save_bag, 4 unload_bag, 5 set_system_with_passcode, 6 load_bag, 7 get_lock_state (1 in, 1 out; bit 2 = unlocked since boot), 9 unlock_device, 10 wrap_key, 11 unwrap_key, 12 unlock_bag/test_stashed_kek, 13 lock_bag, 14 get_system, 15 change_secret_se, 16 internal_state, 17 get_device_state (1 in, struct out <=4K: DER SET of SEQUENCE{UTF8 key, INTEGER}: ss state, sls lock_state (MKBGetDeviceLockState returns it), sb backoff, sbo, sfa failed attempts, sfao, sgs generation, sas assertions, sgpe grace, srcd countdown, sr reserved), 18 recover_with_escrow_bag, 19 obliterate_class_d, 20 drain_backup_keys, 21/22 set/clear_backup_bag, 23 get_bag_uuid, 24 rewrap_key_for_backup, 26/27 assert_hold/drop, 30/31 set/get_configuration, 33-37 stash, 38 auth_token_create, 40 generation, 41 fdr_hmac_data, 42 verify_password, 43 _aks_operation, 44 remote_session, 49/50 signing keys, 51/53/54 stash enable/persist/escrow, 55 unload_session_bags, 57/58 remote peer, 59-62 smartcard, 63 migrate_s_key, 65 set_keybag_for_volume_with_cookie_persona, 66/67 sync bags, 68 copy_volume_cookie_persona, 69-73 se_*, 74-79/84/85/99 fv_* (FileVault/VEK), 80/81 absinthe, 82 make_public_backup_bag, 83 drop_auxiliary_auth, 86 kext get/set options, 87 invalidate_bag, 88-91/94/95/106/107 se_*, 92 lower_iteration_count, 93 get_internal_info, 96-98/117 keybag_persona create/list/delete, 100/101 assert promote/consume, 102/103 notify_state set/is_set, 104 fairplay, 105 change_secret_epilogue, 108 delete_xart_leak, 110-113 backup volume, 114 sealed_hashes_set, 115 prewarm_sps, 118-128 AKSIdentity*/AKSGetLastUser.
  - Patch **0038**: `iokit/Kernel/arm/SweetKeyStore.cpp` (class AppleKeyStore on IOResources, IOUserClientClass AppleKeyStoreUserClient; personality in KernelConfigTables.cpp): 0/4/5/9/12/13/26/27/55/102 success, 14 -> handle 0, 7 -> 0x4, 17 -> DER state (ss 4, sls 0), others kIOReturnUnsupported; logs `SWEET AKS: <proc> sel N arg0 in a/b out c/d -> ret` for every call.
  - Tools: shared cache copied to `research/dsc/` (git-ignored; ipsw needs a writable dir for its .a2s symbol cache); `ipsw dyld disass research/dsc/dyld_shared_cache_arm64 --image AppleKeyStore|MobileKeyBag`; scratchpad `annot2.py BIN DIS FIXUPS` annotates llvm-objdump output with strings and import names (`ipsw macho info --fixups`).
- **0037 bindfs (phone boot 0037w pending photo).** Boot 0036mw 16:57:47 UTC, photo IMG_20261016_190102: WRITABLE ROOT WORKS: `/dev/ufsroot0 on / (hfs, local, noatime)` after mount_hfs update (GetMasterBlock EBUSY harmless), coredump of mount written to /cores (rw). Then `mount: failed to mount /private/preboot/5CBE3601.../usr/standalone/firmware -> ...: Operation not supported by device (19)` -> exit 74 -> launchd panic `mount[2] exited`. Cause: the macOS-derived config had nullfs but no bindfs (ENODEV = unknown fs type). Caller passes env 0 -> bind not required, ENOENT (missing source dir) tolerated. Patch **0037** adds `bindfs` to FILESYS_BASE in MASTER.arm64.sweet; CI `38936550483` -> `xnu/out-0037` (bindfs_vfsops present; QEMU probe regression OK). Image `shim/out/shim-boot-0037w.img` (0037 + sweet-0036hi.adt + ufsrw=1 rootrw=1) booted 17:08:35 UTC (`research/boot0037w.log`). NOTE: userdata has now been modified by rw boots; it no longer equals the v2 image, so sparsediff with v2 as OLD is not safe any more (full reflash or a new baseline needed).
- **0036 phone: launchd boot tasks run; mount -P 1 needs /chosen/boot-manifest-hash.** Boot 0036hr 16:15:32 UTC, photo IMG_20261016_185236: platform check passes; fsck boot task runs (`fsck: not booting main or diagnostic OS. Skipping fsck on OS container`); mount-phase-1: `failed to get filesystem info` x2 (no IODeviceTree:/filesystems/fstab, non-fatal), `mount: data volume missing, but not required in env: 0`, mount_hfs update of /: `GetMasterBlock: Error 16 opening /dev/ufsroot0` (EBUSY, mounted block dev, non-fatal) then mount() EROFS (read-only boot) -> `mount: / failed with 1`; then `failed to get boot-manifest-hash` -> errx exit 66 -> launchd panic `mount[3] exited`. /sbin/mount: fn 0x100005f90 reads IODeviceTree:/chosen boot-manifest-hash (hex), bindfs-mounts /private/preboot/<HEX>/usr/standalone/firmware (ENOENT tolerated unless required). `tools/mkadt.py` now adds `boot-manifest-hash` = SHA-384("sweet boot manifest") (5CBE3601...5205). ADTs `shim/out/sweet-0036hi.adt`, `research/q0036-hi.adt` (QEMU probe OK, csops 0x26000001). Image `shim/out/shim-boot-0036mw.img` (0036 + new ADT + ufsrw=1 rootrw=1), booted 16:57:47 UTC (`research/boot0036mw.log`): FIRST WRITABLE BOOT of userdata (restore source: v2 image on SSD).
- **0036 CS_SIGNED (phone boot 0036hr pending photo).** Phone boot 0035hr 2026-10-16 15:57:02 UTC (`research/boot0035hr.log`, photo IMG_20261016_180249): highmem works on hardware; shared cache maps (trust-cache warnings only), Apple launchd runs (`Darwin Bootstrapper Version 7.0.0`, `entering ondemand mode`), starts boot task fsck, then userspace panic `boot task is not a platform binary (fsck, /sbin/fsck)`. launchd+0x3fea0: `csops(pid, CS_OPS_STATUS)` must have bit 0x04000000. Cause: nothing set CS_SIGNED (AMFI does it in vnode_check_signature), so csproc_get_blob() returns NULL for every process and csops never reports CS_PLATFORM_BINARY (also breaks per-process cdhash/entitlement queries). QEMU probe init (`csops` status printer, scratchpad csq/) on 0035: `0x02000001`; patch **0036** (`*cs_flags |= CS_SIGNED` in the SWEET AMFI hook), CI `38929635791` -> `xnu/out-0036`: `0x26000001`. Images `shim/out/shim-boot-0036hr.img` / `-0036hw.img` (same cmdlines as 0035). 0036hr booted 16:15:32 UTC (`research/boot0036hr.log`). Next launchd boot tasks (embedded __config plist): fsck -qL and mount -P 1/2 (RequireSuccess); no /etc/fstab on the image.
- **0035 ENTITLEMENTS + PLATFORM BINARIES (QEMU verified).** `xnu/patches/0035-sweet-amfi-entitlements-platform-binaries.patch`: new `iokit/Kernel/arm/SweetEntitlements.cpp` (OSObject subclass: OSDictionary from OSUnserializeXML of the signature's XML entitlements + original XML for CS_OPS_ENTITLEMENTS_BLOB); `bsd/kern/sweet_amfi.c` answers queryEntitlementBoolean/String(+WithProc, string also matches array members), copyEntitlementAsOSObject(+WithProc, retained), asdict (retained), get_xml (kalloc_data copy); built-in MAC policy "SWEET AMFI" (registered from bsd_init before vfs/exec) with mpo_vnode_check_signature: every signed binary on the MNT_ROOTFS mount gets CS_PLATFORM_BINARY (stand-in for AMFI's static trust cache: iOS system binaries are ad-hoc, cd_flags 0x2, platform byte 0), and attaches entitlements ONLY for the writable copy (cs_blob != csb_ro_addr; revalidation passes the RO blob). LESSON: first version attached in adjustContextWithoutMonitor -> QEMU `unable to adjust OSEntitlements context without monitor: 53` because ubc_cs_convert_to_multilevel_hash (4K-page signatures on 16K kernel) sets csb_entitlements_blob = NULL; ALL iOS 16 binaries (launchd, backboardd, SpringBoard) use 4K code pages, so this would have broken launchd on the phone. Boot-arg `sweet_amfi_debug=1` logs `SWEET AMFI: <ident>: N entitlements (test: ...)`. `tools/mkinit.py OBJ OUT [ENTS.plist]` adds an XML entitlements blob (special slot -5; default output byte-identical). QEMU `research/q0035-ent` (RAM disk `research/root-hfs-ent.img`, init with 3 test entitlements, highmem): `org.sweet.init: 3 entitlements (test: bool 1 string 1 array 1)` then init PID 1. MAC policies loaded: 0034 = 1, 0035 = 2 (QMP `mac_policy_list`). CI `38909807230` -> `xnu/out-0035`. Phone images: `shim/out/shim-boot-0035hr.img` (highmem, ro), `-0035hw.img` (highmem, +ufsrw=1 rootrw=1), `-0035r.img` (low mem fallback).
- **PHONE TEST ORDER (updated):** 0035hr -> if instant reset, 0035r -> then 0035hw.

- **HIGHMEM: XNU in the upper DDR bank, ~3.95 GiB (was 1.2 GiB).** Live FDT memory = <0x80000000 2G> + <0x1_00000000 0xfcc00000>; all fixed reserved-memory carve-outs are in the low bank (highest: ramdump_fb 0xaf000000, rmtfs ~0xfde01000), dynamic pools have alloc-ranges <= 0xffffffff, UFS node has no `iommus` (Linux DMAs anywhere). `tools/mkadt.py --highmem` sets /chosen dram-base 0x100000000 dram-size 0xfcc00000; `tools/mkpayload.py` now takes phys_base/mem_size from the ADT (default payloads byte-identical, verified); `tools/qemu-sweet.py` sizes -m from the payload (8G for highmem). Patch **0034** (`0034-sweet-ufs-dma-above-4g.patch`): UFS refuses DMA memory above 4G without UFSHCI CAP.64AS (bit 24), logs `DMA at 0x...`. CI `38905889883` success -> `xnu/out-0034`. **QEMU verified** (`research/q0034-hi`, ADT `research/q0034-hi.adt` --qemu --highmem, HFS RAM disk): phys_base 0x100000000, init PID 1 heartbeat, no panic; `max_mem` = `mem_size` = 0xfcc00000 read via QMP (`research/q0034-hi-mem`). Phone images: `shim/out/shim-boot-0034hr.img` (read-only) / `-0034hw.img` (+ufsrw=1 rootrw=1), ADT `shim/out/sweet-0034hi.adt` (asmb SIP + sweet-ufs + highmem). PHONE RISK: unknown runtime TZ/XPU protection in the upper bank would show as an instant reset; fall back to 0033r/w. Watchdog ruled out for the overnight reset: msm-watchdog bark is 20 s (qcom,bark-time 0x4e20) yet panic screens stay up for many minutes.

- **Offline research 2026-10-16 (user away, phone unavailable). Images rebuilt** `shim/out/shim-boot-0033r.img` / `-0033w.img` now also carry `wdt_test=no_user_checkin`. NEXT ON PHONE: boot 0033r (expect past in6_nigroup), then 0033w (first writes: rw root fixes HFS link-chain bits itself and gives /var for launchd sockets /var/run/syslog, /var/run/lockdown.sock).
- **launchd.plist** (`/System/Library/xpc/launchd.plist`, compiled; 532 daemons, 66 RunAtLoad/KeepAlive, list in scratchpad `early-daemons.txt`). `_PanicOnCrash` daemons: containermanagerd/usermanagerd (InternalOnly), lockdownd/remoted/trustd/remotepairingdeviced (AutomationOnly), **watchdogd unconditional** (KeepAlive SuccessfulExit=false). watchdogd needs IOKit `IOWatchdog` kext service; if absent it exits only when `kern.hv_vmm_present` (ADT `/defaults/vmm-present`, hvg_sysctl.c) or with boot-arg `wdt_test=no_user_checkin` ("detected testing boot-args to not run, exiting"; reads kern.bootargs). Using the boot-arg (vmm-present would change many daemons; keep as an option).
- **GUI path research (QuartzCore in the shared cache, `ipsw dyld str CACHE STR`, ~10 s/search):** CA::WindowServer has IOMFBServer/IOMFBDisplay (Apple DCP/IOMobileFramebuffer), AppleCLCDDisplay, AppleRGBOutDisplay, **VirtualServer/VirtualDisplay** and **MemorySurface**, EAGLServer. Renderers: CA::OGL::MetalContext, GLContext and a **CPU software rasterizer CA::OGL::SW** (samplers/blend modes; "image is too large for software renderer"). Env knobs: `CA_ENABLE_OGL`, `CA_DISPLAY_TYPE`, `CA_FORCE_LOCAL_SERVER` (249 CA_* vars). Hypothesis (unverified): backboardd's render server could run a VirtualServer/MemorySurface with the SW renderer and we copy the surface to the ABL framebuffer -> needs disassembly of CA::WindowServer server creation. Expected other GUI walls: IOSurface (closed-source kext; needs a reimplementation), IOMobileFramebuffer user client, IOHID touch events, AppleKeyStore/keybag (SEP) for lock state, MobileGestalt answers (AppleCLCD etc.).

- **0032r RESULT (boot 05:07:50 UTC, `research/boot0032r.log`, photo IMG_20261016_071200): SHARED CACHE MAPPED, LAUNCHD RUNS.** With SIP relaxed (ADT asmb) the `not in trust cache` lines are only warnings for every subcache (.31 ... .42.dyldlinkedit); no SIP rejection; libSystem loads; launchd configures networking (`skip attaching fsw to lo0 using legacy TX model`) -> kernel data abort far 0x28 in `SHA1Init` (symbolized as sha1_init) from `in6_nigroup` (IPv6 on lo0): g_crypto_funcs NULL. Kernel addresses are unslid: `~/swift/usr/bin/llvm-symbolizer --obj=KERNEL ADDR` works directly.
- **0032** BearSSL SHA-1 (`0032-sweet-bearssl-sha1.patch`), **0033** BearSSL SHA-384/512 (`0033-sweet-bearssl-sha384-sha512.patch`, BearSSL ctx stored in SHA512_CTX, static-asserted to fit; ubc_subr.c uses SHA-384 for code directories). `0020-stage-bearssl.sh` now also stages hash/sha1.c, hash/sha2big.c, codec/{dec,enc}{32,64}be.c. CI `38854909053` success (0032-only run `38854802073` superseded). Kernel `xnu/out-0033` (SHA1Init -> _br_sha1_init verified by disassembly; nm symbols have a leading underscore). Images (ADT sweet-0032): `shim/out/shim-boot-0033r.img` (read-only), `shim-boot-0033w.img` (+ufsrw=1 rootrw=1). Still NULL g_crypto_funcs users: des, chacha20poly1305, rsa, aesxts, rand, flow_divert.
- `research/check-patch-order.py` now skips patches touching CI-staged sweet_hfs sources (0031) instead of stopping.

- **0031r RESULT (boot 05:03:52 UTC 2026-10-16, `research/boot0031r.log`, photo IMG_20261016_070508): SHARED CACHE FOUND.** dyld now opens `dyld_shared_cache_arm64` (v2 image hard links), kernel refuses to map it: `shared_region: ... map(...'dyld_shared_cache_arm64'): not in trust cache` -> `vnode is not SIP-protected` (vm_unix.c: macOS arm64 path needs trust cache, else root-owned + SF_RESTRICTED unless CSR_ALLOW_UNRESTRICTED_FS) -> `dyld cache '(null)' not loaded: syscall to map cache into shared region failed` -> libSystem not loaded -> coredump to /cores fails error 30 (EROFS) -> panic initproc failed -> "MACH Reboot" (spins; screen kept). Lots of `hfs: set hardlink bit on vol=iOSRoot cnid=... linkid=...` spam (Linux-made hard links lack the link-chain bit; read-only mount cannot persist the fix). FIX: ADT `/chosen/asmb` with `lp-sip0`=0x6f (u64; incl. CSR_ALLOW_UNRESTRICTED_FS) and `lp-sip1`=1 (unauthenticated root), `tools/mkadt.py` -> `shim/out/sweet-0032.adt`. Images with kernel 0031: `shim/out/shim-boot-0032r.img` (read-only) and `shim-boot-0032w.img` (+ufsrw=1 rootrw=1).

- **2026-10-16 morning:** userdata now = **v2** image (`diff-v1-v2.simg` flashed 21:06:50 UTC 2026-10-15, OKAY, `research/flash-userdata-diff-v2.log`); future diffs use `ios16-root-20H392-v2.img` as OLD. Booted `shim-boot-0029k.img` (ignition_level=1) right after (`research/boot0029k-v2.log`); **no photo** (user asleep). Next morning the phone was in PixelOS recovery = some hardware reset (ABL then booted Android, which cannot use userdata). OBSERVATION: our kernel cannot reset the SoC itself (`PE_halt_restart` is never set; reboot/halt print "MACH Reboot"/"CPU halted" and spin), so the reset came from outside XNU: Qualcomm watchdog or a TZ/XPU violation. Unknown which; re-boot 0029k and watch/video until the reset. Do NOT tap factory reset/format data in recovery (would wipe the iOS image).
- **0030** (`xnu/patches/0030-sweet-ufs-writes.patch`, CI `38852655542`): UFS WRITE(10) + read-modify-write for partial 4 KiB blocks + SYNCHRONIZE CACHE (DKIOCSYNCHRONIZE), only with boot-arg `ufsrw=1`; `ufs_write_blocks` re-checks partition bounds before every write (only place data goes out).
- **0031** (`xnu/patches/0031-sweet-read-write-root.patch`, CI `38852837176`): boot-arg `rootrw=1` clears MNT_RDONLY before the root mount (no data volume on sweet: /private/var is on the root; image has no /etc/fstab); Apple HFS accepts a dirty non-journaled ROOT read-write on SWEET (logs "mounting dirty non-journaled root read-write"). Later: journaled HFS for crash safety. Kernel `xnu/out-0031` (CI `38852837176` success, 5m31s; 0030 run cancelled by the newer push). Boot images (phone ADT `sweet-0028.adt`, ramdisk byte-matched): `shim/out/shim-boot-0031r.img` = 0029k args (read-only, ignition_level=1) and `shim/out/shim-boot-0031w.img` = same + `ufsrw=1 rootrw=1`. PLAN: boot 0031r first and film until the reset (diagnose overnight reset), then 0031w (first ever writes to userdata; v2 image on the SSD is the restore source). `research/check-patch-order.py` cannot check 0031 (staged sweet_hfs files are not in its index); CI stage scripts run first, so CI is the check.

- **ignition_level=1 result** (boot 21:01:39 UTC, `research/boot0029k.log`, photo IMG_20261015_230308): preboot/cryptex stages skipped (need >= 2/3), `dylib_cache: finding shared cache on system volume: ignition level = 1, search root fd = 4, subpath = System/Library/Caches/com.apple.dyld/` -> not found -> `ignition boot failed: 19` -> no shared cache -> libSystem not loaded. FIX IN PROGRESS: image v2 = copy of the flashed image + `/System/Library/Caches/com.apple.dyld/` with HARD LINKS to the 44 cryptex cache files (no extra space; avoids symlink-following doubts), then `tools/sparsediff.py ios16-root-20H392.img ios16-root-20H392-v2.img diff.simg` and flash only the diff. Boot with `ignition_level=1` (shim-boot-0029k.img).
- **ignition_level=0 result** (boot 20:58:07 UTC, `research/boot0029j.log`, photo IMG_20261015_230037): all stages skipped as "ignition level insufficient" (hello/preboot/cryptex1 sniff >= 2, select os cryptex path/graft >= 3, **dyld_cache >= 1**), `ignition boot failed: 89`, "ignition partially disabled", then same `Library not loaded: /usr/lib/libSystem.B.dylib (no such file, no dyld cache)`. => dyld gets the shared cache directory from ignition's dyld_cache stage. Next: `ignition_level=1` (`shim/out/shim-boot-0029k.img`) to skip preboot/cryptex stages but run dyld_cache; its log "finding shared cache on %s ... subpath = %s" will show where it searches. If it searches rootfs /System/Library/Caches/com.apple.dyld, add a symlink there (image rebuild; consider a diff-only sparse flash tool to avoid rewriting 12 GB).
- **APPLE dyld/launchd RUNNING (libignition) with `unentitled_ios_sim_launch=1`** (boot 20:53:24 UTC, `research/boot0029i.log`, photo IMG_20261015_225617): kernel prints "Allowing spawn of iOS binary ... boot-arg set to true"; `shared_region: ... check_np ... vm_shared_region_start_address() failed` (no region yet, normal); dyld's built-in **libignition** (Darwin Ignition Sequence 1.0.0, libignition-51~1974; prints rd=ufsroot0, hardware target sweet, ignition level 0x5, platform 0x2, boot spec local, 7 stages): `hello from launchd.1` -> `preboot: mounting preboot` -> `failed to lookup preboot: 25` (ENOTTY: looks for a separate Preboot volume by role) -> ignition fails -> dyld `Library not loaded: /usr/lib/libSystem.B.dylib ... (no such file, no dyld cache)` -> launchd exit -> panic initproc failed. dyld boot-args found via strings: `ignition_level`, `ignition_force_dylib_root` (forced rootfs/livefs/cryptex fallback), `ignition_halt_after`, `ignition_live_app_graft`; dyld cache search paths include /System/Cryptexes/OS, /System/Volumes/Preboot/Cryptexes/OS/, /private/preboot/Cryptexes/OS/ (present in our image). Next try `ignition_level=0` (`shim/out/shim-boot-0029j.img`).
- **APPLE launchd EXECUTED FROM UFS (2026-10-15).** Flashed iOS image: `img2simg` -> `ios16-root-20H392.simg` (12.1 GB) then `fastboot -S 512M flash userdata ...simg` (24 chunks, 307 s, `research/flash-userdata-ios16.log`; a raw-image flash was killed by earlyoom at 2.6 GB RSS - always flash the sparse image). ABL fastboot hung on getvar after the flash; power+vol-down fixed it. Boot 0029u 20:49:04 UTC (`research/boot0029u-ios16.log`), photo IMG_20261015_225134: `hfs: mounted iOSRoot` -> load_init_program /sbin/launchd -> panic `unexpected SIGKILL of launchd (CS_KILLED) with reason -- namespace 9 code 0xe` = OS_REASON_EXEC / EXEC_EXIT_REASON_WRONG_PLATFORM: our kernel is XNU_TARGET_OS_OSX, iOS-platform binaries are "alien" and refused unless spawn attr platform set or DEVELOPMENT TUNABLE `unentitled_ios_sim_launch`. Next try: same kernel, cmdline + `unentitled_ios_sim_launch=1` (`shim/out/shim-boot-0029i.img`). LONGER TERM: macOS-config kernel marks iOS maps alien (vm_map_mark_alien) and differs from iOS in many policies; an iPhoneOS-config kernel build may eventually be needed.
- **iOS 16 ROOT IMAGE BUILT:** `/run/media/dipa/android/ios-sweet-ipsw/ios16-root-20H392.img` (16 GiB case-sensitive HFS+, label iOSRoot, 12 GB used, fsck OK after `fsck.hfsplus -y` rewrote 32 non-ASCII localized WorkflowKit Shortcut names Linux decomposes differently). Built by `tools/mkiosroot.sh OS.dmg SYSTEMOS.dmg APPOS.dmg OUT.img [SIZE]` (needs sudo; apfs-fuse as root; OS dmg is UDIF -> link must end .dmg). Contents: iPhone X 20H392 OS root + SystemOS cryptex at /private/preboot/Cryptexes/OS (so /System/Cryptexes/OS -> cache, 44 files, dyld_v1 arm64) + AppOS at .../App. /sbin/launchd and /usr/lib/dyld root:wheel 0755. NEXT: (confirm) `fastboot flash userdata ios16-root-20H392.img` (auto-sparse), boot 0029u (rd=ufsroot0) -> Apple launchd attempt.
- **MILESTONE ON HARDWARE: BOOT FROM INTERNAL FLASH.** 0029 CI `38797924912` PASSED, `xnu/out-0029` SHA256 `a68bc847...2a37`. Image `shim/out/shim-boot-0029u.img` (payload-0029u = 0029 kernel + `shim/out/sweet-0028.adt` + `rd=ufsroot0`, NO RAM disk). Boots 20:01:34 and 20:12:37 UTC (`research/boot0029u*.log`), photo IMG_20261015_221403: `SWEET UFS: "userdata" on LUN 0: first block 0x2b8c00, 109643 MiB, read-only` -> `BSD root: ufsroot0, major 1, minor 0` -> `hfs: mounted SweetRoot on device b(1, 0)` -> `SWEET: root volume is not authenticated (error 25); continuing unsealed` -> `load_init_program ... /sbin/launchd` -> `*** SWEET userspace: init running as PID 1 ***` -> heartbeat (ran for minutes unattended). userdata currently holds the 8 MB `research/root-hfs.img`. NEXT: build a multi-GB HFS+ image with the iOS 16 (iPhone X 20H392) userland (OS rootfs + SystemOS cryptex contents incl. dyld shared cache at /System/Library/Caches/com.apple.dyld; preserve modes/owners/symlinks; decompress LZBITMAP via apfs-fuse), flash it to userdata (sparse, needs user OK), then try Apple's dyld/launchd. Driver is read-only (root mounts RDONLY), fine for first launchd attempts.
- **userdata FLASHED with the 8 MB HFS test volume** (user said "flash it", 2026-10-15 19:53:17 UTC, `research/flash-userdata-hfs-test.log`: `fastboot flash userdata research/root-hfs.img` OKAY; pre-checks: one sweet device, partition-size:userdata 0x1AC4BFB000, partition-type f2fs, image fsck OK, SHA256 3626ea69...). Android userdata is now destroyed (expected/approved). Boot 0028u at 19:53:20 (`research/boot0028u-hfs.log`), photo IMG_20261015_215541: `BSD root: ufsroot0` -> **`hfs: mounted SweetRoot on device b(1, 0)` from internal UFS** -> panic `rootvp not authenticated after mounting @bsd_init.c:931` (arm64 macOS-config requires FSIOC_KERNEL_ROOTAUTH sealed root for non-ramdisk roots). Patch **0029** (`dd1c284`): SWEET logs `SWEET: root volume is not authenticated (error N); continuing unsealed` instead of panicking (Apple configs keep the panic; pivot_root still requires auth). CI **`38797924912`** running. Next: download out-0029, phone image with sweet-0028.adt + rd=ufsroot0 (no RAM disk), boot -> expect init from UFS.
- **UFS ROOT DRIVER VERIFIED ON HARDWARE (read-only).** 0028 CI `38796139570` PASSED, `xnu/out-0028` SHA256 `8b981640...9da6`; QEMU HFS RAM-disk regression `research/q0028-hfs` still runs init. Phone boot 2026-10-15 19:50:24 UTC (`research/boot0028u.log`, image `shim/out/shim-boot-0028u.img`, phone ADT `shim/out/sweet-0028.adt` with /sweet-ufs, NO RAM disk, `rd=ufsroot0`), photos IMG_20261015_215151/215220: `SWEET UFS: "userdata" on LUN 0: first block 0x2b8c00, 109643 MiB, read-only` -> `BSD root: ufsroot0, major 1, minor 0` -> `hfs_ValidateHFSPlusVolumeHeader: unknown Volume Signature : f188` (Android-encrypted data, as expected) -> `cannot mount root, errno = 19`, kernel retries mountroot (no panic). Nothing written to flash. NEXT (destructive, needs user confirmation right before): `fastboot flash userdata research/root-hfs.img` (8 MB HFS with test init) then boot rd=ufsroot0 -> expect init from internal flash.
- **PATCH 0028 (`33aceac`): XNU read-only UFS root device**, CI **`38796139570`** running (next artifacts xnu/out-0028, research/bt29, run29.log). `bsd/dev/sweet_ufs.c`: reuses ABL's UFSHCI state (like the shim probe), takes over UTRL at a kmem_alloc_contig region (DMA layout: UTRL 0x0, UCD 0x1000, 1 MiB bounce 0x4000), verifies UTRLBA readback before any doorbell, IE=0 polled, one SCSI cmd at a time on LUN0 (TUR x3, READ(10) via bounce, PRDT 256 KiB chunks), flush_dcache64 by PA around each command (host not dma-coherent per DT), finds GPT partition by name (`ufsroot=` boot-arg, default `userdata`), exposes `/dev/ufsroot0`/`rufsroot0` (512-byte logical sectors, physical 4 KiB, DKIOC* ioctls), refuses writes (EROFS). IOKitBSDInit: `rd=ufsroot0` -> sweet_ufs_rootdev() (lazy init) else panic. ADT: `tools/mkadt.py` adds `/sweet-ufs` reg <0x1d84000 0x3000> for the PHONE only (not --qemu). Local compile OK, imports resolve. Sandbox research/bt28 (pre0028 originals). FIRST PHONE TEST PLAN (non-destructive): boot 0028 with phone ADT + `rd=ufsroot0` and NO RAM disk: expect `SWEET UFS: "userdata" on LUN 0: first block 0x2b8c00, 109643 MiB` + `BSD root: ufsroot0`, then root mount failure (userdata is still Android-encrypted) -> panic. That validates the driver before flashing an HFS image into userdata (needs explicit user confirmation at that time).
- **SUPERSEDES the 64 GiB iosroot GPT plan: user said "u can delete android" (2026-10-15).** Use the existing `userdata` partition (LUN0 sda34, 4K LBA 0x2B8C00, 0x1AC4B MiB ~107 GiB) directly as the iOS root: NO GPT changes. Keep bootloaders, recovery (OrangeFox), modem/persist/fsg/modemst untouched. Write the HFS image later with `fastboot flash userdata` (sparse, auto-split under the 768 MiB limit). Android will no longer boot normally (expected; reinstallable). Order: XNU UFS driver first, read-only against the current GPT; flash only once it can locate userdata. Nothing erased yet.
- **DECIDED (user, 2026-10-15): 64 GiB `iosroot` on LUN0 (sda), taken from userdata (wipes Android user data; Android/super kept).** Planned GPT (4K LBAs): userdata 0x2B8C00..0xD7D6FF (~43 GiB, keep type/unique GUIDs and attributes); iosroot 0xD7D700..0x1D7D6FF (0x1000000 blocks = 64 GiB, 1 MiB aligned); backup GPT area unchanged. Procedure: user backs up phone data -> boot OrangeFox recovery (adb) -> back up GPT (sgdisk --backup + raw dd of LBA 0-5 and last 6 blocks) to research/ -> sgdisk edit -> Format Data -> verify Android boots to setup. NOT EXECUTED YET.
- **INTERNAL UFS WORKS FROM THE SHIM (read-only), user authorized internal-UFS approach incl. flashing (2026-10-15, "i allow everything").** Shim probe `shim/ufs.c` (commit `12ed3ed` + filter): ufshc@1d84000 is UFSHCI 2.1 (ver 0x210, cap 0x1587031F, 32 slots), ABL leaves HCE=1, HCS=0x10F (device present, lists ready, UIC ready); probe takes over UTRL at its own buffer (verifies UTRLBA readback before any doorbell), TEST UNIT READY/READ CAPACITY/READ(10) all succeed. LUN0 = 0x1D7D800 x 4 KiB (~126.6 GB), valid GPT (64 entries at LBA 2). Photos IMG_20261015_212916/213325/213429. Big LUN0 partitions (start in 4K LBAs / MiB): super 0xCA00/0x2200 (8.5 GiB), logdump 0x22CA00/64, minidump 0x230A00/128, rawdump 0x238A00/128, recovery 0x240C00/128, cache 0x248C00/384 ext4, exaid 0x260C00/384, cust 0x278C00/1024 ext4, **userdata 0x2B8C00/0x1AC4B MiB (~107 GiB), fs unreadable = encrypted (metadata encryption)**. cache..cust contiguous = only 1.75 GiB (too small for iOS ~10+ GiB). Plan needing user consent: shrink userdata in GPT (wipes Android data) and add an `iosroot` partition at the end of LUN0. LUNs 1-5 not listed yet (sdb..sdf backed up in backup/lun).
- **fastboot limit measured (2026-10-15, read-only getvar):** `max-download-size: 805306368` (768 MiB); `max-fetch-size` unsupported; `is-userspace: no` (ABL fastboot). A `fastboot boot` image (shim+kernel+RAM disk) must be < 768 MiB, so the 2.5 GiB iOS shared cache cannot ride in the boot RAM disk even if XNU gets all RAM. Real userland needs storage access (UFS driver, or USB host) or a much smaller cache. Unlocking full RAM is still needed later (GUI).
- **iOS 16 USERLAND SOURCE (Claude, 2026-10-15).** Chose **iPhone X (iPhone10,3/10,6, D22/D221AP)** iOS **16.7.16 (20H392)** over iPhone 8: same A11 (no PAC -> plain arm64, runs on Kryo 470/ARMv8.2), last iOS for A11; X userland is home-button-less and tall-screen (1125x2436 vs sweet 1080x2400), better fit for later GUI. Note the X has its OWN SystemOS cryptex (different digest from iPhone 8's). IPSW URL in `research/ipsw-x/URL.txt` (+ BuildManifest). Images on the user's external SSD (NOT in git, do not format that disk: it holds the user's photos): `/run/media/dipa/android/ios-sweet-ipsw/iPhone10,3_16.7.16_20H392/` — `087-86593-047.dmg` = Cryptex1,SystemOS (2,743,074,816 B), `087-86698-044.dmg` = OS rootfs (4,730,814,044 B), both zip CRC-32 verified, plus Firmware/*.root_hash/.trustcache/.mtree. AppOS cryptex is 087-86715-047.dmg (10 MB, same as iPhone 8).
  - Images are raw APFS; files use LZBITMAP (decmpfs type 14). 7z cannot decode. Tools: `ipsw` 3.1.738 (AUR ipsw-bin, user-approved) needs apfs-fuse on Linux; **apfs-fuse** built in user space (system cmake broken: cmake 4.4.4 wants libjsoncpp.so.27, jsoncpp 1.9.6 installed = partial upgrade, NOT fixed) with pip cmake + `-DCMAKE_POLICY_VERSION_MINIMUM=3.5 -DCMAKE_CXX_FLAGS="-include cstdint"`, installed to `~/.local/bin/apfs-fuse` (+apfs-dump-quick). Mount via a comma-free symlink (apfs-fuse splits options on ',' in `iPhone10,3`; exFAT has no symlinks -> put link elsewhere): `apfs-fuse LINK/087-86698-044.dmg MNT` -> `MNT/root/...`; unmount `fusermount3 -u MNT`.
  - Verified from headers: `dyld_shared_cache_arm64` magic `dyld_v1   arm64`; `/sbin/launchd`, `/usr/lib/dyld` = cputype 0x100000c subtype 0 (plain arm64). libSystem exists only inside the cache.
  - **BLOCKER for real userland via RAM disk:** shared cache = 3.10 GiB in 44 files (~2.5 GiB without the 592 MB `.symbols`), but the kernel manages only 1.20 GiB (0xb0000000..0xfd000000). Options: (A) give XNU the phone's full ~6 GB (banks 0x80000000+2G and 0x100000000+0xfcc00000, carve-out holes need pmap support) AND check fastboot max-download-size for a multi-GB boot image; (B) storage driver (Qualcomm UFS) to read a root from flash (no flashing allowed: would need a file/partition strategy); (C) run against individual dylibs extracted from the cache (uncertain).
- **MILESTONE ON HARDWARE: HFS+ ROOT FILESYSTEM -> PID 1.** Boot 2026-10-15 18:22:12 UTC (`research/boot0027b.log`, image `shim/out/shim-boot-0027b.img`), photo `IMG_20261015_202334.jpg`: `BSD root: md0` -> `hfs: mounted SweetRoot on device b(1, 0)` -> `load_init_program: attempting to load /sbin/launchd` -> `*** SWEET userspace: init running as PID 1 ***` -> repeated `SWEET init: still alive`, no panic. Kernel 0027 (built-in Apple OSS HFS + BearSSL MD5), init with SP alignment fix. NEXT: real iOS 16 userland on the HFS image (dyld, libSystem/dyld shared cache, launchd). Known gaps: entitlements (none granted), SHA-1/SHA-384/512 providers, no storage driver (RAM disk only), root mounted read-only.
- **PHONE HFS ROOT (0027) + SIGBUS ROOT-CAUSED.** Phone boot 2026-10-15 17:49:06 UTC (`research/boot0027.log`, photo `IMG_20261015_200031.jpg`): `hfs: mounted SweetRoot on device b(1, 0)` (HFS works on hardware), init printed its first line, then `pid 1 exited -- exit reason namespace 2 subcode 0xa` = SIGNAL/SIGBUS -> `initproc failed to start` panic. Diagnostic boot 18:08:13 UTC (`research/boot0027d.log`, image `shim/out/shim-boot-0027d.img`, diag init `research/diag-init` from scratch diag-init.S with [a][b][c] markers, `cs_debug=1`; photo `IMG_20261015_201547.jpg`): output `PID [a][b]` then SIGBUS -> fault at first `strb w21,[sp]`; no code-signing messages. Cause: kernel enters a static binary with sp at argc, not necessarily 16-aligned (depends on arg/apple string lengths, differs mockfs vs HFS); EL0 SP alignment check -> EXC_ARM_SP_ALIGN -> SIGBUS (sleh handle_sp_align). QEMU does not enforce SP alignment. NOT a kernel bug: real binaries start in dyld which aligns. Fix `1a8fc15`: sweet-init aligns sp at entry. Rebuilt `research/root-hfs.img`, QEMU `research/q0027-hfs2` OK. Phone image `shim/out/shim-boot-0027b.img` SHA256 `098ba46c...c5c` (payload-0027b, ramdisk match check-0027b) ready, awaiting FASTBOOT. Lesson: Assembly `;` is a comment in Apple arm64 asm (use .macro, not ;-joined #define).
- **HFS ROOT WORKS (QEMU).** 0027 CI `38779441895` PASSED, `xnu/out-0027` SHA256 `a8643886...5f6a`. QEMU `research/q0027-hfs` (RAM disk = `research/root-hfs.img`, rd=md0): `BSD root: md0` -> `hfs: mounted SweetRoot on device b(1, 0)` -> `load_init_program: attempting to load /sbin/launchd` -> `*** SWEET userspace: init running as PID 1 ***` + heartbeat, no panic. Phone image `shim/out/shim-boot-0027.img` (payload-0027 = 0027 kernel + sweet-0021.adt + root-hfs.img + rd=md0, ramdisk byte-match check-0027) ready; awaiting FASTBOOT for phone test.
- **HFS ROOT WORK (Claude), patches 0026-0027.**
  - 0026 (`f0e990c` + link fix `64c96f4`): Apple OSS **hfs-627.100.6** (commit `31d5ec238dfab485e78a9a30b8b92d13e8914f03`, paired with xnu-8796.141.3 in macos-135 release.json) staged by `xnu/patches/0026-stage-hfs.sh` into `bsd/sweet_hfs` (core + hfs_encodings; AppleKeyStore include/key prototypes guarded by CONFIG_PROTECT; SDK TargetConditionals copied). New config option `sweet_hfs` (MASTER + MASTER.arm64.sweet); 40 `optional sweet_hfs` files; Makefile.template foreach adds `_CFLAGS_ADD = -include sweet_hfs_compat.h -I...` (MUST come after kernel -D flags; compat undefs BSD/XNU_KERNEL_PRIVATE and the CONFIG_* HFS tests so kext-config.h decides: macOS profile, no content protection). `sweet_hfs_iokit.c` replaces hfs_iokit.cpp/hfs_encodings_kext.cpp: `sweet_hfs_register()` called in bsd_init after vfsinit (encodings init, vfs_fsadd VFS_TBLCANMOUNTROOT, zones, sysctls); is_ejectable 0, iterate_media none, serial KERN_NOT_SUPPORTED, OSKextGetCurrentLoadTag -> kOSKextInvalidLoadTag (renamed via compat macro). hfs_encodings' own `hfs_allocated` renamed per object (separate kexts on Apple; first CI `38777325964` failed on that duplicate at link). mockfs now validates Mach-O magic (its TODO) so non-Mach-O roots fall through to HFS (new fs entries come AFTER mockfs in vfsconf). CI `38778133720` PASSED, `xnu/out-0026` SHA256 `0b49170c...701a`, prints `SWEET HFS: hfs-627.100.6 registered`.
  - HFS+ image: `research/root-hfs.img` (8 MB, mkfs.hfsplus from AUR hfsprogs installed with user approval; loop-mounted with sudo; /sbin/launchd = research/sweet-init, /dev; fsck.hfsplus OK). QEMU `research/q0026-hfs`: `BSD root: md0` then data abort in MD5Init from hfs_getvoluuid (mount computes volume UUID).
  - 0027 (`14bf2b7`): 0020 stager also copies BearSSL hash/md5.c + codec/dec32le.c/enc32le.c; `corecrypto_md5.c` SWEET branch converts MD5_CTX <-> br_md5_context around br_md5_* calls; wrappers sweet_md5.c/sweet_dec32le.c/sweet_enc32le.c. Host test 40/40 match md5sum. CI **`38779441895`** running.
  - Local tooling: `tools/xnu-cc.py` has `XNU_CC_POST` (flags after logged ones). Sandbox `research/bt28/xnu` = 0025 CI tree + 0026/0027 edits; originals `research/pre0026`, `research/pre0027`. HFS local objects `research/hfs-objs`. Checker entries updated to bt28.
  - SHA-1 / SHA-384/512 still have no provider.
- **MILESTONE ON HARDWARE: USERSPACE PID 1 RUNS ON THE PHONE.** Boot 2026-10-15 17:16:00 UTC (`research/boot0025.log`: send OKAY0.410s, boot OKAY0.135s), image `shim/out/shim-boot-0025.img` SHA256 `9dbfa0b1...89db0`. Photo `IMG_20261015_191733.jpg`: `BSD root: md0` -> `load_init_program: attempting to load /sbin/launchd` -> `*** SWEET userspace: init running as PID 1 ***` -> repeated `SWEET init: still alive` (5 s heartbeat), no panic. Kernel 0025 + mockfs RAM disk + built-in no-entitlements AMFI. No flashing performed.
- **NEXT (toward real iOS userland):** real root filesystem with real binaries. Options: (a) build Apple OSS `hfs` (macOS 13.5 tag `hfs-627.100.6`) into SWEET like libpthread, then an HFS RAM disk image; (b) iOS 16 dyld + libSystem/dyld shared cache from the IPSW (needs APFS or repacking onto HFS). Expected hurdles: entitlements (sweet_amfi grants none), SHA-1/MD5/SHA-384/512 providers (BearSSL), missing kexts/daemons. Current init is a static test program, not launchd.
- **MILESTONE: USERSPACE RUNS (QEMU).** 0025 CI `38774788048` PASSED, `xnu/out-0025` SHA256 `5496069b...4877`. QEMU `research/q0025-rd` (150 s, no panic): `BSD root: md0` -> `load_init_program: attempting to load /sbin/launchd` -> `*** SWEET userspace: init running as PID 1 ***` -> `SWEET init: still alive` every 5 s. Exec, ad-hoc SHA-256 code signature, syscalls, devfs /dev/console, select timeouts all work. Phone image prepared: `shim/out/shim-boot-0025.img` 16,515,072 bytes SHA256 `9dbfa0b15140c0bd733a16c4f727f6a7df44a8741f98d8e266d5f2fa4f689db0` (payload-0025 = 0025 kernel + sweet-0021.adt + research/sweet-init + rd=md0; ramdisk byte-match check-0025). Waiting for user to put phone in FASTBOOT.
- **0024 CI `38773277811` PASSED**, `xnu/out-0024` SHA256 `a0ba964b...4348`. QEMU `research/q0024-rd` and **PHONE (boot 2026-10-15 17:05:55 UTC, `research/boot0024.log`, image `shim/out/shim-boot-0024.img` SHA256 `cf3dac86...6964`, 16,510,976 bytes, payload `shim/out/payload-0024.bin` = 0024 kernel + `shim/out/sweet-0021.adt` + RAM disk `research/sweet-init` + rd=md0; ramdisk byte-match `check-0024`)** agree: `Added memory device md0`, `BSD root: md0`, `load_init_program: attempting to load /sbin/launchd`, then data abort in accelerate_entitlement_queries (PC 0x...77d2458, FAR 0x1a0) = NULL AMFI interface. Photo `IMG_20261015_190715.jpg`. RAM disk root is physically verified.
- **0025 (`2518c79`)**: new `bsd/kern/sweet_amfi.c` registers a built-in AMFI interface at EARLY_BOOT/MIDDLE: no entitlements (adjustContextWithoutMonitor succeeds without creating a context, queries KERN_DENIED, copies NULL/KERN_NOT_FOUND, get_xml/transmuted false); WithMonitor KERN_NOT_SUPPORTED; OSEntitlements_query and query_context_to_object panic explicitly (CoreEntitlements closed; no kernel caller); TrustCache version 0 (0015 keys on trust_cache_rt==NULL, img4 absent -> still unavailable); CoreEntitlements table zero (PMAP_CS only). Compiles locally; checker updated (bt27 entries). CI **`38774788048`** running. Next artifacts `xnu/out-0025`, `research/bt29`, `research/run29.log`. Real iOS binaries will need real entitlements later (no OSS CoreEntitlements exists).
- **0021-0024 RAM-disk-root iteration (Claude), QEMU only so far, no new phone boot since 0020.** Each kernel tested with `tools/mkpayload.py KERNEL research/q0021.adt OUT --ramdisk research/sweet-init --cmdline "debug=0xc serial=3 cpus=1 keepsyms=1 -enable_kprintf_spam -noprogress rd=md0"` then `tools/qemu-sweet.py OUT DIR --secs 150 --kernel KERNEL --fail-on-panic` (PATH needs ~/swift/usr/bin for llvm-nm). Fresh ADTs: `research/q0021.adt` (QEMU), `shim/out/sweet-0021.adt` (phone).
  - 0021 CI `38769532000` PASSED, `xnu/out-0021` SHA256 `2b7500a1...962e`, `research/bt25`/`run25.log`. QEMU `research/q0021-rd`: md0 root, then assert `iomediaClass` in IOService::publishHiddenMedia.
  - 0022 (`20ece9c`, publishHiddenMedia without IOMedia class) CI `38770666158` PASSED, `xnu/out-0022` SHA256 `a4d0e787...30c5`, `research/bt26`/`run26.log`. QEMU `research/q0022-rd`: data abort in SHA256_Init (NULL g_crypto_funcs) from vm_kernel_addrhash_internal.
  - 0023 (`c8089d1`, libkern SHA256_Init/Update/Final use built-in ccsha256_ltc_di + ccdigest_init/update on SWEET; also serves code-signing SHA-256; SHA-1/MD5/SHA-384/512 still have NO provider - BearSSL from 0020 could supply them later) CI `38771876423` PASSED, `xnu/out-0023` SHA256 `d763fed7...1003`, `research/bt27`/`run27.log`. QEMU `research/q0023-rd`: **mockfs mounted md0, `load_init_program: attempting to load /sbin/launchd`**, then panic `mockfs_fsnode_vnode failed to create fictitious pages ... rvalue = 5` (mockfs.c:351).
  - 0024 (`3293c80`): mockfs used memdev mi_base (4K page number of a VIRTUAL kernel address for IOKit RAMDisk, truncated to 32 bits) << PAGE_SHIFT as a physical address. Now zero-copy pager mapping only when mi_phys (with 4K units); virtual md uses pagein/blockmap/strategy -> memdev bcopy. memdev's own mdPhys path assumes 4K ppnums (unsafe on 16K arm64), so do NOT switch the RAMDisk to physical. CI **`38773277811`** running. Next artifacts `xnu/out-0024`, `research/bt28`, `research/run28.log`.
  - Sandboxes: bt25/bt26/bt27 contain the next patch's edited files; pristine copies in `research/pre0022`..`pre0024`.
- **PATCH 0021 (Claude): RAM disk root via mockfs -> first userspace program.** Commits `9c37771` (initial; CI `38768500280` FAILED: mockfs_fsnode.c kfree_type(mockfs_fsnode_t) typed-alloc static assert; local xnu-cc stubs `__builtin_xnu_types_compatible` so it can't catch this) and `193772f` (fix), CI **`38769532000`** running: https://github.com/dipa-studio/ios-sweet/actions/runs/38769532000. Next artifacts: `xnu/out-0021`, `research/bt25`, `research/run25.log`.
  - Kernel: `config/MASTER.arm64.sweet` FILESYS_BASE += `mockfs` (XNU's built-in FS: root device is itself a Mach-O, served as /sbin/launchd, plus /dev for devfs). Upstream mockfs bit-rot fixed: kalloc_type/kfree_type used the POINTER typedef mockfs_fsnode_t (nodes were 8 bytes) -> `struct mockfs_fsnode`. `IOService::setRootMedia` asserted IOBlockStorageDriver class exists (IOStorageFamily absent): SWEET-only, a missing class means root=NULL (same as IOSetImageBoot); Apple path keeps assert. All 21 patches apply (`research/check-patch-order.py`); 5 TUs compile locally with -DMOCKFS (`research/mockfs-objs`), imports resolve vs 0020 kernel. Sandbox `research/bt24/xnu` now holds 0021 versions of those 3 files; pristine 0020 copies in `research/pre0021`.
  - Tools: `tools/mkpayload.py --ramdisk IMAGE` appends IMAGE as an extra payload segment right after the kernel, moves kernel_end past it (shim unchanged: ADT+boot_args follow it, image stays below topOfKernelData), and adds ADT `/chosen/memory-map` `RAMDisk`=<phys,size>. Boot with `rd=md0`. Without --ramdisk output is byte-identical to existing 0020 QEMU and phone payloads (verified). `tools/sweet-init.S` + `tools/mkinit.py`: PIC static init (open /dev/console, print PID, heartbeat every 5 s via select, never exits) wrapped into a static arm64 Mach-O (__PAGEZERO, __TEXT@0x100000000, LC_UNIXTHREAD, ad-hoc SHA-256 CodeDirectory v0x20400, 4K pages). Build: `~/swift/usr/bin/clang -target arm64-apple-ios16.0 -c tools/sweet-init.S -o X.o && tools/mkinit.py X.o research/sweet-init` (ld64.lld cannot link static iOS). Signature not verified by a real codesign; the kernel will tell.
  - QEMU with 0020 kernel + RAM disk (`research/q0020-rd.bin`, rd=md0, 150 s `research/q0020-rd150`): `Added memory device md0`, **`BSD root: md0, major 1, minor 0`** (plumbing works), then the setRootMedia assert (now fixed in 0021). NOTE: QEMU needs >60 s to reach IOFindBSDRoot (60 s run showed nothing after stf0; likely RTC/inittodr wait), so use --secs 150.
  - NEXT: download 0021, QEMU 150 s with ramdisk; expect mockfs mount then init exec -> `*** SWEET userspace: init running as PID 1 ***`. Then phone boot with same payload (phone ADT shim/out/sweet-0020.adt pattern + --ramdisk + rd=md0).
- **0020 PHONE RESULT (user transcription of screen, 2026-10-15): KERNEL INIT COMPLETE, WAITING FOR ROOT.** After Skywalk self-tests PASSED, kminit, ifnet_attach lo0/gif0/stf0, screen prints `BSD`, then `Waiting on <dict><key>IOProviderClass</key><string>IOMedia</string><key>Content</key><string>Apple_HFS</string></dict>` and `Failed to write boot-picker-bringup-reason to NVRAM.` No panic. This is IOFindBSDRoot waiting for a root device (none exists); NVRAM warning is expected (no NVRAM driver). QEMU `cpu_idle` snapshot is presumably the same wait (not GDB-confirmed; milestone GDB run was cancelled by user since phone answered it). Draft `research/check-milestones20.gdb` (hbreaks inittodr/vfs_mountroot/IOFindBSDRoot/bsd_utaskbootstrap) left uncommitted/ignored.
- **NEXT MILESTONE: root filesystem -> launchd.** Plan: (1) RAM disk: shim places an image in RAM, ADT /chosen/memory-map `RAMDisk` entry, boot-arg `rd=md0` (XNU md driver). (2) HFS is a separate kext on Apple; build Apple OSS `hfs` (tag paired with macOS 13.5 in distribution-macOS macos-135 release.json) into SWEET like libpthread 0019. APFS is closed. (3) Minimal HFS image with iOS 16 launchd (later: dyld/shared cache; AMFI/code-signing absent will be a later hurdle). User's end goal is full iOS GUI.
- **0020 (AES) VERIFIED + PHONE BOOTED (Claude took over after Codex usage limit).** Actions `38765422261` (`ab9e23f`) PASSED; kernel `xnu/out-0020/kernel.development.sweet` checksum OK; buildtree `research/bt24`, log `research/run24.log`. Actual-kernel AES checks PASS (`research/check-aes20.gdb` / `.log`, 12 extra CBC cases match OpenSSL). 45s QEMU `research/q0020`: no panic, zero unknown glyphs, past old TCP/AES panic -> Skywalk self-tests PASSED -> bsd_autoconf kminit -> ifnet_attach lo0/gif0/stf0; final snapshot PC in `cpu_idle` (idle or waiting; NOT yet diagnosed, could be root-device wait). Image `shim/out/shim-boot-0020.img` 16,461,824 bytes SHA256 `775200cb02d95fc750981516b79d91dcdc96184bbe67a38f9d57c59b4a391828`, ramdisk byte-matches `payload-0020.bin` (`check-0020`). **Phone temporarily booted 2026-10-15 16:10:00 UTC**: one FASTBOOT product sweet, send OKAY0.407s, boot OKAY0.134s, total0.549s, exit0 (`research/boot0020.log`). Awaiting user photo; do not reboot the phone before it. NEXT: read photo; diagnose what QEMU waits on after stf0 (GDB backtrace of threads / longer run). Codex's STOP request below is complete.
- User requests STOP after completing the current0020 AES iteration (Actions/QEMU/phone), then leave a precise committed handoff for another AI. User says FASTBOOT ready again after0019 photo. Do not start a new blocker fix after this iteration.
- Goal: iOS16-generation XNU on Redmi Note10Pro sweet/SM7150. Always commit, use gh/Actions for kernel builds, keep this handoff current. Temporary fastboot boot only; preserve Android/backups. No userland/root filesystem boot yet.
- **Patch0020 update:** initial `e71098d` / Actions `38765012466` superseded by scalar-only compile flags. Added -mgeneral-regs-only to all six provider/BearSSL TUs and corecrypto_aes.c; object disassembly now confirms no SIMD. Updated implementation `ab9e23f`, Actions `38765422261` queued/running: https://github.com/dipa-studio/ios-sweet/actions/runs/38765422261. Do not launch another run. portable BearSSL AES CBC and legacy one-block ECB wired directly into SWEET corecrypto_aes.c. Genuine bitslice implementation, no CPU AES/SIMD requirement, heap or fake global crypto table. Source fetched by `0020-stage-bearssl.sh` from official BearSSL git at immutable `7bea48e5e850ab4cafbe68d3765cdaba13a86d6f`; MIT license retained, downloaded source stays out of git. Kernel limits include adapter only. All128/192/256-bit keys, CBC encrypt/decrypt, copied contexts, in-place/out-of-place; zero block count and size overflow handled, invalid keys clear context. Seven TUs compile to arm64 objects (`research/aes-objs`), imports resolve, all20 patches apply and sources match (`research/patch0020-check.log`). Sandbox `research/bt23/xnu`, originals `research/pre0020`. NEXT: Actions then actual-kernel NIST/random CBC/ECB checks and >=45s QEMU before another phone boot. Next artifacts out-0020 / bt24 / run24.log. 0020 updated CI pending. Local sources/checks match the scalar-only patch.
- **Latest built kernel0019**, implementation `256d3f0`, patches0001-0019. Actions `38763072907` PASSED (4m5s): https://github.com/dipa-studio/ios-sweet/actions/runs/38763072907. Kernel `xnu/out-0019/kernel.development.sweet`, SHA256 `a27df7568f03fb541cf0e8024c0a594fa178a85054fcf9eba29158cbd4c5ecc0`; checksum verified. Log/source `research/run23.log` / `research/bt23` (no nested .git). Seven pthread source/build/header files and staged adaptations byte-match local compile inputs.
- **0019 hardware photo received** `IMG_20261015_175306.jpg`: pthread registration visible, passes mbinit and DLIL checksum/scheduling, same AES fault as QEMU: PC`0xfffffe00079174e0` (`aes_encrypt_key128`), LR`0xfffffe000767c3a4` (`tcp_init`), FAR0x78, x8=0. Disassembly proves NULL g_crypto_funcs->ccaes_cbc_encrypt. Photo processed; no more0019 observation pending. General crypto table remains absent, other hash/mode operations may still fault after0020. DO NOT bypass TCP or install fake crypto. XNU already contains SHA256/HMAC implementations; AES source there is a dispatch wrapper. Full future provider interface libkern/libkern/crypto/register_crypto.h. Apple/corecrypto default README describes evaluation-only licensing, so no external corecrypto was fetched or staged; BearSSL selected for this portable AES integration.
- **0019 pthread FIXED in QEMU and observed beyond its init on phone**: 45s QEMU `research/q0019`, zero unknown glyphs, then AES panic. Actual-kernel API checks PASS `research/check-pthread19.gdb` / `.log`, guest `research/q0019-api`: function/callback table identity, actual provider pthread_init returns, locks/global hash/threadcall/typed zones initialized, thread_selfid via syscall shim + buffer bounds, process hash init/delete via shims restores NULL. Monitor quit prints expected remote-disconnect after PASS. All fixture guests stopped.
- **0019 provider**: genuine Apple libpthread-514.100.2 commit `a6c70ca0e544347a0377babf748f831577ec24f9`, exact paired release with xnu8796.141.3 in distribution-macOS/macos-135/release.json (`research/macos-135-release.json`). 0019 shell stage runs before patches (workflow copies *.sh); three SWEET wrapper TUs use kext BSD header view, vm_fault_external, renamed provider-side pthread_kern/current_uthread; register real function table at EARLY_BOOT SECOND, real pthread_init later. Stager applies bounded address casts, zero user addresses, proper panic format. SWEET opaque ksyn storage enlarged48->56 for trailing kwe_uth, checked with provider static assertion. Local pre-CI TargetConditionals fixture was syntax-only; artifact bt23 carries actual SDK header and CI is authoritative.
- **Phone0019 temporarily booted** 2026-10-15 15:51:36 UTC: exactly one FASTBOOT/product sweet verified; send OKAY0.406s, boot OKAY0.134s, total0.546s, exit0 (`research/boot0019.log`). Image `shim/out/shim-boot-0019.img`, 16,457,728 bytes, SHA256 `19429a57e486b856880df9e27327ed488e0139345311fdb0350974e72103a9a1`. Phone ADT/payload `shim/out/sweet-0019.adt` / `payload-0019.bin` timer19, unpacked ramdisk byte-match (`check-0019`). EntryPA0xb146b488, kernelendPA0xb2000000, boot_argsPA0xb2004000/top0xb2008000. Last user FASTBOOT+USB reply preceded this boot; do not assume phone is still in FASTBOOT.
- **CPU0018 physically verified** by `IMG_20261015_173951 (2).jpg`: boot CPU0 registered, real SGI1 verified, initialization complete -> BSD/MAC/mbinit -> old pthread-table panic. SweetCPU uses legacy IOCPU, ml_processor_register/processor_start/initCPU, real SGI1 clears SIGPdisabled before max CPUs completion; no forced flags/skipped waits. CPU APIs and two-CPU rejection passed (`research/check-cpu18.gdb`, `q0018-api`, `q0018-smp`). Single core; SMP/suspend unsupported. CURRENT SWEET has NO USE_APPLEARMSMP.
- QEMU next run: generate fresh `tools/mkadt.py research/q0020.adt --qemu` (timer27), mkpayload with `debug=0xc serial=3 cpus=1 keepsyms=1 -enable_kprintf_spam -noprogress`, then `tools/qemu-sweet.py PAYLOAD OUT --secs 45 --kernel KERNEL --fail-on-panic`. 12s can miss later panics because IORTC waits30s. Runner snapshot only: panic exit2, blank/incomplete exit3; absence of panic does not mean complete boot. Qualcomm XPU/ABL/panel and phone SMC PSCI require hardware checks.
- Local checker `tools/xnu-cc.py research/run23.log research/bt23 FILTER --per-file`, XNU_CC_OBJDIR for objects. For new BearSSL TUs add XNU_CC_EXTRA with -I bt23/xnu/libkern/crypto/sweet_bearssl/{inc,src}. Patch checker `research/check-patch-order.py` uses temporary upstream index; source fixtures/artifacts ignored under research. GDB mask registers to unsigned64, use function-entry manual-call return traps, discard manipulated guests. No QEMU guest intentionally left running.

## Session log and earlier handoffs (superseded by the active summary above)

### Prior 0019 transition notes (superseded)

- Goal: iOS 16 generation XNU on sweet. Always commit completed work, use gh/Actions for kernel builds, keep this handoff current. Temporary fastboot boot only; preserve Android/backups.
- **0019 build PASSED** Actions `38763072907` (4m5s), implementation `256d3f0`. Kernel `xnu/out-0019/kernel.development.sweet`, SHA256 `a27df7568f03fb541cf0e8024c0a594fa178a85054fcf9eba29158cbd4c5ecc0`; checksum verified. Log/source `research/run23.log` / `research/bt23`; all seven patched files and staged provider adaptations match local compile inputs. Prefer bt23 as the next baseline.
- **0019 pthread FIXED in QEMU**: 45s run `research/q0019` registers provider, passes mbinit, DLIL SUM16 checks and DLIL thread scheduling. Actual-kernel GDB checks `research/check-pthread19.gdb` / `.log` PASS: function/callback table identity, real _pthread_init returns, locks/global hash/cleanup threadcall/typed zones non-NULL, thread_selfid via actual syscall shim with output bounds, process hash init/delete through actual shims restores NULL. Guest stopped after tests; no fixture left running. GDB monitor quit prints expected remote disconnect after PASS.
- **Current next blocker:** QEMU0019 panic data abort FAR0x78 at `aes_encrypt_key128` PC`0xfffffe00079174e0`, called by `tcp_init` LR`0xfffffe000767c3a4`. Disassembly confirms `g_crypto_funcs == NULL`, loading ccaes_cbc_encrypt at+0x78. General crypto registration is still absent; DO NOT bypass TCP or supply fake crypto. Next integrate a genuine compatible crypto implementation/provider (AES first needed here, other digest/mode APIs also used). XNU contains SHA256/HMAC but no AES implementation; its corecrypto_aes.c is a dispatch wrapper. Full crypto table is in libkern/libkern/crypto/register_crypto.h.
- **0019 phone image prepared and verified**, user reports FASTBOOT+USB again; exactly one device/product sweet verified. `shim/out/shim-boot-0019.img`, 16,457,728 bytes, SHA256 `19429a57e486b856880df9e27327ed488e0139345311fdb0350974e72103a9a1`; unpacked ramdisk matches phone payload (`shim/out/check-0019`, `payload-0019.bin`, `sweet-0019.adt`, timer19). EntryPA0xb146b488; kernelendPA0xb2000000; boot_argsPA0xb2004000/top0xb2008000. Usual debug cmdline cpus=1/-noprogress. **Temporarily booted 2026-10-15 15:51:36 UTC**: send OKAY0.406s, boot OKAY0.134s, total0.546s, exit0 (`research/boot0019.log`). User asked for photo after45s. Await the photo; DO NOT reboot again before observation. Bootloader acceptance only; no0019 physical progress observed yet.
- **Hardware photo confirms 0018 progress** (`IMG_20261015_173951 (2).jpg`): real phone prints `SWEET CPU: boot CPU 0 registered, SGI1 verified, initialization complete`, enters BSD/MAC, reaches `mbinit: done`, then the same missing-pthread-function-table panic as QEMU at pthread_shims.c:318. CPU completion/interrupt delivery is now physically observed. The photo was received; no further phone boot performed yet.
- **Patch0019 committed/pushed `256d3f0`; Actions `38763072907` queued/running:** https://github.com/dipa-studio/ios-sweet/actions/runs/38763072907. Do not launch a duplicate. genuine Apple OSS libpthread-514.100.2 provider (immutable commit `a6c70ca0e544347a0377babf748f831577ec24f9`), paired with xnu-8796.141.3 by Apple's `distribution-macOS/macos-135/release.json` (`research/macos-135-release.json`). `0019-stage-libpthread.sh` fetches/stages it before patches; workflow now copies shell scripts too. SWEET-only wrappers compile all three real kernel sources, rename provider-side symbols, use kext header view and vm_fault_external, register the real function table at EARLY_BOOT SECOND. Existing pthread_init then runs the actual provider initialization. No pthread wait/syscall is bypassed. Source staging includes bounded explicit address casts/zero user addresses and panic-format fixes. SWEET kernel opaque ksyn storage enlarged from48 to56 bytes to contain this provider's trailing kwe_uth, with a provider size assertion. Local compile of three provider TUs plus pthread_shims/kern_fork passed; imports resolve and provider exports do not collide with existing kernel symbols. All19 patches apply and changed sources match (`research/patch0019-check.log`). Source sandbox `research/bt22/xnu`, originals `research/pre0019`, objects `research/pthread-objs`. Local TargetConditionals fixture only has target macros for syntax; CI stages the real macOS SDK header and is authoritative. Next Actions artifacts: out-0019 / bt23 / run23.log; run QEMU >=45 seconds. 0019 CI is pending; no 0019 QEMU run yet.
- **Latest kernel implementation `e7d9550`, patches0001-0018; CI `38760004398` PASSED (3m56s)**: https://github.com/dipa-studio/ios-sweet/actions/runs/38760004398. No build is pending. Kernel `xnu/out-0018/kernel.development.sweet`, SHA256 `b3c8d59acc88f93a2c836eb2527a05ed4fbaac7c580a2ea8c3b795137f4aadf1`; checksum verified. Source/log `research/bt22` / `research/run22.log` (baseline for patch0019; no nested .git). New driver/config sources match CI exactly.
- **CPU wait FIXED in QEMU**: SweetCPU uses legacy IOCPU, validates single boot CPU, ml_processor_register -> processor_start -> initCPU real SGI1 -> scheduler/IOKit completion -> ml_set_max_cpus. It does NOT force a flag or skip a wait. CPU APIs passed: Running CPU0, processor_array[0] association, SGI signalling enabled, name, unsupported secondary-start error (`research/check-cpu18.gdb` / `.log`, `research/q0018-api`). Single-core only; SMP and suspend unsupported. Two-CPU topology fails explicitly (`research/q0018-smp`).
- **Next blocker reproduced in 45s QEMU** (`research/q0018-long`, zero unknown glyphs): BSD initialization reaches MAC framework, network mcache and `mbinit: done`, then **`pthread kernel extension not loaded (function table is NULL). @pthread_shims.c:318`**. Do not bypass pthread_init: find/integrate the matching open-source libpthread kernel implementation and register its real function table. A 12s run `research/q0018` looked panic-free before the 30s IORTC wait elapsed; use >=45s or GDB checkpoints for the next iteration. No userland/root filesystem boot yet.
- **Phone 0018 TEMPORARILY BOOTED** 2026-10-15 **15:31:15 UTC**: exactly one FASTBOOT device verified product sweet; send OKAY0.400s, boot OKAY0.134s, total0.539s, exit0. Local log `research/boot0018.log`. This confirms bootloader acceptance only. User was asked for a photo; await it, DO NOT reboot the phone again before their observation. No flashing performed.
- Current hardware image `shim/out/shim-boot-0018.img`, **16,437,248 bytes**, SHA256 **`b7a23595d143a76c72c9fe2cfcc5d77a8f16987b5af1a2703bbffdfa6922908c`**. Phone ADT/payload `shim/out/sweet-0018.adt` / `shim/out/payload-0018.bin` (timer19), unpacked ramdisk exactly matches payload (`shim/out/check-0018`). EntryPA0xb146b488; kernelendPA0xb1ffc000; boot_argsPA0xb2000000/top0xb2004000. Command line `debug=0xc serial=3 cpus=1 keepsyms=1 -enable_kprintf_spam -noprogress`.
- QEMU payload/ADT `research/q0018.bin` / `research/q0018.adt` (timer27). Run `python3 tools/qemu-sweet.py research/q0018.bin research/NEW-OUT --secs 45 --kernel xnu/out-0018/kernel.development.sweet --fail-on-panic`; fresh ADT seed for a new payload. Output fb.png/fb.txt/regs.txt/qemu.log/result.json. Visible panic exit2; blank/incomplete decode exit3; no_panic_observed is snapshot-only, not successful boot. -noprogress prevents the graphical indicator corrupting console text. Qualcomm XPU/bootloader/panel and SMC PSCI still need physical validation.
- Patches0014-0017 fixed PRNG registration/direct SHA256, explicit unavailable trust-cache service with rejected loads/no matches, built-in SweetPlatformExpert, and timer PPI from ADT (phone19/default19, QEMU27). All their checks/artifacts are preserved in the history below. CURRENT SWEET has NO USE_APPLEARMSMP; do not assume gCPUIC/gAIC/gPMGR AppleARMSMP globals exist.
- Local single-file checker: tools/xnu-cc.py research/run22.log research/bt22 FILTER --per-file, output via XNU_CC_OBJDIR. Patch checker `research/check-patch-order.py` applies all18 via temporary index, matches sandbox sources. Sandbox for0018 `research/bt21/xnu`, originals `research/pre0018`, objects `research/cpu-objs`. First compiler issues were missing machine/atomic.h and nonexistent getNameSymbol; fixed and both TUs compiled successfully before CI. Fixtures/artifacts under research are local-only/ignored.
- GDB: mask int(register)&((1<<64)-1) for unsigned kernel pointers; use function-entry manual-call return traps, discard manipulated guests. No QEMU fixture is intentionally left running.

### Earlier active handoff snapshot (superseded)


- **0018 milestone:** Actions `38760004398` PASSED (3m56s), checksums passed, new CPU/build files byte-match CI tree. Kernel `xnu/out-0018/kernel.development.sweet`, SHA256 `b3c8d59acc88f93a2c836eb2527a05ed4fbaac7c580a2ea8c3b795137f4aadf1`; log/tree `research/run22.log` / `research/bt22`. QEMU `research/q0018` 12s: boot CPU registered, SGI1 verified, CPU initialization complete, **BSD initialization entered** (copyright, MAC framework, buffer headers), no panic/zero unknown glyphs. Direct CPU API checks PASS (`research/check-cpu18.gdb`, `.log`, `research/q0018-api`): CPU0 Running, processor matches processor_array[0], real SGI enabled, CPU name correct, secondary-start returns KERN_NOT_SUPPORTED. Two-CPU ADT correctly panics before registration (`research/q0018-smp`). Longer 45s run `research/q0018-long` still running; next BSD wait/fault not yet identified.
- **Prepared 0018 phone image:** `shim/out/shim-boot-0018.img`, 16,437,248 bytes, SHA256 `b7a23595d143a76c72c9fe2cfcc5d77a8f16987b5af1a2703bbffdfa6922908c`. Phone ADT/payload `shim/out/sweet-0018.adt` / `shim/out/payload-0018.bin`, usual debug args with cpus=1 and -noprogress. Unpacked ramdisk byte-compared (`shim/out/check-0018`). Entry PA remains 0xb146b488; kernel end PA 0xb1ffc000, boot_args 0xb2000000/top0xb2004000. User reports FASTBOOT+USB ready; read-only check found exactly one product sweet. NEXT: temporary fastboot boot of this verified image, record send/boot results, then await hardware photo without rebooting again.
- Patch 0018 committed/pushed **`e7d9550`**; Actions **`38760004398`** queued/running: https://github.com/dipa-studio/ios-sweet/actions/runs/38760004398. Do not launch a duplicate run.
- Active continuation: patch **0018** implemented in `iokit/Kernel/arm/SweetCPU.cpp` + arm64 source list + exact qcom,kryo470 personality. Keeps legacy IOCPU, accepts ONLY the single boot CPU, fills ml_processor_info from parsed topology with CPU object as cpu_id, calls ml_processor_register and processor_start. initCPU sends SGI1 via ICC_SGI1R_EL1 and waits (1-second deadline) for real cpu_signal_handler to clear SIGPdisabled. Only after successful startup calls ml_cpu_init_completed/cpusRunning and publishes completion/max CPUs. Secondary startup/suspend are explicitly unsupported. Local C++ compile passed for both TUs (`research/cpu-objs`), all imports resolve, object contains dsb ishst / ICC_SGI1R / isb; all18 patches apply in order and match sources. Sandbox `research/bt21/xnu`, originals `research/pre0018`; next CI artifacts should use `xnu/out-0018`, `research/bt22`, `research/run22.log`. User has the phone available; first run QEMU, then prepare/temporarily boot useful hardware progress.
- Goal: iOS 16 generation XNU on Redmi Note 10 Pro / sweet. User wants persistent progress, commits, kernel builds via `gh` Actions, and this handoff kept current across agent switches. Temporary `fastboot boot` only; preserve Android and backups.
- Latest kernel implementation: **`aa3f991`**, patches **0001-0017**. All four new Actions builds PASSED: 0014 `38748543058` (4m0s), 0015 `38749549779` (4m3s), 0016 `38750733996` (4m3s), 0017 **`38751507437` (4m7s)**. Latest: https://github.com/dipa-studio/ios-sweet/actions/runs/38751507437. No build is pending.
- **Current blocker: CPU initialization has no SWEET CPU driver.** QEMU registers SweetPlatformExpert, then kernel_bootstrap_thread waits in **kperf_init_early -> ml_wait_max_cpus**. Confirmed via actual-kernel GDB call stack (`research/locate-cpu-wait2.log` / `.symbols`) and normal-run `max_cpus_initialized == 2` (MAX_CPUS_WAIT). Do not force the flag or remove the wait. Next implement real CPU registration and completion using XNU's CPU/processor interfaces. CURRENT SWEET uses legacy IOCPU (`USE_APPLEARMSMP` is absent); enabling AppleARMSMP is a separate architectural change requiring GIC/PMGR services. No userland/root filesystem boot yet.
- Fixed this session: PC=0 unregistered PRNG callback (0014, built-in HMAC-SHA256 provider + direct entropy/write_random hashing); absent Image4/AMFI trust-cache service (0015, unavailable runtime, loads rejected and queries no-match); missing platform driver (0016, SweetPlatformExpert exact personality); incorrect QEMU timer IRQ (0017, validated ADT PPI property, phone default19/QEMU27).
- **Latest kernel** `xnu/out-0017/kernel.development.sweet`, SHA256 `055a80190ab998b4df9203f1102072dcc78faad1779a537a514e522b682b582f`. Buildtree/log **`research/bt21` / `research/run21.log`**; all nine changed C/C++/header/config files byte-match local checked sources. Checksums passed. Entry PA `0xb146b488`, kernel end PA `0xb1ff4000`. Preferred baseline for patch 0018: `research/bt21/xnu` (no nested .git).
- **QEMU verified**: `research/q0017-noprogress` ran **30 seconds**, no visible panic, **zero unknown glyphs**, IRQ exceptions returned normally (4 IRQs, tickless idle). It still waits for CPU completion, so this is NOT a completed boot. Earlier 15s run `research/q0017` captured 122 IRQs, timer value27, GICR_ISENABLER0 `0x08000002`, and CPU WAIT; graphical progress overlay corrupted 13 glyphs. Add **`-noprogress`** to keep the console readable. New runner classifies incomplete/blank decoding explicitly (exit3 with --fail-on-panic), visible panic exits2. Snapshot-only; use regs/GDB to diagnose stalls.
- Current QEMU payload/ADT: **`research/q0017-noprogress.bin` / `research/q0017.adt`**. Run: `python3 tools/qemu-sweet.py research/q0017-noprogress.bin research/NEW-OUT --secs 30 --kernel xnu/out-0017/kernel.development.sweet --fail-on-panic`. Generate fresh seed with mkadt for a new payload. QEMU virt models generic ARM execution, not Qualcomm XPU/bootloader/panel or the phone's SMC PSCI conduit.
- **Prepared phone image**: **`shim/out/shim-boot-0017.img`**, 16,416,768 bytes, SHA256 `51ff7fe30b4a6668c3452ffe1da922c5ac30cb8de60625c2a652587ecbd0ec92`. Phone ADT/payload `shim/out/sweet-0017.adt` / `shim/out/payload-0017.bin` (timer19). Unpacked ramdisk exactly matches payload (`shim/out/check-0017`). Command line **`debug=0xc serial=3 cpus=1 keepsyms=1 -enable_kprintf_spam -noprogress`**. NOT sent to phone this session: known CPU-driver wait should be addressed in QEMU first. Last actual phone boot remains 0013; user's latest photo `IMG_20261015_160033.jpg` confirmed the old PRNG PC=0 panic.
- Direct QEMU/GDB API checks: PRNG 600-byte chunking, buffer bounds, changing output, zero-length reads/writes, user reseed, contended refresh, generator1 init/output PASS again on latest0017 (`research/check-prng17.gdb` / `.log`, guest `research/q0017-api`). Trust-cache unavailable-service/argument/output cases PASS on0015 (`research/check-trustcache.gdb` / `.log`). Platform registration + target/product normal/truncated/zero/null/bounds PASS on0016 (`research/check-platform.gdb`, `research/check-platform3.log`). Different platform ID correctly retains IOPanicPlatform fallback (`research/q0016-negative`). Timer PPI32 and size2 correctly panic (`research/q0017-badppi`, `research/q0017-badsize`); omitted property selects19 (`research/q0017-default`). These are API/bring-up checks, not crypto certification or SMP scheduling validation.
- Local checker **`research/check-patch-order.py`** verifies all17 patches and changed source equality using a temporary upstream git index. Fixtures/logs/artifacts under research are local-only and ignored. For GDB unsigned kernel pointers, mask `int(register_value) & ((1<<64)-1)`; x30/x29 may be rendered signed. Stop at a function entry for manual-call return traps, and discard each manipulated guest after API tests. All fixture QEMU guests have been stopped.


- User wants persistent progress toward iOS 16, commits for completed changes, builds through `gh` / GitHub Actions.
- Keep this file current at every milestone so another agent can resume immediately, including when usage limits interrupt a session.
- Patch 0017 committed/pushed `aa3f991`, Actions `38751507437` running: https://github.com/dipa-studio/ios-sweet/actions/runs/38751507437. Next artifacts: xnu/out-0017, research/bt21, research/run21.log. Do not duplicate.
- Patch 0016 kernel downloaded/checksum verified: SHA256 `d06336c54baa06e0df6561a8bd7df98a9b9f7502c9381c62d1a44c045cd1ce46`, `xnu/out-0016/kernel.development.sweet`; buildtree/log `research/bt20` / `research/run20.log`. QEMU `research/q0016` (10s) prints platform expert registered, zero unknown glyphs, no panic observed BUT stalls (timer mapping still wrong until 0017). Direct actual-kernel GDB tests passed for registered instance and target/product names, including maxLength=1/0 and NULL, sentinels intact (`research/check-platform.gdb`, `research/check-platform3.log`, `research/q0016-api3`). First two fixture attempts used premature/wrong return breakpoints; discarded, corrected fixture uses start-return observation then a function-entry return trap. No phone boot yet.
- Patch 0016 CI `38750733996` PASSED (4m3s); artifacts not yet downloaded/booted. Patch 0017 prepared to fix QEMU timer fidelity BEFORE interpreting future no-panic/stall runs: actual `qemu-system-aarch64 -M virt,gic-version=3,dumpdtb=research/qemu-virt.dtb ...` timer property has virtual PPI 11 => INTID 27, while phone uses INTID 19. Kernel formerly hardcoded 19. New optional /arm-io/gic virtual-timer-intid property selects the PPI (validate exact u32 and 16..31); missing property retains phone default 19. One RO-late global drives GIC enable and sleh_irq dispatch. tools/mkadt.py emits phone19/QEMU27. Both C TUs compile (`research/timer-objs`), ADT serialize/parse checks confirm values/addresses, all 17 patches apply and match. Sandbox `research/bt19/xnu`, originals `research/pre0017`; initial local sleh compile failed due read-only exported header not updated, fixed export and BOTH recompiled successfully. CI exports normally.
- Architecture correction for next agent: CURRENT SWEET board_config does NOT define USE_APPLEARMSMP; it compiles the legacy IOCPU path, not cpu_boot_thread/IOPMGR AppleARMSMP. Existing roadmap mentions AppleARMSMP as a future approach. Do not look for gCPUIC/gAIC/gPMGR globals in the current kernel: they are absent. Determine the actual CPU-init wait after platform registration before choosing the next driver architecture.
- Patch 0016 committed/pushed as `0dcdf5c`; Actions `38750733996` running: https://github.com/dipa-studio/ios-sweet/actions/runs/38750733996. Next artifacts: `xnu/out-0016`, `research/bt20`, `research/run20.log`.
- Patch 0016 implemented: new `iokit/Kernel/arm/SweetPlatformExpert.cpp`, arm64 source list, built-in personality in KernelConfigTables.cpp guarded by ARM64_BOARD_CONFIG_SWEET. Matches only xiaomi,sweet at score 10000, keeps IOPanicPlatform fallback for other hardware. Uses IODTPlatformExpert base initialization/power domain and createNubs CPU logical-ID annotation; overrides top-level publishing because base requires nonexistent Apple NVRAM /options. Publishes real CPU/top-level nodes, provides bounded target/product names, and registers the platform service. GIC/PMGR and arm-io child-bus drivers remain separate work. Both C++ TUs compile (`research/platform-objs`), all imports resolve against 0015/own objects, all 16 patches apply and sources match. Sandbox `research/bt19/xnu`; originals `research/pre0016`. NEXT: full Actions/QEMU; inspect CPU boot waits after the platform registers, do not equate absence of panic with successful boot.
- Patch 0015 CI `38749549779` PASSED (4m3s), checksum verified. Kernel `xnu/out-0015/kernel.development.sweet`, SHA256 `ca1b424a596c7058550ad1659080a333e7643270f019656401d80bf2b876645f`; buildtree/log `research/bt19` / `research/run19.log`. QEMU `research/q0015` (10s, zero unknown glyphs) passes trust-cache handling and machine lockdown, then panics `Unable to find driver for this platform: "xiaomi,sweet" @IOPlatformExpert.cpp:2319` (IOPanicPlatform fallback). Next concrete work: add a built-in SWEET IODTPlatformExpert personality/class; keep the fallback for mismatched platforms. No phone boot yet.
- Direct trust-cache API checks PASSED in the actual 0015 kernel under QEMU/GDB (`research/check-trustcache.gdb`, `research/check-trustcache.log`, `research/q0015-api`): runtime pointers NULL, hash/UUID queries return NOT_FOUND, typed/untyped/legacy loads return NOT_SUPPORTED, capabilities outputs zero and bounds preserved, invalid-argument cases still reject. Second PRNG check also verifies contended refresh returns immediately (`research/check-prng2.log`, `research/q0014-api2`).
- Patch 0015 committed/pushed `8f851d4`, Actions run `38749549779` running: https://github.com/dipa-studio/ios-sweet/actions/runs/38749549779. Do not duplicate.
- Direct PRNG API checks passed in the REAL 0014 kernel under QEMU/GDB, stopped before trust-cache init (`research/check-prng.gdb`, log `research/check-prng.log`, guest `research/q0014-api`). Invoked read_random for 600 bytes (chunking and buffer sentinel intact), repeated output differed, zero-length read/write succeeded, write_random(64-byte input) succeeded, secondary generator 1 initialized and generated distinct output. QEMU log has no exceptions during these checks; guest was discarded after the tests. This tests API behavior, not a cryptographic certification or SMP scheduling.
- Patch 0015 implemented in `bsd/kern/kern_trustcache.c`: SWEET with missing Image4/AMFI marks both runtime pointers NULL and logs service unavailability. Existing static loader handles NULL. Public load APIs return KERN_NOT_SUPPORTED; hash/UUID queries return KERN_NOT_FOUND; capabilities outputs are zero with KERN_NOT_SUPPORTED. Invalid-input checks remain, and Apple paths/available-provider initialization retain existing behavior. No trust is granted. Local arm64 compile passed (`research/trustcache-objs`), all 15 patches apply and sources match. Sandbox `research/bt18/xnu`, baseline `research/pre0015`. Next: Actions/QEMU and direct unavailable-service API checks using GDB.
- Patch 0014 CI `38748543058` PASSED (4m0s), artifact checksum passed. Kernel `xnu/out-0014/kernel.development.sweet`, SHA256 `741de20c851755d333759d7e668346f3edb4f325efac4cc7c142d80d1f5ff75c`; buildtree/log `research/bt18` / `research/run18.log`. QEMU run `research/q0014` (10s, zero unknown glyphs) prints `SWEET PRNG: HMAC-SHA256 registered`, passes commpage initialization, loads vnguard policy, THEN panics `image4 interface not available @kern_trustcache.c:253`. PC=0 fault FIXED IN QEMU. No new phone boot performed.
- Next work: SWEET currently has neither AppleImage4 nor AMFI. `trust_cache_runtime_init` unconditionally requires both; unlike BCM2837, SWEET enters this startup path. Investigate an explicitly unavailable trust-cache runtime with rejected loads/no query matches while providers are absent; preserve all Apple-platform checks. Merely skipping the startup call would leave later AMFI/IMG4 dereferences unsafe. Existing load_static_trust_cache already handles trust_cache_rt == NULL.
- QEMU runner now supports `--kernel MATCHING_KERNEL --fail-on-panic`: runtime font extraction from the payload produces exact `fb.txt`, plus `result.json`; a visible panic returns 2. Baseline 0013 re-run `research/q0013-text` detects the same NULL callback panic with zero unknown glyphs. Synthetic glyph roundtrip (including literal `?`) and invalid-VA rejection passed. Screen rows remain circular, not a full log; `no_panic_observed` does not prove successful boot. README has the invocation.
- Patch 0014 committed/pushed as `be61f99`; Actions run `38748543058` is running: https://github.com/dipa-studio/ios-sweet/actions/runs/38748543058. Do not start a duplicate build.
- 2026-10-15 active: hardware photo `IMG_20261015_160033.jpg` confirms the same PC=0 instruction-fetch abort as QEMU (LR `0xfffffe0007443fe4` = read_random). Independently reproduced with kernel 0013 in `research/q0013` (8-second run); prior allocator fix works. Latest tooling commit reviewed: `8d66d2d`.
- Patch 0014 implemented: registers a built-in HMAC-SHA256 DRBG provider at EARLY_BOOT/FIRST, before commpage creation. A shared mutex serializes output/reseed across CPUs (correctness first; no per-CPU scaling yet), initgen validates CPU identities, refresh uses try-lock and the existing entropy filter/health tests. SWEET entropy accumulation and write_random now use the built-in SHA256 directly; no incomplete g_crypto_funcs table is registered. The existing bootloader-seed requirement remains enforced.
- Local validation: both PRNG translation units compile to arm64 objects in `research/prng-objs`; no SHA256 wrapper imports remain. All 14 patches apply in CI order and resulting PRNG sources match local inputs. Sandbox `research/bt17/xnu`, originals `research/pre0014`, checker `research/check-patch-order.py`. NEXT: Actions kernel build, download to `xnu/out-0014`, run the QEMU payload before requesting another phone boot. Baseline QEMU ADT/payload are `research/q0013.adt` / `research/q0013.bin`.
- 2026-10-15 08:15 QEMU EMULATION WORKS (`tools/qemu-sweet.py`, see "QEMU emulation" below). Patch 0013 VERIFIED in QEMU: boot passes kmem_crypto_init and ulock_initialize. NEXT BLOCKER (reproduced in QEMU, expected on hardware too): `pmap_create_commpages -> random() -> RandomULong -> read_random -> prng_funcs.refresh == NULL` (instruction fetch abort at pc 0, lr read_random+0x34). Nobody calls `register_and_init_prng` (closed corecrypto kext does it on Apple). Fix = patch 0014: SWEET-registered cckprng_funcs provider (osfmk/prng/prng_random.c); note random_cpu_init also panics while !prng_ready. The 07:26 hardware boot of 0013 will most likely show this same panic.
- Previous hardware boot: patch 0013 (`a3a46e2`) CI `38686345689` PASSED (3m44s), image `shim/out/shim-boot-0013.img` was temporarily booted on 2026-10-15 at 05:26 UTC: send OKAY (0.407s), boot OKAY (0.134s), total 0.546s. Superseded by the hardware/QEMU PC=0 observation and patch 0014 work above.
- Latest kernel implementation commit: `8f851d4`. Latest successful kernel CI: `38749549779` (patch 0015), https://github.com/dipa-studio/ios-sweet/actions/runs/38749549779.
- CURRENT image: `shim/out/shim-boot-0013.img`, 16,412,672 bytes, SHA256 `110d1c46aee4b60253db24b6535e9781c4cf0fd25ca2a70e9016cf81378cea25`. Kernel `xnu/out-0013/kernel.development.sweet`, SHA256 `f0b1d375995316c550ce7014ff234d8271e9b9ac2857795ceff41b76ba2cd740`, plain arm64. CI log confirms 0013 applied; checksums passed. Entry PA `0xb146b488`, kernel end PA `0xb1ff4000`.
- Current log/buildtree: `research/run17.log`, `research/bt17` (extracted, no nested .git; preferred baseline for patch 0014). Payload/ADT: `shim/out/payload-0013.bin`, `shim/out/sweet-0013.adt` (includes /defaults). Unpacked ramdisk byte-compared with payload in `shim/out/check-0013`.
- Patch-0012 original image: `shim/out/shim-boot-0012.img`, 16,412,672 bytes, SHA256 `cf4b8ec4a65a51888d71c17d09cd0831d6b761b90e2531fdb8e575c32f4fd24a`. Kernel `xnu/out-0012/kernel.development.sweet`, SHA256 `69b78f49f6459cc63a0af44e7cf73c1779ef72130ef72b12ae86c88183ffc742`; checksums passed and sweet_early_relocate symbol present. Entry PA remains `0xb146b488`, kernel end PA `0xb1ff4000`.
- Patch-0012 log/tree: `research/run16.log`, `research/bt16` (extracted, no nested .git; preferred baseline for next patch). CI log confirms 0012 applied. Payload `shim/out/payload-0012.bin`, ADT `shim/out/sweet-0012.adt`; packed ramdisk byte-compared with payload in `shim/out/check-0012`.
- Active payload command line: `debug=0xc serial=3 cpus=1 keepsyms=1 -enable_kprintf_spam`.
- Latest observed photo: `/home/dipa/Downloads/IMG_20261015_071346.jpg` (local only). Stages 9 (kernel framebuffer VA), 10 (TTBR0 off/TLB flush), 11 (physmap table pointers) and 12 (calling pmap_bootstrap) all visible. Persistent diagnostics are VERIFIED ON HARDWARE.
- pmap.c:1987 is the assert after SecureDTLookupEntry(NULL, "/defaults", &entry). The pmap-max-asids property itself is optional; an empty /defaults uses XNU's MAX_ASIDS. Do not bypass the assertion or guess an ASID limit.
- Previous payload-only fix image: `shim/out/shim-boot-0012-defaults.img`, SHA256 `3ff61a268853c6ea7cbf284833f1346a1d791980ca366b6e1a215a86e040512b` (16,412,672 bytes). Same kernel/CI as 0012; ADT 2516 bytes (`shim/out/sweet-0012-defaults.adt`), root /defaults present with no ASID override. Payload `shim/out/payload-0012-defaults.bin`; unpacked ramdisk exactly matches payload (`shim/out/check-0012-defaults`). This boot reached the allocator crypto NULL-pointer fault below.
- Latest hardware photo: `/home/dipa/Downloads/IMG_20261015_071608.jpg` (local only). Normal serial framebuffer console works. VM bootstrap/zone initialization, logging, scheduler, IPC, KDP and ulock_initialize print before the kmem_crypto_init data abort. gPanicBase warnings are expected because PLATFORM_PANIC_LOG_DISABLED is configured, and are not the faulting call.
- Faulting instruction: `ldr x0, [x8, #0x150]` in crypto_random_kmem_ctx_size; x8 = NULL g_crypto_funcs. Source: libkern/crypto/corecrypto_rand.c and osfmk/vm/vm_kern.c:2448. rand.h explicitly permits NON-cryptographic kmem RNGs, but requires no locking in generation and context size <=256. Do not substitute read_random here: the global PRNG provider is also unregistered and kmem generation must remain lock-free. early_random may seed contexts during single-CPU bootstrap; it uses the built-in HMAC-SHA256 DRBG with the host-generated ADT seed.
- Patch 0013 keeps the replacement entirely private to vm_kern.c: SplitMix64 state is 8 bytes per CPU/sizeclass, initialized using early_random. Uniform selection uses rejection sampling to avoid modulo bias. Other platforms retain the original corecrypto calls; SWEET's generic crypto APIs/registration remain untouched. Reference: https://prng.di.unimi.it/splitmix64.c (Sebastiano Vigna, public domain).
- Validation: vm_kern.c compiles to arm64 (`research/kmem-rng-objs`, using `research/run16.log` + `research/bt16`). Undefined symbols include early_random and NO crypto_random_* references. All 13 patches apply in CI order and match the checked source. Original saved as `research/vm_kern.pre0013.c`.
- RNG host checks: extracted actual new helper in `research/kmem-rng-check.c`; 16,384 outputs match the author's downloaded reference (`research/splitmix64-reference.c`), 147,456 bounded outputs satisfy their limits (including 1 and UINT64_MAX), and a forced rejection advances correctly. Full kernel crypto services and the registered kernel PRNG provider remain future work; this patch only supplies the allocator RNG contract.
- Patch-0011 artifacts: kernel `xnu/out-0011/kernel.development.sweet`, log `research/run15.log`, extracted buildtree `research/bt15` (no nested .git). CI log confirms patch 0011 applied; artifact checksums passed. Kernel is plain arm64, entry VA `0xfffffe000746b488` -> PA `0xb146b488`, kernel end PA still `0xb1ff4000`.
- Patch-0011 image: 16,412,672 bytes, SHA256 `29ad5cbfc752473de4af2c471a24a8b34f92da4bff5afec65c614b90cd3ad53a`. Kernel SHA256 `8ac3a956894b09f7bd0d890de8c5de38c65513287feb1e1bcd12db8ca772ee5c`. Payload/ADT in `shim/out/payload-0011.bin`, `shim/out/sweet-0011.adt`. Header unpacked/checked in `shim/out/check-0011`.
- First patch-0011 attempt timed out waiting for FASTBOOT; superseded by the successful send/boot recorded above. Do not repeat the boot before the user reports the current screen.
- Patch-0011 photo: `/home/dipa/Downloads/IMG_20261015_070218.jpg` (local only). Visible stages 1-8 and old red shim text; entry PA B146B488, boot args PA B1FF8000 / top B1FFC000. No evidence yet locating execution after stage 8.
- Patch-0012 sandbox: `research/bt15/xnu` (NO nested .git). Proposed permanent debug VA: VM_MIN_KERNEL_ADDRESS + ARM_TT_L2_SIZE, in the reserved gap below gVirtBase and above low globals; map the same PA framebuffer as Normal-NC in the final TTBR1 before arm_vm_physmap_init changes phystokv(). Keep the early panic sink until normal kprintf startup.
- Patch 0012 validation: all 4 changed C translation units compiled to arm64 objects in `research/post-ttbr0-objs`; internal header export added to osfmk/arm64/Makefile and recreated locally in EXPORT_HDRS for pe_serial.c. All 12 patches apply in CI order and match all 6 edited files. Baselines are saved under `research/pre0012/`.
- Actual mapping-helper host model (`research/early-map-check.c`, barrier stubbed only for host compilation) confirms: VA `0xfffffe0002000000`, L1 index 2016, L2 index 1; descriptor `0x006000009c000605` = framebuffer PA, Normal-NC, outer-shareable, EL1 RW, PXN+UXN. All other L2 entries preserved. The gap is excluded by ARM_LARGE_MEMORY's pmap_virtual_region(0).
- Next boot command line MUST add `-enable_kprintf_spam`: DEVELOPMENT disables kprintf_output by default even when DB_KPRT is set (`pexpert/arm/pe_kprintf.c`). Planned command line: `debug=0xc serial=3 cpus=1 keepsyms=1 -enable_kprintf_spam`.

### Patch 0012 screen legend (after original stages 1-8)
- 9: kernel framebuffer VA live; 10: TTBR0 off / TLB flushed; 11: physmap pointers rebound.
- 12: calling pmap_bootstrap; 13: pmap_bootstrap returned; 14: early I/O page tables ready; 15: arm_vm_init returned.
- 16: calling serial_init; 17: fbcon config read / mapping; 18: fbcon mapping returned; 19: serial_init returned; 20: kprintf startup complete.
- Normal serial initialization clears the screen, so earlier stages may disappear before 19. If serial exists, early console disables after 20; otherwise early panic output stays enabled.
- Local source sandbox: `research/bt13/xnu` (git baseline `623b060`, patches 0001-0008 already in baseline; uncommitted export edits correspond to patch 0009). Preserve those edits when producing patch 0010.
- Previous compile log/tree: `research/run13.log`, `research/bt13`; previous kernel: `xnu/out/kernel.development.sweet`. New successful log/tree: `research/run14.log`, `research/bt14`; new kernel: `xnu/out-0010/kernel.development.sweet`.
- Current device access: patch-0012 image was temporarily started from FASTBOOT; no adb connection is expected. Never flash partitions for bring-up; use `fastboot boot` with the shim image.
- Patch `0010` lives in `xnu/patches/0010-sweet-early-framebuffer-debug.patch`. Its exact compiled sources are under `research/bt13/xnu`; generated objects are in `research/early-objs`.
- Local checks passed: all 5 changed/new translation units compiled to arm64 Mach-O objects; new console only imports `_doprnt` and `iso_font` (both exist in the previous kernel). All 10 patches applied to a temporary upstream git index in CI order, and all 7 resulting changed source files matched the local compile inputs.
- Reproduce changed-file compilation: `XNU_CC_OBJDIR="$PWD/research/early-objs" python3 tools/xnu-cc.py research/run13.log research/bt13 arm_init.c arm_vm_init.c kern/debug.c arm64/start.s osfmk/arm64/sweet_early.c --per-file` (create the output directory first). The helper now accepts explicit new source paths absent from the old artifact's Makefiles and rejects empty selections.
- Device command result: `adb reboot bootloader`, then `timeout 30s fastboot boot shim/out/shim-boot-0010.img`: send OKAY (16028 KB), boot OKAY, total 0.541s. This confirms bootloader acceptance only, not XNU progress.
- The successful boot above was on 2026-10-14. On 2026-10-15, `timeout 45s fastboot boot ...` timed out waiting for a device; no image was sent. Boot image SHA256 rechecked and unchanged. No new build is needed to repeat the trial.
- Earlier retry: `timeout 90s fastboot boot shim/out/shim-boot-0010.img` timed out (exit 124). This is superseded by the successful 2026-10-15 repeat boot recorded above; do not repeat it until the user reports the screen.
- User observation confirms MMU-on C entry, platform expert, CPU topology/bootstrap, startup bootstrap and cpu_init all complete. Failure is within arm_vm_physmap_init (non-XNU_MONITOR branch), before stage 8 / TTBR0 teardown. Old red shim text remains behind the early console; this is expected because only written rows are cleared.
- New edit/compile sandbox is `research/bt14/xnu` (extracted artifact, NO nested .git; `git diff` there would act on the parent project). Use a saved baseline file / generated unified diff, or explicitly initialize a local baseline before editing. `research/bt13/xnu` does have its own baseline git repo.
- Exact user-reported panic: `arm_vm_init.c:1606 Assertion failed: (temp_ptov_table[ptov_index - 1].va + temp_ptov_table[ptov_index - 1].len) <= physmap_end`.
- Root cause: MacOSX build sets `ARM_LARGE_MEMORY=1`; `XNU_MONITOR` is off. Block alignment in arm_vm_physmap_slide can add gaps, but the non-PPL large-memory physmap_end omitted the padding already present in the small-memory branch. Patch 0011 reserves PTOV_TABLE_SIZE*ARM_TT_TWIG_SIZE (8*32MB) in both the aperture bound and its L1 allocation; monitor/PPL builds retain zero padding. The assertion is preserved.
- Validation: `arm_vm_init.c` compiled to an arm64 object using `research/run14.log` + `research/bt14` (object in `research/physmap-objs`). All 11 patches apply in CI order and produce exactly that source. Host harness `research/physmap-check.c` extracts the real XNU slide function with page-table-write stubs: all 65,536 page-aligned slides within 1GB checked against the current kernel memory layout; old bound fails 65,504 cases, padded bound fails zero; worst overrun 0x1ffc000 bytes. Baseline source saved as `research/arm_vm_init.pre0011.c`.
- CI: https://github.com/dipa-studio/ios-sweet/actions/runs/38638702083 (success; artifacts and full log downloaded).
- New image: `shim/out/shim-boot-0010.img` (16,412,672 bytes, SHA256 `ed2c270e0081bad5ff517be415f9bfe8805463aea7866732203fa97ac737e64e`). Previous image preserved as `shim/out/shim-boot-pre0010.img`.
- New kernel SHA256: `3ee05270cc291c49589a101678f904b1b69cb2f2575e05398bce8a4e052f409a`. Artifact checksums passed; arm64 (not arm64e), early-console symbols present. Payload entry VA `0xfffffe000746a488` -> PA `0xb146a488`; kernel end PA `0xb1ff4000`. Command line remains `debug=0xc serial=3 cpus=1 keepsyms=1`.

### Patch 0010 screen legend
- Bottom-left white 64x32 tile: assembly entered `start_first_cpu`, before page tables/MMU.
- Text `SWEET EARLY 1`: entered `arm_init` with MMU on; 2: platform expert done; 3: CPU topology done; 4: CPU bootstrap done; 5: startup bootstrap done; 6: CPU init done; 7: entering `arm_vm_init`; 8: leaving bootstrap TTBR0.
- `SWEET EARLY PANIC:` prints a copy of panic arguments before normal panic handling needs per-CPU/thread state.
- In patches 0010/0011 the console disabled before TTBR0 invalidation; patch 0012 replaces that with a persistent kernel VA alias and diagnostics through normal serial/kprintf startup (see its legend above).
- Screen contents require a physical observation from the user: adb cannot capture a framebuffer after Android has been replaced by a bare-metal kernel.

## QEMU emulation (2026-10-15)
- `tools/mkadt.py OUT.adt --qemu` = same ADT with QEMU virt GICD 0x08000000 / GICR 0x080a0000 / CNTFRQ 62.5 MHz.
- `tools/qemu-sweet.py PAYLOAD OUTDIR [--secs N] [--hmp "x /8gx ADDR"] [--gdb]`: host-side copy of shim/loader.c
  (segments + ADT + boot_args at their PAs, 6-instruction stub sets x0 and jumps), `-M virt,gic-version=3 -cpu cortex-a76`
  (same ID_AA64MMFR0 as Kryo 470), 4G RAM so 0x9c000000 fb and 0xb0000000 kernel are plain RAM.
  Outputs `fb.png` (the screen), `regs.txt`, `qemu.log` (exceptions with ESR/FAR/ELR). `--gdb` halts with a stub on :1234
  (system `gdb` + `set architecture aarch64`, `hbreak *VA` works with the MMU on).
- Not emulated: Qualcomm XPUs, ABL, real panel, PSCI conduit (QEMU virt uses hvc). Hardware still decides those.
- Example: `python3 tools/mkadt.py /tmp/q.adt --qemu && python3 tools/mkpayload.py xnu/out-0013/kernel.development.sweet /tmp/q.adt /tmp/pq.bin --cmdline 'debug=0xc serial=3 cpus=1 keepsyms=1 -enable_kprintf_spam' && python3 tools/qemu-sweet.py /tmp/pq.bin /tmp/q`

## Layout
- `backup/`  partition dumps + full sdb..sdf LUNs, `SHA256SUMS` (all verified on-device == local)
- `dtb/`     live FDT (from OrangeFox), PixelOS boot.img dtb, dtbo, dts versions
- `shim/`    bare-metal boot shim (`./build.sh` -> `out/shim-boot.img`)
- `research/` mainline sm7150 dts, XNU pe_fiq.c etc, PocketDarwin patches
- `tools/unpack_bootv2.py`

## Device access
- No root in PixelOS 17 (user build, adb root disabled). Root = `fastboot boot recovery/recovery.img` (OrangeFox R12.0_2, temp boot, not flashed).
- `fastboot boot` works for stock boot.img, OrangeFox, and our shim.
- Shim resets itself via PSCI SYSTEM_RESET; IMEM restart_reason 0x77665500 is seen
  (bootreason=bootloader) but ABL still boots Android, so it does not stop in fastboot.

## Hardware facts (live DT + shim measurements)
- Framebuffer (ABL cont splash): 0x9c000000, 1080x2400, stride 4320, a8r8g8b8, panel is DSC *video* mode (no kick needed).
- RAM: 0x80000000+2G, 0x100000000+0xfcc00000. Live reserved-memory = PixelOS base dtb + sweet dtbo fixups.
- GICv3: GICD 0x17a00000, GICR 0x17a60000 (stride 0x20000, 8 PEs). GICD_TYPER 0x007B041D: SecurityExtn=1 (DS=0).
  ABL leaves GICD_CTLR = 0x10 (ARE_NS on, groups off). Writing 0x13 reads back 0x12: EnableGrp1A (bit1) is the one that matters.
- GIC Group 1 VERIFIED (shim 2c): vtimer INTID 19 = 30 IRQs/300ms, ptimer INTID 18 = 30, SGI 1 to self = 10/10.
  ICC_SRE=1 already, ICC_CTLR 0x8440, priority/enable writes stick. GICR_IGROUPR0 and GICD_IGROUPRn read 0 from NS
  even though Group 1 delivery works (RAZ in NS view) - do not use them as a health check.
  INTID 28 shows pending constantly (unknown PPI 12).
- Timer 19.2 MHz. Qualcomm PPI numbering: secure-phys/phys/virt/hyp = PPI 1/2/3/0 -> vtimer INTID 19, ptimer 18 (NOT 27/30).
- PSCI 1.1 via SMC, SMCCC 1.1. CPU_ON ok; SYSTEM_SUSPEND and SYSTEM_RESET2 unsupported.
- SMP: CPU_ON works for all 7 secondaries (MPIDR 0x81000n00).
- Entry EL1, MMU off, x0 = DTB (magic ok). ID_AA64MMFR0 = ...101122: 16K granule YES, 4K YES.
- No serial console: debug UART SE is in SPI mode on sweet. Screen is the only debug channel.

## XNU implications
- XNU GICv3 path (pexpert/arm/pe_fiq.c, VMAPPLE) puts the timer (PPI 27) in Group 0 = FIQ. With SecurityExtn=1,
  Group 0 is secure -> impossible from NS EL1. Need: Group 1 IRQ, ICC_IGRPEN1, INTID 19, and the timer handled in the IRQ path.
- XNU VMAPPLE PSCI uses `hvc`; sweet needs `smc`.
- PocketDarwin NonAppleGenericCpu.patch only swaps -mcpu=apple-h7 for -march=armv8-a.

## Milestone 3 (2026-10-14): 16K MMU verified
- ABL loads the Image at 0x80080000 (base 0x80000000 + 0x80000) regardless of text_offset=0.
- 16K granule, T0SZ=28 (L2 start, 32MB blocks), MAIR 0x44ff00, TCR 0x1409CB51C, PARange=2 (40-bit PA).
- Only own image pages WB (Qualcomm XPUs: never map carve-outs cacheable); fb Normal-NC; rest Device.
- AT S1E1R checks all as expected; unmapped -> translation fault L2.
- Fill fb: 110 ms (MMU off) -> 3.5 ms (NC). Memory loop 70 ms -> 0.7 ms. vtimer + SGI IRQs still fine with MMU on.

## XNU loader design notes (xnu-8796)
- Entry: `_start` -> `start_first_cpu`, x0 = boot_args (PA), MMU off, EL1. boot_args: Revision/Version 2,
  virtBase/physBase/memSize/topOfKernelData, Boot_Video (fb 0x9c000000, rowBytes 4320, 1080x2400, depth 32),
  deviceTreeP/Length (ADT), CommandLine[608], bootFlags, memSizeActual.
- start.s maps [kernel mach header .. physBase+memSize) with cacheable BLOCKS. On Qualcomm every XPU carve-out
  must therefore lie below the kernel: use physBase = 0xb0000000 (above ramdump_fb 0xaf000000+16M,
  cdsp_sec, qseecom), end before rmtfs 0xfde01000 -> memSize ~0x4d000000 for bring-up.
- Base ADT: iPhone 8 d20ap DeviceTree from iOS 16.7.16 IPSW (tools/remotezip.py + tools/adt.py; LZFSE payload).
  Template values are empty: the loader must fill chosen/*, memory-map, cpu*/reg etc. like iBoot.
- XNU build: GitHub Actions (dipa-studio/ios-sweet, xnu.yml) via blacktop/darwin-xnu-build, MACOS_VERSION=13.5.
  New-clang fixes in xnu/patches; Xcode 16 iig is incompatible (IORPC.kernelContent) -> macos-14 runner, oldest Xcode.

## Kernel architecture plan (SWEET machine config)
- First stock build (VMAPPLE) is arm64e (PAC). Kryo 470 = ARMv8.2, no PAC -> SWEET must build plain arm64
  (HAS_APPLE_PAC is only defined for __arm64e__, so arm64 drops PAC automatically).
- Template: VMAPPLE (16K pages, GICv3 code in pe_fiq.c) minus APPLEVIRTUALPLATFORM hypercalls/paravirt PAC,
  plus BCM2837 (generic ARM: no APPLE_ARM64_ARCH_FAMILY Apple sysregs). Do not link the KDK lib<cfg>.os.*.a.
- Timer: XNU expects it on FIQ (sleh_fiq -> rtclock_intr). SWEET: GIC Group 1, so sleh_irq must ack ICC_IAR1,
  route INTID 19 to the same timer path, SGIs to cpu_signal_handler, EOI via ICC_EOIR1.
- SMP/interrupts: open-source AppleARMSMP (USE_APPLEARMSMP) needs an IOInterruptController (AIC role) and an
  IOPMGR (CPU power -> PSCI CPU_ON via SMC). Plan: built-in IOKit classes (SweetGIC, SweetPMGR, platform
  expert) compiled into the kernel and matched via iokit/KernelConfigTables.cpp -> no closed kexts needed.
- Debug: xnu patch 0003 sweet-fbcon = kprintf drawn on the framebuffer (ADT node "sweet-fbcon").
- ADT /arm-io ranges must not map to parent 0 (pe_arm_get_soc_base_phys()==0 disables serial): use parent 0x1000000.

## Status 2026-10-14 late: first XNU boot attempt
- SWEET kernel builds (CI run 38635343732, patches 0001-0009). Verified offline: arm64, no PAC, no >v8.2 code,
  70300 classic relocs all in range (slide 0 = no loader work), entry = __start.
- Boot: shim loader worked (initrd 0x846F0000-0x855FE3E0, BOOTARG 0xB1FF8000, JUMP 0xB146A488) but screen stayed
  red -> xnu died/hung before serial_init (fbcon). kprintf is a no-op before STARTUP_SUB_KPRINTF.
- Historical next-step plan (patch 0010, now implemented and built; see active handoff above): early fb debug channel
  1. start.s start_first_cpu (after mov x20,x0 / mov x21,#0): PA marker band (MMU off, direct store to 0x9c000000).
  2. start.s after both create_bootstrap_mapping calls: add ONE block entry to the existing V=P L2 table
     (x25 + 2*PGBYTES; do NOT call create_bootstrap_mapping again: fb and RAM share L1 entry 0, it would replace
     the L2 table). Entry = TYPE_BLOCK|VALID|SH(OUTER)|ATTRINDX(CACHE_ATTRINDX_WRITECOMB=1)|AF|PNX|NX|0x9c000000,
     index = (va & ARM_TT_L2_INDEX_MASK) >> ARM_TT_L2_SHIFT.
  3. new osfmk/arm64/sweet_early.c (+files.arm64 entry): sweet_early_mark(n) colored bands at screen bottom and
     sweet_early_putc using iso_font via VA=PA while the bootstrap TTBR0 is live; disable before
     arm_vm_init's set_mmu_ttb(invalid_ttep) (arm_vm_init.c:2148).
  4. markers in arm_init after PE_init_platform, ml_parse_cpu_topology, cpu_bootstrap, kernel_startup_bootstrap,
     cpu_init, before arm_vm_init.
  5. panic hook at top of panic_trap_to_debugger: va_copy + _doprnt(fmt, &copy, sweet_early_putc, 16).
  Verify with tools/xnu-cc.py (compile+symbols) and patch-order simulation before the single CI run.
## 2026-10-25: fail-closed MT6897 LK entry contract

Added `duchamp/loader/mt6897_entry.c` after comparing the MT8167 LK bootshim
reference with the Duchamp firmware evidence. The gate accepts only EL1
(`CurrentEL=4`), requires `SCTLR_EL1.M/C/I` clear, and bounds the aligned FDT
pointer received in `x0` to a caller-provided live-memory range. EL2 and
MMU/cache-on entry fail closed. This is host-tested metadata validation, not a
phone boot or proof that LK supplies the same register contract.
