#!/usr/bin/env python3
"""Run the resident protocol Image on QEMU virt and verify its visual receipt."""

import argparse
import json
import shutil
import socket
import struct
import subprocess
import tempfile
import time
from pathlib import Path


FB_BASE = 0xFCC2F000
FB_STRIDE = 4992
FB_WIDTH = 1220
FB_HEIGHT = 2712
BAND_HEIGHT = FB_HEIGHT // 12
EXPECTED = [0xFF00FF00] * 8 + [
    0xFF00FFFF, 0xFFFF00FF, 0xFF00FFFF, 0xFFFF00FF]


def qmp_call(stream, execute, **arguments):
    request = {"execute": execute}
    if arguments:
        request["arguments"] = arguments
    stream.write(json.dumps(request).encode() + b"\n")
    stream.flush()
    while True:
        reply = json.loads(stream.readline())
        if "return" in reply:
            return reply["return"]
        if "error" in reply:
            raise RuntimeError(reply["error"])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", type=Path, required=True)
    parser.add_argument("--capture", type=Path, required=True)
    parser.add_argument("--memory", default="4G")
    parser.add_argument("--wait", type=float, default=0.5)
    args = parser.parse_args()
    qemu = shutil.which("qemu-system-aarch64")
    if not qemu:
        raise SystemExit("qemu-system-aarch64 is not installed")
    image = args.image.resolve()
    if not image.is_file():
        raise SystemExit(f"missing Image: {image}")

    listener = socket.socket()
    listener.bind(("127.0.0.1", 0))
    port = listener.getsockname()[1]
    listener.close()
    with tempfile.TemporaryDirectory(prefix="duchamp-resident-") as temporary:
        raw = Path(temporary) / "framebuffer.raw"
        command = [
            qemu, "-M", "virt,gic-version=3", "-cpu", "cortex-a76",
            "-smp", "1", "-m", args.memory, "-nodefaults", "-nographic",
            "-kernel", str(image), "-no-reboot",
            "-qmp", f"tcp:127.0.0.1:{port},server,nowait",
        ]
        process = subprocess.Popen(
            command, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE, text=True)
        try:
            deadline = time.time() + 5
            connection = None
            while time.time() < deadline and process.poll() is None:
                try:
                    connection = socket.create_connection(("127.0.0.1", port), 0.2)
                    connection.settimeout(None)
                    break
                except OSError:
                    time.sleep(0.05)
            if connection is None:
                stderr = process.stderr.read() if process.poll() is not None else ""
                raise RuntimeError(f"QMP did not become ready: {stderr}")
            with connection, connection.makefile("rwb") as stream:
                json.loads(stream.readline())
                qmp_call(stream, "qmp_capabilities")
                time.sleep(args.wait)
                qmp_call(stream, "stop")
                qmp_call(stream, "pmemsave", val=FB_BASE,
                         size=FB_STRIDE * FB_HEIGHT, filename=str(raw))
                stream.write(b'{"execute":"quit"}\n')
                stream.flush()
            process.wait(timeout=5)
        finally:
            if process.poll() is None:
                process.kill()
                process.wait()

        data = raw.read_bytes()
        args.capture.write_bytes(data)
        for row, expected in enumerate(EXPECTED):
            offset = (row * BAND_HEIGHT + BAND_HEIGHT // 2) * FB_STRIDE
            first = struct.unpack_from("<I", data, offset)[0]
            last = struct.unpack_from("<I", data, offset + (FB_WIDTH - 1) * 4)[0]
            padding = struct.unpack_from("<I", data, offset + FB_WIDTH * 4)[0]
            if first != expected or last != expected or padding != 0:
                raise SystemExit(
                    f"row {row}: first={first:#010x} last={last:#010x} "
                    f"padding={padding:#010x} expected={expected:#010x}")
    print("resident-protocol-qemu: PASS rows=12")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
