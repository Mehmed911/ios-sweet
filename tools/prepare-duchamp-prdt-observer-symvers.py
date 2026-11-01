#!/usr/bin/env python3
"""Prepare the minimal captured-ABI symbol set for the PRDT observer.

The source CRCs come only from the six pinned vendor modules already captured
from the Duchamp software image. The tool is offline and never contacts or
modifies a phone.
"""

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path


BASE_SCRIPT = Path(__file__).with_name("prepare-duchamp-probe-symvers.py")
REQUIRED_SYMBOLS = {
    "_raw_spin_lock_irqsave": "EXPORT_SYMBOL",
    "_raw_spin_unlock_irqrestore": "EXPORT_SYMBOL",
    "__tracepoint_android_vh_ufs_fill_prdt": "EXPORT_SYMBOL_GPL",
    "device_create_file": "EXPORT_SYMBOL_GPL",
    "device_remove_file": "EXPORT_SYMBOL_GPL",
    "iommu_get_domain_for_dev": "EXPORT_SYMBOL_GPL",
    "memstart_addr": "EXPORT_SYMBOL",
    "module_layout": "EXPORT_SYMBOL",
    "of_find_compatible_node": "EXPORT_SYMBOL",
    "of_find_device_by_node": "EXPORT_SYMBOL",
    "put_device": "EXPORT_SYMBOL_GPL",
    "sg_next": "EXPORT_SYMBOL",
    "sysfs_emit": "EXPORT_SYMBOL_GPL",
    "synchronize_rcu": "EXPORT_SYMBOL_GPL",
    "synchronize_srcu": "EXPORT_SYMBOL_GPL",
    "tracepoint_probe_register": "EXPORT_SYMBOL_GPL",
    "tracepoint_probe_unregister": "EXPORT_SYMBOL_GPL",
    "tracepoint_srcu": "EXPORT_SYMBOL_GPL",
}


def load_base():
    spec = importlib.util.spec_from_file_location("duchamp_probe_symvers", BASE_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def prepare(modules_dir, output_dir):
    if output_dir.exists():
        raise FileExistsError(f"refusing to overwrite existing output: {output_dir}")

    base = load_base()
    combined = {}
    module_receipts = {}
    symbol_sources = {}
    this_module_sizes = set()
    this_module_relocation_sets = set()

    for name, expected_hash in base.PINNED_MODULES.items():
        path = modules_dir / name
        data = path.read_bytes()
        actual_hash = sha256(data)
        if actual_hash != expected_hash:
            raise ValueError(f"pinned module hash mismatch: {name}")
        _, symbols, this_module_bytes, relocation_offsets = base.parse_module(data)
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
    if len(this_module_relocation_sets) != 1:
        raise ValueError("captured modules disagree on struct module relocations")

    output_dir.mkdir(parents=True)
    lines = []
    selected = {}
    for symbol in sorted(REQUIRED_SYMBOLS):
        crc = combined[symbol]
        export = REQUIRED_SYMBOLS[symbol]
        lines.append(f"0x{crc:08x}\t{symbol}\tvmlinux\t{export}\t\n")
        selected[symbol] = {
            "crc": f"0x{crc:08x}",
            "export": export,
            "observed_in": sorted(symbol_sources[symbol]),
        }

    symvers = "".join(lines).encode("utf-8")
    (output_dir / "Module.symvers").write_bytes(symvers)
    receipt = {
        "report_version": 1,
        "profile": "duchamp-ufs-prdt-observer",
        "target": {"device": "duchamp", "soc": "mt6897"},
        "vermagic": base.VERMAGIC,
        "modules": module_receipts,
        "symbols": selected,
        "module_symvers": {"bytes": len(symvers), "sha256": sha256(symvers)},
        "module_contract": {
            "this_module_bytes": this_module_sizes.pop(),
            "this_module_relocation_offsets": list(
                this_module_relocation_sets.pop()
            ),
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
        description="Prepare captured Duchamp CRCs for the passive PRDT observer."
    )
    parser.add_argument("modules", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    print(json.dumps(prepare(args.modules, args.output), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
