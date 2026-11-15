# MT6768 loader behavior and Duchamp differences

Pinned reference `ad65e1f4b3ba479e9d7ada98f17398b83cc6f285`; exact paths and
function anchors are also stored in HAKIOS_REFERENCE_INVENTORY.json.

1. `tools/chainboot.py` accepts only Android header v2, takes the real Android
   Image, prefixes mtkloader at offset 0, Android at 0x40000 and optional XNUP
   payload aligned to 16. It fills arm64 res2/res3, gzip-compresses and rejects
   output above 32 MiB. It is not a Duchamp v4 packer.
2. `mtkloader/start.S` and `link.ld` assume 0x40080000, LK's x0 DTB, masked
   interrupts, MMU/cache state, local vectors/stack and BSS. jump_to_kernel
   enters EL1h; chain_stub relocates Android over the loader with a DTB in x0.
3. `mtkloader/mtkloader.c` builds an Apple device tree/boot_args, loads Mach-O
   and optionally reads the system from MSDC/eMMC. Its CPU ordering, RAM,
   GIC/UART, panel, touch firmware and PWRAP are this Infinix's facts.
4. `pmsg_take` consumes an Android request `DARWIN-REDWOOD:BOOT-XNU`.
   `boot_choice` defaults Android. The parser scans the whole pmsg capacity,
   not just its valid ring bytes; a Duchamp implementation must not replay
   stale bytes or ignore ring wrapping.
5. `mtkloader_main` checks retained RUNNING/DONE markers; interrupted/returned
   XNU paths save logs and chain Android. xnu_return_stub cleans caches and
   restores loader execution; watchdog/PSCI/watcher behaviors depend on this
   platform's reset/retention/cache contract.
6. `tools/boot-xnu.sh` writes /dev/pmsg0 and reboots. `tools/xnu-cycle.sh`
   automatically flashes boot_a. `tools/gpt-carve.py` and system-flash.sh modify
   storage. None is run or imported as an executable phone action here.

Duchamp adaptations preserve the existing SWEETXNU entry/packer. The new
devices/duchamp/mtkloader/boot_choice.c implements a bounded RAM-buffer policy:
Android unless access/retention/publication/recovery assertions all hold, only
live ring bytes scanned, wrapped/duplicate requests consumed before selection.
The policy has no MMIO, reset, slot, storage or firmware operation. The existing
QEMU boot-once path calls it and publishes consumed bytes with a barrier. It
uses the existing checked payload entry after a fresh model A readback. QMP
proves one real XNU entry and replay rejection after a host reset. Physical
retention and Android chainboot remain unproven.

The build.sh/build_flashed.py names are retained as offline adapters to the
existing loader. A DUCHAMP_TARGET=qemu guard is mandatory. Their container is
explicitly an emulator review artifact, not a flashable phone image. There is
no automatic A/B switch, physical return guarantee or modified Android boot path.
Physical loader integration remains blocked by retained RAM/cache publication
and Android v4/vendor_boot/recovery validation. This independent policy work
does not bypass the blocked physical-UFS phase.
