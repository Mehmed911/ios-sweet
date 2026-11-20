# Published development baseline — 2026-11-20

This branch contains the Duchamp source, patches, tests and reports. Its status is
**BLOCKED_BY_UNKNOWN_ABI** for the original 20F66 accelerator contract and
**BLOCKED_BY_MEMORY_EVIDENCE** for the physical device. A custom Darwin GUI and
successful original-service startup are not proof of an authentic SpringBoard
frame or Mali hardware support.

The restored original-service QEMU run used source-built kernel SHA-256
`4ae22e3d38d0be2372fc66703db6b5b957803c55b743ed4190c4725a0a17cedd`,
verified against its 1127 source link inputs. Fresh results were services22/22,
IOSurface24/24, IOKit26/26, and296/296 installed hashes. New offline ABI tests
passed36/36;15 original code intervals and29 instruction anchors were rebound
to the original cache. No authentic SpringBoard frame was verified.

Start with `docs/DUCHAMP_IOACCELERATORES_ABI_V2.md`,
`docs/DUCHAMP_GRAPHICS_ABI_FIELD_MAP.md` and
`docs/DUCHAMP_QEMU_DISK_SPACE_RECOVERY.md`. The byte map under
`research/graphics-abi-20F66/selector2-field-map.json` is an authored analysis
partition, not a complete Apple ABI structure. The test sources remain in
`tools/`; cleaning generated test output does not remove those tests.

Apple binaries, extracted operating-system images, device dumps, original
firmware/recovery images, generated virtual RAM, large test roots and toolchain
build artifacts are intentionally not published. The existing build reports
describe their required sources, versions and hashes. These local inputs must
be supplied before reproducing the corresponding full-system tests; a plain
clone is not a redistributable iOS installation.

The desktop working copy retains the source-built kernel, source-link receipt,
native32+4MiB candidate, Android recovery files, original input fixtures and
test evidence. Disk cleanup is restricted to obsolete generated output after
the remote branch is verified. No physical device operation is part of this
publication or cleanup.
