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
import zlib
from pathlib import Path


DEFAULT_WIDTH = 1220
DEFAULT_HEIGHT = 2712
DEFAULT_STRIDE = 4992
DEFAULT_MARKER_WIDTH = 16
DEFAULT_MARKER_HEIGHT = 32
DEFAULT_PIXEL = 0xFF00FFFF
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def decode_qemu_png(data, *, width, height, stride):
    """Return the runner's filter-0 RGB PNG as XNU little-endian pixels."""
    if not data.startswith(PNG_SIGNATURE):
        raise ValueError("not a PNG framebuffer")
    offset = len(PNG_SIGNATURE)
    header = None
    compressed = bytearray()
    saw_end = False
    while offset < len(data):
        if offset + 12 > len(data):
            raise ValueError("truncated PNG chunk")
        length, = struct.unpack_from(">I", data, offset)
        kind = data[offset + 4:offset + 8]
        end = offset + 12 + length
        if end > len(data):
            raise ValueError("truncated PNG payload")
        payload = data[offset + 8:offset + 8 + length]
        checksum, = struct.unpack_from(">I", data, offset + 8 + length)
        if zlib.crc32(kind + payload) & 0xFFFFFFFF != checksum:
            raise ValueError("PNG chunk CRC mismatch")
        if kind == b"IHDR":
            if header is not None or length != 13:
                raise ValueError("invalid PNG header")
            header = struct.unpack(">IIBBBBB", payload)
        elif kind == b"IDAT":
            compressed.extend(payload)
        elif kind == b"IEND":
            if length != 0:
                raise ValueError("invalid PNG end chunk")
            saw_end = True
            offset = end
            break
        offset = end
    expected_header = (width, height, 8, 2, 0, 0, 0)
    if header != expected_header:
        raise ValueError(f"unexpected PNG header {header!r}")
    if not compressed or not saw_end or offset != len(data):
        raise ValueError("incomplete PNG framebuffer")
    try:
        rows = zlib.decompress(bytes(compressed))
    except zlib.error as error:
        raise ValueError("invalid PNG compressed data") from error
    row_bytes = width * 3
    if len(rows) != height * (row_bytes + 1):
        raise ValueError("unexpected PNG row data size")
    raw = bytearray(stride * height)
    for y in range(height):
        source = y * (row_bytes + 1)
        if rows[source] != 0:
            raise ValueError("unsupported PNG row filter")
        row = rows[source + 1:source + 1 + row_bytes]
        for x in range(width):
            r, g, b = row[x * 3:x * 3 + 3]
            struct.pack_into("<I", raw, y * stride + x * 4,
                             0xFF000000 | r << 16 | g << 8 | b)
    return bytes(raw)


def load_framebuffer(path, *, width, height, stride):
    data = path.read_bytes()
    if data.startswith(PNG_SIGNATURE):
        return decode_qemu_png(
            data, width=width, height=height, stride=stride), "qemu-png"
    return data, "raw-a8r8g8b8"


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
                        help="raw little-endian 32-bit dump or qemu-sweet PNG")
    parser.add_argument("--width", type=int, default=DEFAULT_WIDTH)
    parser.add_argument("--height", type=int, default=DEFAULT_HEIGHT)
    parser.add_argument("--stride", type=int, default=DEFAULT_STRIDE)
    parser.add_argument("--marker-width", type=int, default=DEFAULT_MARKER_WIDTH)
    parser.add_argument("--marker-height", type=int, default=DEFAULT_MARKER_HEIGHT)
    parser.add_argument("--pixel", type=lambda value: int(value, 0),
                        default=DEFAULT_PIXEL)
    args = parser.parse_args()

    data, source_format = load_framebuffer(
        args.framebuffer, width=args.width, height=args.height,
        stride=args.stride)
    result = verify_witness(
        data, width=args.width, height=args.height,
        stride=args.stride, marker_width=args.marker_width,
        marker_height=args.marker_height, expected=args.pixel)
    result["source_format"] = source_format
    print(json.dumps(result, indent=2))
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
