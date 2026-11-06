# Duchamp: combined services RAM-root candidate

## Checkpoint and scope

The preceding physical-phone trial proved unchanged Apple launchd as PID 1
and one root C service through eleven heartbeats. This next candidate reuses
that exact XNU kernel and replaces its 32 MiB HFS RAM root with the existing
combined launchctl/syslogd/notifyd fixture. The CLI is pinned Procursus FOSS
launchctl; launchd, dyld, xpcproxy, syslogd and notifyd are unchanged Apple
executables. Two diagnostic clients and an observer exercise the services.

The new service batch is locally proved and its physical-phone CONTROL PASS
markers have now been photographed in the approved trial recorded below.
Physical UFS/DMA/IOMMU/resource ownership remain closed. The candidate does not
establish SpringBoard, Mali acceleration, touchscreen or a complete iOS system.
It keeps `cpus=1`, `rd=md0` and the existing 512 MiB high-RAM XNU window.

## Exact private artifacts, 2026-11-06

| Artifact | SHA-256 |
| --- | --- |
| `work/phone-services-candidate-v3/duchamp-services-batch-avb-none-lz4.img` | `545112503a5e9052db709572cc840758619f2b7e27c9aa58c0af2a3924a8f6a8` |
| `work/phone-services-candidate-v3/verification.json` | `0b15c708455f7d8c23625e24dc476dd039532286f5d43ed4f8399bbfd695e63f` |
| `work/phone-services-batch-v2/qemu-proof/run/verification.json` | `772c3971d0b455a9013b9d933e7147ef1b97b9e7e7a7d3b22464a3336eab191d` |
| Phone-proven `kernel.development.sweet` | `e465723a540844817a5b9cb36c14984d660f9a8e41f6638240527b469189182b` |
| Combined `root.hfs` | `3e800f071990192fefd69684477618532c85ab85accbd74f750a51c2f70e6baf` |
| Phone payload | `35c8ae57b4dacf3b9015a72202d4e4412427ee4ad2980f655fd3e633920ed4c7` |
| QEMU payload | `63341fb1282ab49fdb8f1290cf648568eb173e9098e606b2124b1a3cd6c92cd7` |

The final image is 67,108,864 bytes, boot-v4 with legacy LZ4 and an AVB NONE
hash footer. Its compressed Image is 13,646,827 bytes and fits the original
16,318,464-byte pre-vbmeta region. Stock metadata is preserved except the
kernel size; no bootloader, vbmeta partition, slot selection or userdata change
is part of this candidate. These artifacts contain private device inputs or
Apple binaries and must remain outside git.

## Fresh test results

`tools/replay-duchamp-services-batch.sh` freshly booted the combined fixture in
QEMU using the same kernel as the successful phone trial. All 74 guest checks
passed in 71.368 host seconds with the default QEMU clock. The saved RAM disk,
guest files, framebuffer output and verification report are retained under
`work/phone-services-batch-v2/qemu-proof`. Observed process IDs were notifyd 7,
syslogd 4, clients 5 and 6, and observer 3. The checks cover distinct processes,
executable provenance, six ASL records, notification state and cancellation,
client shutdown and two continuing server heartbeats. Final markers include:

```text
SWEET launchctl: NOTIFYD CONTROL PASS server=7 syslogd=4 clients=5,6
SWEET launchctl: SYSLOGD CONTROL PASS server=4 clients=5,6 messages=6
SWEET launchctl: heartbeat=2 syslogd_running=1 server=4 probes_stopped=1
```

The packager then passed all 12 checks: pinned inputs, complete guest proof,
byte-identical QEMU payload reconstruction, root size, both ELF/embedded
payloads, native entry/handoff/return checks, complete materialization byte
comparison, actual bootshim-to-XNU entry in QEMU, stock boot container layout,
AVB footer verification and byte-identical LZ4 roundtrip. Its bootshim entry
test is separate from the full service run. Neither proves phone timing or
the phone's execution of the new combined batch.

Negative checks rejected an existing output directory and an actual failed
earlier guest proof before creating a candidate. Shell and Python syntax
checks passed. Candidate/proof v1 failures and intermediate v2 packaging are
preserved; v3 is the selected artifact.

## Linker correction

The initial packaging audit caught an undefined `DUCHAMP_IMAGE_BASE` sentinel
in default legacy ELFs. `build.sh` now explicitly defines the default base as
zero. Mode-specific overrides remain explicit. Independent builds verified
capture base zero, layout base `0x40000000` and QEMU LK transport base
`0x40200000`, without undefined symbols or relocations. Capture/layout
verifiers passed. `shim.ld` has no change. An attempted linker-script default
was rejected when its explicit-base layout failed and is not the final fix.

## Local replay

With the saved private fixtures and current local source state available,
run inside Ubuntu/WSL from the repository root, using new output directories:

```sh
sh tools/replay-duchamp-services-batch.sh work/services-replay-NEW
python3 tools/package-duchamp-services-candidate.py \
  --proof-dir work/services-replay-NEW/qemu-proof \
  --output work/services-candidate-NEW
```

The replay allocates, runs and exports its native Linux temporary directory
within one WSL invocation. The selected build includes existing local loader
changes; the packaging report pins their source hashes. This is a local
fixture workflow, not a claim that a clean checkout includes private inputs
or all pre-existing uncommitted source changes.

## Next hardware decision

No phone access or partition write occurred while preparing this batch. The
last verified physical state is original Android restored after the preceding
launchd trial. That restore wrote stock successfully; a transient, poorly
reported ADB follow-up failed, then independent read-only checks established
completed Android boot and the exact original live boot hash. Preserve that
qualification rather than reporting a clean helper run.

The user separately approved this image's `boot_a` trial with original Android
restoration under the repository's per-step destructive-action rule.
Before writing, recheck device/slot/unlock/battery and live stock hashes, take
a fresh binary-safe backup, and prepare recovery against that exact backup.
The recovery helper must log the failing command and tolerate bounded read-only
ADB transport errors during boot observation; it must never retry a flash
automatically. Observe the two CONTROL PASS markers and the continuing
heartbeat, then restore and independently verify original Android and boot_a.
If the phone stops earlier, retain the last readable output and restore;
QEMU success is not permission to enable physical UFS or undocumented MMIO.

## Approved physical trial: photographed service PASS and Android restored

The user's approval followed the exact image and test results above. Fresh
read-only preflight established Duchamp/MT6897, slot `_a`, completed original
Android boot, unlocked state, Magisk root, 85% charging battery and matching
live boot_a/vendor_boot_a/lk_a hashes. A fresh binary-safe 64 MiB boot_a backup
matched original SHA-256
`1b972f4f1c98428f2fca1e7c1c8cf463e0122a70a290e482be3230c7838e3e12`.
The copied candidate and report still matched their pinned hashes.

Fastboot independently reconfirmed product/slot/unlock/partition size. Sending
and writing only boot_a returned OKAY, total 1.766 seconds. Reboot was accepted.
The user's clear physical-phone photo then showed both CONTROL PASS lines
listed above, plus heartbeat 1, 2 and 3 with syslogd still running as PID 4 and
the two probes stopped. notifyd was PID 7, clients were PID 5 and 6, and each
client reported normal exit with three ASL messages. Notification probe and
cancellation markers are visible. This establishes the combined RAM-root
service checkpoint on Duchamp; it does not import all 74 saved-guest checks
into the physical test or prove hardware UFS.

The photograph is preserved privately as
`work/phone-services-flash-trial-v1/phone-services-observation-01.jpg`, SHA-256
`652315d665cae36a5e2b957d2c645f7be18bfa4bd3aa5c3188a2b06efb956dda`.
Visible `vm_shared_region_start_address() failed` messages did not stop the
photographed CLI commands from returning status zero or the service checks
from passing. Their broader effect is not established by this trial.

The private restore helper was prepared before flashing, syntax-checked and
dry-run against the fresh backup. It logs command/arguments/exit/output on
failure, permits bounded retries only for read-only post-reboot ADB checks,
and makes exactly one stock flash attempt. After the phone re-entered Fastboot,
it wrote original boot_a successfully (1.819 seconds), rebooted Android and
finished with PASS/exit code zero. One transient ADB `sys.boot_completed` read
failed with device-not-found during reboot; the improved observation loop
logged the exact command and tolerated it without repeating the flash.

An independent read-only follow-up reconfirmed boot_completed=1, Duchamp/MT6897,
slot `_a`, the original V816.0.17.0.UNLMIXM fingerprint, Magisk root and live
boot_a SHA-256 matching the fresh original backup. Its private JSON report is
`work/phone-services-flash-trial-v1/android-recovery-followup.json`, SHA-256
`4040e55a2f0a9a653750c92f69df67360015a1796f7f71bcf0919319115ccd54`.
Restoration completed at 04:16:17 local time. Helper exec session 82953 ended;
no restoration is pending. Evidence and scripts remain outside git under
`work/phone-services-flash-trial-v1`. No additional phone trial is authorized
by the completed combined-services test; continue independent local work and
review any materially different hardware action separately.
