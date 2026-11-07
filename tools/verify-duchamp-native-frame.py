#!/usr/bin/env python3
"""Check native SwapSetLayer, SwapEnd and a captured QEMU framebuffer."""
import argparse
import hashlib
import json
from pathlib import Path

STRIDE = 4992
HEIGHT = 2712
ACTIVE_ROW_BYTES = 1220 * 4


def sha(data):
    return hashlib.sha256(data).hexdigest()


def verify(run, swap_id=None):
    layout = json.loads((run / 'layout.json').read_text())
    if not layout['qemu_only'] or layout['physical_storage']:
        raise ValueError('expected QEMU-only trace')
    events = [json.loads(line) for line in (run / 'quartzcore-events.jsonl').read_text().splitlines()]
    end = next((i for i, e in enumerate(events) if e['event'] == 'present_done'
                and (swap_id is None or e['swap_id'] == swap_id)), None)
    prior = events if end is None else events[:end]
    observed = dict(springboard_context_commits=sum(
        e['event'] == 'context_commit' and e['process'] == 'SpringBoard' for e in prior),
        springboard_surface_create_calls=sum(
            e['event'] == 'iosurface_create' and e['process'] == 'SpringBoard' for e in prior),
        setup_context_commits=sum(e['event'] == 'context_commit' and e['process'] == 'Setup' for e in prior))
    if end is None:
        return dict(verified=False, reason='no captured eligible present', **observed)
    present = events[end]
    capture = present.get('capture', 'native-frame.raw')
    if capture not in ('native-frame.raw', 'native-frame-%08x.raw' % present['swap_id']):
        raise ValueError('unexpected native capture filename')
    frame = (run / capture).read_bytes()
    def same_swap(event):
        return event.get('swap_id') == present['swap_id']

    sample = next((e for e in reversed(events[:end]) if e['event'] == 'layer_pixels' and same_swap(e)), None)
    if sample is None:
        return dict(verified=False, reason='present contains no validated row samples', **observed)
    layer, surface = sample['layer'], sample['surface_id']
    if not (surface and 0 <= layer < 4 and int(present['mask'], 16) & (1 << layer)
            and present['surfaces'][layer] == surface):
        raise ValueError('row sample differs from the active present layer')
    swap_index = next((i for i in range(end - 1, -1, -1)
        if events[i]['event'] == 'swap' and events[i]['process'] == 'backboardd'
        and same_swap(events[i]) and events[i]['surfaces'] == present['surfaces']
        and events[i]['mask'] == present['mask']), None)
    layer_write = False
    if swap_index is not None:
        swap = events[swap_index]
        for i, e in enumerate(events[:swap_index]):
            if (e['event'] == 'layer_surface_id' and e['pid'] == swap['pid']
                    and e['layer'] == layer and e['surface_id'] == surface):
                arguments = [int(e[k], 16) for k in ('connection', 'surface')]
                layer_write = layer_write or any(
                    call['event'] == 'kern_swap_set_layer' and call['pid'] == swap['pid']
                    and [int(a, 16) for a in call['args'][:3]] == [arguments[0], layer, arguments[1]]
                    for call in events[:i])
    rows = sample['rows']
    matched = 0
    for row in rows:
        offset, size = row['offset'], row['bytes']
        if not 0 <= offset < offset + size <= len(frame) or offset % STRIDE + size > ACTIVE_ROW_BYTES:
            raise ValueError('sample outside active framebuffer pixels')
        actual = sha(frame[offset:offset + size])
        matched += row['matches'] and row['source_sha256'] == row['physical_sha256'] == actual
    active = b''.join(frame[i:i + ACTIVE_ROW_BYTES] for i in range(0, len(frame), STRIDE))
    rgb_nonblack = any(any(active[channel::4]) for channel in range(3))
    checks = dict(swap_end=swap_index is not None, swap_set_layer=layer_write,
        scanout_hash=len(frame) == STRIDE * HEIGHT and sha(frame) == present['sha256'],
        source_rows=bool(rows) and matched == len(rows),
        changed_rows=any(row['changed'] for row in rows) and present['before_sha256'] != present['sha256'])
    return dict(verified=all(checks.values()), checks=checks, swap_id=present['swap_id'],
        surface_id=surface, layer=layer, matched_rows=matched, sampled_rows=len(rows),
        active_rgb_nonblack=rgb_nonblack, capture=capture, setup_pid=present.get('setup_pid'), **observed)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run', type=Path)
    parser.add_argument('--swap-id', type=lambda value: int(value, 0))
    args = parser.parse_args()
    report = verify(args.run, args.swap_id)
    print(json.dumps(report, indent=2))
    return 0 if report['verified'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
