#!/usr/bin/env python3
"""Pack one immutable SWEETXNU payload for the MT6897 LK RAM provider."""

import argparse
import pathlib
import struct

MAGIC = b"DUCHLKR1"
VERSION = 1
HEADER_SIZE = 64
FLAG_IMMUTABLE = 1


def receipt(data):
    value = 1469598103934665603
    for byte in data:
        value ^= byte
        value = value * 1099511628211 & 0xFFFFFFFFFFFFFFFF
    value ^= len(data)
    return value * 1099511628211 & 0xFFFFFFFFFFFFFFFF


def build(payload, generation):
    if not payload:
        raise ValueError("payload is empty")
    if generation <= 0 or generation > 0xFFFFFFFFFFFFFFFF:
        raise ValueError("generation must be in 1..2^64-1")
    total = HEADER_SIZE + len(payload)
    header = struct.pack(
        "<8sIIQQQQQQ",
        MAGIC,
        VERSION,
        HEADER_SIZE,
        total,
        generation,
        HEADER_SIZE,
        len(payload),
        receipt(payload),
        FLAG_IMMUTABLE,
    )
    assert len(header) == HEADER_SIZE
    return header + payload


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("payload", type=pathlib.Path)
    parser.add_argument("output", type=pathlib.Path)
    parser.add_argument("--generation", type=lambda value: int(value, 0),
                        required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error(f"refusing to overwrite {args.output}")
    data = args.payload.read_bytes()
    capsule = build(data, args.generation)
    args.output.write_bytes(capsule)
    print(f"{args.output}: {len(capsule)} bytes, generation "
          f"{args.generation}, payload {len(data)}, receipt "
          f"0x{receipt(data):016x}")


if __name__ == "__main__":
    main()
