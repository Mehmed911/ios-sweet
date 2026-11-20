# Duchamp full kernel QEMU result

**The modified kernel has no full QEMU boot result in this run.** Linux ld64 emitted an executable from reference XNU objects and the freshly built runtime dependencies. The existing validator accepted its reference layout and denied it as a dual-RAMDisk candidate because the old object set lacks `_duchamp_dual_ramdisk_init`.

No dual-RAMDisk payload was generated or booted from that image. There are no new observations for md0, md1, HFS+, `/private/var`, `/var`, `/dev/console`, launchd PID 1, Mach IPC, dyld, static Mach-O, syslogd, `EROFS`, `ENOSPC`, or post-boot md0 equality. The [existing guest integration runner](../tools/test-duchamp-readonly-var.py) and [Mach-O tests](../tools/test-duchamp-darwin-ramroot.sh) are ready for use with the exact hash of the new source-built kernel once it passes the [candidate gate](../tools/duchamp_xnu_link.py).

The stack probe passed 10/10 isolated ARM64 Linux user-mode cases under QEMU, including read-only stack memory, unchanged SP, and expected faults on intervening and final guard pages. The test exited 0. The dual-RAMDisk host layout regression passed 12/12 on the existing fixture. [Stack probe log](../../../outputs/duchamp-linux-firehose-20261117/stack-qemu-run.log), [layout test log](../../../outputs/duchamp-linux-firehose-20261117/dual-layout-regression.log).

The tools operated on saved files only. The phone, Android slots, LK, BL31, partitions and physical UFS were untouched. Sources were left uncommitted and no Git push was made. [Linux link evidence and remaining compiler dependency](DUCHAMP_LINUX_XNU_LINK_STATUS.md).
