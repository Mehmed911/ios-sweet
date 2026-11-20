"""Independent framebuffer bytes for app lifecycle and real VirtIO contacts."""
import hashlib
import json
from duchamp_live_input_oracle import render


def frames():
    red, blue = (2, 12, 16, 70, 44), (3, 60, 28, 72, 44)
    moved, resized = (2, 26, 22, 70, 44), (3, 60, 28, 82, 48)

    def r(windows, focus, pointer, held=False):
        return render(windows, focus, pointer, held, app_buttons=True)
    return dict(apps=r([blue, red], 2, (0, 0)),
                dual=r([moved, resized], 3, (140, 74)),
                cancelled=r([moved, resized], 3, (120, 55)),
                background=r([moved], 2, (120, 55)),
                foreground=r([moved, resized], 3, (120, 55)),
                closed=r([moved], 2, (120, 55)),
                restarted=r([moved, blue], 3, (120, 55)),
                crashed=r([blue], 3, (40, 50), True),
                crash_restarted=r([blue, red], 2, (40, 50), True),
                fresh_contact=r([blue, red], 2, (40, 50)),
                empty=r([], 0, (40, 50)),
                final=r([red, blue], 3, (40, 50)))


def write(out):
    result = []
    for name, raw in frames().items():
        (out / ('expected-' + name + '.raw')).write_bytes(raw)
        result.append(dict(name=name, x=320, y=1664, width=160, height=96, sha256=hashlib.sha256(raw).hexdigest()))
    path = out / 'app-touch-frame-sequence.json'
    path.write_text(json.dumps(result, indent=2) + '\n')
    return path
