#!/usr/bin/env python3
"""Wrap the local QEMU runner to read XNU's circular log at its final stop.

Usage: qemu_kernel_log.py KERNEL LOG RUNNER [runner arguments...]
No guest patching; QMP memsave reads the stopped virtual CPU's address space.
"""
import json
from pathlib import Path
import runpy
import socket
import struct
import sys
import tempfile

from duchamp_ufs_xnu_replay import symbols

TOOLS = Path(__file__).resolve().parent


def capture(endpoint, kernel, output):
    names = symbols(kernel)
    channel = runpy.run_path(str(TOOLS / "duchamp-qemu-windows.py"))["qmp_channel"]
    with socket.socket(socket.AF_UNIX) as sock, tempfile.TemporaryDirectory(prefix="xnumsg") as temporary:
        sock.settimeout(10)
        sock.connect(endpoint)
        call = channel(sock)

        def read(address, size, name):
            path = Path(temporary) / name
            call("memsave", val=address, size=size, filename=str(path), **{"cpu-index": 0})
            data = path.read_bytes()
            if len(data) != size:
                raise ValueError("Short QEMU virtual memory capture")
            return data

        pointer, = struct.unpack("<Q", read(names["_msgbufp"], 8, "ptr"))
        magic, size, index, _, buffer = struct.unpack("<4IQ", read(pointer, 24, "header"))
        if magic != 0x063061 or not 0 < size <= 1048576 or not 0 <= index < size:
            raise ValueError("Invalid XNU message buffer")
        data = read(buffer, size, "ring")
    output.write_text((data[index:] + data[:index]).replace(b"\0", b"").decode(errors="replace"))
    output.with_suffix(".json").write_text(json.dumps(dict(source="QMP memsave at final stopped CPU",
        msgbuf_pointer=hex(pointer), ring_address=hex(buffer), bytes=size, next=index,
        guest_modified=False, phone_access=False), indent=2) + "\n")


def main():
    kernel, output, runner = (Path(value).resolve() for value in sys.argv[1:4])
    runner_args = sys.argv[4:]
    api = runpy.run_path(str(runner))
    entry = api["main"]
    original = entry.__globals__["qmp"]

    def qmp(endpoint, *commands, **kwargs):
        result = original(endpoint, *commands, **kwargs)
        if "info registers" in commands:
            capture(endpoint, kernel, output)
        return result

    entry.__globals__["qmp"] = qmp
    sys.argv = [str(runner), *runner_args]
    return entry()


if __name__ == "__main__":
    raise SystemExit(main())
