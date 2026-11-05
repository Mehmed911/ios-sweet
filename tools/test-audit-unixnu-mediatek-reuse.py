#!/usr/bin/env python3
"""Unit tests for the static UniXNU/MediaTek reuse audit."""

import importlib.util
from pathlib import Path
import tempfile
import unittest


REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "tools" / "audit-unixnu-mediatek-reuse.py"
SPEC = importlib.util.spec_from_file_location(
    "audit_unixnu_mediatek_reuse", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


REVISIONS = {
    "ruby": MODULE.RUBY_REVISION,
    "unixnu": MODULE.UNIXNU_REVISION,
    "darwinboot": MODULE.DARWINBOOT_REVISION,
    "merlinx": MODULE.MERLINX_REVISION,
}


def put(root, relative, text):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def fixture(base):
    ruby = base / "ruby"
    unixnu = base / "unixnu"
    merlinx = base / "merlinx"
    duchamp = base / "duchamp-project"

    put(ruby, "docs/en/01-architecture.md", """
LK has no `boot:` command, so every experiment is flashed to `boot_a`.
shim/loader (raw AArch64) at 0x40080000
""")
    put(ruby, "docs/en/02-hardware.md", """
| GIC | GICv3 | dist `0x0c000000+0x40000` |
| Redistributor | `0x0c040000+0x200000` |
| Timer | timer | `clock-frequency=13000000` |
| LK scan buffer | `0x7cdfc000`, pitch 4352 |
""")
    put(ruby, "docs/en/03-boot-chain.md", """
-> gzip kernel -> 0x40080000
-> jump K64, EL1h, x0 = DTB
""")
    put(ruby, "src/bringup/shim.S", """
mov x19, x0
mrs x0, CurrentEL
msr sctlr_el1, x0
""")
    put(ruby, "src/bringup/shim.c", "#define FB_BASE 0x7ba10000UL\n")
    put(ruby, "src/ufs-probe/ufs.c", """
/* LK has already initialised the controller. */
#define UFS_BASE 0x11270000UL
uintptr_t ucd_pa = (uintptr_t)&ucd;
uintptr_t buf_pa = (uintptr_t)buf;
__asm__ volatile("dsb sy" ::: "memory");
ufs_wr(REG_UTRLDBR, 1);
""")
    put(ruby, "patches/0080-ruby-ufs.patch", """
su.dma_pa = ptoa_64(pn);
su.lun = (uint8_t)lun;
""")

    put(unixnu, "docs/guide/requirements.md",
        "An unlockable bootloader that accepts `fastboot boot`.\n")
    put(unixnu, "docs/guide/boot.md", """
fastboot boot out/<device>/<os_profile>/<config>/boot/boot.img
gzip of BootShim plus the UEFI firmware volume
BootShim starts the firmware volume
""")
    put(unixnu, "docs/concepts/boot-chain.md", """
Bootloader to BootShim
UEFI to UniXNU
UniXNU to DarwinBoot
DarwinBoot to XNU
""")
    put(unixnu, "package/UniXNUPkg/Include/Protocol/UniXNULoader.h", """
UNIXNU_LOADER_BOOT_REQUEST
CONST CHAR16  *KernelPath;
CONST CHAR16  *BootArgs;
VOID          *DeviceTree;
VOID          *Ramdisk;
""")
    put(unixnu, "drivers/DarwinBoot/DarwinBootPkg/Driver/Entry.S", """
// x0=boot_args PA
dc civac, x4
ic iallu
msr sctlr_el1, x4
br x1
""")
    put(unixnu, "drivers/DarwinBoot/DarwinBootPkg/Driver/BootArgs.h", """
CHAR8   CommandLine[1024];
STATIC_ASSERT (sizeof (DARWIN_BOOT_ARGS) == 0x480, "boot_args ABI");
""")
    put(unixnu, "drivers/DarwinBoot/DarwinBootPkg/Driver/DarwinBoot.c", """
ExitBootServices
DarwinEnter (ArgsAddress
EFI_COMPROMISED_DATA
""")

    put(merlinx, "docs/devices/merlinx.md", """
The bootloader rejects fastboot boot, so use fastboot flash boot for p33.
""")
    put(merlinx, "board.toml", """
soc = "MT6768"
loader = "firmware"
dsc = "Platforms/Xiaomi/merlinxPkg/merlinx.dsc"
""")

    put(duchamp, "duchamp/board.toml", """
[board]
codename = "duchamp"
soc = "MediaTek MT6897"
[interrupts]
gicd_base = "0x0c400000"
gicr_base = "0x0c440000"
[timer]
frequency = "0x00c65d40"
[framebuffer]
base = "0xfcc2f000"
stride = 4992
width = 1220
height = 2712
[boot]
ram_only = false
flash_allowed = false
""")
    put(duchamp, "duchamp/MT6897-DMA-IOMMU-FIRMWARE-EVIDENCE.md",
        "The node is `/soc/ufshci@112b0000`.\n")
    put(duchamp, "duchamp/loader/materialize.c", """
#define COMMAND_LINE_LENGTH 608u
_Static_assert(sizeof(struct boot_args_v2) == 736, "boot_args size");
""")
    put(duchamp, "duchamp/loader/MT6897-RAM-LAUNCH.md", """
There is no documented LK or UEFI entry provider.
The provider gate therefore remains closed.
""")
    return ruby, unixnu, merlinx, duchamp


class UnixnuMediatekAuditTests(unittest.TestCase):
    def test_valid_fixture_records_exact_platform_differences(self):
        with tempfile.TemporaryDirectory() as temporary:
            paths = fixture(Path(temporary))
            report = MODULE.analyze_sources(*paths, REVISIONS)
            self.assertTrue(report["passed"])
            self.assertEqual(report["observed"]["ruby"]["timer_frequency"],
                             13_000_000)
            self.assertTrue(report["differences"]["timer_frequency"]["equal"])
            self.assertFalse(report["differences"]["gicd_base"]["equal"])
            self.assertFalse(report["differences"]["gicr_base"]["equal"])
            self.assertFalse(report["differences"]["ufs_base"]["equal"])
            self.assertFalse(
                report["gates"]["ram_only_entry_provider_available"])
            self.assertFalse(
                report["gates"]["darwinboot_drop_in_abi_compatible"])

    def test_matching_ruby_gic_is_fail_closed_for_manual_review(self):
        with tempfile.TemporaryDirectory() as temporary:
            paths = fixture(Path(temporary))
            hardware = paths[0] / "docs/en/02-hardware.md"
            text = hardware.read_text(encoding="utf-8")
            hardware.write_text(
                text.replace("0x0c000000", "0x0c400000"), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "GICD unexpectedly match"):
                MODULE.analyze_sources(*paths, REVISIONS)

    def test_ruby_probe_cache_change_requires_review(self):
        with tempfile.TemporaryDirectory() as temporary:
            paths = fixture(Path(temporary))
            source = paths[0] / "src/ufs-probe/ufs.c"
            source.write_text(
                source.read_text(encoding="utf-8") + "\ndc civac, x4\n",
                encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "gained explicit data-cache"):
                MODULE.analyze_sources(*paths, REVISIONS)

    def test_missing_boot_method_marker_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            paths = fixture(Path(temporary))
            architecture = paths[0] / "docs/en/01-architecture.md"
            architecture.write_text(
                architecture.read_text(encoding="utf-8").replace(
                    "flashed to `boot_a`", "loaded by an unknown method"),
                encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "flashed to.*boot_a"):
                MODULE.analyze_sources(*paths, REVISIONS)


if __name__ == "__main__":
    unittest.main(verbosity=2)
