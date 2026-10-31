# MT6897 phone bootstrap candidate — 2026-10-31

This milestone prepares, but does not deploy, a diagnostic XNU image for the
POCO X6 Pro (`duchamp`). It uses the newest kernel that passed the virtual
UFS/HFS+/PID 1 QEMU path, plus separate phone and QEMU ADTs generated from the
saved live FDT. No fastboot command, phone write, partition access, or physical
MMIO was performed while producing or validating this candidate.

The candidate deliberately omits a root-device argument and keeps `rootrw=0`.
It does not enable the QEMU UFS gate or a physical MT6897 UFS provider. On real
hardware its useful endpoint is therefore the framebuffer console at the first
physical GIC/timer/scheduler failure, or the normal root-device wait if those
subsystems work. It cannot boot the full system from phone storage.

## Pinned inputs

| Input | SHA-256 |
| --- | --- |
| XNU kernel, CI run `41236137474` | `fa23d6319ab2af1b669146bd4a17d66f6726703bee0ced8d1e607e1bc0db81d9` |
| Phone ADT | `efa8ca6254a0534ebe79c0c9a38b12d07b9a468a7bf32ed30c348511553e6101` |
| QEMU twin ADT | `5ddf0057a50d97be8fc2a08ad88e443ab3460290f6fc532f5f4dbc063562eebe` |
| Saved live FDT | `9c49589f70044127be8941a9ea5537977f440ccd5ac15cfd24e120c8a1181d29` |
| Stock `boot_a`, used only as packaging metadata | `1b972f4f1c98428f2fca1e7c1c8cf463e0122a70a290e482be3230c7838e3e12` |

Both payloads use:

```text
debug=0xc serial=3 cpus=1 keepsyms=1 -enable_kprintf_spam -noprogress rootrw=0 sweet_console_fb=1
```

The phone payload SHA-256 is
`7bdd16748a4bb715815e13a532f9403536e735fbdceeeb8bdf4031edb23a708a`.
The QEMU twin payload SHA-256 is
`8b5348cad759d9d87ff3a3299d6937aefba3fdc10201d55c8fade1f05aec69b1`.

## Actual local results

- Payload source reconstruction passed for both profiles against the pinned
  kernel. Each payload has ten segments, no fixups, and virtual entry
  `0xfffffe0007480488`.
- The live-FDT guard accepted the bounded `0x1c0000000 + 0x20000000` window.
  Physical entry is `0x1c1480488`, ADT is `0x1c2568000`, boot arguments are at
  `0x1c256c000`, and the highest planned address is `0x1c2570000`.
- Host entry-gate, handoff-ready, return-channel, payload-preflight,
  materializer, and return-slot tests passed. Both embedded payloads compare
  byte-for-byte with their source files.
- The phone and QEMU jump ELFs have no relocations or unresolved symbols and
  each contains exactly one final indirect branch.
- The QEMU twin traversed bootshim, materialization, handoff, and XNU entry
  with the captured phone FDT and 8 GiB RAM. The framebuffer test passed with
  `91,324` white XNU pixels after 20 seconds.
- The saved-DTB offline gate passed all 12 grouped components in 12.566
  seconds: boot profile, FDT, GIC, PSCI, timer, power/DMA, firmware/IOMMU
  providers, UFS clocks, UFS topckgen, and UFS polling. Physical backends stayed
  disabled.
- The phone wrapper is a 64 MiB Android boot-v4 image using legacy LZ4 and an
  AVB hash footer with algorithm `NONE`. `avbtool verify_image` verified the
  footer, vbmeta, and boot hash. Its 8,533,184-byte compressed kernel
  decompresses byte-for-byte to the phone bootshim image.

The prepared image is ignored build output at
`research/mt6897-phone-boot-v2/duchamp-xnu-latest-diagnostic.img`, SHA-256
`a83f0792ccd883c19a8225641b4e96090fb08673375e71fe93123e0dafddfaa8`.
The machine-readable record is
`research/mt6897-phone-boot-v2/manifest.json`. Neither file is authorization to
write `boot_a`.

## Read-only Android evidence

A separate read-only ADB observation matched the saved device model. Android
reported `duchamp`, MT6897, and boot controller `112b0000.ufshci`. Its live
GICv3 counters advanced for the architected timer at HWIRQ 27 and for all nine
saved-DTB UFS interrupts at HWIRQs 200 and 209-216. This proves Android runtime
delivery and boot-controller identity only. It does not prove that XNU owns
those resources or that its UFS DMA/IOMMU route is usable.

## Remaining physical boundary

This candidate can test the single boot CPU, GICv3, architected timer,
scheduler, and framebuffer console on the phone only after a separate explicit
hardware-test decision. It cannot close the storage boundary. Enabling physical
UFS still requires a documented installed-firmware contract, secure resource
ownership, runtime DMA ops/fwspec/domain, controller capabilities, descriptor
and data address masks, and cache ownership. Secondary CPU power-up and Mali
acceleration are also unverified. Until those facts are measured, the physical
storage provider remains closed and this is not a phone-ready iOS build.
