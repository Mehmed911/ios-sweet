#!/usr/bin/env python3
"""Verify the one-shot Duchamp XNU timer-IRQ framebuffer witness.

The witness is deliberately small and does not use the early text console: the
first virtual-timer IRQ that returns from rtclock_intr() paints a 16x32 cyan
rectangle in the bottom-right corner.  Checking the pixel immediately to the
left of every witness row prevents a pre-existing full-width bootshim band from
being mistaken for the XNU marker.
"""

import argparse
import json
import struct
from pathlib import Path


DEFAULT_WIDTH = 1220
DEFAULT_HEIGHT = 2712
DEFAULT_STRIDE = 4992
DEFAULT_MARKER_WIDTH = 16
DEFAULT_MARKER_HEIGHT = 32
DEFAULT_PIXEL = 0xFF00FFFF


def verify_witness(data, *, width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT,
                   stride=DEFAULT_STRIDE,
                   marker_width=DEFAULT_MARKER_WIDTH,
                   marker_height=DEFAULT_MARKER_HEIGHT,
                   expected=DEFAULT_PIXEL):
    if width <= 0 or height <= 0 or stride < width * 4:
        raise ValueError("invalid framebuffer geometry")
    if not 0 < marker_width < width or not 0 < marker_height <= height:
        raise ValueError("invalid witness geometry")
    required = stride * height
    if len(data) != required:
        raise ValueError(
            f"framebuffer size is {len(data)}, expected exactly {required}")

    start_x = width - marker_width
    start_y = height - marker_height
    matches = 0
    boundary_different = 0
    first_mismatch = None
    for y in range(start_y, height):
        boundary, = struct.unpack_from("<I", data, y * stride + (start_x - 1) * 4)
        boundary_different += boundary != expected
        for x in range(start_x, width):
            pixel, = struct.unpack_from("<I", data, y * stride + x * 4)
            if pixel == expected:
                matches += 1
            elif first_mismatch is None:
                first_mismatch = {"x": x, "y": y, "actual": f"0x{pixel:08x}"}

    total = marker_width * marker_height
    passed = matches == total and boundary_different == marker_height
    return {
        "passed": passed,
        "expected_pixel": f"0x{expected:08x}",
        "marker": {
            "x": start_x,
            "y": start_y,
            "width": marker_width,
            "height": marker_height,
        },
        "matching_pixels": matches,
        "expected_pixels": total,
        "boundary_rows_not_marker_color": boundary_different,
        "expected_boundary_rows": marker_height,
        "first_mismatch": first_mismatch,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("framebuffer", type=Path,
                        help="raw little-endian 32-bit Duchamp framebuffer dump")
    parser.add_argument("--width", type=int, default=DEFAULT_WIDTH)
    parser.add_argument("--height", type=int, default=DEFAULT_HEIGHT)
    parser.add_argument("--stride", type=int, default=DEFAULT_STRIDE)
    parser.add_argument("--marker-width", type=int, default=DEFAULT_MARKER_WIDTH)
    parser.add_argument("--marker-height", type=int, default=DEFAULT_MARKER_HEIGHT)
    parser.add_argument("--pixel", type=lambda value: int(value, 0),
                        default=DEFAULT_PIXEL)
    args = parser.parse_args()

    result = verify_witness(
        args.framebuffer.read_bytes(), width=args.width, height=args.height,
        stride=args.stride, marker_width=args.marker_width,
        marker_height=args.marker_height, expected=args.pixel)
    print(json.dumps(result, indent=2))
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
