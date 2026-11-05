#!/usr/bin/env python3
"""Audit UniXNU MediaTek sources against the saved Duchamp platform contract.

The audit is static and fail closed.  It reads pinned source checkouts and the
local Duchamp descriptions, records the exact differences, and decides which
parts are design references versus safe integration candidates.  It never
contacts a phone, builds a boot image, performs MMIO, or writes a partition.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
import tomllib


RUBY_REVISION = "f92f29031e971f257196e19562243411302ea87c"
UNIXNU_REVISION = "e2fdae4312d0acc3d8a52bc457101e7918095e6a"
DARWINBOOT_REVISION = "3c75734014cdab0acd9541e88057b7606ee7ae08"
MERLINX_REVISION = "c6b28c4ffda1ed62ef75c2580980d6387d7eb67c"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def read_text(root: Path, relative: str) -> str:
    path = root / relative
    require(path.is_file(), f"missing source file: {path}")
    return path.read_text(encoding="utf-8")


def git_revision(root: Path) -> str:
    process = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        capture_output=True, text=True, check=False)
    require(process.returncode == 0,
            f"cannot read Git revision for {root}: {process.stderr.strip()}")
    revision = process.stdout.strip().lower()
    require(re.fullmatch(r"[0-9a-f]{40}", revision) is not None,
            f"invalid Git revision for {root}")
    return revision


def require_markers(text: str, label: str, markers: tuple[str, ...]) -> None:
    for marker in markers:
        require(marker in text, f"{label} no longer contains {marker!r}")


def capture_hex(text: str, pattern: str, label: str) -> int:
    match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
    require(match is not None, f"cannot recover {label}")
    return int(match.group(1), 16)


def capture_dec(text: str, pattern: str, label: str) -> int:
    match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
    require(match is not None, f"cannot recover {label}")
    return int(match.group(1), 10)


def parse_board(board_path: Path) -> dict[str, int | str | bool]:
    require(board_path.is_file(), f"missing Duchamp board file: {board_path}")
    with board_path.open("rb") as stream:
        board = tomllib.load(stream)
    require(board.get("board", {}).get("codename") == "duchamp",
            "board.toml is not the Duchamp profile")
    require(board.get("board", {}).get("soc") == "MediaTek MT6897",
            "board.toml SoC differs from MT6897")

    def number(section: str, key: str) -> int:
        value = board.get(section, {}).get(key)
        if isinstance(value, str):
            return int(value, 0)
        require(isinstance(value, int), f"missing board value {section}.{key}")
        return value

    return {
        "codename": "duchamp",
        "soc": "MediaTek MT6897",
        "gicd_base": number("interrupts", "gicd_base"),
        "gicr_base": number("interrupts", "gicr_base"),
        "timer_frequency": number("timer", "frequency"),
        "framebuffer_base": number("framebuffer", "base"),
        "framebuffer_stride": number("framebuffer", "stride"),
        "framebuffer_width": number("framebuffer", "width"),
        "framebuffer_height": number("framebuffer", "height"),
        "ram_only": bool(board.get("boot", {}).get("ram_only")),
        "flash_allowed": bool(board.get("boot", {}).get("flash_allowed")),
    }


def analyze_sources(ruby: Path, unixnu: Path, merlinx: Path,
                    duchamp: Path, revisions: dict[str, str]) -> dict:
    ruby_arch = read_text(ruby, "docs/en/01-architecture.md")
    ruby_hw = read_text(ruby, "docs/en/02-hardware.md")
    ruby_boot = read_text(ruby, "docs/en/03-boot-chain.md")
    ruby_shim_s = read_text(ruby, "src/bringup/shim.S")
    ruby_shim_c = read_text(ruby, "src/bringup/shim.c")
    ruby_ufs = read_text(ruby, "src/ufs-probe/ufs.c")
    ruby_ufs_patch = read_text(ruby, "patches/0080-ruby-ufs.patch")

    unixnu_requirements = read_text(unixnu, "docs/guide/requirements.md")
    unixnu_boot = read_text(unixnu, "docs/guide/boot.md")
    unixnu_chain = read_text(unixnu, "docs/concepts/boot-chain.md")
    unixnu_protocol = read_text(
        unixnu, "package/UniXNUPkg/Include/Protocol/UniXNULoader.h")
    darwin_entry = read_text(
        unixnu, "drivers/DarwinBoot/DarwinBootPkg/Driver/Entry.S")
    darwin_args = read_text(
        unixnu, "drivers/DarwinBoot/DarwinBootPkg/Driver/BootArgs.h")
    darwin_boot = read_text(
        unixnu, "drivers/DarwinBoot/DarwinBootPkg/Driver/DarwinBoot.c")

    merlin_board = read_text(merlinx, "board.toml")
    merlin_device = read_text(merlinx, "docs/devices/merlinx.md")

    duchamp_board = parse_board(duchamp / "duchamp/board.toml")
    duchamp_dma = read_text(
        duchamp, "duchamp/MT6897-DMA-IOMMU-FIRMWARE-EVIDENCE.md")
    duchamp_materialize = read_text(duchamp, "duchamp/loader/materialize.c")
    duchamp_launch = read_text(
        duchamp, "duchamp/loader/MT6897-RAM-LAUNCH.md")

    require_markers(ruby_arch, "ruby architecture", (
        "LK has no `boot:` command",
        "flashed to `boot_a`",
        "shim/loader (raw AArch64) at 0x40080000",
    ))
    require_markers(ruby_boot, "ruby boot chain", (
        "-> gzip kernel -> 0x40080000",
        "-> jump K64, EL1h, x0 = DTB",
    ))
    require_markers(ruby_shim_s, "ruby shim entry", (
        "mov x19, x0",
        "mrs x0, CurrentEL",
        "msr sctlr_el1, x0",
    ))
    require_markers(ruby_ufs, "ruby UFS probe", (
        "LK has already initialised the",
        "uintptr_t ucd_pa = (uintptr_t)&ucd",
        "uintptr_t buf_pa = (uintptr_t)buf",
        "ufs_wr(REG_UTRLDBR, 1)",
        "__asm__ volatile(\"dsb sy\"",
    ))
    require("dc " not in ruby_ufs and "dc\t" not in ruby_ufs,
            "ruby UFS probe gained explicit data-cache maintenance; review it")
    require_markers(ruby_ufs_patch, "ruby XNU UFS patch", (
        "su.dma_pa = ptoa_64(pn)",
        "su.lun = (uint8_t)lun",
    ))

    require_markers(unixnu_requirements, "UniXNU requirements", (
        "accepts `fastboot boot`",
    ))
    require_markers(unixnu_boot, "UniXNU boot guide", (
        "fastboot boot out/<device>/<os_profile>/<config>/boot/boot.img",
        "gzip of BootShim plus the UEFI firmware volume",
        "BootShim starts the firmware volume",
    ))
    require_markers(unixnu_chain, "UniXNU boot chain", (
        "Bootloader to BootShim",
        "UEFI to UniXNU",
        "UniXNU to DarwinBoot",
        "DarwinBoot to XNU",
    ))
    require_markers(unixnu_protocol, "UniXNU loader protocol", (
        "UNIXNU_LOADER_BOOT_REQUEST",
        "CONST CHAR16  *KernelPath",
        "CONST CHAR16  *BootArgs",
        "VOID          *DeviceTree",
        "VOID          *Ramdisk",
    ))
    require_markers(darwin_entry, "DarwinBoot entry", (
        "x0=boot_args PA",
        "dc civac, x4",
        "ic iallu",
        "msr sctlr_el1, x4",
        "br x1",
    ))
    require_markers(darwin_args, "DarwinBoot boot_args", (
        "CHAR8   CommandLine[1024]",
        "sizeof (DARWIN_BOOT_ARGS) == 0x480",
    ))
    require_markers(darwin_boot, "DarwinBoot loader", (
        "ExitBootServices",
        "DarwinEnter (ArgsAddress",
        "EFI_COMPROMISED_DATA",
    ))

    require_markers(merlin_device, "merlinx device record", (
        "bootloader rejects fastboot boot",
        "fastboot flash boot",
        "p33",
    ))
    require_markers(merlin_board, "merlinx board", (
        'soc = "MT6768"',
        'loader = "firmware"',
        'dsc = "Platforms/Xiaomi/merlinxPkg/merlinx.dsc"',
    ))

    require_markers(duchamp_materialize, "Duchamp boot_args", (
        "#define COMMAND_LINE_LENGTH 608u",
        "sizeof(struct boot_args_v2) == 736",
    ))
    require_markers(duchamp_launch, "Duchamp RAM launch gate", (
        "There is no documented LK or UEFI entry provider",
        "therefore remains closed",
    ))

    ruby_values = {
        "kernel_load": capture_hex(
            ruby_boot, r"gzip kernel -> 0x([0-9a-f]+)", "ruby kernel load"),
        "gicd_base": capture_hex(
            ruby_hw, r"dist `0x([0-9a-f]+)\+0x", "ruby GICD base"),
        "gicr_base": capture_hex(
            ruby_hw, r"Redistributor \| `0x([0-9a-f]+)\+0x", "ruby GICR base"),
        "timer_frequency": capture_dec(
            ruby_hw, r"clock-frequency=([0-9]+)", "ruby timer frequency"),
        "framebuffer_visible": capture_hex(
            ruby_hw, r"LK scan buffer \| `0x([0-9a-f]+)`", "ruby visible framebuffer"),
        "framebuffer_shim": capture_hex(
            ruby_shim_c, r"#define FB_BASE 0x([0-9a-f]+)UL", "ruby shim framebuffer"),
        "ufs_base": capture_hex(
            ruby_ufs, r"#define UFS_BASE\s+0x([0-9a-f]+)UL", "ruby UFS base"),
    }
    duchamp_values = dict(duchamp_board)
    duchamp_values["ufs_base"] = capture_hex(
        duchamp_dma, r"/soc/ufshci@([0-9a-f]+)", "Duchamp UFS base")

    differences = {
        "gicd_base": {
            "ruby": ruby_values["gicd_base"],
            "duchamp": duchamp_values["gicd_base"],
            "equal": ruby_values["gicd_base"] == duchamp_values["gicd_base"],
        },
        "gicr_base": {
            "ruby": ruby_values["gicr_base"],
            "duchamp": duchamp_values["gicr_base"],
            "equal": ruby_values["gicr_base"] == duchamp_values["gicr_base"],
        },
        "timer_frequency": {
            "ruby": ruby_values["timer_frequency"],
            "duchamp": duchamp_values["timer_frequency"],
            "equal": ruby_values["timer_frequency"] == duchamp_values["timer_frequency"],
        },
        "framebuffer_base": {
            "ruby_visible": ruby_values["framebuffer_visible"],
            "ruby_early_shim": ruby_values["framebuffer_shim"],
            "duchamp": duchamp_values["framebuffer_base"],
            "equal": ruby_values["framebuffer_visible"] == duchamp_values["framebuffer_base"],
        },
        "ufs_base": {
            "ruby": ruby_values["ufs_base"],
            "duchamp": duchamp_values["ufs_base"],
            "equal": ruby_values["ufs_base"] == duchamp_values["ufs_base"],
        },
        "boot_args_abi": {
            "unixnu_darwin23_size": 0x480,
            "unixnu_command_line": 1024,
            "duchamp_xnu8796_size": 736,
            "duchamp_command_line": 608,
            "equal": False,
        },
    }

    require(not differences["gicd_base"]["equal"],
            "Ruby and Duchamp GICD unexpectedly match; review the audit")
    require(not differences["gicr_base"]["equal"],
            "Ruby and Duchamp GICR unexpectedly match; review the audit")
    require(not differences["framebuffer_base"]["equal"],
            "Ruby and Duchamp framebuffers unexpectedly match; review the audit")
    require(not differences["ufs_base"]["equal"],
            "Ruby and Duchamp UFS bases unexpectedly match; review the audit")

    return {
        "schema": "duchamp-unixnu-mediatek-reuse-v1",
        "passed": True,
        "scope": (
            "static pinned-source comparison only; no phone, fastboot, boot image, "
            "MMIO, UFS command or partition access"
        ),
        "sources": {
            "ruby": {
                "revision": revisions["ruby"],
                "url": "https://github.com/lky005/ruby-ios-bringup",
            },
            "unixnu": {
                "revision": revisions["unixnu"],
                "url": "https://github.com/UniXNU/UniXNU",
            },
            "darwinboot": {
                "revision": revisions["darwinboot"],
                "url": "https://github.com/UniXNU/DarwinBoot",
            },
            "merlinx": {
                "revision": revisions["merlinx"],
                "url": "https://github.com/Gytis283123/UniXNU-merlinx",
            },
        },
        "observed": {
            "ruby": {
                **ruby_values,
                "entry_el": "EL1h",
                "entry_x0": "FDT",
                "boot_method": "flash boot_a",
                "ufs_dma_addressing": "direct pointer-as-PA",
                "ufs_explicit_data_cache_maintenance": False,
                "ufs_reuses_lk_initialized_host": True,
            },
            "unixnu": {
                "entry_requirement": "bootloader starts BootShim",
                "documented_temporary_method": "fastboot boot",
                "loader_chain": ["BootShim", "UEFI", "UniXNU", "DarwinBoot", "XNU"],
                "darwin_enter_el": "EL1 only",
                "darwin_enter_cleans_owned_window": True,
                "darwin_enter_disables_mmu_and_caches": True,
            },
            "merlinx": {
                "soc": "MT6768",
                "boot_method": "flash p33/boot",
                "fastboot_boot_supported": False,
                "storage": "NativeEmmc",
            },
            "duchamp": duchamp_values,
        },
        "differences": differences,
        "components": [
            {
                "name": "UniXNU loader protocol",
                "classification": "reusable-after-uefi-entry",
                "reason": "board-neutral request interface; it does not create the missing LK caller",
            },
            {
                "name": "DarwinBoot validation and placement",
                "classification": "reference-or-adapt",
                "reason": "useful bounded Mach-O/ADT/trust-cache checks; current Darwin 23 boot_args ABI is not the XNU 8796 ABI",
            },
            {
                "name": "DarwinEnter cache/MMU handoff",
                "classification": "reference-or-adapt",
                "reason": "EL1 ordered cache publication is useful, but it assumes UEFI ownership and a validated owned window",
            },
            {
                "name": "Ruby LK/FDT entry probe",
                "classification": "concept-only",
                "reason": "x0/CurrentEL capture is portable; hard-coded MT6877 memory, watchdog and framebuffer values are not",
            },
            {
                "name": "Ruby GIC and timer",
                "classification": "algorithm-only",
                "reason": "timer frequency matches, but GICD/GICR bases differ from the captured MT6897 FDT",
            },
            {
                "name": "Ruby framebuffer",
                "classification": "software-algorithm-only",
                "reason": "both documented Ruby framebuffer addresses differ from Duchamp geometry and reservation",
            },
            {
                "name": "Ruby UFS probe/XNU patch",
                "classification": "do-not-reuse-on-phone",
                "reason": "MT6877 base, inherited-LK state, direct pointer-as-PA DMA and no explicit cache/IOMMU contract",
            },
            {
                "name": "Ruby/Merlinx phone entry",
                "classification": "disallowed-by-current-policy",
                "reason": "both rely on writing a boot partition when fastboot boot is absent",
            },
        ],
        "gates": {
            "ram_only_entry_provider_available": False,
            "duchamp_uefi_port_available": False,
            "darwinboot_drop_in_abi_compatible": False,
            "ruby_device_constants_reusable": False,
            "ruby_ufs_physical_reuse_allowed": False,
            "phone_execution_authorized": False,
            "partition_write_authorized": False,
        },
        "next_safe_work": [
            "retain the existing LK RAM-entry provider gate as closed",
            "reuse UniXNU/DarwinBoot validation ideas only in QEMU or host tests",
            "continue requiring an MT6897-specific documented RAM caller before phone launch",
            "keep the physical MT6897 UFS backend fail closed until firmware, cache and DMA ownership are proven",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ruby", required=True, type=Path)
    parser.add_argument("--unixnu", required=True, type=Path)
    parser.add_argument("--merlinx", required=True, type=Path)
    parser.add_argument("--duchamp", type=Path,
                        default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--require-ram-provider", action="store_true",
                        help="fail unless an eligible no-write RAM entry exists")
    args = parser.parse_args()

    if args.output.exists():
        parser.error(f"refusing to overwrite existing output: {args.output}")

    try:
        revisions = {
            "ruby": git_revision(args.ruby),
            "unixnu": git_revision(args.unixnu),
            "darwinboot": git_revision(args.unixnu / "drivers/DarwinBoot"),
            "merlinx": git_revision(args.merlinx),
        }
        expected = {
            "ruby": RUBY_REVISION,
            "unixnu": UNIXNU_REVISION,
            "darwinboot": DARWINBOOT_REVISION,
            "merlinx": MERLINX_REVISION,
        }
        for name, revision in revisions.items():
            require(revision == expected[name],
                    f"{name} revision {revision} differs from pinned {expected[name]}")
        report = analyze_sources(
            args.ruby, args.unixnu, args.merlinx, args.duchamp, revisions)
    except (OSError, ValueError, tomllib.TOMLDecodeError) as error:
        parser.error(str(error))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"UniXNU MediaTek audit: PASS; report={args.output}")
    print("ram-only entry provider: unavailable (fail closed)")
    if args.require_ram_provider and not report["gates"]["ram_only_entry_provider_available"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
