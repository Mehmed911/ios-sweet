#!/usr/bin/env python3
"""Replace one same-sized embedded file in a copied disk image.

The old byte sequence must occur exactly once.  The source image is never
modified; this is intended for controlled updates of the tiny diagnostic HFS
image when no HFS writer is available on the build host.
"""

from pathlib import Path
import hashlib
import sys


if len(sys.argv) != 5:
    raise SystemExit("usage: replace-embedded-file.py IMAGE OLD NEW OUTPUT")

image_path, old_path, new_path, output_path = map(Path, sys.argv[1:])
image = image_path.read_bytes()
old = old_path.read_bytes()
new = new_path.read_bytes()

if len(old) != len(new):
    raise SystemExit(f"refusing size change: old={len(old)} new={len(new)}")
count = image.count(old)
if count != 1:
    raise SystemExit(f"old file must occur exactly once in image; found {count}")
offset = image.index(old)
updated = image[:offset] + new + image[offset + len(old):]
if len(updated) != len(image):
    raise SystemExit("internal error: image size changed")
if updated.count(new) != 1:
    raise SystemExit("new file verification failed")

output_path.write_bytes(updated)
digest = hashlib.sha256(updated).hexdigest()
print(f"replaced {len(old)} bytes at offset {offset}")
print(f"wrote {output_path} ({len(updated)} bytes, sha256 {digest})")
