# Duchamp HakiOS-style device layer

This is an additive adapter for the existing ios-sweet duchamp-bootstrap port.
It does not replace its working XNU build, bootshim, firmware contracts or driver
implementations. No MT6768/MT6833 hardware driver is renamed into this tree.

The real common-tree main schema supports a device-carried `soc/` layer, so the
device.conf/configs/soc layout is used instead of inventing a second registration
mechanism. Original checker revision:
`63fc2b4633bac3af8e57dadab9f5a8d4cb940438`.

* hardware.json: deterministic selected declarations from the pinned saved
  FDT; all runtime MMIO/resource permissions remain UNKNOWN.
* configs/ and soc/: upstream-native metadata with every foreign built-in and
  runtime hardware option disabled. This is not a new working upstream kernel.
* mtkloader/boot_choice.c: bounded one-session policy used by the guarded QEMU
  loader. Physical pmsg, slot selection and Android fallback remain unproven.
* mtkloader/build.sh: builds the canonical existing ARM64 bootshim with its
  QEMU guard. BOOT_ONCE=1 links the policy into the emulator image.
* mtkloader/build_flashed.py: retains the reference name but only packages an
  offline v4/LZ4 **QEMU-only** review image. It never flashes.

From the repository root, in WSL:

```sh
make -f devices/duchamp/Makefile hardware-check DTB=../phone-fdt.bin
make -f devices/duchamp/Makefile test OUT=out/duchamp/new-test DTB=../phone-fdt.bin
```

For the original upstream metadata check, use its pinned main worktree and link
this device under that private tree's devices/duchamp. Then run
`tools/hakios-device.py check duchamp mt6897` there. The offline test accepts
`--upstream PATH` and refuses another checker revision or device link.

To include a review container, supply an existing validated SWEETXNU payload and
an explicitly offline, empty-ramdisk Android-v4 header template:

```sh
python3 tools/test-duchamp-hakios-port.py --dtb ../phone-fdt.bin \
  --output out/duchamp/new-review --payload /path/to/payload.bin \
  --boot-template /path/to/qemu-only-header-template.img
```

Outputs include native and ARM64 test binaries/logs, the loader ELF/Image,
one-session and menu test logs/screens, optional .img and .manifest.json, and
verification.json. All outputs are local and ignored by git. Existing paths are
refused. A physical target is deliberately rejected by build.sh.

Full-kernel source build/test provenance and the exact upstream comparison are
in docs/HAKIOS_SOURCE_AUDIT.md and docs/DUCHAMP_PORT_STATUS.md. Physical UFS,
power/clock/cache ownership and Android fallback remain unproven. No tool here
invokes ADB, fastboot, partition writes or physical firmware operations.
