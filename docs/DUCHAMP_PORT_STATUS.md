# Duchamp native-port status — 2026-11-15

This request produced source changes, builds and offline execution. It did not
complete physical UFS, Android chainboot, native GPU or iOS GUI support. No
subsystem below is labelled VERIFIED on compilation alone.

| Phase | Status | Completed work / remaining boundary |
| --- | --- | --- |
| 0 Source verification | ANALYZED | Five requested repositories checked, immutable revisions recorded; 770 device-reference files mapped, additional common/Linux scopes inventoried |
| 1 Existing baseline | TESTED_OFFLINE | Existing bootshim/payload/mapper retained; new complete-source XNU boot plus readonly root regression |
| 2 Hardware configuration | TESTED_OFFLINE | Native HakiOS metadata/checker; pinned FDT map, reservations/providers and explicit UNKNOWN permissions |
| 3 MT6833 UFS analysis | ANALYZED | No-transfer reader reproduced; unsafe invented GPT geometry rejected; Linux/Xiaomi dependencies compared |
| 4 Physical MT6897 UFS | BLOCKED | Portable INQUIRY is implemented/tested offline; physical read-access, resources, DMA/cache and PHY/clock/IRQ contracts remain unproven |
| 5 MT6768 loader analysis | ANALYZED | Actual source/header/payload/chainboot/pmsg/return/reset assumptions documented |
| 6 Physical loader integration | BLOCKED | The guarded QEMU loader consumes the request and enters XNU once. Physical retained pmsg/cache publication and real Android v4 fallback are unproven |
| 7 Build/package | TESTED_OFFLINE | Complete source kernel, source-built loader, payload and QEMU-only v4/LZ4 review container; no phone deployment |
| 8 Other hardware | NOT_STARTED | No new GPU/audio/radio driver activated; follow verified storage/loader prerequisites |
| 9 Darwin userspace | NOT_STARTED | Existing diagnostic/Darwin tests preserved; no new shared-region/GUI claim |
| 10 Complete physical validation | BLOCKED | Offline evidence saved; a future specific phone trial requires established prerequisites and approval |

## Actual build and test evidence

* Full-source macOS CI [43753027593](https://github.com/Mehmed911/ios-sweet/actions/runs/43753027593)
  succeeded at `eb6cb0b61cb7030caff7958bf2e619c409f9249d` on the isolated ref
  codex/duchamp-ufs-inquiry-20261115, with 324 verified inputs. No unrelated
  working changes were included. Complete 16781160-byte kernel SHA-256:
  `4176a10872a39839291f4783ccb0ae738e043a9da5db2c258412bc9f297af590`.
  Artifact source/manifest/checksums and the native root-adapter to dufs_inquiry
  call were verified. No replay or binary patch was applied.
* Seven full-XNU/QEMU MCQ cases pass. Standard INQUIRY returned version 5,
  vendor `QEMU`, product `QEMU HARDDISK`, revision `2.5+`. The read-only GPT/HFS+
  root reached diagnostic PID 1 in 34.224 host seconds, with 34 MCQ completions
  and 28 READ(16) commands; PID 1 verified bytes and EROFS. The observed values
  describe the emulator device, not the phone.
* The same kernel passed standard INQUIRY in legacy queue mode and reached
  diagnostic PID 1 in 33.847 seconds. The MCQ regression with the INQUIRY
  option absent reached PID 1 in 33.876 seconds using 33 completions.
* Missing DMA/cache grants and an inherited-mode record produce empty UFS
  traces. Invalid pool DMA and absent SQ synchronization reject submission.
  Injected device-side DMA failure produces one submission, zero completions/
  SCSI commands and a bounded timeout. These are synthetic permission/cache
  fixtures, not physical MediaTek evidence.
* Native ASan/UBSan and ARM64 QEMU models each pass 131 transport/INQUIRY checks
  (79 existing polling checks plus 52 added checks), including malformed or
  unchanged responses, absent readiness and wrong UPIU tag. Output stays
  unchanged on failure. No public arbitrary-CDB/write API was introduced.
* The new one-session RAM policy passes 251 checks on both host and ARM64,
  including every wrap position, duplicate consumption, stale bytes, malformed
  headers and denial before dereferencing a proposed buffer. The QEMU loader
  now uses that same parser and publishes the consumed bytes before handoff.
* The original upstream main checker accepts duchamp and its carried mt6897
  SoC. All 25 foreign driver symbols and enabled foreign runtime arguments are
  disabled. Generated arguments contain only `cpus=1`.
* Six QEMU menu cases pass, including Android default/timeout, button edges and
  reset only after simulated A readback. Thirteen one-session cases pass.
  A wrapped request enters the actual XNU kernel once. QMP records the kernel
  PC and framebuffer text. A host-triggered reset preserves the consumed
  ring, rejects replay on B and returns to the A model. A wrong or absent
  readback blocks the kernel jump. Physical Android chainboot remains unproven.

## Review artifacts

`out/duchamp/hakios-port-final-20261115/duchamp-qemu-review-elf-verified.img` is **QEMU-only**,
8581120 bytes (about 8.18 MiB), SHA-256
`5d7383baee906669d9c3b399875dff17aab236b5dbbb260937f024e096e82d3a`.
Its ARM64 loader and 16770368-byte SWEETXNU payload come from actual source-built
code/the checked complete kernel. Legacy-LZ4 decompression matches the loader
byte-for-byte; stock header metadata is preserved. The manifest explicitly
records that the one-session parser is linked, the tested loader survived
round-trip validation, and physical Android chainboot remains unverified.
The packer also checks the raw loader against the linked ELF and rejects a
modified byte before creating an image.
The container is unsigned and reserved for QEMU.

Builds are reproduced by tools/test-duchamp-hakios-port.py and
devices/duchamp/Makefile. Full-kernel reproduction uses the pinned CI ref;
tools/test-duchamp-ufs-mcq-xnu.py --snapshot --inquiry tests it without patching.
Compiler commands, versions, receipts, all logs and trace hashes are archived in
the outer workspace's outputs/duchamp-hakios-port-20261115. Private upstream
checkouts/downloads are not committed.

## Next native boundary

Obtain a verified initialization or documented handoff establishing readable,
powered, clock-stable UFS MMIO for this XNU entry, then use the existing passive
observer to capture queues. Before issuing a command, establish exclusive
controller/resources, PA-to-DMA translation and cache ownership. Separately
prove retained-request publication and the Android/vendor_boot/recovery path
before binding the one-session policy. Do not infer any of these from a DT node,
metadata status, QEMU success or the community stub. No ADB, flashing, reboot,
slot change, partition modification, UFS write or bootloader relock was executed.
