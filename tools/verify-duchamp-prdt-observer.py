#!/usr/bin/env python3
"""Statically verify the passive Duchamp UFS PRDT observer.

The verifier is local-only. It checks the complete imported symbol/CRC set,
compiler identity, module ABI layout, metadata and source receipt before an
artifact can be considered for a separately approved phone test.
"""

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import struct


BASE_SCRIPT = Path(__file__).with_name("verify-duchamp-dma-iommu-probe.py")
EXPECTED_COMPILER = (
    "Android (10087095, +pgo, +bolt, +lto, -mlgo, based on r487747c) "
    "clang version 17.0.2 "
    "(https://android.googlesource.com/toolchain/llvm-project "
    "d9f89f4d16663d5012e5c09495f3b30ece3d2362)"
)
EXPECTED_INFO = {
    "name": "duchamp_ufs_prdt_observer",
    "license": "GPL v2",
    "target_device": "duchamp",
    "target_soc": "mt6897",
    "target_kernel": "6.1.57-android14-11-gcf2c2dc91b9e-ab11782407",
    "observation_mode": "existing-io-only",
    "depends": "",
}
SIGNATURE_MARKER = b"~Module signature appended~\n"


def load_base():
    spec = importlib.util.spec_from_file_location("duchamp_probe_verify", BASE_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def verify(module_path, symvers_receipt_path, source_path, output_dir):
    if output_dir.exists():
        raise FileExistsError(f"refusing to overwrite existing output: {output_dir}")

    base = load_base()
    module = module_path.read_bytes()
    source = source_path.read_bytes()
    receipt_data = symvers_receipt_path.read_bytes()
    receipt = json.loads(receipt_data)
    if receipt.get("report_version") != 1:
        raise ValueError("unsupported symbol receipt version")
    if receipt.get("profile") != "duchamp-ufs-prdt-observer":
        raise ValueError("wrong symbol receipt profile")

    headers, sections = base.elf_layout(module)
    try:
        info = base.parse_modinfo(sections[".modinfo"]["data"])
        comments = [
            item.decode("utf-8")
            for item in sections[".comment"]["data"].split(b"\0")
            if item
        ]
        versions = base.parse_versions(sections["__versions"]["data"])
    except KeyError as error:
        raise ValueError(f"missing required module section: {error.args[0]}") from error

    for key, expected in EXPECTED_INFO.items():
        if info.get(key) != expected:
            raise ValueError(f"unexpected modinfo value for {key}")
    if info.get("vermagic") != receipt["vermagic"]:
        raise ValueError("module vermagic differs from captured modules")
    if comments != [EXPECTED_COMPILER]:
        raise ValueError("module compiler differs from captured modules")
    if SIGNATURE_MARKER in module:
        raise ValueError("unexpected appended module signature")

    expected_versions = {
        name: details["crc"] for name, details in receipt["symbols"].items()
    }
    if versions != expected_versions:
        raise ValueError("module symbol CRC set differs from captured modules")
    undefined = base.undefined_symbols(headers, sections)
    expected_undefined = sorted(set(expected_versions) - {"module_layout"})
    if undefined != expected_undefined:
        raise ValueError("module has an unexpected undefined symbol set")

    try:
        this_module_bytes = len(sections[".gnu.linkonce.this_module"]["data"])
        relocation_data = sections[".rela.gnu.linkonce.this_module"]["data"]
    except KeyError as error:
        raise ValueError(f"missing module ABI section: {error.args[0]}") from error
    if len(relocation_data) % 24:
        raise ValueError("unexpected struct module relocation entry size")
    relocation_offsets = sorted(
        struct.unpack_from("<Q", relocation_data, offset)[0]
        for offset in range(0, len(relocation_data), 24)
    )
    contract = receipt["module_contract"]
    if this_module_bytes != contract["this_module_bytes"]:
        raise ValueError(
            "struct module size mismatch: "
            f"candidate=0x{this_module_bytes:x}, "
            f"captured=0x{contract['this_module_bytes']:x}"
        )
    if relocation_offsets != contract["this_module_relocation_offsets"]:
        raise ValueError("struct module relocation offsets differ from captured modules")

    symvers_path = symvers_receipt_path.with_name("Module.symvers")
    symvers = symvers_path.read_bytes()
    if sha256(symvers) != receipt["module_symvers"]["sha256"]:
        raise ValueError("Module.symvers hash differs from its receipt")

    result = {
        "report_version": 1,
        "verdict": "static-verification-passed",
        "target": {"device": "duchamp", "soc": "mt6897"},
        "build": {
            "gki_commit": "cf2c2dc91b9e9f016dc25cf095b1fe34cb5dfcb6",
            "compiler": EXPECTED_COMPILER,
            "vermagic": receipt["vermagic"],
        },
        "module": {
            "name": module_path.name,
            "bytes": len(module),
            "sha256": sha256(module),
            "architecture": "AArch64",
            "elf_type": "ET_REL",
            "signature_appended": False,
            "this_module_bytes": this_module_bytes,
            "this_module_relocation_offsets": relocation_offsets,
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
            "sha256": sha256(receipt_data),
            "module_symvers_sha256": sha256(symvers),
        },
        "safety": {
            "offline_only": True,
            "phone_access": False,
            "module_loaded": False,
            "runtime_values_observed": False,
            "storage_io_issued": False,
            "dma_mapping_created": False,
            "mmio_accessed": False,
            "firmware_called": False,
        },
    }
    output_dir.mkdir(parents=True)
    (output_dir / "verification.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return result


def main():
    parser = argparse.ArgumentParser(
        description="Verify the passive Duchamp UFS PRDT observer offline."
    )
    parser.add_argument("module", type=Path)
    parser.add_argument("symvers_receipt", type=Path)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    print(
        json.dumps(
            verify(args.module, args.symvers_receipt, args.source, args.output),
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
