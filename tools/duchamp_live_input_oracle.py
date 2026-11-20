"""Independent final pixels for real-device GUI input tests."""
import hashlib
import json
import struct


def render(windows, focus, pointer, pressed=False, app_buttons=False):
    p = []
    for y in range(96):
        for x in range(160):
            c = 0xff102030 if y < 10 or y >= 80 else 0xff183040
            if 84 <= y < 92 and (12 <= x < 38 or 48 <= x < 74):
                c = 0xffe28a50 if x < 40 else 0xff589cdb
            if 3 <= y < 6 and 6 <= x < 50 and x % 5 < 3:
                c = 0xffd5e4ed
            if app_buttons and 84 <= y < 92 and (86 <= x < 104 or 108 <= x < 126 or 130 <= x < 150):
                c = 0xff86ac75 if x < 104 else 0xffc86a6a if x < 126 else 0xffad8bcd
            for wid, wx, wy, w, h in windows:
                u, v = x - wx, y - wy
                if not (0 <= u < w and 0 <= v < h):
                    continue
                c = 0xffe28a50 if wid == 2 else 0xff589cdb
                if 13 <= v < 17 and 6 <= u < 154:
                    c = 0xfff5e9dc
                if v < 9:
                    c = 0xffe8edf0 if focus == wid else 0xff7a8a98
                    if 3 <= v < 6 and 5 <= u < 25 and u % 5 < 3:
                        c = 0xff26323c
                if not u or not v or u == w - 1 or v == h - 1 or (u >= w - 5 and v >= h - 5):
                    c = 0xff26323c
            px, py = pointer
            if 0 <= x - px < 4 and 0 <= y - py < 5 and x - px <= (y - py) // 2:
                c = 0xffffdd55 if pressed else 0xfff3f5f7
            p.append(c)
    return struct.pack('<' + 'I' * len(p), *p)


def frames():
    red, blue = (2, 12, 16, 70, 44), (3, 60, 28, 72, 44)
    resized = (2, 26, 22, 80, 50)
    return dict(desktop=render([], 0, (0, 0)), windows=render([red, blue], 3, (0, 0)),
                focus=render([blue, red], 2, (24, 38)), move=render([blue, (2, 26, 22, 70, 44)], 2, (34, 25)),
                resize=render([blue, resized], 2, (104, 70)), disconnected=render([blue, resized], 2, (40, 50)),
                reconnected=render([resized, blue], 3, (120, 50)))


def write(out):
    result = []
    for name, raw in frames().items():
        (out / ('expected-' + name + '.raw')).write_bytes(raw)
        result.append(dict(name=name, x=320, y=1664, width=160, height=96, sha256=hashlib.sha256(raw).hexdigest()))
    path = out / 'live-frame-sequence.json'
    path.write_text(json.dumps(result, indent=2) + '\n')
    return path
