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
saved-DTB UFS interrupts at HWIRQs 200 and 209-216.

Replaying the fuller archived read-only capture also verified that the live FDT
kept the pinned critical topology, Linux reserved the exact GICD, GICR, UFS and
UFS-PHY ranges, and the installed SCMI endpoint identifies as MediaTek protocol
1.0 through `scmi-tinysys`. The UFS ancestry has no `iommus` or `iommu-map`,
Linux exposes no UFS `iommu_group`, and its supplier links contain no IOMMU.
The `/soc` `dma-ranges` property decodes to one identity window from `0x0` for
`0x1000000000` bytes (64 GiB).

The running `ufs_mediatek_mod` GNU build ID
`df7eecc22450fb6e6eceaaef4b3fe8ceb46b2a84` also matches the pinned module
extracted from the saved `vendor_boot` (SHA-256
`7043e1109b4c356a914fdc92ffbe463c0c43cb27342f6ccce1517a2086b02493`).
This links the static UFS client instruction audit to the installed client
binary identity; it is not a reproducible source-build match and does not
identify or validate the secure monitor.

This proves Android runtime delivery and a DT-described direct DMA address
window. It still does not prove physical DMA bypass, firewall permission,
coherency, or that XNU owns or can safely use those resources.

## Fail-closed readiness assessment

`tools/assess-duchamp-mt6897-phone-readiness.py` now combines the archived
live-runtime report, a fresh allowlisted read-only shell report, the captured
active `tee_a` binary inspection, its static UFS SiP-handler audit, the
read-only DMA/IOMMU ownership audit, the 12-component offline gate, the saved
UFS and firmware client audits, the contract model, the candidate manifest,
and the actual 64 MiB candidate image.
It pins the FDT, UFS module hash and GNU build ID, direct 64 GiB identity
window, interrupt identities, captured BL31 binary, candidate size and image
hash. It refuses an older runtime report that lacks the saved-module receipt
or decoded DMA window, and it requires the fail-closed UFS runtime-contract
fields from report version 2.

Seventeen mutation/guard tests pass. They reject a changed module build ID,
changed DMA window, candidate-image mismatch, captured-firmware mismatch,
changed selector path, unclean probe removal, unsafe offline action, or an
unreviewed promotion of BL31 effects, physical IOMMU bypass, resource
ownership, HCCAP, SWIOTLB transfer, coherency, or XNU DMA readiness. The actual
combined result is
`research/mt6897-phone-readiness/maxspeed-20261101-v12/result.json`, SHA-256
`7ff95f516c4d6df6240be956c58f98f91054d9731fddcc037a2d2a31abfa0ed9`:

- evidence validation and the safe offline stage pass;
- the diagnostic candidate is present and matches SHA-256
  `a83f0792ccd883c19a8225641b4e96090fb08673375e71fe93123e0dafddfaa8`;
- the sysfs capability list exposes only `clock_scaling` and `write_booster`,
  but the loaded MediaTek debug driver's bounded `/proc/ufs_debug` summary
  reports effective host capabilities `0x55c7051f`. The pinned UFSHCI masks
  decode this as 64-bit-addressing and MCQ support;
- the separately approved read-only UFS-device probe measured 64-bit streaming
  and coherent masks, a 36-bit `bus_dma_limit`, null DMA-ops pointers and no
  Linux IOMMU fwspec/domain. Pinned GKI source therefore selects generic
  `dma-direct` at observation;
- the UFS device has a SWIOTLB pool pointer and `swiotlb=noforce` remains the
  command-line policy, but no transfer was traced through the pool. Cache
  ownership and physical firewall behavior remain unverified;
- the current two-second read-only sample observed timer HWIRQ 27 advance by
  5760 and the nine DT-pinned UFS HWIRQs advance by 105 in total;
- the Android SCSI host reports `can_queue=63`, `nr_hw_queues=8`,
  `sg_tablesize=128`, and `cmd_per_lun=31`, proving that this Android build is
  using a multiqueue UFS host. The proc summary independently reports MCQ
  supported/enabled, `nr_hw_queues=8`, `nutrs=64`, and device queue depth 64;
- a 1200-line-bounded recursive UFS sysfs inventory contains no HCCAP- or
  DMA-mask-named entry. The bounded kernel-log result contains only four
  SELinux denials from a rejected `readlink` traversal; it is not a UFS
  controller failure;
- the bounded ATF log identifies installed BL31 as
  `lts-v2.8.6(release):2fbca47`, built `07:19:18, Dec 18 2024`;
- a separate read-only capture of the active `tee_a` is exactly 5 MiB,
  SHA-256 `37d7d5acbe02289465af9702cbcafb1986394332a3462badda398556d32e587d`.
  Its first `atf` entry is 953,976 bytes, SHA-256
  `716222a632e4a0623a2e467e17f1d36f38a37f79a1c026447fe724e75e90e07e`,
  and contains the same release, build and `common_2.6.1(6897-1.2)` strings;
- the captured BL31 registers `MTK_SIP_KERNEL_UFS_CONTROL` for
  `0xc2000276`. Exact instruction regions route REFCLK selector 8, MTCMOS
  selector 512 and MCQ selector 1024 to non-empty handlers. Known selectors
  share a common zero-return exit, so a zero SMC reply is explicitly not
  promoted into proof of a physical effect;
- the captured MTCMOS helpers write the secure-firmware power-unlock register
  `0x1c001000`, then control registers `0x1c001e10` and `0x1c001e14`, polling
  bits 30 and 31. These are static readback candidates, not authorization for
  XNU to access firmware-owned MMIO;
- exact public source equivalence, runtime UFS effects and secure ownership
  remain unverified;
- phone execution remains unauthorized;
- full system boot and the physical UFS backend remain not ready.

The pinned live report is
`research/mt6897-live-evidence/14480520-210535/runtime-report-v7.json`, SHA-256
`fb1fa60b1b6df4f50f7794520be959ba7997f9433cea0f23dc818df9b5681660`.
The current allowlisted shell report is
`research/mt6897-shell-runtime/live-20261101-v7/result.json`, SHA-256
`35c3f29baab1411fb6ac99cbc7fcd3a42c9fb7ebf844f97a103678c6f02a0fc4`.
The local binary reports are
`research/mt6897-firmware-live/20261101-v1/inspection.json` and
`research/mt6897-firmware-live/20261101-v1/ufs-sip-audit-v2.json`.

The upstream TF-A
[lts-v2.8.6 release](https://github.com/ARM-software/arm-trusted-firmware/releases/tag/lts-v2.8.6)
points to commit `ff0bd5f`, not the observed `2fbca47`. Exact commit lookup in
the upstream and public MediaTek mirror returned no match. The observed build
must therefore remain an unmatched vendor fork until its exact source or
installed binary is available; an upstream version label is not equivalence.

The shell collector used only fixed read commands, including a two-second,
256-KiB-bounded ATF log read. It performed no phone write, fastboot, partition
access, MMIO, or SMC. A later, separate operation read the exact active
`tee_a` block device into the local evidence directory after checking its
target and 5 MiB size; it did not write the device. Both binary inspectors and
the readiness assessment operate on local files only. A zero exit status means
the evidence is consistent, not that a phone trial is authorized.

```sh
python3 tools/assess-duchamp-mt6897-phone-readiness.py \
  research/mt6897-phone-readiness/replay-new \
  --live-report research/mt6897-live-evidence/14480520-210535/runtime-report-v7.json \
  --shell-runtime research/mt6897-shell-runtime/live-20261101-v7/result.json \
  --firmware-binary-report research/mt6897-firmware-live/20261101-v1/inspection.json \
  --firmware-sip-audit research/mt6897-firmware-live/20261101-v1/ufs-sip-audit-v2.json \
  --dma-ownership-audit research/mt6897-dma-ownership/live-20261101-v2/result.json \
  --offline-gate research/mt6897-offline-gate/maxspeed-20261031-v18/result.json \
  --saved-audit research/mt6897-contract/audit-v3/result.json \
  --client-audit research/mt6897-routing/client-audit-v1/result.json \
  --contract-model research/mt6897-contract/check-v4/result.json \
  --candidate-manifest research/mt6897-phone-boot-v2/manifest.json \
  --candidate-image research/mt6897-phone-boot-v2/duchamp-xnu-latest-diagnostic.img
```

## Remaining physical boundary

This candidate can test the single boot CPU, GICv3, architected timer,
scheduler, and framebuffer console on the phone only after a separate explicit
hardware-test decision. It cannot close the storage boundary. Enabling physical
UFS still requires a documented installed-firmware contract, secure resource
ownership, physical firewall/translation behavior, actual bounce requirements
and cache-maintenance ownership. The live masks, Linux DMA path and Linux IOMMU
state are now measured. Secondary CPU power-up and Mali acceleration are also
unverified. Until the remaining facts are measured, the physical storage
provider remains closed and this is not a phone-ready iOS build.
