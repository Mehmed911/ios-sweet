#!/usr/bin/env python3
"""Independent Python reference: never reads guest-produced expected pixels."""
import hashlib
import json
from pathlib import Path
import struct

W, H = 160, 96


def frames():
    scenarios = (
        ('desktop', (), 0, (0, 0)),
        ('windows', ((2, 12, 16, 70, 44), (3, 60, 28, 72, 44)), 3, (0, 0)),
        ('focus', ((3, 60, 28, 72, 44), (2, 12, 16, 70, 44)), 2, (24, 38)),
        ('move', ((3, 60, 28, 72, 44), (2, 26, 22, 70, 44)), 2, (34, 25)),
        ('resize', ((3, 60, 28, 72, 44), (2, 26, 22, 80, 50)), 2, (104, 70)),
        ('cleanup', ((2, 26, 22, 80, 50),), 2, (104, 70)),
        ('restart', ((2, 12, 16, 70, 44),), 2, (0, 0)),
    )
    result = {}
    for name, windows, focus, pointer in scenarios:
        pixels = []
        for y in range(H):
            for x in range(W):
                c = 0xff183040
                if y < 10 or y >= H - 16:
                    c = 0xff102030
                if H - 12 <= y < H - 4 and (12 <= x < 38 or 48 <= x < 74):
                    c = 0xffe28a50 if x < 40 else 0xff589cdb
                if 3 <= y < 6 and 6 <= x < 50 and x % 5 < 3:
                    c = 0xffd5e4ed
                for wid, wx, wy, width, height in windows:
                    u, v = x - wx, y - wy
                    if not (0 <= u < width and 0 <= v < height):
                        continue
                    c = 0xffe28a50 if wid == 2 else 0xff589cdb
                    if 13 <= v < 17 and 6 <= u < W - 6:
                        c = 0xfff5e9dc
                    if v < 9:
                        c = 0xffe8edf0 if focus == wid else 0xff7a8a98
                        if 3 <= v < 6 and 5 <= u < 25 and u % 5 < 3:
                            c = 0xff26323c
                    if not u or not v or u == width - 1 or v == height - 1 or (u >= width - 5 and v >= height - 5):
                        c = 0xff26323c
                px, py = pointer
                if 0 <= x - px < 4 and 0 <= y - py < 5 and x - px <= (y - py) // 2:
                    c = 0xfff3f5f7
                pixels.append(c)
        result[name] = struct.pack('<' + 'I' * len(pixels), *pixels)
    return result


def write(out):
    out = Path(out)
    specs = []
    for name, raw in frames().items():
        (out / ('expected-' + name + '.raw')).write_bytes(raw)
        specs.append(dict(name=name, x=320, y=1664, width=W, height=H,
                          sha256=hashlib.sha256(raw).hexdigest()))
    path = out / 'gui-frame-sequence.json'
    path.write_text(json.dumps(specs, indent=2) + '\n')
    return path
