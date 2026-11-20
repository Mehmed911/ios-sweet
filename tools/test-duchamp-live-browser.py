#!/usr/bin/env python3
"""Linux browser pointer actions through the normal live GUI, not GW injection.

Requires an isolated Playwright installation. These are automated browser
events, not a claim that a human or physical mouse operated this test.
"""
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
    argv = [sys.executable, '-B', 'tools/run-duchamp-live-input.py', session,
            '--artifacts', a.artifacts.resolve(), '--kernel-manifest', a.kernel_manifest.resolve(),
            '--mkfs', a.mkfs.resolve(), '--seconds', '240']
    checks = {}
    log = out / 'session.log'
    started = time.monotonic()
    with log.open('wb') as f:
        process = subprocess.Popen(list(map(str, argv)), stdout=f, stderr=subprocess.STDOUT)
        try:
            info = session / 'viewer/viewer.json'
            for _ in range(1000):
                if info.exists():
                    url = json.loads(info.read_text())['url']
                    break
                if process.poll() is not None:
                    raise RuntimeError(log.read_text()[-3000:])
                time.sleep(.1)
            else:
                raise TimeoutError('viewer unavailable')
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=True)
                page = browser.new_page(viewport={'width': 1000, 'height': 800})
                errors = []
                page.on('pageerror', lambda e: errors.append(str(e)))
                page.goto(url)
                page.wait_for_function("document.getElementById('state').textContent.includes('Mouse connected')", timeout=120000)

                def raw():
                    rgba = bytes(page.evaluate("Array.from(document.getElementById('screen').getContext('2d').getImageData(0,0,160,96).data)"))
                    p = bytearray(rgba)
                    p[0::4], p[2::4] = rgba[2::4], rgba[0::4]
                    return bytes(p)

                def wait(name, expected, seconds=70):
                    end = time.monotonic() + seconds
                    while time.monotonic() < end:
                        captured = raw()
                        if captured == expected:
                            (out / (name + '.raw')).write_bytes(captured)
                            page.screenshot(path=str(out / (name + '.png')))
                            checks[name] = True
                            return
                        page.wait_for_timeout(100)
                    page.screenshot(path=str(out / ('failed-' + name + '.png')))
                    raise TimeoutError(name)

                def move(x, y, steps=1):
                    box = page.locator('#screen').bounding_box()
                    assert box
                    page.mouse.move(box['x'] + (x + .25) * box['width'] / 160,
                                    box['y'] + (y + .25) * box['height'] / 96, steps=steps)

                def drain():
                    page.wait_for_function('!sending && queue.length===0')

                def click(x, y):
                    move(x, y)
                    page.mouse.down()
                    page.wait_for_timeout(100)
                    page.mouse.up()
                    drain()

                red, blue = (2, 12, 16, 70, 44), (3, 60, 28, 72, 44)
                wait('desktop', render([], 0, (0, 0)))
                click(24, 88)
                wait('launch_red', render([red], 2, (24, 88)))
                click(60, 88)
                wait('launch_blue', render([red, blue], 3, (60, 88)))
                click(24, 38)
                wait('focus_red', render([blue, red], 2, (24, 38)))
                pending = []

                def delay_drag_start(route):
                    body = route.request.post_data_json
                    if not pending and body.get('x') == 20 and body.get('y') == 19 and body.get('left') is False:
                        pending.append(route)  # Hold only the pre-press move.
                    else:
                        route.continue_()

                page.route('**/event', delay_drag_start)
                move(20, 19)
                page.mouse.down()
                move(34, 25, steps=3)
                page.mouse.up()
                for _ in range(100):
                    if pending:
                        break
                    page.wait_for_timeout(20)
                assert len(pending) == 1
                pending[0].continue_()
                drain()
                page.unroute('**/event', delay_drag_start)
                checks['queued_press_preserves_drag_origin'] = True
                moved = (2, 26, 22, 70, 44)
                wait('drag_window', render([blue, moved], 2, (34, 25)))
                move(94, 64)
                page.mouse.down()
                page.wait_for_timeout(150)
                move(104, 70, steps=3)
                page.wait_for_timeout(150)
                page.mouse.up()
                drain()
                resized = (2, 26, 22, 80, 50)
                wait('resize_window', render([blue, resized], 2, (104, 70)))
                move(40, 50)
                page.mouse.down()
                page.wait_for_timeout(150)
                box = page.locator('#screen').bounding_box()
                page.mouse.move(box['x'] + box['width'] + 30, box['y'] + box['height'] + 30)
                page.mouse.up()
                drain()
                wait('outside_release', render([blue, resized], 2, (159, 95)))
                move(40, 50)
                page.mouse.down()
                drain()
                wait('held_before_close', render([blue, resized], 2, (40, 50), True))
                page.close()
                time.sleep(4)  # No heartbeat: source watchdog must release.
                page = browser.new_page(viewport={'width': 1000, 'height': 800})
                page.goto(url)
                page.wait_for_function("document.getElementById('state').textContent.includes('Mouse connected')")
                wait('reconnect_released', render([blue, resized], 2, (40, 50)))
                click(120, 50)
                wait('reconnected_focus', render([resized, blue], 3, (120, 50)))
                checks['no_javascript_errors'] = not errors
                version = browser.version
                browser.close()
            process.wait(timeout=220)
            checks['normal_session_exit'] = process.returncode == 0
            journal = [json.loads(line) for line in (session / 'viewer/input-events.jsonl').read_text().splitlines()]
            checks['actual_browser_pointer_path'] = len([e for e in journal if e.get('origin') == 'browser-pointer']) >= 10
            checks['no_device_test_injection'] = not any(e.get('origin') == 'qmp-device-test' for e in journal)
            checks['source_lost_forces_release'] = any(e.get('origin') in ('source-timeout', 'source-disconnect') and e.get('left') is False for e in journal)
            result = dict(passed=all(checks.values()), checks=checks, browser=version,
                          elapsed_seconds=time.monotonic() - started, argv=list(map(str, argv)), exit_code=process.returncode,
                          input_origin='automated Linux Chromium pointer -> HTTP -> QMP -> VirtIO -> XNU -> normal shell',
                          human_mouse_claimed=False, phone_operations=[], physical_status='BLOCKED_BY_MEMORY_EVIDENCE')
            (out / 'verification.json').write_text(json.dumps(result, indent=2) + '\n')
            print(json.dumps(result, indent=2))
            return 0 if result['passed'] else 1
        finally:
            if process.poll() is None:
                process.send_signal(2)
                try:
                    process.wait(timeout=20)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()


if __name__ == '__main__':
    raise SystemExit(main())
