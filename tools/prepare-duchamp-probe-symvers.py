#!/usr/bin/env python3
"""Extract a minimal, provenance-checked Module.symvers for the probe.

Only CRCs already embedded in the captured, live-matching Duchamp vendor
modules are accepted. The tool never contacts or modifies a phone.
"""

import argparse
import hashlib
import json
from pathlib import Path
import struct


VERMAGIC = (
    "6.1.57-android14-11-maybe-dirty SMP preempt mod_unload "
    "modversions aarch64"
)
PINNED_MODULES = {
    "iommu_debug.ko": "7bb7fdaf9ee4fbe9893a86c3792a5c75e3766b880e9f63792b25c462eda6c3d2",
    "iommu_secure.ko": "50651ee6ebd1f4f287d9bca036f4033b6084162bc83380111b9c7a13089fa194",
    "mtk_iommu.ko": "0d5b3e49a2639b96d605f5b6ce7ffaeb9c4737484aa88afec866a79006936073",
    "phy-mtk-ufs.ko": "0581b58a406deeb53453e05b37ce1bb2991bea33412ecbc0284e90eba9fc6159",
    "ufs-mediatek-dbg.ko": "1bc5ebe41d206fe8caf44cd823c52bfe935e1fcd89f0548585ee74fef06781f3",
    "ufs-mediatek-mod.ko": "7043e1109b4c356a914fdc92ffbe463c0c43cb27342f6ccce1517a2086b02493",
}
REQUIRED_SYMBOLS = {
    "device_create_file": "EXPORT_SYMBOL_GPL",
    "device_remove_file": "EXPORT_SYMBOL_GPL",
    "of_find_compatible_node": "EXPORT_SYMBOL",
    "of_find_device_by_node": "EXPORT_SYMBOL",
    "iommu_get_domain_for_dev": "EXPORT_SYMBOL_GPL",
    "put_device": "EXPORT_SYMBOL_GPL",
    "sysfs_emit": "EXPORT_SYMBOL_GPL",
    "module_layout": "EXPORT_SYMBOL",
}


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def cstring(data, offset):
    if not 0 <= offset < len(data):
        raise ValueError("ELF string offset is outside its section")
    end = data.find(b"\0", offset)
    if end < 0:
        raise ValueError("unterminated ELF string")
    return data[offset:end].decode("utf-8")


def elf_sections(data):
    if data[:6] != b"\x7fELF\x02\x01":
        raise ValueError("expected little-endian ELF64 module")
    if struct.unpack_from("<HH", data, 16) != (1, 183):
        raise ValueError("expected AArch64 ET_REL module")
    table = struct.unpack_from("<Q", data, 40)[0]
    stride, count, names_index = struct.unpack_from("<HHH", data, 58)
    if stride != 64 or not 0 < names_index < count < 65536:
        raise ValueError("unexpected ELF section table")
    headers = [
        struct.unpack_from("<IIQQQQIIQQ", data, table + index * stride)
        for index in range(count)
    ]

    def body(header):
        start, size = header[4], header[5]
        if start < 0 or size < 0 or start + size > len(data):
            raise ValueError("ELF section extent is outside the module")
        return data[start : start + size]

    names = body(headers[names_index])
    return {cstring(names, header[0]): body(header) for header in headers}


def parse_module(data):
    sections = elf_sections(data)
    try:
        modinfo = sections[".modinfo"]
        versions = sections["__versions"]
        this_module = sections[".gnu.linkonce.this_module"]
        this_module_relocations = sections[".rela.gnu.linkonce.this_module"]
    except KeyError as error:
        raise ValueError(f"missing required module section: {error.args[0]}") from error

    info = {}
    for item in modinfo.split(b"\0"):
        key, separator, value = item.partition(b"=")
        if separator:
            info.setdefault(key.decode("utf-8"), []).append(value.decode("utf-8"))
    if info.get("vermagic") != [VERMAGIC]:
        raise ValueError("captured module vermagic differs")

    if len(versions) % 64:
        raise ValueError("unexpected __versions entry size")
    symbols = {}
    for offset in range(0, len(versions), 64):
        crc = struct.unpack_from("<Q", versions, offset)[0]
        if crc > 0xFFFFFFFF:
            raise ValueError("module symbol CRC is wider than 32 bits")
        raw_name = versions[offset + 8 : offset + 64]
        name = raw_name.split(b"\0", 1)[0].decode("utf-8")
        if not name:
            raise ValueError("empty name in __versions")
        previous = symbols.setdefault(name, crc)
        if previous != crc:
            raise ValueError(f"conflicting CRC for {name}")
    if len(this_module_relocations) % 24:
        raise ValueError("unexpected struct module relocation entry size")
    relocation_offsets = sorted(
        struct.unpack_from("<Q", this_module_relocations, offset)[0]
        for offset in range(0, len(this_module_relocations), 24)
    )
    return info, symbols, len(this_module), relocation_offsets


def prepare(modules_dir, output_dir):
    if output_dir.exists():
        raise FileExistsError(f"refusing to overwrite existing output: {output_dir}")

    combined = {}
    module_receipts = {}
    symbol_sources = {}
    this_module_sizes = set()
    this_module_relocation_sets = set()
    for name, expected_hash in PINNED_MODULES.items():
        path = modules_dir / name
        data = path.read_bytes()
        actual_hash = sha256(data)
        if actual_hash != expected_hash:
            raise ValueError(f"pinned module hash mismatch: {name}")
        _, symbols, this_module_bytes, relocation_offsets = parse_module(data)
        this_module_sizes.add(this_module_bytes)
        this_module_relocation_sets.add(tuple(relocation_offsets))
        module_receipts[name] = {
            "bytes": len(data),
            "sha256": actual_hash,
            "this_module_bytes": this_module_bytes,
            "this_module_relocation_offsets": relocation_offsets,
        }
        for symbol, crc in symbols.items():
            if symbol in combined and combined[symbol] != crc:
                raise ValueError(f"captured modules disagree on CRC for {symbol}")
            combined[symbol] = crc
            symbol_sources.setdefault(symbol, []).append(name)

    missing = sorted(set(REQUIRED_SYMBOLS) - set(combined))
    if missing:
        raise ValueError("required CRCs are absent: " + ", ".join(missing))
    if len(this_module_sizes) != 1:
        raise ValueError("captured modules disagree on struct module size")
    this_module_bytes = this_module_sizes.pop()
    if len(this_module_relocation_sets) != 1:
        raise ValueError("captured modules disagree on struct module relocations")
    this_module_relocation_offsets = list(this_module_relocation_sets.pop())

    output_dir.mkdir(parents=True)
    lines = []
    selected = {}
    for symbol in sorted(REQUIRED_SYMBOLS):
        crc = combined[symbol]
        export = REQUIRED_SYMBOLS[symbol]
        # Linux 6.1 modpost expects the fifth namespace column even when the
        # exported symbol has no namespace.
        lines.append(f"0x{crc:08x}\t{symbol}\tvmlinux\t{export}\t\n")
        selected[symbol] = {
            "crc": f"0x{crc:08x}",
            "export": export,
            "observed_in": sorted(symbol_sources[symbol]),
        }

    symvers = "".join(lines).encode("utf-8")
    (output_dir / "Module.symvers").write_bytes(symvers)
    receipt = {
        "report_version": 4,
        "target": {"device": "duchamp", "soc": "mt6897"},
        "vermagic": VERMAGIC,
        "modules": module_receipts,
        "symbols": selected,
        "module_symvers": {"bytes": len(symvers), "sha256": sha256(symvers)},
        "module_contract": {
            "this_module_bytes": this_module_bytes,
            "this_module_relocation_offsets": this_module_relocation_offsets,
        },
        "safety": {
            "offline_only": True,
            "phone_access": False,
            "module_loading": False,
            "kernel_memory_access": False,
        },
    }
    (output_dir / "receipt.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return receipt


def main():
    parser = argparse.ArgumentParser(
        description="Prepare pinned Duchamp probe symbol CRCs without phone access."
    )
    parser.add_argument("modules", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = prepare(args.modules, args.output)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
