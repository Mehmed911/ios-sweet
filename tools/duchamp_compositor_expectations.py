#!/usr/bin/env python3
"""Independent pixel oracle for the bounded straight-alpha compositor test."""
import hashlib
import json
from pathlib import Path


def frames():
    result = {}
    for name in ('blend', 'dirty', 'zorder', 'restored', 'cleanup_overlay', 'cleanup_all'):
        pixels = bytearray()
        for y in range(32):
            for x in range(64):
                color = (16, 32, 48) if name == 'cleanup_all' else (255, 0, 0)
                if name in ('blend', 'dirty', 'restored') and 16 <= x < 48 and 8 <= y < 24:
                    # Straight-alpha source-over onto the opaque red surface.
                    foreground = (0, 255, 0) if name != 'blend' and x < 24 and y < 16 else (0, 0, 255)
                    color = tuple((s * 128 + d * 127 + 127) // 255 for s, d in zip(foreground, color))
                r, g, b = color
                pixels += bytes((b, g, r, 255))
        result[name] = bytes(pixels)
    return result


def write(output):
    output = Path(output)
    sequence = []
    for name, pixels in frames().items():
        (output / ('expected-' + name + '.raw')).write_bytes(pixels)
        sequence.append(dict(name=name, x=320, y=1664, width=64, height=32,
                             sha256=hashlib.sha256(pixels).hexdigest()))
    path = output / 'frame-sequence-spec.json'
    path.write_text(json.dumps(sequence, indent=2) + '\n')
    return path
