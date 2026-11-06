# Duchamp runtime PC/x0 phone trial, 2026-11-06

The user explicitly accepted flashing for this trial. The approved deployment
is one isolated PC/x0 capture image written to `boot_a`, followed by restoration
of the original `boot_a`. This supersedes the prior no-partition-write rule
for this trial only. It does not authorize a physical UFS backend, bootloader
replacement, a vbmeta change, a slot switch, or userdata changes.

## Preparation and recovery

Read-only ADB checks confirmed Duchamp/MT6897, unlocked bootloader, active slot
`_a`, completed Android boot, Magisk root and an 81% charging battery. The build
fingerprint remained POCO Android 14 `V816.0.17.0.UNLMIXM`.

The live `boot_a` hash matched the saved original. A fresh, binary-safe 64 MiB
backup was then copied directly to the host and independently hashed. The live
`vendor_boot_a` and `lk_a` hashes also matched the pinned handoff contract.

| Artifact | SHA-256 |
| --- | --- |
| Live/original/fresh backup `boot_a` | `1b972f4f1c98428f2fca1e7c1c8cf463e0122a70a290e482be3230c7838e3e12` |
| Live `vendor_boot_a` | `d1d1887eba4f7b4920fc4292de5cf4e9aa6e7ce474a6b45ffeb4141434743e49` |
| Live `lk_a` | `f85373d3b4cdf3c959e38bbbfe198a2857e03a5266c6f2a40c319549a5ba957a` |
| Capture ARM64 Image | `2a7dff64f5e28afa5e7eef74e99ea2d3a273df367f341047891ba3a4ea6d20ea` |
| Capture boot-v4/LZ4/AVB-NONE image | `d4d39727f226cd1551df1f5bc11775c1cd05654fa661b1f65ae6d308902e023c` |

The capture Image is 40,912 bytes, position-independent, without ELF
relocations or unresolved symbols. Its isolated entry records `_head` through
`adr` and preserves inherited `x0`; it does not dereference the FDT or link an
XNU payload, transport, storage operation or watchdog modification.

The fresh build passed its actual AArch64 QEMU RAM-record and framebuffer
tests. QEMU observed PC `0x40200000`, `x0=0x48000000`, EL1. These emulator values
are not physical phone measurements.

The 64 MiB phone wrapper preserves the stock Android boot-v4 metadata, uses
legacy LZ4 and a new AVB-NONE boot hash footer. AOSP avbtool verified the footer
and boot hash; decompression matched the tested ARM64 Image byte-for-byte.

The local recovery helper validates the fresh backup, the device identity,
active slot, unlock state and exact partition size before writing only
`boot_a`. It then reboots Android and requires boot completion, correct device
identity and a live root SHA-256 read matching the restored backup.

## Actual deployment state

Fastboot confirmed `product=duchamp`, `current-slot=a`, `unlocked=yes`,
`secure=no`, and a 64 MiB `boot_a` partition. Sending and writing the diagnostic
image both returned OKAY; total flash time was 1.771 seconds. Fastboot also
accepted the diagnostic reboot.

The user supplied a photograph showing two bright text rows on a dark display,
consistent with the capture renderer. Exposure and blur obscure the individual
hexadecimal digits. Neither PC nor x0 can be transcribed reliably from this
photo, so their numeric hardware values remain unverified. The private evidence
copy is `phone-pc-x0-observation-01.jpg`, SHA-256
`1f3931fd8ea8db9ca585d5698b146452d869fc3f50cc72a5694374dc12323667`.

The user returned the phone to Fastboot. The guarded recovery helper sent and
wrote the original `boot_a` successfully (1.834 seconds), rebooted Android, and
verified `sys.boot_completed=1`, Duchamp/MT6897, slot `_a`, and the live `boot_a`
hash matching the original backup. Recovery completed at 02:57:20 local time.
A separate ADB check reconfirmed the original Android build fingerprint and
Magisk root (`uid=0`). The helper has exited successfully.

The phone is back on its original Android boot image. The numeric PC/x0
measurement remains incomplete because the photo is unreadable; it must not
be filled from static LK metadata or QEMU values. A clearer capture is needed
before promoting those runtime address claims.

Private build, backup and transcript files are under the ignored directory
`work/phone-pc-x0-flash-trial-v1`. The 64 MiB QEMU-only LK transport layout
artifact was not used in this phone trial.
