# HakiOS file mapping

Every tracked MT6768 and community MT6833 file is listed, including unported files. An empty destination means no equivalent was invented. See reference-inventory.json for hashes, includes, critical line anchors and scan scope.

## mt6768: `ad65e1f4b3ba479e9d7ada98f17398b83cc6f285` (80 files)

| Exact source path | Existing/new Duchamp counterpart | Action |
| --- | --- | --- |
| `.gitignore` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `AGENTS.md` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `LEGAL.md` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `LICENSE` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `LICENSE.APSL` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `NOTICE` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `README.md` | `docs/HAKIOS_SOURCE_AUDIT.md` | Reference claims compared with actual source; no claim of device validation |
| `README.ru.md` | `docs/HAKIOS_SOURCE_AUDIT.md` | Reference claims compared with actual source; no claim of device validation |
| `configs/x6826b.config` | `devices/duchamp/configs/duchamp_defconfig`, `devices/duchamp/soc/configs/mt6897.config` | Adapt schema; disable foreign hardware and runtime flags |
| `configs/x6826b_defconfig` | `devices/duchamp/configs/duchamp_defconfig`, `devices/duchamp/soc/configs/mt6897.config` | Adapt schema; disable foreign hardware and runtime flags |
| `device.conf` | `devices/duchamp/device.conf` | Adapt metadata; physical claims are not inherited |
| `docs/bluetooth-mtk-porting.md` | `docs/HAKIOS_SOURCE_AUDIT.md` | Reference claims compared with actual source; no claim of device validation |
| `docs/bluetooth-x6826b.md` | `docs/HAKIOS_SOURCE_AUDIT.md` | Reference claims compared with actual source; no claim of device validation |
| `docs/camera-x6826b.md` | `docs/HAKIOS_SOURCE_AUDIT.md` | Reference claims compared with actual source; no claim of device validation |
| `docs/metal-x6826b-plan.md` | `docs/HAKIOS_SOURCE_AUDIT.md` | Reference claims compared with actual source; no claim of device validation |
| `docs/sensors-x6826b.md` | `docs/HAKIOS_SOURCE_AUDIT.md` | Reference claims compared with actual source; no claim of device validation |
| `docs/wifi-x6826b.md` | `docs/HAKIOS_SOURCE_AUDIT.md` | Reference claims compared with actual source; no claim of device validation |
| `docs/x6826b-emmc.md` | `duchamp/drivers/ufs_readonly.c`, `duchamp/drivers/ufs_register_snapshot.c`, `duchamp/xnu/qemu_ufs.c` | Compare concepts only; MT6833 reader is incomplete, MSDC/eMMC and Qualcomm initialization are incompatible |
| `docs/x6826b-wallpaper.md` | `docs/HAKIOS_SOURCE_AUDIT.md` | Reference claims compared with actual source; no claim of device validation |
| `kernel/README.md` | `docs/HAKIOS_SOURCE_AUDIT.md` | Reference claims compared with actual source; no claim of device validation |
| `kernel/bsd/dev/redwood_btsk.c` | None (not ported) | Review dependencies only; hardware/runtime port deferred until UFS and recovery validation |
| `kernel/bsd/dev/redwood_connsys.c` | None (not ported) | Review dependencies only; hardware/runtime port deferred until UFS and recovery validation |
| `kernel/bsd/dev/redwood_emmc.c` | `duchamp/drivers/ufs_readonly.c`, `duchamp/drivers/ufs_register_snapshot.c`, `duchamp/xnu/qemu_ufs.c` | Compare concepts only; MT6833 reader is incomplete, MSDC/eMMC and Qualcomm initialization are incompatible |
| `kernel/bsd/dev/redwood_mali.c` | None (not ported) | Review dependencies only; hardware/runtime port deferred until UFS and recovery validation |
| `kernel/bsd/dev/redwood_mtkbt_skel.c` | None (not ported) | Review dependencies only; hardware/runtime port deferred until UFS and recovery validation |
| `kernel/bsd/dev/redwood_mtkcam.c` | None (not ported) | Review dependencies only; hardware/runtime port deferred until UFS and recovery validation |
| `kernel/bsd/dev/redwood_mtkkeys.c` | None (not ported) | Review dependencies only; hardware/runtime port deferred until UFS and recovery validation |
| `kernel/bsd/dev/redwood_mtkwifi.c` | None (not ported) | Review dependencies only; hardware/runtime port deferred until UFS and recovery validation |
| `kernel/bsd/dev/redwood_scp.c` | None (not ported) | Review dependencies only; hardware/runtime port deferred until UFS and recovery validation |
| `kernel/bsd/dev/redwood_tcm.c` | None (not ported) | Review dependencies only; hardware/runtime port deferred until UFS and recovery validation |
| `kernel/bsd/dev/redwood_wpa.c` | None (not ported) | Review dependencies only; hardware/runtime port deferred until UFS and recovery validation |
| `kernel/bsd/sys/redwood_camera.h` | None (not ported) | Review dependencies only; hardware/runtime port deferred until UFS and recovery validation |
| `kernel/bsd/sys/redwood_emmc.h` | `duchamp/drivers/ufs_readonly.c`, `duchamp/drivers/ufs_register_snapshot.c`, `duchamp/xnu/qemu_ufs.c` | Compare concepts only; MT6833 reader is incomplete, MSDC/eMMC and Qualcomm initialization are incompatible |
| `kernel/bsd/sys/redwood_wpa.h` | None (not ported) | Review dependencies only; hardware/runtime port deferred until UFS and recovery validation |
| `kernel/iokit/Kernel/RedwoodBluetooth.cpp` | None (not ported) | Review dependencies only; hardware/runtime port deferred until UFS and recovery validation |
| `kernel/iokit/Kernel/RedwoodMali.cpp` | None (not ported) | Review dependencies only; hardware/runtime port deferred until UFS and recovery validation |
| `kernel/patches/redwood_pwrap_lock.patch` | None (not ported) | Review dependencies only; hardware/runtime port deferred until UFS and recovery validation |
| `mtkloader/build.sh` | `devices/duchamp/mtkloader/build.sh` | Preserve existing SWEETXNU/EL/memory gates; physical Android v4 chainboot remains unproven |
| `mtkloader/build_fbdiag.sh` | None (not ported) | Hardware-specific helper or diagnostic: dependency-scanned; no renamed/cross-SoC copy |
| `mtkloader/build_flashed.py` | `devices/duchamp/mtkloader/build_flashed.py` | Preserve existing SWEETXNU/EL/memory gates; physical Android v4 chainboot remains unproven |
| `mtkloader/diag.c` | None (not ported) | Hardware-specific helper or diagnostic: dependency-scanned; no renamed/cross-SoC copy |
| `mtkloader/diag_start.S` | None (not ported) | Hardware-specific helper or diagnostic: dependency-scanned; no renamed/cross-SoC copy |
| `mtkloader/fbdiag.c` | None (not ported) | Hardware-specific helper or diagnostic: dependency-scanned; no renamed/cross-SoC copy |
| `mtkloader/fbdiag_start.S` | None (not ported) | Hardware-specific helper or diagnostic: dependency-scanned; no renamed/cross-SoC copy |
| `mtkloader/link.ld` | `duchamp/bootshim/shim.ld` | Preserve existing SWEETXNU/EL/memory gates; physical Android v4 chainboot remains unproven |
| `mtkloader/loop.S` | None (not ported) | Hardware-specific helper or diagnostic: dependency-scanned; no renamed/cross-SoC copy |
| `mtkloader/msdc.h` | `duchamp/drivers/ufs_readonly.c`, `duchamp/drivers/ufs_register_snapshot.c`, `duchamp/xnu/qemu_ufs.c` | Compare concepts only; MT6833 reader is incomplete, MSDC/eMMC and Qualcomm initialization are incompatible |
| `mtkloader/mtkcam.h` | None (not ported) | Hardware-specific helper or diagnostic: dependency-scanned; no renamed/cross-SoC copy |
| `mtkloader/mtkconnsys.h` | None (not ported) | Hardware-specific helper or diagnostic: dependency-scanned; no renamed/cross-SoC copy |
| `mtkloader/mtkdbg.h` | None (not ported) | Hardware-specific helper or diagnostic: dependency-scanned; no renamed/cross-SoC copy |
| `mtkloader/mtkloader.c` | `duchamp/bootshim/shim.c` | Preserve existing SWEETXNU/EL/memory gates; physical Android v4 chainboot remains unproven |
| `mtkloader/mtkmali.h` | None (not ported) | Hardware-specific helper or diagnostic: dependency-scanned; no renamed/cross-SoC copy |
| `mtkloader/mtkpwrap.h` | None (not ported) | Hardware-specific helper or diagnostic: dependency-scanned; no renamed/cross-SoC copy |
| `mtkloader/mtkspi.h` | None (not ported) | Hardware-specific helper or diagnostic: dependency-scanned; no renamed/cross-SoC copy |
| `mtkloader/start.S` | `duchamp/bootshim/start.S` | Preserve existing SWEETXNU/EL/memory gates; physical Android v4 chainboot remains unproven |
| `mtkloader/tcm.h` | None (not ported) | Hardware-specific helper or diagnostic: dependency-scanned; no renamed/cross-SoC copy |
| `pull-firmware.sh` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/boot-xnu.sh` | None (not ported) | Not imported: executes partition/slot/reboot operations prohibited in this task |
| `tools/cache-name.py` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/cam-probe.sh` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/camrx.py` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/camtable.py` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/camthumb.py` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/chainboot.py` | `duchamp/bootshim/pack_boot.py` | Header-v2/gzip/32-MiB packer cannot replace Duchamp v4/LZ4/64-MiB packaging; no Android chainboot equivalence |
| `tools/fbshot.py` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/frames.py` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/gpt-carve.py` | None (not ported) | Not imported: executes partition/slot/reboot operations prohibited in this task |
| `tools/gpu-probe.sh` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/mkfont8x16.swift` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/mktouchfw.py` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/msdc-test.sh` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/rwm-recipes.py` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/system-flash.sh` | None (not ported) | Not imported: executes partition/slot/reboot operations prohibited in this task |
| `tools/touch-probe.sh` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/xl` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/xnu-cycle.sh` | None (not ported) | Not imported: executes partition/slot/reboot operations prohibited in this task |
| `userland/camera/README.md` | `docs/HAKIOS_SOURCE_AUDIT.md` | Reference claims compared with actual source; no claim of device validation |
| `userland/camera/camera_device.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/camera/camera_isp.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/camera/camera_isp.h` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |

## mt6833: `c24467f3074d9bfbd7cb92e2d20beacd91e468b5` (690 files)

| Exact source path | Existing/new Duchamp counterpart | Action |
| --- | --- | --- |
| `.gitattributes` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `.gitignore` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `CHANGELOG.md` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `COMMUNITY.md` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `COMPLIANCE.md` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `CONTRIBUTING.md` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `LEGAL.md` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `LICENSE` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `LICENSE.APSL` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `Makefile` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `NOTICE` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `README.md` | `docs/HAKIOS_SOURCE_AUDIT.md` | Reference claims compared with actual source; no claim of device validation |
| `README.uk.md` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `README.zh.md` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `THIRD_PARTY_LICENSES.md` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `VERSION` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `ci/github-check.yml` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `configs/boot-args.lst` | `devices/duchamp/configs/duchamp_defconfig`, `devices/duchamp/soc/configs/mt6897.config` | Adapt schema; disable foreign hardware and runtime flags |
| `configs/common_defconfig` | `devices/duchamp/configs/duchamp_defconfig`, `devices/duchamp/soc/configs/mt6897.config` | Adapt schema; disable foreign hardware and runtime flags |
| `configs/defconfig` | `devices/duchamp/configs/duchamp_defconfig`, `devices/duchamp/soc/configs/mt6897.config` | Adapt schema; disable foreign hardware and runtime flags |
| `configs/open.config` | `devices/duchamp/configs/duchamp_defconfig`, `devices/duchamp/soc/configs/mt6897.config` | Adapt schema; disable foreign hardware and runtime flags |
| `configs/persist.config` | `devices/duchamp/configs/duchamp_defconfig`, `devices/duchamp/soc/configs/mt6897.config` | Adapt schema; disable foreign hardware and runtime flags |
| `configs/symbols.tsv` | `devices/duchamp/configs/duchamp_defconfig`, `devices/duchamp/soc/configs/mt6897.config` | Adapt schema; disable foreign hardware and runtime flags |
| `configs/trace.config` | `devices/duchamp/configs/duchamp_defconfig`, `devices/duchamp/soc/configs/mt6897.config` | Adapt schema; disable foreign hardware and runtime flags |
| `configs/virt.config` | `devices/duchamp/configs/duchamp_defconfig`, `devices/duchamp/soc/configs/mt6897.config` | Adapt schema; disable foreign hardware and runtime flags |
| `devices/README.md` | `docs/HAKIOS_SOURCE_AUDIT.md` | Reference claims compared with actual source; no claim of device validation |
| `devices/light/boot.log` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `devices/light/configs/light.config` | `devices/duchamp/configs/duchamp_defconfig`, `devices/duchamp/soc/configs/mt6897.config` | Adapt schema; disable foreign hardware and runtime flags |
| `devices/light/configs/light_defconfig` | `devices/duchamp/configs/duchamp_defconfig`, `devices/duchamp/soc/configs/mt6897.config` | Adapt schema; disable foreign hardware and runtime flags |
| `devices/light/device.conf` | `devices/duchamp/device.conf` | Adapt metadata; physical claims are not inherited |
| `devices/light/hardware_specs.md` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `devices/light/plan.md` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `devices/light/poco_m4_5g.dtb` | `devices/duchamp/hardware.json` | Reject foreign hardware data; derive facts from pinned Duchamp FDT |
| `devices/light/poco_m4_5g.dts` | `devices/duchamp/hardware.json` | Reject foreign hardware data; derive facts from pinned Duchamp FDT |
| `devices/light/poco_m4_5g_dtbo.dtb` | `devices/duchamp/hardware.json` | Reject foreign hardware data; derive facts from pinned Duchamp FDT |
| `devices/light/poco_m4_5g_dtbo.dts` | `devices/duchamp/hardware.json` | Reject foreign hardware data; derive facts from pinned Duchamp FDT |
| `devices/light/roadmap.md` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `devices/manifest.conf` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `devices/qemu/configs/qemu_defconfig` | `devices/duchamp/configs/duchamp_defconfig`, `devices/duchamp/soc/configs/mt6897.config` | Adapt schema; disable foreign hardware and runtime flags |
| `devices/qemu/device.conf` | `devices/duchamp/device.conf` | Adapt metadata; physical claims are not inherited |
| `devices/qemu/u-boot/files/configs/hakios_qemu_defconfig` | `devices/duchamp/configs/duchamp_defconfig`, `devices/duchamp/soc/configs/mt6897.config` | Adapt schema; disable foreign hardware and runtime flags |
| `docs/air-report.md` | `docs/HAKIOS_SOURCE_AUDIT.md` | Reference claims compared with actual source; no claim of device validation |
| `docs/air.md` | `docs/HAKIOS_SOURCE_AUDIT.md` | Reference claims compared with actual source; no claim of device validation |
| `docs/boot-args.md` | `docs/HAKIOS_SOURCE_AUDIT.md` | Reference claims compared with actual source; no claim of device validation |
| `docs/cellular.md` | `docs/HAKIOS_SOURCE_AUDIT.md` | Reference claims compared with actual source; no claim of device validation |
| `docs/comparison.md` | `docs/HAKIOS_SOURCE_AUDIT.md` | Reference claims compared with actual source; no claim of device validation |
| `docs/concepts/architecture.md` | `docs/HAKIOS_SOURCE_AUDIT.md` | Reference claims compared with actual source; no claim of device validation |
| `docs/configs.md` | `docs/HAKIOS_SOURCE_AUDIT.md` | Reference claims compared with actual source; no claim of device validation |
| `docs/devices/index.md` | `docs/HAKIOS_SOURCE_AUDIT.md` | Reference claims compared with actual source; no claim of device validation |
| `docs/devices/qemu.md` | `docs/HAKIOS_SOURCE_AUDIT.md` | Reference claims compared with actual source; no claim of device validation |
| `docs/devices/redwood.md` | `docs/HAKIOS_SOURCE_AUDIT.md` | Reference claims compared with actual source; no claim of device validation |
| `docs/devices/x6826b.md` | `docs/HAKIOS_SOURCE_AUDIT.md` | Reference claims compared with actual source; no claim of device validation |
| `docs/driver-review/README.md` | `docs/HAKIOS_SOURCE_AUDIT.md` | Reference claims compared with actual source; no claim of device validation |
| `docs/driver-review/adsp-battery-cpufreq.md` | `docs/HAKIOS_SOURCE_AUDIT.md` | Reference claims compared with actual source; no claim of device validation |
| `docs/driver-review/camera-haptic-torch.md` | `docs/HAKIOS_SOURCE_AUDIT.md` | Reference claims compared with actual source; no claim of device validation |
| `docs/driver-review/gpu-display.md` | `docs/HAKIOS_SOURCE_AUDIT.md` | Reference claims compared with actual source; no claim of device validation |
| `docs/driver-review/input.md` | `docs/HAKIOS_SOURCE_AUDIT.md` | Reference claims compared with actual source; no claim of device validation |
| `docs/driver-review/loader.md` | `docs/HAKIOS_SOURCE_AUDIT.md` | Reference claims compared with actual source; no claim of device validation |
| `docs/driver-review/policy-glue.md` | `docs/HAKIOS_SOURCE_AUDIT.md` | Reference claims compared with actual source; no claim of device validation |
| `docs/driver-review/sound.md` | `docs/HAKIOS_SOURCE_AUDIT.md` | Reference claims compared with actual source; no claim of device validation |
| `docs/driver-review/storage.md` | `docs/HAKIOS_SOURCE_AUDIT.md` | Reference claims compared with actual source; no claim of device validation |
| `docs/driver-review/wifi-bringup.md` | `docs/HAKIOS_SOURCE_AUDIT.md` | Reference claims compared with actual source; no claim of device validation |
| `docs/driver-review/wifi-stack.md` | `docs/HAKIOS_SOURCE_AUDIT.md` | Reference claims compared with actual source; no claim of device validation |
| `docs/drivers-config.md` | `docs/HAKIOS_SOURCE_AUDIT.md` | Reference claims compared with actual source; no claim of device validation |
| `docs/dual-boot.md` | `docs/HAKIOS_SOURCE_AUDIT.md` | Reference claims compared with actual source; no claim of device validation |
| `docs/getting-started/building.md` | `docs/HAKIOS_SOURCE_AUDIT.md` | Reference claims compared with actual source; no claim of device validation |
| `docs/getting-started/index.md` | `docs/HAKIOS_SOURCE_AUDIT.md` | Reference claims compared with actual source; no claim of device validation |
| `docs/getting-started/phone.md` | `docs/HAKIOS_SOURCE_AUDIT.md` | Reference claims compared with actual source; no claim of device validation |
| `docs/getting-started/qemu.md` | `docs/HAKIOS_SOURCE_AUDIT.md` | Reference claims compared with actual source; no claim of device validation |
| `docs/index.md` | `docs/HAKIOS_SOURCE_AUDIT.md` | Reference claims compared with actual source; no claim of device validation |
| `docs/install-safe.md` | `docs/HAKIOS_SOURCE_AUDIT.md` | Reference claims compared with actual source; no claim of device validation |
| `docs/install.md` | `docs/HAKIOS_SOURCE_AUDIT.md` | Reference claims compared with actual source; no claim of device validation |
| `docs/legal-review.md` | `docs/HAKIOS_SOURCE_AUDIT.md` | Reference claims compared with actual source; no claim of device validation |
| `docs/metal-plan.md` | `docs/HAKIOS_SOURCE_AUDIT.md` | Reference claims compared with actual source; no claim of device validation |
| `docs/net-review.md` | `docs/HAKIOS_SOURCE_AUDIT.md` | Reference claims compared with actual source; no claim of device validation |
| `docs/port-pkg110.md` | `docs/HAKIOS_SOURCE_AUDIT.md` | Reference claims compared with actual source; no claim of device validation |
| `docs/porting/drivers.md` | `docs/HAKIOS_SOURCE_AUDIT.md` | Reference claims compared with actual source; no claim of device validation |
| `docs/porting/index.md` | `docs/HAKIOS_SOURCE_AUDIT.md` | Reference claims compared with actual source; no claim of device validation |
| `docs/porting/repositories.md` | `docs/HAKIOS_SOURCE_AUDIT.md` | Reference claims compared with actual source; no claim of device validation |
| `docs/reference/drivers.md` | `docs/HAKIOS_SOURCE_AUDIT.md` | Reference claims compared with actual source; no claim of device validation |
| `docs/reference/tools.md` | `docs/HAKIOS_SOURCE_AUDIT.md` | Reference claims compared with actual source; no claim of device validation |
| `docs/ru/cellular.md` | `docs/HAKIOS_SOURCE_AUDIT.md` | Reference claims compared with actual source; no claim of device validation |
| `docs/ru/dual-boot.md` | `docs/HAKIOS_SOURCE_AUDIT.md` | Reference claims compared with actual source; no claim of device validation |
| `docs/ru/metal.md` | `docs/HAKIOS_SOURCE_AUDIT.md` | Reference claims compared with actual source; no claim of device validation |
| `docs/ru/notes.md` | `docs/HAKIOS_SOURCE_AUDIT.md` | Reference claims compared with actual source; no claim of device validation |
| `docs/site/README.md` | `docs/HAKIOS_SOURCE_AUDIT.md` | Reference claims compared with actual source; no claim of device validation |
| `docs/site/index.html` | `docs/HAKIOS_SOURCE_AUDIT.md` | Reference claims compared with actual source; no claim of device validation |
| `docs/u-boot.md` | `docs/HAKIOS_SOURCE_AUDIT.md` | Reference claims compared with actual source; no claim of device validation |
| `docs/uefi-boot.md` | `docs/HAKIOS_SOURCE_AUDIT.md` | Reference claims compared with actual source; no claim of device validation |
| `docs/versioning.md` | `docs/HAKIOS_SOURCE_AUDIT.md` | Reference claims compared with actual source; no claim of device validation |
| `docs/windows.md` | `docs/HAKIOS_SOURCE_AUDIT.md` | Reference claims compared with actual source; no claim of device validation |
| `drivers/README.md` | `docs/HAKIOS_SOURCE_AUDIT.md` | Reference claims compared with actual source; no claim of device validation |
| `drivers/audio/conf` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `drivers/audio/hakios.adsp.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `drivers/audio/hakios.audio.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `drivers/audio/hakios.guard.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `drivers/audio/hakios.mic.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `drivers/audio/hakios.sound.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `drivers/audio/hakios.speaker.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `drivers/audio/hakios.virtio_sound.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `drivers/bluetooth/conf` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `drivers/bluetooth/hakios.bt.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `drivers/camera/conf` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `drivers/camera/hakios.camera.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `drivers/camera/hakios.torch.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `drivers/core/conf` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `drivers/core/hakios.platform.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `drivers/core/hakios.socinfo.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `drivers/core/hakios.stubs.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `drivers/core/hakios.stubs.cpp` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `drivers/core/hakios.version.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `drivers/gpu/conf` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `drivers/gpu/hakios.adreno.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `drivers/gpu/hakios.gpu.cpp` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `drivers/haptic/conf` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `drivers/haptic/hakios.haptic.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `drivers/input/conf` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `drivers/input/hakios.buttons.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `drivers/input/hakios.focaltech_fw.h` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `drivers/input/hakios.goodix.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `drivers/input/hakios.input.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `drivers/input/hakios.virtio_input.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `drivers/map` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `drivers/modem/conf` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `drivers/modem/hakios.cell.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `drivers/modem/hakios.ipa.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `drivers/modem/hakios.mpss.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `drivers/modem/hakios.nas.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `drivers/modem/hakios.qmi.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `drivers/net/conf` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `drivers/net/hakios.net.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `drivers/net/hakios.virtio_net.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `drivers/power/conf` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `drivers/power/hakios.battery.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `drivers/power/hakios.battery.cpp` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `drivers/power/hakios.battguard.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `drivers/power/hakios.cpufreq.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `drivers/power/hakios.pmic.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `drivers/power/hakios.thermal.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `drivers/storage/conf` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `drivers/storage/hakios.apfs_check.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `drivers/storage/hakios.image.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `drivers/storage/hakios.sparse.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `drivers/storage/hakios.ufs.c` | `duchamp/drivers/ufs_readonly.c`, `duchamp/drivers/ufs_register_snapshot.c`, `duchamp/xnu/qemu_ufs.c` | Compare concepts only; MT6833 reader is incomplete, MSDC/eMMC and Qualcomm initialization are incompatible |
| `drivers/storage/hakios.ufshc.c` | `duchamp/drivers/ufs_readonly.c`, `duchamp/drivers/ufs_register_snapshot.c`, `duchamp/xnu/qemu_ufs.c` | Compare concepts only; MT6833 reader is incomplete, MSDC/eMMC and Qualcomm initialization are incompatible |
| `drivers/storage/hakios.ufshc.h` | `duchamp/drivers/ufs_readonly.c`, `duchamp/drivers/ufs_register_snapshot.c`, `duchamp/xnu/qemu_ufs.c` | Compare concepts only; MT6833 reader is incomplete, MSDC/eMMC and Qualcomm initialization are incompatible |
| `drivers/storage/hakios.virtio_blk.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `drivers/wifi/conf` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `drivers/wifi/hakios.apple80211.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `drivers/wifi/hakios.lx.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `drivers/wifi/hakios.sta.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `drivers/wifi/hakios.wifi.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `drivers/wifi/hakios.wlan.cpp` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `drivers/wifi/hakios.wlfw.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `mkxnuimg.py` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `mtk/.gitignore` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `mtk/README.md` | `docs/HAKIOS_SOURCE_AUDIT.md` | Reference claims compared with actual source; no claim of device validation |
| `mtk/loader/build.sh` | `devices/duchamp/mtkloader/build.sh` | Preserve existing SWEETXNU/EL/memory gates; physical Android v4 chainboot remains unproven |
| `mtk/loader/build_fbdiag.sh` | None (not ported) | Hardware-specific helper or diagnostic: dependency-scanned; no renamed/cross-SoC copy |
| `mtk/loader/build_flashed.py` | `devices/duchamp/mtkloader/build_flashed.py` | Preserve existing SWEETXNU/EL/memory gates; physical Android v4 chainboot remains unproven |
| `mtk/loader/diag.c` | None (not ported) | Hardware-specific helper or diagnostic: dependency-scanned; no renamed/cross-SoC copy |
| `mtk/loader/diag_start.S` | None (not ported) | Hardware-specific helper or diagnostic: dependency-scanned; no renamed/cross-SoC copy |
| `mtk/loader/fbdiag.c` | None (not ported) | Hardware-specific helper or diagnostic: dependency-scanned; no renamed/cross-SoC copy |
| `mtk/loader/fbdiag_start.S` | None (not ported) | Hardware-specific helper or diagnostic: dependency-scanned; no renamed/cross-SoC copy |
| `mtk/loader/link.ld` | `duchamp/bootshim/shim.ld` | Preserve existing SWEETXNU/EL/memory gates; physical Android v4 chainboot remains unproven |
| `mtk/loader/loop.S` | None (not ported) | Hardware-specific helper or diagnostic: dependency-scanned; no renamed/cross-SoC copy |
| `mtk/loader/msdc.h` | `duchamp/drivers/ufs_readonly.c`, `duchamp/drivers/ufs_register_snapshot.c`, `duchamp/xnu/qemu_ufs.c` | Compare concepts only; MT6833 reader is incomplete, MSDC/eMMC and Qualcomm initialization are incompatible |
| `mtk/loader/mtkconnsys.h` | None (not ported) | Hardware-specific helper or diagnostic: dependency-scanned; no renamed/cross-SoC copy |
| `mtk/loader/mtkdbg.h` | None (not ported) | Hardware-specific helper or diagnostic: dependency-scanned; no renamed/cross-SoC copy |
| `mtk/loader/mtkloader.c` | `duchamp/bootshim/shim.c` | Preserve existing SWEETXNU/EL/memory gates; physical Android v4 chainboot remains unproven |
| `mtk/loader/mtkmali.h` | None (not ported) | Hardware-specific helper or diagnostic: dependency-scanned; no renamed/cross-SoC copy |
| `mtk/loader/mtkpwrap.h` | None (not ported) | Hardware-specific helper or diagnostic: dependency-scanned; no renamed/cross-SoC copy |
| `mtk/loader/mtkspi.h` | None (not ported) | Hardware-specific helper or diagnostic: dependency-scanned; no renamed/cross-SoC copy |
| `mtk/loader/start.S` | `duchamp/bootshim/start.S` | Preserve existing SWEETXNU/EL/memory gates; physical Android v4 chainboot remains unproven |
| `mtk/loader/tcm.h` | None (not ported) | Hardware-specific helper or diagnostic: dependency-scanned; no renamed/cross-SoC copy |
| `mtk/mt6768/configs/mt6768.config` | `devices/duchamp/configs/duchamp_defconfig`, `devices/duchamp/soc/configs/mt6897.config` | Adapt schema; disable foreign hardware and runtime flags |
| `mtk/mt6768/drivers/gpu/conf` | None (not ported) | Review dependencies only; hardware/runtime port deferred until UFS and recovery validation |
| `mtk/mt6768/drivers/gpu/hakios.mali.c` | None (not ported) | Review dependencies only; hardware/runtime port deferred until UFS and recovery validation |
| `mtk/mt6768/drivers/gpu/hakios.mali.cpp` | None (not ported) | Review dependencies only; hardware/runtime port deferred until UFS and recovery validation |
| `mtk/mt6768/drivers/input/conf` | None (not ported) | Review dependencies only; hardware/runtime port deferred until UFS and recovery validation |
| `mtk/mt6768/drivers/input/hakios.mtk_keys.c` | None (not ported) | Review dependencies only; hardware/runtime port deferred until UFS and recovery validation |
| `mtk/mt6768/drivers/input/hakios.mtk_scp.c` | None (not ported) | Review dependencies only; hardware/runtime port deferred until UFS and recovery validation |
| `mtk/mt6768/drivers/input/hakios.tcm.c` | None (not ported) | Review dependencies only; hardware/runtime port deferred until UFS and recovery validation |
| `mtk/mt6768/drivers/storage/conf` | None (not ported) | Review dependencies only; hardware/runtime port deferred until UFS and recovery validation |
| `mtk/mt6768/drivers/storage/hakios.mtk_emmc.c` | `duchamp/drivers/ufs_readonly.c`, `duchamp/drivers/ufs_register_snapshot.c`, `duchamp/xnu/qemu_ufs.c` | Compare concepts only; MT6833 reader is incomplete, MSDC/eMMC and Qualcomm initialization are incompatible |
| `mtk/mt6768/drivers/wifi/conf` | None (not ported) | Review dependencies only; hardware/runtime port deferred until UFS and recovery validation |
| `mtk/mt6768/drivers/wifi/hakios.mtk_connsys.c` | None (not ported) | Review dependencies only; hardware/runtime port deferred until UFS and recovery validation |
| `mtk/mt6768/soc.conf` | `devices/duchamp/soc/soc.conf` | Use MT6897 facts, not MT6833 core/GPU descriptions |
| `mtk/mt6833/configs/mt6833.config` | `devices/duchamp/configs/duchamp_defconfig`, `devices/duchamp/soc/configs/mt6897.config` | Adapt schema; disable foreign hardware and runtime flags |
| `mtk/mt6833/drivers/audio/conf` | None (not ported) | Review dependencies only; hardware/runtime port deferred until UFS and recovery validation |
| `mtk/mt6833/drivers/audio/hakios.mt6833_audio.c` | None (not ported) | Review dependencies only; hardware/runtime port deferred until UFS and recovery validation |
| `mtk/mt6833/drivers/cellular/conf` | None (not ported) | Review dependencies only; hardware/runtime port deferred until UFS and recovery validation |
| `mtk/mt6833/drivers/cellular/hakios.mt6833_ccci.c` | None (not ported) | Review dependencies only; hardware/runtime port deferred until UFS and recovery validation |
| `mtk/mt6833/drivers/gpu/conf` | None (not ported) | Review dependencies only; hardware/runtime port deferred until UFS and recovery validation |
| `mtk/mt6833/drivers/gpu/hakios.mt6833_mali.c` | None (not ported) | Review dependencies only; hardware/runtime port deferred until UFS and recovery validation |
| `mtk/mt6833/drivers/input/conf` | None (not ported) | Review dependencies only; hardware/runtime port deferred until UFS and recovery validation |
| `mtk/mt6833/drivers/input/hakios.mt6833_keys.c` | None (not ported) | Review dependencies only; hardware/runtime port deferred until UFS and recovery validation |
| `mtk/mt6833/drivers/input/hakios.mt6833_touch.c` | None (not ported) | Review dependencies only; hardware/runtime port deferred until UFS and recovery validation |
| `mtk/mt6833/drivers/storage/conf` | None (not ported) | Review dependencies only; hardware/runtime port deferred until UFS and recovery validation |
| `mtk/mt6833/drivers/storage/hakios.mt6833_ufs.c` | `duchamp/drivers/ufs_readonly.c`, `duchamp/drivers/ufs_register_snapshot.c`, `duchamp/xnu/qemu_ufs.c` | Compare concepts only; MT6833 reader is incomplete, MSDC/eMMC and Qualcomm initialization are incompatible |
| `mtk/mt6833/drivers/wifi/conf` | None (not ported) | Review dependencies only; hardware/runtime port deferred until UFS and recovery validation |
| `mtk/mt6833/drivers/wifi/hakios.mt6833_connsys.c` | None (not ported) | Review dependencies only; hardware/runtime port deferred until UFS and recovery validation |
| `mtk/mt6833/soc.conf` | `devices/duchamp/soc/soc.conf` | Use MT6897 facts, not MT6833 core/GPU descriptions |
| `mtk/tools/boot-xnu.sh` | None (not ported) | Not imported: executes partition/slot/reboot operations prohibited in this task |
| `mtk/tools/cache-name.py` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `mtk/tools/chainboot.py` | `duchamp/bootshim/pack_boot.py` | Header-v2/gzip/32-MiB packer cannot replace Duchamp v4/LZ4/64-MiB packaging; no Android chainboot equivalence |
| `mtk/tools/fbshot.py` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `mtk/tools/frames.py` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `mtk/tools/gpt-carve.py` | None (not ported) | Not imported: executes partition/slot/reboot operations prohibited in this task |
| `mtk/tools/gpu-probe.sh` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `mtk/tools/mkfont8x16.swift` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `mtk/tools/mktouchfw.py` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `mtk/tools/msdc-test.sh` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `mtk/tools/rwm-recipes.py` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `mtk/tools/system-flash.sh` | None (not ported) | Not imported: executes partition/slot/reboot operations prohibited in this task |
| `mtk/tools/touch-probe.sh` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `mtk/tools/xnu-cycle.sh` | None (not ported) | Not imported: executes partition/slot/reboot operations prohibited in this task |
| `prebuilt/SHA256SUMS` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `prebuilt/hakios-kernel` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `prebuilt/loader.efi` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `prebuilt/userland/HakiosAudio` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `prebuilt/userland/child` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `prebuilt/userland/cpu_test` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `prebuilt/userland/hello` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `prebuilt/userland/hello_dyn` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `prebuilt/userland/init` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `prebuilt/userland/libhakios.app.dylib` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `prebuilt/userland/libhakios.dylib` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `prebuilt/userland/libhakios.media.dylib` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `prebuilt/userland/libhakios.sb.dylib` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `prebuilt/userland/libhakios.tweaks.dylib` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `prebuilt/userland/mg_test` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `prebuilt/userland/net_test` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `prebuilt/userland/rwtouch` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `prebuilt/userland/sound_test` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `prebuilt/userland/stage0` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `prebuilt/userland/surf_test` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `prebuilt/userland/svc_test` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `qemu/daemonlog.sh` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `qemu/run-darwin.sh` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `qemu/run-hfs-test.sh` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `qemu/run-u-boot.sh` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `qemu/run.sh` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `qemu/screendump.sh` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `qemu/stop.sh` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `qemu/sym.py` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `qemu/symstack.py` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `qemu/touch.py` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `qemu/where.py` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `socs/README.md` | `docs/HAKIOS_SOURCE_AUDIT.md` | Reference claims compared with actual source; no claim of device validation |
| `sysimage/ipsw-member.py` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `sysimage/mkvarskel.py` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `sysimage/select-system.py` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `sysimage/unpack.sh` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/air/atomiccheck.py` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/air/check.sh` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/air/corpus.py` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/air/cpuref.py` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/air/intrincheck.py` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/air/kernelcheck.py` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/air/libcheck.py` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/air/mk-host.sh` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/air/reader-check.sh` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/air/texcheck.sh` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/air/texopcheck.py` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/android/build.sh` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/android/f2fs-resize.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/apfs/apfs-tool.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/apfs/apfs.py` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/apfs/bench-phone.sh` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/apfs/bench-qemu.sh` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/apfs/build-tool.sh` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/apfs/check-image.py` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/apfs/check-image.sh` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/apfs/dmg.py` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/apfs/fmt_check.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/apfs/fnvsum.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/apfs/host-shim/x86/adler32_impl.h` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/apfs/host-shim/x86/decompress_impl.h` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/apfs/mkapfs.py` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/apfs/mksparse.py` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/apfs/mkstore.py` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/apfs/run-tests.sh` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/apfs/test_fetch.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/apfs/test_format.py` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/apfs/test_namehash.py` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/apfs/test_namenorm.py` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/apfs/test_sparse.py` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/apfs/txn-probe.py` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/apfs/verify.py` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/apfs/write-tests.py` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/apfs/write-tests.sh` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/backup-partitions-test.py` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/backup-partitions.py` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/boot-args-test.py` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/boot-args.py` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/buttons-session.sh` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/buttons-watch.sh` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/camraw.py` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/camsensor.py` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/camtuning.py` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/darwin-write.py` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/docs-check.py` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/docs-gen.py` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/doctor.sh` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/drivers-check.py` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/dt-thermal.py` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/fdtbuild.py` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/flash-fingerprint.sh` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/font_trim.py` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/frames.py` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/guard-test.sh` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/guard_test.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/hakios-config-test.py` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/hakios-config.py` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/hakios-device-test.py` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/hakios-device.py` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/jb-preinstall.py` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/kernel-delta.sh` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/kernel-version-test.py` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/kernel-version.py` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/latency.py` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/macos-bin/README.md` | `docs/HAKIOS_SOURCE_AUDIT.md` | Reference claims compared with actual source; no claim of device validation |
| `tools/macos-bin/flock` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/macos-bin/sha256sum` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/macos-bin/stat` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/macos-bin/timeout` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/make-kernel.sh` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/mesa/air-frontend.patch` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/mesa/air-ir3.patch` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/mesa/air/air2nir.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/mesa/air/air_bitcode.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/mesa/air/air_bitcode.h` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/mesa/air/air_intrinsics.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/mesa/air/air_layout.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/mesa/air/air_metallib.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/mesa/air/air_module.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/mesa/air/air_module.h` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/mesa/air/air_print.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/mesa/air/air_private.h` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/mesa/air/air_run.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/mesa/air/air_to_nir.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/mesa/air/meson.build` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/mesa/air/nir_air.h` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/mesa/freedreno-darwin.patch` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/mesa/hakios-drm/hakios.drm.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/mesa/hakios-drm/xf86drm.h` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/mesa/ir3-round-default.patch` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/mesa/osmesa-es-profile.patch` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/metal-plugin-test.sh` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/metal_plugin_test.m` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/metallib-test.sh` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/metallib.py` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/metallib_test.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/mk-ath11k.sh` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/mk-jb.sh` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/mk-libdeflate.sh` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/mk-mesa.sh` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/mk-wlfw.sh` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/mkdatavol.py` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/mkesp-test.py` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/mkesp.py` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/mkubootimg.py` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/modem-cycle-win.sh` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/modem-cycle.sh` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/new-device-test.py` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/new-device.py` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/new-workspace.sh` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/provenance-check.py` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/provenance-test.py` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/provenance.allow` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/publish-repos.sh` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/qmi-test/extract.py` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/qmi-test/run-nas.sh` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/qmi-test/run.sh` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/qmi-test/shim/linux/mutex.h` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/qmi-test/shim/linux/soc/qcom/qmi.h` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/qmi-test/shim/sys/systm.h` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/qmi-test/test_nas.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/qmi-test/test_qmi.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/recording.py` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/soc-args-test-aoss.py` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/soc-args-test.sh` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/soc-args.py` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/soc-only-changes-test.sh` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/soc-only-changes.sh` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/sound.py` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/sparse-split.py` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/ufs-super.py` | `duchamp/drivers/ufs_readonly.c`, `duchamp/drivers/ufs_register_snapshot.c`, `duchamp/xnu/qemu_ufs.c` | Compare concepts only; MT6833 reader is incomplete, MSDC/eMMC and Qualcomm initialization are incompatible |
| `tools/ufs-survey.py` | `duchamp/drivers/ufs_readonly.c`, `duchamp/drivers/ufs_register_snapshot.c`, `duchamp/xnu/qemu_ufs.c` | Compare concepts only; MT6833 reader is incomplete, MSDC/eMMC and Qualcomm initialization are incompatible |
| `tools/update-prebuilt.sh` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/userdata-carve.py` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/win-bin/flock` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/wpa-test/reference.py` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/wpa-test/run.sh` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `tools/wpa-test/test_wpa.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/build.sh` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/com.hakios.demo.plist` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/com.hakios.varstore.plist` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/com.hakios.wifi.plist` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/jobinfo.py` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/libmini/mini.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/libmini/mini.h` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/libmini/start.S` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/mkeagl.py` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/mkjobs.py` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/rc.darwin` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/rc.jobs` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/rc.jobs.air` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/rc.jobs.air2` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/rc.jobs.airkernels` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/rc.jobs.airtex` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/rc.jobs.apfs` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/rc.jobs.bake` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/rc.jobs.battery` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/rc.jobs.battery2` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/rc.jobs.battery3` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/rc.jobs.buttons` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/rc.jobs.calendar` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/rc.jobs.camera` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/rc.jobs.cameras` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/rc.jobs.cc` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/rc.jobs.cow` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/rc.jobs.darwin` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/rc.jobs.demo` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/rc.jobs.fairplay` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/rc.jobs.flashcache` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/rc.jobs.flashcheck` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/rc.jobs.flashlock` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/rc.jobs.flashroot` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/rc.jobs.flashsound` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/rc.jobs.fonts` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/rc.jobs.fps` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/rc.jobs.gfx` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/rc.jobs.gltest` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/rc.jobs.haptic` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/rc.jobs.haptic2` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/rc.jobs.jb` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/rc.jobs.jbreg` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/rc.jobs.jiggle` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/rc.jobs.latency` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/rc.jobs.launch` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/rc.jobs.loud` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/rc.jobs.metal` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/rc.jobs.mic` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/rc.jobs.net` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/rc.jobs.persist` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/rc.jobs.persist0` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/rc.jobs.persist1` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/rc.jobs.persist5` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/rc.jobs.persist6` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/rc.jobs.photo` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/rc.jobs.pl` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/rc.jobs.preinstalled` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/rc.jobs.safari` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/rc.jobs.sileo` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/rc.jobs.snaps` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/rc.jobs.sound` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/rc.jobs.speakers` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/rc.jobs.speed` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/rc.jobs.ssh` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/rc.jobs.strip` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/rc.jobs.switcher` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/rc.jobs.torch` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/rc.jobs.tour` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/rc.jobs.tweakinstall` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/rc.jobs.u2f` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/rc.jobs.uib` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/rc.jobs.unlock` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/rc.jobs.users` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/rc.jobs.vblur` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/rc.jobs.voicememos` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/rc.jobs.volume` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/rc.jobs.wifipw` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/rc.launchd` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/rc.u2f` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/src/HakiosMetal.m` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/src/HakiosMetal.plist` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/src/apfs_mmap_test.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/src/audio_plugin.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/src/audio_plugin.plist` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/src/battery_test.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/src/battery_test.entitlements` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/src/camera_avtest.m` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/src/camera_device.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/src/camera_isp.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/src/camera_isp.h` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/src/camera_test.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/src/cg_test.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/src/child.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/src/cow_test.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/src/cpu_test.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/src/dlopen_test.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/src/eagl.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/src/eagl_slots.txt` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/src/font_test.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/src/gl_osmesa.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/src/gl_test.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/src/hakios.audio.h` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/src/hakios.camera.h` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/src/hakios.gl.h` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/src/hakios.input.h` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/src/hakios_metallib.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/src/hakios_metallib.h` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/src/hello.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/src/hello_dyn.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/src/hfs_test.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/src/init.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/src/inject.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/src/inject_app.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/src/inject_media.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/src/inject_sb.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/src/inject_tweaks.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/src/keychain_test.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/src/keychain_test.entitlements` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/src/metal_test.m` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/src/mg_test.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/src/net_test.m` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/src/record_test.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/src/record_test.entitlements` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/src/rwtouch.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/src/shm_test.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/src/snap_test.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/src/sound_test.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/src/stage0.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/src/surf_test.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/src/svc_test.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/src/torch_test.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/src/tweaks/redbare.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/src/tweaks/redtest.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/src/u2f_test.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/src/var_store.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/src/vol_ls.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/src/wifipw_test.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/src/wifipw_test.entitlements` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/var/mobile/Library/Preferences/com.apple.Accessibility.plist` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/var/mobile/Library/Preferences/com.apple.VideoProcessing.plist` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/var/mobile/Library/Preferences/com.apple.assistant.support.plist` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/var/mobile/Library/Preferences/com.apple.coremedia.plist` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/var/mobile/Library/Preferences/com.apple.frontboard.plist` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/var/mobile/Library/Preferences/com.apple.keyboard.preferences.plist` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/var/mobile/Library/Preferences/com.apple.migration.plist` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/var/mobile/Library/Preferences/com.apple.purplebuddy.plist` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `userland/var/mobile/Library/Preferences/com.apple.springboard.plist` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `wifi/lx/include/linux/irq.h` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `wifi/lx/include/linux/of.h` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `wifi/lx/include/linux/of_irq.h` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `wifi/lx/include/linux/of_reserved_mem.h` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `wifi/lx/include/linux/remoteproc.h` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `wifi/lx/include/linux/rhashtable.h` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `wifi/lx/include/linux/soc/qcom/qmi.h` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `wifi/lx/include/lx_more.h` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `wifi/lx/include/lx_os.h` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `wifi/lx/include/lx_prelude.h` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `wifi/lx/include/machine/pcpu.h` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `wifi/lx/include/stdbool.h` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `wifi/lx/include/stddef.h` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `wifi/lx/include/stdint.h` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `wifi/lx/include/sys/cdefs.h` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `wifi/lx/include/sys/linker_set.h` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `wifi/lx/patches/include-linux-device.h.patch` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `wifi/lx/patches/include-linux-etherdevice.h.patch` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `wifi/lx/patches/include-linux-io.h.patch` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `wifi/lx/patches/include-linux-socket.h.patch` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `wifi/lx/patches/include-net-cfg80211.h.patch` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `wifi/lx/patches/include-net-mac80211.h.patch` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `wifi/lx/src/lx.h` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `wifi/lx/src/lx_80211.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `wifi/lx/src/lx_base.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `wifi/lx/src/lx_bus.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `wifi/lx/src/lx_wpa.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `wifi/lx/src/lx_wpa.h` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xl` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu-build.sh` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu-deps/build/lzbitmap/libzbitmap.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu-deps/build/lzbitmap/libzbitmap.h` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu-deps/build/lzbitmap/unzbm.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu-deps/build/pthread/build.sh` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu-deps/build/pthread/inc/TargetConditionals.h` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu-deps/gen-iig-stubs.py` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu-deps/host/bin/codesign` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu-deps/host/bin/iig` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu-deps/host/bin/install` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu-deps/host/bin/plutil` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu-deps/host/bin/sw_vers` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu-deps/host/bin/xcrun` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu-deps/host/bin/xnu-clang` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu-deps/hostinc/architecture/byte_order.h` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu-deps/hostinc/copyfile.h` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu-deps/hostinc/hostcompat.h` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu-deps/hostinc/libc.h` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu-deps/hostinc/mach-o/arch.h` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu-deps/hostinc/mach-o/swap.h` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu-deps/hostinc/mach/mach_init.h` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu-deps/hostinc/mach/machine.h` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu-deps/hostinc/mach/machine/thread_status.h` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu-deps/hostinc/mach/vm_prot.h` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu-deps/hostinc/xnu_clang_compat.h` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu-deps/iig-impl/OSObject.iig.cpp` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu-deps/iig-impl/undefined-all.txt` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu-deps/setup.sh` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu-env.sh` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu/README.md` | `docs/HAKIOS_SOURCE_AUDIT.md` | Reference claims compared with actual source; no claim of device validation |
| `xnu/apply.sh` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu/export.sh` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu/files/bsd/hfs/hfs_builtin.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu/files/bsd/kern/kern_minimac.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu/files/bsd/miscfs/apfs/apfs.h` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu/files/bsd/miscfs/apfs/apfs_deflate.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu/files/bsd/miscfs/apfs/apfs_format.h` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu/files/bsd/miscfs/apfs/apfs_lib.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu/files/bsd/miscfs/apfs/apfs_lib.h` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu/files/bsd/miscfs/apfs/apfs_store.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu/files/bsd/miscfs/apfs/apfs_store.h` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu/files/bsd/miscfs/apfs/apfs_vfsops.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu/files/bsd/miscfs/apfs/apfs_vnops.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu/files/bsd/miscfs/apfs/apfs_write.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu/files/bsd/miscfs/apfs/apfs_write.h` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu/files/bsd/miscfs/apfs/apfs_zbitmap.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu/files/bsd/miscfs/apfs/libdeflate/COPYING` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu/files/bsd/miscfs/apfs/libdeflate/common_defs.h` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu/files/bsd/miscfs/apfs/libdeflate/lib/adler32.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu/files/bsd/miscfs/apfs/libdeflate/lib/arm/adler32_impl.h` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu/files/bsd/miscfs/apfs/libdeflate/lib/arm/cpu_features.h` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu/files/bsd/miscfs/apfs/libdeflate/lib/arm/crc32_impl.h` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu/files/bsd/miscfs/apfs/libdeflate/lib/arm/crc32_pmull_helpers.h` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu/files/bsd/miscfs/apfs/libdeflate/lib/arm/crc32_pmull_wide.h` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu/files/bsd/miscfs/apfs/libdeflate/lib/arm/matchfinder_impl.h` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu/files/bsd/miscfs/apfs/libdeflate/lib/cpu_features_common.h` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu/files/bsd/miscfs/apfs/libdeflate/lib/decompress_template.h` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu/files/bsd/miscfs/apfs/libdeflate/lib/deflate_constants.h` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu/files/bsd/miscfs/apfs/libdeflate/lib/deflate_decompress.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu/files/bsd/miscfs/apfs/libdeflate/lib/lib_common.h` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu/files/bsd/miscfs/apfs/libdeflate/lib/zlib_constants.h` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu/files/bsd/miscfs/apfs/libdeflate/lib/zlib_decompress.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu/files/bsd/miscfs/apfs/libdeflate/libdeflate.h` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu/files/bsd/miscfs/apfs/libzbitmap/libzbitmap.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu/files/bsd/miscfs/apfs/libzbitmap/libzbitmap.h` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu/files/bsd/miscfs/ramfs/ramfs.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu/files/bsd/pthread/pthread_kext_static.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu/files/bsd/sys/hakios.apfs_check.h` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu/files/bsd/sys/hakios.audio.h` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu/files/bsd/sys/hakios.camera.h` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu/files/bsd/sys/hakios.input.h` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu/files/bsd/sys/hakios.ipa.h` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu/files/bsd/sys/hakios.lx.h` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu/files/bsd/sys/hakios.nas.h` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu/files/bsd/sys/hakios.net.h` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu/files/bsd/sys/hakios.qmi.h` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu/files/bsd/sys/hakios.qrtr.h` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu/files/bsd/sys/hakios.sparse.h` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu/files/bsd/sys/hakios.sta.h` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu/files/bsd/sys/hakios.version.h` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu/files/bsd/sys/hakios.virtio_blk.h` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu/files/iokit/Kernel/GenericARMPE.cpp` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu/files/iokit/Kernel/MiniAppleKeyStore.cpp` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu/files/iokit/Kernel/MiniDrivers.h` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu/files/iokit/Kernel/MiniIOMobileFramebuffer.cpp` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu/files/iokit/Kernel/MiniIONetworkStack.cpp` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu/files/iokit/Kernel/MiniIOSurface.cpp` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu/files/iokit/Kernel/MiniIOSurface.h` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu/files/libkern/amfi/miniamfi.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu/files/libkern/amfi/miniamfi_entitlements.cpp` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu/files/osfmk/arm64/generic_arm64_support.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu/files/osfmk/arm64/gic_v3_irq.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu/files/osfmk/arm64/kpc.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu/files/osfmk/arm64/loader_return.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu/files/osfmk/arm64/ppl/sart.h` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu/files/osfmk/arm64/ppl/uat.h` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu/files/osfmk/arm64/psci_smp.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu/files/osfmk/arm64/psci_smp.h` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu/files/osfmk/arm64/tunables/tunables.s` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu/files/osfmk/arm64/user_exception_trace.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu/files/osfmk/minicrypto/mc_aes.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu/files/osfmk/minicrypto/mc_digests.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu/files/osfmk/minicrypto/mc_provider.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu/files/osfmk/minicrypto/minicrypto.h` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu/hakios.patch` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu/hfs/core.list` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu/hfs/encodings.list` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu/hfs/hfs.patch` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu/hfs/hfs.sh` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnu/sync-drivers.sh` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnuloader/build.sh` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnuloader/efi.h` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnuloader/im4p.py` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnuloader/loader.c` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnuloader/mkidentity.py` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnuloader/mkidentity.sh` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
| `xnuloader/mkpayload.py` | None (not ported) | Inventoried and scanned where textual; not needed for the bounded offline port stage |
