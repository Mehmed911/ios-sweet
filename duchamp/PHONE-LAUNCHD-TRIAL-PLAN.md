# Duchamp hardware checkpoint: Apple launchd from a RAM root

## Concrete objective

Boot the existing single-CPU Duchamp XNU candidate, mount its embedded 32 MiB
HFS RAM root, execute the unchanged Apple launchd/dyld and xpcproxy, and observe
one diagnostic C service as a child of PID 1. Stop at the service heartbeats
and restore the original Android boot image.

The earlier phone photographs established a diagnostic PID 1, fork/exec, RAM
files and IPC. The current PC/x0 photo additionally established runtime Image
`_head=0x40000000` and incoming `x0=0x47c80000`. Repeating those earlier
checkpoints individually is not the next objective. This candidate exercises
the original Apple process launcher on the phone.

## Exact prepared image

- Path: `work/phone-launchd-candidate-v1/duchamp-apple-launchd-avb-none-lz4.img`.
- Bytes: `67108864`.
- SHA-256: `e36b7632ff402d39db162081c2c5bb401540651ba87a38d9fdd21afd6ca80686`.
- XNU SHA-256: `e465723a540844817a5b9cb36c14984d660f9a8e41f6638240527b469189182b`.
- RAM root SHA-256: `491aa78408c423c50e8b59644e416e94b643ed3eb119158d52684af4176c8b3f`.
- Physical XNU window: `0x1c0000000 + 0x20000000`.
- Planned XNU entry: `0x1c1480488`.
- CPU count: `1`; root device: `md0`.

The image contains a phone ADT. The saved matching QEMU profile previously
proved original launchd/dyld, xpcproxy and a persistent root C service with all
15 service checks passing. The separate physical-phone evidence is recorded
below; its scope is not inferred from the QEMU result.

## Fresh local revalidation, 2026-11-06

Copied the candidate and verifier into the new independent directory
`work/phone-launchd-recheck-20261106-v1` and reran its complete offline verifier.
It passed 17/17 checks. The revalidation rebuilt the phone/QEMU payloads
byte-for-byte, checked both linked ELFs and their embedded payloads, ran the
native loader tests, reached actual XNU entry through the bootshim in QEMU,
verified the LZ4 roundtrip and AVB-NONE hash footer, and validated the pinned
previous 15-check service proof. It did not rerun that entire service fixture
or contact a phone.

The new verification report is byte-identical to the original, SHA-256
`e3e7faeb50977552385ee8c304bc54035f7ad6887492df1f844cd350f33287a6`.
Original candidate files and existing user changes were preserved.

## Hardware trial scope

This is a different image and execution scope from the isolated PC/x0 capture.
After reviewing the concrete image and recovery plan, the user explicitly
approved this Apple-launchd `boot_a` trial with stock Android restoration.
The offline revalidation itself performed no phone access.

Before an approved trial, recheck the exact connected device, slot, unlock
state, battery and original `boot_a`, and capture a fresh backup. Write only
`boot_a`, observe the Apple launchd/service output, and use the proven guarded
restoration to verify original Android boot, build, root and live partition
hash. Preserve bootloaders, vbmeta, init_boot, other slots and userdata.

Physical UFS, DMA/IOMMU and firmware/resource ownership stay closed. Successful
RAM-root launchd would establish a larger userspace checkpoint; it would not
prove SpringBoard, Mali acceleration, touchscreen, persistent storage, or a
complete iOS system.

## Approved physical trial: PASS with photographed service output

Read-only preflight reconfirmed Duchamp/MT6897, slot `_a`, unlocked bootloader,
completed original Android boot and an 80% charging battery. Live `boot_a`,
`vendor_boot_a` and `lk_a` hashes matched the saved exact captures. A new
binary-safe 64 MiB `boot_a` backup was taken and verified against original
SHA-256 `1b972f4f1c98428f2fca1e7c1c8cf463e0122a70a290e482be3230c7838e3e12`.
The trial image still matched the pinned `e36b7632...ca80686` SHA-256, and its
copied offline verification report passed all 17 checks.

Fastboot independently reconfirmed product, active slot, unlock state and
`boot_a` size before sending and writing the 64 MiB image. Both operations
returned OKAY; total flash time was 1.770 seconds. Reboot was accepted. No other
partition or slot selection was changed.

The user's legible physical-phone photo shows the launchd service state
changing to `running`, a successful xpcproxy spawn, and:

```text
SWEET launchd service: main pid=3 ppid=1
SWEET launchd service: uid=0 euid=0
SWEET launchd service: parent_path=/sbin/launchd
SWEET launchd service: RAM file verified
SWEET launchd service: heartbeat=1 pid=3 ppid=1
...
SWEET launchd service: heartbeat=11 pid=3 ppid=1
```

The parent path is reported through `proc_pidpath`; PID, parent PID and UID
markers represent process queries, not the fixture's process name alone.
Together with the pinned image/runtime provenance, the photo establishes
original Apple launchd as PID 1 launching the root C service through xpcproxy
on Duchamp. The service verified its RAM file and continued through eleven
heartbeat values. The fixture retains `org.sweet.qemu.c-service` as its label;
that label does not change the physical-phone observation source.

The photograph is stored privately as
`work/phone-apple-launchd-flash-trial-v1/phone-launchd-service-observation-01.jpg`,
SHA-256 `8e2d5566818cd8eb9a94793c60398a67e345d42af61db97256eaf58e09ce3243`.
Visible persona lookup warnings did not prevent this service from starting or
remaining alive. No general persona compatibility, broader service closure,
or wall-clock accuracy is inferred from this checkpoint.

## Completed stock restoration

After the user's return to Fastboot, the guarded helper restored original
`boot_a` successfully (send/write OKAY, 1.838 seconds) and accepted the Android
reboot. Its post-reboot observation then exited on a nonzero ADB command with
an empty diagnostic before producing its final PASS. The exact failed ADB
invocation was not recorded; this was after the successful stock write.

Independent read-only follow-up confirmed Android `sys.boot_completed=1`,
Duchamp/MT6897, slot `_a`, the original `V816.0.17.0.UNLMIXM` build fingerprint,
Magisk `uid=0`, and the live `boot_a` SHA-256 matching the fresh original
backup. Thus recovery is verified independently; the helper itself is not
reported as a clean PASS and no additional flash was needed.

The phone is back on original Android. The trial establishes a RAM-root Apple
launchd/service checkpoint. UFS/DMA/IOMMU/firmware ownership, persistent root,
Mali acceleration, SpringBoard and other phone peripherals remain unproven.

Private image copy, fresh backup, verification, plan and transcripts are under
`work/phone-apple-launchd-flash-trial-v1`.
