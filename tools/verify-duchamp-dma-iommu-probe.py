#!/usr/bin/env python3
"""Statically verify the Duchamp read-only DMA/IOMMU probe.

The verifier consumes only local files. It does not contact a phone and does
not load a kernel module.
"""

import argparse
import hashlib
import json
from pathlib import Path
import struct


EXPECTED_COMPILER = (
    "Android (10087095, +pgo, +bolt, +lto, -mlgo, based on r487747c) "
    "clang version 17.0.2 "
    "(https://android.googlesource.com/toolchain/llvm-project "
    "d9f89f4d16663d5012e5c09495f3b30ece3d2362)"
)
EXPECTED_INFO = {
    "name": "duchamp_dma_iommu_probe",
    "license": "GPL v2",
    "target_device": "duchamp",
    "target_soc": "mt6897",
    "target_kernel": "6.1.57-android14-11-gcf2c2dc91b9e-ab11782407",
    "depends": "",
}
SIGNATURE_MARKER = b"~Module signature appended~\n"


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def cstring(data, offset):
    if not 0 <= offset < len(data):
        raise ValueError("ELF string offset is outside its section")
    end = data.find(b"\0", offset)
    if end < 0:
        raise ValueError("unterminated ELF string")
    return data[offset:end].decode("utf-8")


def elf_layout(data):
    if data[:6] != b"\x7fELF\x02\x01":
        raise ValueError("expected little-endian ELF64 module")
    if struct.unpack_from("<HH", data, 16) != (1, 183):
        raise ValueError("expected AArch64 ET_REL module")

    table = struct.unpack_from("<Q", data, 40)[0]
    stride, count, names_index = struct.unpack_from("<HHH", data, 58)
    if stride != 64 or not 0 < names_index < count < 65536:
        raise ValueError("unexpected ELF section table")
    if table + stride * count > len(data):
        raise ValueError("ELF section table is outside the module")

    headers = [
        struct.unpack_from("<IIQQQQIIQQ", data, table + index * stride)
        for index in range(count)
    ]

    def body(header):
        start, size = header[4], header[5]
        if start + size > len(data):
            raise ValueError("ELF section extent is outside the module")
        return data[start : start + size]

    names = body(headers[names_index])
    sections = {}
    for index, header in enumerate(headers):
        name = cstring(names, header[0])
        sections[name] = {"index": index, "header": header, "data": body(header)}
    return headers, sections


def parse_modinfo(section):
    result = {}
    for item in section.split(b"\0"):
        key, separator, value = item.partition(b"=")
        if not separator:
            continue
        decoded_key = key.decode("utf-8")
        decoded_value = value.decode("utf-8")
        if decoded_key in result:
            raise ValueError(f"duplicate modinfo key: {decoded_key}")
        result[decoded_key] = decoded_value
    return result


def parse_versions(section):
    if len(section) % 64:
        raise ValueError("unexpected __versions entry size")
    result = {}
    for offset in range(0, len(section), 64):
        crc = struct.unpack_from("<Q", section, offset)[0]
        if crc > 0xFFFFFFFF:
            raise ValueError("module symbol CRC is wider than 32 bits")
        name = section[offset + 8 : offset + 64].split(b"\0", 1)[0].decode()
        if not name or name in result:
            raise ValueError("empty or duplicate symbol in __versions")
        result[name] = f"0x{crc:08x}"
    return result


def undefined_symbols(headers, sections):
    try:
        symbol_section = sections[".symtab"]
    except KeyError as error:
        raise ValueError("missing ELF symbol table") from error
    header = symbol_section["header"]
    entry_size = header[9]
    if entry_size != 24 or len(symbol_section["data"]) % entry_size:
        raise ValueError("unexpected ELF64 symbol table")
    strings_index = header[6]
    if strings_index >= len(headers):
        raise ValueError("symbol string table index is invalid")

    strings = next(
        (item["data"] for item in sections.values() if item["index"] == strings_index),
        None,
    )
    if strings is None:
        raise ValueError("missing ELF symbol string table")

    result = set()
    for offset in range(0, len(symbol_section["data"]), entry_size):
        name_offset, _, _, section_index, _, _ = struct.unpack_from(
            "<IBBHQQ", symbol_section["data"], offset
        )
        if section_index == 0 and name_offset:
            result.add(cstring(strings, name_offset))
    return sorted(result)


def verify(module_path, symvers_receipt_path, source_path, output_dir):
    if output_dir.exists():
        raise FileExistsError(f"refusing to overwrite existing output: {output_dir}")

    module = module_path.read_bytes()
    source = source_path.read_bytes()
    symvers_receipt_data = symvers_receipt_path.read_bytes()
    symvers_receipt = json.loads(symvers_receipt_data)
    if symvers_receipt.get("report_version") != 4:
        raise ValueError("unsupported symbol receipt version")

    headers, sections = elf_layout(module)
    try:
        info = parse_modinfo(sections[".modinfo"]["data"])
        comments = [
            item.decode("utf-8")
            for item in sections[".comment"]["data"].split(b"\0")
            if item
        ]
        versions = parse_versions(sections["__versions"]["data"])
    except KeyError as error:
        raise ValueError(f"missing required module section: {error.args[0]}") from error

    for key, expected in EXPECTED_INFO.items():
        if info.get(key) != expected:
            raise ValueError(f"unexpected modinfo value for {key}")
    expected_vermagic = symvers_receipt["vermagic"]
    if info.get("vermagic") != expected_vermagic:
        raise ValueError("module vermagic differs from captured modules")
    if comments != [EXPECTED_COMPILER]:
        raise ValueError("module compiler differs from captured modules")
    if SIGNATURE_MARKER in module:
        raise ValueError("unexpected appended module signature")

    expected_versions = {
        name: details["crc"] for name, details in symvers_receipt["symbols"].items()
    }
    if versions != expected_versions:
        raise ValueError("module symbol CRC set differs from captured modules")
    undefined = undefined_symbols(headers, sections)
    expected_undefined = sorted(set(expected_versions) - {"module_layout"})
    if undefined != expected_undefined:
        raise ValueError("module has an unexpected undefined symbol set")

    try:
        this_module_bytes = len(sections[".gnu.linkonce.this_module"]["data"])
    except KeyError as error:
        raise ValueError("missing struct module section") from error
    expected_this_module_bytes = symvers_receipt["module_contract"][
        "this_module_bytes"
    ]
    if this_module_bytes != expected_this_module_bytes:
        raise ValueError(
            "struct module size mismatch: "
            f"candidate=0x{this_module_bytes:x}, "
            f"captured=0x{expected_this_module_bytes:x}"
        )

    try:
        relocation_data = sections[".rela.gnu.linkonce.this_module"]["data"]
    except KeyError as error:
        raise ValueError("missing struct module relocations") from error
    if len(relocation_data) % 24:
        raise ValueError("unexpected struct module relocation entry size")
    this_module_relocation_offsets = sorted(
        struct.unpack_from("<Q", relocation_data, offset)[0]
        for offset in range(0, len(relocation_data), 24)
    )
    expected_relocation_offsets = symvers_receipt["module_contract"][
        "this_module_relocation_offsets"
    ]
    if this_module_relocation_offsets != expected_relocation_offsets:
        raise ValueError("struct module relocation offsets differ from captured modules")

    symvers_path = symvers_receipt_path.with_name("Module.symvers")
    symvers = symvers_path.read_bytes()
    if sha256(symvers) != symvers_receipt["module_symvers"]["sha256"]:
        raise ValueError("Module.symvers hash differs from its receipt")

    receipt = {
        "report_version": 1,
        "verdict": "static-verification-passed",
        "target": {"device": "duchamp", "soc": "mt6897"},
        "build": {
            "gki_commit": "cf2c2dc91b9e9f016dc25cf095b1fe34cb5dfcb6",
            "compiler": EXPECTED_COMPILER,
            "vermagic": expected_vermagic,
        },
        "module": {
            "name": module_path.name,
            "bytes": len(module),
            "sha256": sha256(module),
            "architecture": "AArch64",
            "elf_type": "ET_REL",
            "signature_appended": False,
            "this_module_bytes": this_module_bytes,
            "this_module_relocation_offsets": this_module_relocation_offsets,
            "undefined_symbols": undefined,
            "symbol_crcs": versions,
        },
        "source": {
            "name": source_path.name,
            "bytes": len(source),
            "sha256": sha256(source),
        },
        "symbol_receipt": {
            "name": symvers_receipt_path.name,
            "sha256": sha256(symvers_receipt_data),
            "module_symvers_sha256": sha256(symvers),
        },
        "safety": {
            "offline_only": True,
            "phone_access": False,
            "module_loaded": False,
            "runtime_values_observed": False,
        },
    }
    output_dir.mkdir(parents=True)
    (output_dir / "verification.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return receipt


def main():
    parser = argparse.ArgumentParser(
        description="Verify the local Duchamp DMA/IOMMU probe without loading it."
    )
    parser.add_argument("module", type=Path)
    parser.add_argument("symvers_receipt", type=Path)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    receipt = verify(args.module, args.symvers_receipt, args.source, args.output)
    print(json.dumps(receipt, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
