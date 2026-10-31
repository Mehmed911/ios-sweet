# MT6897 phone bootstrap candidate — 2026-10-31

This milestone prepares, but does not deploy, a diagnostic XNU image for the
POCO X6 Pro (`duchamp`). It uses the latest kernel that already passed the
read-only virtual-UFS/HFS+ QEMU tests and the separate phone ADT generated from
the saved live FDT. No phone, USB, ADB, fastboot or partition operation was
performed.

The candidate deliberately omits a root-device argument and keeps `rootrw=0`.
It does not enable the QEMU UFS gate or a physical MT6897 UFS provider. On real
hardware its useful endpoint is therefore the framebuffer console at the first
physical GIC/timer/scheduler failure, or the normal root-device wait if those
subsystems work. It cannot boot the full system from phone storage.

## Pinned inputs

| Input | SHA-256 |
| --- | --- |
| XNU kernel, CI run `41156122045`, artifact `13025606915` | `8d47bba9d1f097cba15a4d4747ed28cc7f4026a7b65d87ad472eb6f8a83d731a` |
| Phone ADT | `efa8ca6254a0534ebe79c0c9a38b12d07b9a468a7bf32ed30c348511553e6101` |
| QEMU twin ADT | `5ddf0057a50d97be8fc2a08ad88e443ab3460290f6fc532f5f4dbc063562eebe` |
| Saved live FDT | `9c49589f70044127be8941a9ea5537977f440ccd5ac15cfd24e120c8a1181d29` |
| Stock `boot_a` used only as packaging metadata | `1b972f4f1c98428f2fca1e7c1c8cf463e0122a70a290e482be3230c7838e3e12` |

Both payloads use:

```text
debug=0xc serial=3 cpus=1 keepsyms=1 -enable_kprintf_spam -noprogress rootrw=0 sweet_console_fb=1
```

The phone payload SHA-256 is
`82dd86fd09fb9d858a81280813d10d753adb27e2add0da5880231a5fdc8977e9`.
The QEMU twin payload SHA-256 is
`957997e0ff86e390a9a9f163041064b28a98ecd04e4f04a9bf12c768c5802bba`.

## Actual local results

- Payload source reconstruction passed for both profiles.
- The live-FDT guard accepted ten segments in the bounded
  `0x1c0000000 + 0x20000000` window. Entry stayed at `0x1c1480488`; the
  larger kernel moved ADT to `0x1c2568000`, boot arguments to `0x1c256c000`,
  and top to `0x1c2570000`.
- The 512 MiB materializer test byte-compared every copied segment and ADT,
  verified every zero-filled tail and the complete boot-arguments page, and
  confirmed a corrupt payload writes nothing.
- Both embedded payloads byte-compare with their sources. The phone jump ELF
  has no relocations or unresolved symbols and contains the single final
  indirect branch.
- The QEMU twin traversed bootshim, materialization, handoff and XNU entry with
  the captured phone FDT and 8 GiB RAM. The framebuffer test passed with
  `356280` white XNU pixels after 20 seconds.
- The phone wrapper is a 64 MiB Android boot-v4 image using legacy LZ4 and an
  AVB hash footer with algorithm `NONE`. `avbtool verify_image` verified the
  footer, vbmeta and the boot hash. The 8,528,087-byte compressed kernel
  decompresses byte-for-byte to the phone bootshim image.

The prepared image is ignored build output at
`research/mt6897-phone-boot-v1/duchamp-xnu-latest-diagnostic.img`, SHA-256
`288672ec987ef878bc457598f8f7c760855c1bc7975ada3dc7db3f754e8abc85`.
This record is not authorization to write it to `boot_a`. The Duchamp
bootloader previously rejected RAM-only `fastboot boot`, so any hardware trial
would be a separately approved temporary boot-partition test with the verified
stock restoration path.

## Remaining physical boundary

This candidate can test the single boot CPU, GICv3, architected timer,
scheduler and framebuffer console on the phone. It cannot close the remaining
storage boundary. Enabling physical UFS still requires an installed-monitor
effect contract, secure ownership, runtime DMA ops/fwspec/domain, controller
capabilities, separate effective descriptor/data masks and cache ownership.
Until those facts are measured, the physical storage provider remains closed.
