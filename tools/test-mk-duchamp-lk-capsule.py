#!/usr/bin/env python3
"""Test the MT6897 LK RAM capsule packer."""

import pathlib
import struct
import subprocess
import sys
import tempfile


def receipt(data):
    value = 1469598103934665603
    for byte in data:
        value ^= byte
        value = value * 1099511628211 & 0xFFFFFFFFFFFFFFFF
    value ^= len(data)
    return value * 1099511628211 & 0xFFFFFFFFFFFFFFFF


def main():
    tool = pathlib.Path(__file__).with_name("mk-duchamp-lk-capsule.py")
    payload = b"SWEETXNU"
    with tempfile.TemporaryDirectory(prefix="duchamp-lk-capsule-") as name:
        directory = pathlib.Path(name)
        source = directory / "payload.bin"
        output = directory / "payload.lkram"
        source.write_bytes(payload)
        completed = subprocess.run(
            [sys.executable, str(tool), str(source), str(output),
             "--generation", "0x27"], check=True, capture_output=True,
            text=True)
        data = output.read_bytes()
        fields = struct.unpack_from("<8sIIQQQQQQ", data)
        assert fields == (
            b"DUCHLKR1", 1, 64, 72, 0x27, 64, 8,
            receipt(payload), 1)
        assert data[64:] == payload
        assert "generation 39" in completed.stdout
        refused = subprocess.run(
            [sys.executable, str(tool), str(source), str(output),
             "--generation", "39"], capture_output=True, text=True)
        assert refused.returncode != 0
        assert "refusing to overwrite" in refused.stderr
    print("mk-duchamp-lk-capsule-tests: PASS checks=4")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
