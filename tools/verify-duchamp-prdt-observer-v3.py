#!/usr/bin/env python3
"""Verify the local-only Duchamp UFS PRDT observer v3 artifact."""

import argparse
import importlib.util
import json
from pathlib import Path


BASE = Path(__file__).with_name("verify-duchamp-prdt-observer.py")


def load_base():
    spec = importlib.util.spec_from_file_location("duchamp_prdt_v2_verify", BASE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.EXPECTED_INFO = dict(module.EXPECTED_INFO)
    module.EXPECTED_INFO["name"] = "duchamp_ufs_prdt_observer_v3"
    return module


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("module", type=Path)
    parser.add_argument("symvers_receipt", type=Path)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    verifier = load_base()
    result = verifier.verify(
        args.module, args.symvers_receipt, args.source, args.output
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
