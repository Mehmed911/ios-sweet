#!/usr/bin/env python3
"""Rebuild a SWEETXNU payload from its embedded ADT/cmdline and compare it."""
import argparse
import hashlib
import struct
import tempfile
from pathlib import Path

import mkpayload


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("kernel", type=Path)
    parser.add_argument("payload", type=Path)
    args = parser.parse_args()
    original = args.payload.read_bytes()
    if len(original) < 0x2A8 or original[:8] != b"SWEETXNU":
        raise SystemExit("not a SWEETXNU payload")
    version, segment_count = struct.unpack_from("<II", original, 8)
    adt_offset, adt_size = struct.unpack_from("<QQ", original, 0x20)
    if version != 1 or not 1 <= segment_count <= 32:
        raise SystemExit("unsupported payload header")
    command = original[0x48:0x2A8].split(b"\0", 1)[0].decode()
    adt = original[adt_offset:adt_offset + adt_size]
    with tempfile.TemporaryDirectory(prefix="duchamp-payload-source-") as temp:
        adt_path = Path(temp) / "embedded.adt"
        adt_path.write_bytes(adt)
        rebuilt, info = mkpayload.build(str(args.kernel), str(adt_path), command)
    if rebuilt != original:
        first = next((i for i, pair in enumerate(zip(rebuilt, original))
                      if pair[0] != pair[1]), min(len(rebuilt), len(original)))
        raise SystemExit(
            f"payload mismatch: rebuilt={len(rebuilt)} original={len(original)} "
            f"first_difference={first:#x}")
    print("payload-source-rebuild: PASS")
    print(f"kernel={args.kernel}")
    print(f"entry={info['entry']} segments={segment_count} fixups={info['fixups']}")
    print(f"cmdline={command!r}")
    print(f"sha256={hashlib.sha256(original).hexdigest()}")


if __name__ == "__main__":
    main()
