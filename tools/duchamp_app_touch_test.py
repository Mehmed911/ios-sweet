"""Host device events only; native observer separately verifies app processes."""
import json
from pathlib import Path
import time
from duchamp_touch_input import TouchViewer
from duchamp_live_input import png, qmp
from duchamp_app_touch_oracle import frames


def drive(runtime_path, output, stop=None):
    output = Path(output)
    output.mkdir()
    for _ in range(1800):
        if stop is not None and stop.is_set():
            raise RuntimeError('guest preparation failed before input transport')
        try:
            runtime = json.loads(Path(runtime_path).read_text())
            if Path(runtime['memory']).stat().st_size == runtime['ram_bytes']:
                qmp(runtime['qmp'], 'query-status')
                break
        except (OSError, ValueError, RuntimeError):
            pass
        time.sleep(.1)
    else:
        raise TimeoutError('QEMU touch runtime unavailable')
    viewer = TouchViewer(runtime, output)
    expected, checks = frames(), {}
    sid, seq, heartbeat = None, 0, 0
    try:
        tree = qmp(runtime['qmp'], 'human-monitor-command', {'command-line': 'info qtree'})
        (output / 'qtree.txt').write_text(tree)
        checks['actual_multitouch_device'] = 'virtio-multitouch-device' in tree and '000000000a003c00' in tree
        for _ in range(1800):
            if stop is not None and stop.is_set():
                raise RuntimeError('guest stopped before touch driver readiness')
            try:
                sid = viewer.action('/connect', {})['id']
                break
            except ValueError:
                time.sleep(.1)
        else:
            raise TimeoutError('XNU touch driver not ready')

        def beat():
            nonlocal heartbeat
            if time.monotonic() - heartbeat > .8:
                viewer.action('/heartbeat', dict(id=sid))
                heartbeat = time.monotonic()

        def wait(name, hold=1):
            deadline = time.monotonic() + 90
            while time.monotonic() < deadline:
                if stop is not None and stop.is_set():
                    raise RuntimeError('guest stopped during touch verification')
                beat()
                data = viewer.read()
                if data == expected[name]:
                    (output / (name + '.raw')).write_bytes(data)
                    (output / (name + '.png')).write_bytes(png(data))
                    checks['pixels_' + name] = True
                    for _ in range(hold * 5):
                        beat()
                        time.sleep(.2)
                    return
                time.sleep(.1)
            (output / ('failed-' + name + '.png')).write_bytes(png(viewer.read()))
            raise TimeoutError(name)

        def contact(slot, cid, phase, x, y):
            return dict(slot=slot, id=cid, phase=phase, x=x, y=y)

        def send(*contacts):
            nonlocal seq
            viewer.action('/touch', dict(id=sid, seq=seq + 1, contacts=list(contacts), origin='qmp-multitouch-test'))
            seq += 1

        before = len([e for e in viewer.events if e['kind'] == 'touch_device'])
        for invalid in [contact(11, 1, 'begin', 0, 0), contact(0, 1, 'move', 0, 0), contact(0, 1, 'begin', 160, 0)]:
            try:
                send(invalid)
            except ValueError:
                continue
            raise AssertionError('invalid contact reached device')
        checks['invalid_contacts_zero_device_commands'] = before == len([e for e in viewer.events if e['kind'] == 'touch_device'])
        wait('apps', hold=8)  # Observer is already polling when contacts begin.
        send(contact(0, 1, 'begin', 20, 19), contact(1, 2, 'begin', 130, 70))
        time.sleep(1.2)  # Native observer must see both simultaneous contacts.
        send(contact(0, 1, 'move', 34, 25), contact(1, 2, 'move', 140, 74))
        time.sleep(.3)
        send(contact(0, 1, 'end', 34, 25), contact(1, 2, 'end', 140, 74))
        wait('dual', hold=8)  # Keep the up state stable for the paused RAM observer.
        send(contact(0, 1, 'begin', 40, 50), contact(1, 2, 'begin', 120, 55))
        wait('cancelled')  # Actual native input-process death, not host up events.
        viewer.action('/disconnect', dict(id=sid))
        for _ in range(100):
            try:
                sid = viewer.action('/connect', {})['id']
                break
            except ValueError:
                time.sleep(.1)
        seq = 0
        for name in ['background', 'foreground', 'closed', 'restarted']:
            wait(name, hold=8 if name == 'restarted' else 1)
        send(contact(0, 3, 'begin', 40, 50))
        wait('crashed')
        wait('crash_restarted', hold=8)
        send(contact(0, 3, 'end', 40, 50))
        time.sleep(.2)
        send(contact(0, 4, 'begin', 40, 50))
        time.sleep(.2)
        send(contact(0, 4, 'end', 40, 50))
        for name in ['fresh_contact', 'empty', 'final']:
            wait(name)
        result = dict(passed=all(checks.values()), checks=checks,
                      origin='QMP mtt -> actual VirtIO device -> XNU; no GW touch injection',
                      phone_operations=[], physical_status='BLOCKED_BY_MEMORY_EVIDENCE')
        (output / 'verification.json').write_text(json.dumps(result, indent=2) + '\n')
        return result
    finally:
        viewer.close()
