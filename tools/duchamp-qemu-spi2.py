#!/usr/bin/env python3
"""Attach synthetic FocalTech SPI replies to a Duchamp QEMU-only ADT."""
import argparse
from pathlib import Path

import adt


# Coordinates in the existing SweetHIDTouch space, in gesture order.
SWIPE_Y = (2380, 2350, 2290, 2180, 2020, 1810, 1580, 1350, 1180, 1180)


def reply(payload):
    crc = 0xffff
    for byte in payload:
        crc ^= byte
        for _ in range(8):
            crc = (crc >> 1) ^ (0x8408 if crc & 1 else 0)
    return bytes(7) + bytes(payload) + crc.to_bytes(2, "little")


def report(x, y, phase, finger=0):
    # Round up so the inverse integer scale restores the requested HID position.
    x = (x * (1220 * 16) + 1079) // 1080
    y = (y * (2712 * 16) + 2399) // 2400
    payload = bytearray(91)
    payload[1] = 0x21  # Extended format, one point.
    payload[4:9] = bytes((phase << 6 | x >> 12, (x >> 4) & 0xff,
                          finger << 4 | y >> 12, (y >> 4) & 0xff,
                          (x & 0xf) << 4 | y & 0xf))
    return reply(payload)


def with_fixture(blob):
    root, end = adt.parse(blob)
    chosen = [child for child in root.children if child.name == "chosen"]
    if (end != len(blob) or len(chosen) != 1
            or chosen[0].prop("firmware-version") != b"duchamp-qemu-ufs-fixture-v1\0"):
        raise ValueError("expected the split-root Duchamp QEMU profile")
    if any(child.name == "duchamp-qemu-spi2" for child in root.children):
        raise ValueError("SPI2 fixture is already present")
    frames = [report(540, y, 0 if index == 0 else 1 if index == len(SWIPE_Y) - 1 else 2)
              for index, y in enumerate(SWIPE_Y)]
    corrupted = bytearray(report(320, 1300, 0, finger=9))
    corrupted[-1] ^= 1
    frames.insert(1, bytes(corrupted))
    node = adt.Node()
    node.props = [
        ("name", 0, b"duchamp-qemu-spi2\0"),
        ("compatible", 0, b"qemu,duchamp-spi2-touch-test-v1\0"),
        ("id-high-response", 0, reply(b"\x12")),
        ("id-low-response", 0, reply(b"\x34")),
        ("reports", 0, b"".join(frames)),
    ]
    root.children.append(node)
    return adt.serialize(root)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    try:
        fixture = with_fixture(args.source.read_bytes())
        with args.output.open("xb") as destination:
            destination.write(fixture)
    except (ValueError, OSError) as error:
        parser.exit(1, f"QEMU SPI2 fixture failed: {error}\n")
