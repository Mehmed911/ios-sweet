"""Select the pinned source kernel or explicitly validate a new link receipt."""
import hashlib
import json
from pathlib import Path

BASELINE = 'e7b51ecb16fe9ad21a78455714b2bf26c1dee1fbc3a6a7f0cb3971a9cd569457'


def select(kernel, receipt=None):
    def sha(path):
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()
    actual = sha(kernel)
    if receipt is None:
        if actual != BASELINE:
            raise ValueError('kernel differs from pinned source build; an explicit source-link receipt is required')
        return actual
    r = json.loads(Path(receipt).read_text())
    if (Path(r['kernel']).resolve() != Path(kernel).resolve() or r['sha256'] != actual or
            r['baseline_sha256'] != BASELINE or sha(r['baseline_kernel']) != BASELINE or
            len(r['input_objects']) != 1127 or len({o['object'] for o in r['input_objects']}) != 1127):
        raise ValueError('source-link receipt mismatch')
    for obj in r['input_objects']:
        if sha(obj['object']) != obj['new_object_sha256']:
            raise ValueError('link input changed: ' + obj['object'])
    return actual
