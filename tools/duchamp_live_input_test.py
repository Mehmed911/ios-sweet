"""Drive device-level QMP events through the same local mouse viewer API."""
import hashlib
import json
from pathlib import Path
import time
import urllib.request
import urllib.error
from duchamp_live_input import Viewer, png, qmp
from duchamp_live_input_oracle import frames


def drive(runtime_path, output, browser_pause=False):
    output = Path(output)
    output.mkdir(exist_ok=True)
    deadline = time.monotonic() + 180
    runtime = None
    while time.monotonic() < deadline:
        try:
            runtime = json.loads(Path(runtime_path).read_text())
            if Path(runtime['memory']).stat().st_size == runtime['ram_bytes']:
                qmp(runtime['qmp'], 'query-status')
                break
        except (OSError, ValueError, RuntimeError):
            pass
        time.sleep(.1)
    else:
        raise TimeoutError('QEMU live runtime unavailable')
    viewer = Viewer(runtime, output)
    checks = {}
    try:
        tree = qmp(runtime['qmp'], 'human-monitor-command', {'command-line': 'info qtree'})
        (output / 'qtree.txt').write_text(tree)
        registers = qmp(runtime['qmp'], 'human-monitor-command', {'command-line': 'xp /4wx 0xa003e00'})
        (output / 'virtio-identity.txt').write_text(registers)
        checks['actual_virtual_input_device'] = 'duchamp-pointer' in tree and 'virtio-tablet-device' in tree and all(v in registers for v in ('74726976', '00000002', '00000012', '554d4551'))
        sid, seq, heartbeat = None, 0, 0
        base = viewer.url.split('/#')[0]

        def post(path, body, expect=200):
            req = urllib.request.Request(base + path, json.dumps(body).encode(),
                {'Content-Type': 'application/json', 'X-Input-Token': viewer.token}, method='POST')
            try:
                with urllib.request.urlopen(req, timeout=8) as response:
                    status, data = response.status, response.read()
            except urllib.error.HTTPError as response:
                status, data = response.code, response.read()
            if status != expect:
                raise RuntimeError((path, status, data.decode()))
            return json.loads(data) if status == 200 else None

        def event(x, y, left):
            nonlocal seq
            post('/event', dict(id=sid, seq=seq + 1, x=x, y=y, left=left, origin='qmp-device-test'))
            seq += 1

        def beat():
            nonlocal heartbeat
            if sid and time.monotonic() - heartbeat > .8:
                post('/heartbeat', dict(id=sid))
                heartbeat = time.monotonic()

        expected = frames()

        def wait(name, hold=8):
            end = time.monotonic() + 70
            while time.monotonic() < end:
                beat()
                raw = viewer.read()
                if raw == expected[name]:
                    (output / (name + '.raw')).write_bytes(raw)
                    (output / (name + '.png')).write_bytes(png(raw))
                    checks['pixels_' + name] = True
                    for _ in range(hold * 5):
                        beat()
                        time.sleep(.2)
                    return
                time.sleep(.1)
            (output / ('failure-' + name + '.png')).write_bytes(png(viewer.read()))
            raise TimeoutError('frame not reached: ' + name)

        wait('desktop', hold=0)
        if browser_pause:
            (output / 'browser-ready').write_text(viewer.url + '\n')
            pause_end = time.monotonic() + 75
            while not (output / 'continue-tests').exists() and time.monotonic() < pause_end:
                time.sleep(.1)
            checks['browser_pointer_events'] = any(e.get('origin') == 'browser-pointer' for e in viewer.events)
        for _ in range(100):
            try:
                sid = post('/connect', {})['id']
                break
            except RuntimeError:
                time.sleep(.1)
        else:
            raise TimeoutError('native input driver did not become ready')
        before = len([e for e in viewer.events if e['kind'] == 'device_event'])
        invalid = dict(id=sid, seq=1, x=-1, y=0, left=False, origin='qmp-device-test')
        post('/event', invalid, 400)
        invalid['x'] = 0
        invalid['seq'] = 2
        post('/event', invalid, 400)
        invalid['seq'] = 1
        invalid['id'] = 'stale'
        post('/event', invalid, 400)
        checks['invalid_events_never_reach_device'] = before == len([e for e in viewer.events if e['kind'] == 'device_event'])
        event(0, 0, False)
        wait('desktop')
        for x in (24, 60):
            event(x, 88, True)
            time.sleep(.15)
            event(x, 88, False)
            time.sleep(.5)
        event(0, 0, False)
        wait('windows')
        event(24, 38, True)
        time.sleep(.2)
        event(24, 38, False)
        wait('focus')
        event(20, 19, True)
        time.sleep(.2)
        event(34, 25, True)
        time.sleep(.2)
        event(34, 25, False)
        wait('move')
        event(94, 64, True)
        time.sleep(.2)
        event(104, 70, True)
        time.sleep(.2)
        event(104, 70, False)
        wait('resize')
        event(40, 50, True)
        # Native observer now kickstarts the input process while held. Its
        # real cdev close/reset and endpoint death must force a release.
        wait('disconnected')
        old = sid
        post('/disconnect', dict(id=sid))
        sid = post('/connect', {})['id']
        seq = 0
        post('/heartbeat', dict(id=old), 400)
        event(120, 50, True)
        time.sleep(.2)
        event(120, 50, False)
        wait('reconnected')
        checks['host_source_reconnect'] = sid != old
        result = dict(passed=all(checks.values()), checks=checks,
                      scope='QMP-generated events processed by actual VirtIO tablet and XNU driver; browser events recorded separately',
                      phone_operations=[], physical_status='BLOCKED_BY_MEMORY_EVIDENCE')
        (output / 'verification.json').write_text(json.dumps(result, indent=2) + '\n')
        return result
    finally:
        viewer.close()
