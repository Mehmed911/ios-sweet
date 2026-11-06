# Next Duchamp checkpoint: Apple launchd from a RAM root

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
15 service checks passing. That remains QEMU evidence, not a phone observation.

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
The last explicit reflash request applied to the capture image. A hardware
trial of this prepared image needs a separate user decision. No launchd
candidate has been flashed during this revalidation.

Before an approved trial, recheck the exact connected device, slot, unlock
state, battery and original `boot_a`, and capture a fresh backup. Write only
`boot_a`, observe the Apple launchd/service output, and use the proven guarded
restoration to verify original Android boot, build, root and live partition
hash. Preserve bootloaders, vbmeta, init_boot, other slots and userdata.

Physical UFS, DMA/IOMMU and firmware/resource ownership stay closed. Successful
RAM-root launchd would establish a larger userspace checkpoint; it would not
prove SpringBoard, Mali acceleration, touchscreen, persistent storage, or a
complete iOS system.
