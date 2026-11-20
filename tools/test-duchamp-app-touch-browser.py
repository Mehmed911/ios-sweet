#!/usr/bin/env python3
"""Automated Chromium contacts and toolbar -> native application service/WM."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
from duchamp_live_input_oracle import render
from playwright.sync_api import sync_playwright


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('output', type=Path)
    ap.add_argument('--artifacts', type=Path, required=True)
    ap.add_argument('--kernel-manifest', type=Path, required=True)
    ap.add_argument('--mkfs', type=Path, required=True)
    a = ap.parse_args()
    out = a.output.resolve()
    out.mkdir()
    session = out / 'session'
    argv = list(map(str, [sys.executable, '-B', 'tools/run-duchamp-live-input.py', session,
                         '--artifacts', a.artifacts.resolve(), '--kernel-manifest', a.kernel_manifest.resolve(),
                         '--mkfs', a.mkfs.resolve(), '--seconds', '240', '--applications']))
    checks = {}
    with (out / 'session.log').open('wb') as f:
        p = subprocess.Popen(argv, stdout=f, stderr=subprocess.STDOUT)
        try:
            for _ in range(1200):
                info = session / 'viewer/viewer.json'
                if info.exists():
                    url = json.loads(info.read_text())['url']
                    break
                if p.poll() is not None:
                    raise RuntimeError((out / 'session.log').read_text()[-2000:])
                time.sleep(.1)
            else:
                raise TimeoutError('viewer startup')
            with sync_playwright() as pw:
                browser = pw.chromium.launch(headless=True)
                page = browser.new_page(viewport={'width': 1000, 'height': 800})
                errors = []
                page.on('pageerror', lambda e: errors.append(str(e)))
                page.goto(url)
                page.wait_for_function("document.getElementById('state').textContent.includes('Multitouch connected')", timeout=120000)

                def drain():
                    page.wait_for_function('!sending && queue.length===0', timeout=30000)

                def pixels():
                    rgba = bytes(page.evaluate("Array.from(document.getElementById('screen').getContext('2d').getImageData(0,0,160,96).data)"))
                    b = bytearray(rgba)
                    b[0::4], b[2::4] = rgba[2::4], rgba[0::4]
                    return bytes(b)

                def wait(name, windows, focus, pointer, pressed=False):
                    expected = render(windows, focus, pointer, pressed, app_buttons=True)
                    end = time.monotonic() + 60
                    while time.monotonic() < end:
                        if pixels() == expected:
                            (out / (name + '.raw')).write_bytes(expected)
                            page.screenshot(path=str(out / (name + '.png')))
                            checks[name] = True
                            return
                        page.wait_for_timeout(100)
                    page.screenshot(path=str(out / ('failed-' + name + '.png')))
                    raise TimeoutError(name)

                def position(x, y):
                    box = page.locator('#screen').bounding_box()
                    return dict(x=box['x'] + (x + .25) * box['width'] / 160,
                                y=box['y'] + (y + .25) * box['height'] / 96)

                def click(x, y):
                    page.mouse.move(**position(x, y))
                    page.mouse.down()
                    page.wait_for_timeout(150)
                    page.mouse.up()
                    drain()

                red, blue = (2, 12, 16, 70, 44), (3, 60, 28, 72, 44)
                wait('desktop', [], 0, (0, 0))
                click(24, 88)
                wait('launch_red', [red], 2, (24, 88))
                click(60, 88)
                wait('launch_blue', [red, blue], 3, (60, 88))
                click(24, 38)
                wait('focus_red', [blue, red], 2, (24, 38))
                cdp = page.context.new_cdp_session(page)

                def contacts(kind, points):
                    cdp.send('Input.dispatchTouchEvent', dict(type=kind,
                             touchPoints=[dict(id=cid, **position(x, y), radiusX=1, radiusY=1, force=1) for cid, x, y in points]))
                    drain()

                contacts('touchStart', [(10, 20, 19), (11, 130, 70)])
                page.wait_for_timeout(300)
                contacts('touchMove', [(10, 34, 25), (11, 140, 74)])
                page.wait_for_timeout(300)
                contacts('touchEnd', [])
                moved, resized = (2, 26, 22, 70, 44), (3, 60, 28, 82, 48)
                wait('dual_drag_resize', [moved, resized], 3, (140, 74))
                click(94, 88)
                wait('toolbar_background', [moved], 2, (94, 88))
                click(60, 88)
                wait('toolbar_foreground', [moved, resized], 3, (60, 88))
                click(116, 88)
                wait('toolbar_close', [moved], 2, (116, 88))
                click(60, 88)
                wait('toolbar_relaunch', [moved, blue], 3, (60, 88))
                click(140, 88)
                wait('toolbar_restart', [moved, blue], 3, (140, 88))
                contacts('touchStart', [(10, 40, 50), (11, 120, 50)])
                wait('two_held', [moved, blue], 3, (120, 50), True)
                contacts('touchCancel', [])
                wait('browser_cancel_ends_contacts', [moved, blue], 3, (120, 50))
                checks['no_javascript_errors'] = not errors
                version = browser.version
                browser.close()
            p.wait(timeout=240)
            checks['normal_session_exit'] = p.returncode == 0
            journal = [json.loads(line) for line in (session / 'viewer/input-events.jsonl').read_text().splitlines()]
            events = [e for e in journal if e.get('kind') == 'touch_device']
            active, simultaneous = {}, False
            for event in events:
                for c in event['contacts']:
                    if c['phase'] in ('begin', 'move'):
                        active[c['slot']] = c['id']
                    else:
                        active.pop(c['slot'], None)
                simultaneous |= len(active) >= 2
            checks['actual_two_contact_browser_path'] = simultaneous and any(e['origin'] == 'browser-multitouch' for e in events)
            checks['no_qmp_test_source'] = not any(e['origin'] == 'qmp-multitouch-test' for e in events)
            checks['browser_cancel_path'] = any(c['phase'] == 'cancel' for e in events for c in e['contacts'])
            # Pixel equality alone cannot prove that the restart button caused
            # a new process. Verify the guest's audited PID/birth trace too.
            receipt = out / 'native-postflight'
            native = subprocess.run([sys.executable, '-B', 'tools/verify-duchamp-app-session.py', str(session), str(receipt)],
                                    capture_output=True, text=True, timeout=90)
            (out / 'native-postflight.log').write_text(native.stdout + native.stderr)
            checks['native_lifecycle_postflight'] = native.returncode == 0
            result = dict(passed=all(checks.values()), checks=checks, browser=version, argv=argv, exit_code=p.returncode,
                          origin='automated Linux Chromium/CDP -> DOM PointerEvents -> QMP MTT -> real VirtIO -> XNU',
                          human_or_physical_touch_claimed=False, phone_operations=[], physical_status='BLOCKED_BY_MEMORY_EVIDENCE',
                          image_hashes={p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in out.glob('*.raw')})
            (out / 'verification.json').write_text(json.dumps(result, indent=2) + '\n')
            print(json.dumps(result, indent=2))
            return 0 if result['passed'] else 1
        finally:
            if p.poll() is None:
                p.send_signal(2)
                try:
                    p.wait(timeout=20)
                except subprocess.TimeoutExpired:
                    p.kill()
                    p.wait()


if __name__ == '__main__':
    raise SystemExit(main())
