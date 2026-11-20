#!/usr/bin/env python3
"""Observe a bounded rectangle in QEMU RAM; never write guest pixels."""
import hashlib
import re


def validate_sequence(sequence, fb, max_observations=8):
    if max_observations not in (8, 16) or not isinstance(sequence, list) or not 1 <= len(sequence) <= max_observations:
        raise ValueError('frame sequence exceeds the selected bounded observation profile')
    names = set()
    for entry in sequence:
        if not isinstance(entry, dict) or set(entry) != {'name', 'x', 'y', 'width', 'height', 'sha256'}:
            raise ValueError('invalid sequence observation')
        name = entry['name']
        if not isinstance(name, str) or not re.fullmatch('[a-z_]{1,32}', name) or name in names:
            raise ValueError('invalid or duplicated sequence name')
        names.add(name)
        validate({k: v for k, v in entry.items() if k != 'name'}, fb)
    return sequence


def validate(spec, fb):
    if set(spec) != {'x', 'y', 'width', 'height', 'sha256'}:
        raise ValueError('unexpected framebuffer witness fields')
    if any(type(spec[k]) is not int for k in ('x', 'y', 'width', 'height')):
        raise ValueError('non-integer framebuffer rectangle')
    x, y, w, h = (spec[k] for k in ('x', 'y', 'width', 'height'))
    if not (0 <= x < fb['width'] and 0 <= y < fb['height'] and
            0 < w <= min(256, fb['width'] - x) and 0 < h <= min(256, fb['height'] - y)):
        raise ValueError('invalid framebuffer witness rectangle')
    if (not isinstance(spec['sha256'], str) or len(spec['sha256']) != 64 or
            any(c not in '0123456789abcdef' for c in spec['sha256'])):
        raise ValueError('invalid framebuffer witness digest')
    if fb['stride'] < fb['width'] * 4:
        raise ValueError('invalid framebuffer stride')
    return spec


def observe(raw, spec, fb):
    validate(spec, fb)
    if len(raw) != fb['stride'] * fb['height']:
        raise ValueError('truncated framebuffer sample')
    x, y, w, h = (spec[k] for k in ('x', 'y', 'width', 'height'))
    pixels = b''.join(raw[(y + row) * fb['stride'] + x * 4:
                          (y + row) * fb['stride'] + (x + w) * 4] for row in range(h))
    digest = hashlib.sha256(pixels).hexdigest()
    return pixels, {'matched': digest == spec['sha256'], 'sha256': digest,
                    'rectangle': [x, y, w, h], 'scope': 'QEMU RAM sample; no physical display claim'}
