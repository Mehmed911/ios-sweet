#!/usr/bin/env python3
"""Exercise the Duchamp boot menu using QEMU's emulated UART and framebuffer."""
import argparse
from contextlib import contextmanager
import importlib.util
import json
import os
from pathlib import Path
import select
import socket
import struct
import subprocess
import sys
import tempfile
import time

from test_qemu import FB_BASE, FB_HEIGHT, FB_STRIDE, FB_WIDTH, qmp_call

ACCENT = 0xFF62DDD2
ROWS = FB_HEIGHT // 2 - 350 + 196
SECOND_ROW = ROWS + 172
ENTRY_KEYS_ADDRESS = 0x41000000

tools_dir = Path(__file__).resolve().parents[2] / "tools"
sys.path.insert(0, str(tools_dir))
viewer_spec = importlib.util.spec_from_file_location("sweet_qemu", tools_dir / "qemu-sweet.py")
viewer = importlib.util.module_from_spec(viewer_spec)
viewer_spec.loader.exec_module(viewer)


@contextmanager
def boot(image, output, name, dtb=None, entry_keys=None, *,
         ram_fixtures=(), warm_reset=False):
    with tempfile.TemporaryDirectory(prefix="duchamp-menu-") as directory:
        qmp_path = Path(directory) / "qmp"
        command = [
            "qemu-system-aarch64", "-M", "virt,gic-version=3",
            "-cpu", "cortex-a76", "-m", "8G", "-smp", "1",
            "-nodefaults", "-display", "none", "-monitor", "none",
            "-serial", "stdio", "-qmp", f"unix:{qmp_path},server=on,wait=off",
            "-kernel", str(image),
        ]
        if not warm_reset:
            command.append("-no-reboot")
        if dtb is not None:
            command += ["-dtb", str(dtb.resolve())]
        if entry_keys is not None:
            fixture = Path(directory) / "entry-keys.bin"
            fixture.write_bytes(struct.pack("<4sHBB", b"DKEY", *entry_keys))
            command += ["-device", f"loader,file={fixture},addr={ENTRY_KEYS_ADDRESS:#x},force-raw=on"]
        for fixture, address in ram_fixtures:
            command += ["-device", f"loader,file={fixture},addr={address:#x},force-raw=on"]
        with (output / f"{name}.qemu.log").open("wb") as stderr:
            with subprocess.Popen(command,
                    stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                    stderr=stderr) as process:
                transcript = bytearray()
                try:
                    yield process, qmp_path, Path(directory), transcript
                finally:
                    process.terminate()
                    try:
                        process.wait(3)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()
                    transcript.extend(process.stdout.read())
                    (output / f"{name}.serial.log").write_bytes(transcript)


def expect(process, transcript, line, timeout=5, *, after=0):
    marker = line.encode() + b"\n"
    deadline = time.monotonic() + timeout
    while (position := transcript.find(marker, after)) == -1:
        remaining = deadline - time.monotonic()
        if remaining <= 0 or not select.select([process.stdout], [], [], remaining)[0]:
            raise RuntimeError(f"Timed out waiting for {line!r}: {transcript[-600:]!r}")
        chunk = os.read(process.stdout.fileno(), 4096)
        if not chunk:
            raise RuntimeError(f"QEMU stopped before {line!r}: {transcript[-600:]!r}")
        transcript.extend(chunk)
    return position + len(marker)


def press(process, keys):
    process.stdin.write(keys)
    process.stdin.flush()


@contextmanager
def qmp_session(qmp_path):
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
        connection.settimeout(5)
        connection.connect(str(qmp_path))
        with connection.makefile("rwb") as stream:
            json.loads(stream.readline())
            qmp_call(stream, "qmp_capabilities")
            yield stream


def framebuffer(qmp_path, temp):
    raw = temp / "frame.raw"
    with qmp_session(qmp_path) as stream:
        qmp_call(stream, "stop")
        registers = qmp_call(stream, "human-monitor-command",
                             **{"command-line": "info registers"})
        qmp_call(stream, "pmemsave", val=FB_BASE, size=FB_STRIDE * FB_HEIGHT,
                 filename=str(raw))
        qmp_call(stream, "cont")
    return raw.read_bytes(), registers


def verify_focus(raw, focus):
    colors = [struct.unpack_from("<I", raw, y * FB_STRIDE + 90 * 4)[0]
              for y in (ROWS + 5, SECOND_ROW + 5)]
    if [color == ACCENT for color in colors] != [focus == "A", focus == "B"]:
        raise RuntimeError(f"Incorrect focus {focus}: {colors!r}")
    if struct.unpack_from("<I", raw, FB_WIDTH * 4)[0] != 0:
        raise RuntimeError("Framebuffer stride padding changed")


def save_screen(output, name, raw):
    viewer.write_png(output / f"{name}.png", raw,
                     {"width": FB_WIDTH, "height": FB_HEIGHT, "stride": FB_STRIDE})


def verify_entry_keys(image, output):
    cases = (
        ("neutral", (0xffff, 0, 3), "0 ARMED 1", b""),
        ("volume-up", (0xfffe, 0, 3), "1 ARMED 0", b"\x81\x80"),
        ("volume-down", (0xffff, 2, 3), "2 ARMED 0", b"\x82\x80"),
        ("power", (0xffff, 4, 3), "4 ARMED 0", b"\x84\x80"),
        ("incomplete", (0xffff, 0, 1), "UNAVAILABLE", b"\x84\x80"),
        ("invalid-pmic", (0xffff, 8, 3), "UNAVAILABLE", b"\x84\x80"),
        ("missing", None, "UNAVAILABLE", b"\x84\x80"),
    )
    results = {}
    for name, fixture, state, initial_keys in cases:
        marker = f"DUCHAMP ENTRY KEYS {state}"
        with boot(image, output, f"entry-{name}", entry_keys=fixture) as (guest, _qmp, _temp, log):
            expect(guest, log, "DUCHAMP MENU READY")
            if log.splitlines()[:2] != [marker.encode(), b"DUCHAMP MENU READY"]:
                raise RuntimeError(f"Incorrect entry sample for {name}: {log!r}")
            # Fresh volume up, fresh volume down, then fresh power on Android.
            press(guest, initial_keys + bytes.fromhex("81 80 82 80 84"))
            expect(guest, log, "DUCHAMP ANDROID NEXT SLOT REQUEST A")
            press(guest, b"!")
            expect(guest, log, "DUCHAMP ANDROID BLOCKED NEXT SLOT")

        actions = [line for line in log.splitlines() if
                   line.startswith((b"DUCHAMP MENU FOCUS", b"DUCHAMP MENU CHOICE"))]
        if actions != [b"DUCHAMP MENU FOCUS B", b"DUCHAMP MENU FOCUS A",
                       b"DUCHAMP MENU CHOICE A CONFIRMED"]:
            raise RuntimeError(f"Unexpected button actions for {name}: {actions!r}")
        results[name] = {"entry_state": state, "fresh_key_actions": ["B", "A", "confirm A"]}
        print(f"entry-{name}: PASS {state}", flush=True)
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("preview", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--with-xnu", type=Path)
    parser.add_argument("--xnu-dtb", type=Path)
    parser.add_argument("--entry-keys-image", type=Path)
    args = parser.parse_args()
    if bool(args.with_xnu) != bool(args.xnu_dtb):
        parser.error("--with-xnu and --xnu-dtb must be supplied together")
    args.output.mkdir()
    results = {}
    active_image = args.with_xnu or args.preview
    # Held power, bad sample, held volume up, chord, volume down, then fresh power.
    key_edges = bytes.fromhex("84 84 80 88 84 80 81 81 80 86 84 80 82 82 80 84")
    cases = (
        ("confirm-a", active_image, args.xnu_dtb, b"swx\r", "A CONFIRMED", "A"),
        ("confirm-b", args.preview, None, b"s\r", "B PREVIEW", "B"),
        ("timeout", active_image, args.xnu_dtb, b"s", "A TIMEOUT", "A"),
        ("buffered-readback", active_image, args.xnu_dtb, b"\rA", "A CONFIRMED", "A"),
        ("key-edges", active_image, args.xnu_dtb, key_edges, "A CONFIRMED", "A"),
    )
    for name, image, dtb, keys, choice, focus in cases:
        with boot(image.resolve(), args.output, name, dtb) as (guest, qmp, temp, log):
            expect(guest, log, "DUCHAMP MENU READY")
            if name == "confirm-b":
                initial, _ = framebuffer(qmp, temp)
                verify_focus(initial, "A")
                save_screen(args.output, "menu", initial)
            press(guest, keys)
            expect(guest, log, f"DUCHAMP MENU CHOICE {choice}", timeout=12)
            if focus == "A":
                expect(guest, log, "DUCHAMP ANDROID NEXT SLOT REQUEST A")
                if name == "confirm-a":
                    press(guest, b"B")
                    expect(guest, log, "DUCHAMP ANDROID BLOCKED NEXT SLOT")
                else:
                    expect(guest, log, "DUCHAMP ANDROID BLOCKED NO READBACK")
            if name != "buffered-readback" and b"DUCHAMP MENU FOCUS B\n" not in log:
                raise RuntimeError("The menu did not highlight Slot B")
            if name == "confirm-a" and b"DUCHAMP MENU FOCUS A\n" not in log:
                raise RuntimeError("The menu did not return focus to Slot A")
            if name == "key-edges":
                focus_events = [line for line in log.splitlines() if b"MENU FOCUS" in line]
                if focus_events != [b"DUCHAMP MENU FOCUS B", b"DUCHAMP MENU FOCUS A"]:
                    raise RuntimeError(f"Unexpected actions from button samples: {focus_events}")
            raw, regs = framebuffer(qmp, temp)
            verify_focus(raw, focus)
            if "PC=fffffe" in regs:
                raise RuntimeError("An Android or preview choice entered the XNU kernel")
            if name == "confirm-b":
                save_screen(args.output, "selected-b", raw)
        if b"DUCHAMP ANDROID NEXT SLOT VERIFIED" in log or (
                focus == "B" and b"DUCHAMP ANDROID NEXT SLOT REQUEST" in log):
            raise RuntimeError("Unexpected Android slot dispatch")
        results[name] = {"choice": choice, "framebuffer_focus": focus}
        if focus == "A":
            results[name]["return_blocked"] = "wrong slot" if name == "confirm-a" else "no readback"
        if name == "key-edges":
            results[name]["focus_events"] = ["B", "A"]
        print(f"{name}: PASS {choice}", flush=True)

    with boot(active_image.resolve(), args.output, "android-reset", args.xnu_dtb) as (
            guest, qmp, _temp, log):
        expect(guest, log, "DUCHAMP MENU READY")
        with qmp_session(qmp) as stream:
            press(guest, b"\r")
            expect(guest, log, "DUCHAMP ANDROID NEXT SLOT REQUEST A")
            press(guest, b"A")
            expect(guest, log, "DUCHAMP ANDROID NEXT SLOT VERIFIED A")
            while packet := stream.readline():
                event = json.loads(packet)
                if event.get("event") == "SHUTDOWN" and event["data"]["reason"] == "guest-reset":
                    break
            else:
                raise RuntimeError("QEMU did not report a guest reset")
        if guest.wait(5) != 0:
            raise RuntimeError("QEMU failed while handling the verified Android return")
    results["android-reset"] = {"next_slot_readback": "A", "qmp": "guest-reset", "mock_firmware": True}
    print("android-reset: PASS verified simulated Slot A, then guest reset", flush=True)

    if args.with_xnu:
        with boot(args.with_xnu.resolve(), args.output, "xnu", args.xnu_dtb) as (guest, qmp, temp, log):
            expect(guest, log, "DUCHAMP MENU READY")
            press(guest, bytes.fromhex("80 82 80 84"))
            expect(guest, log, "DUCHAMP MENU CHOICE B XNU")
            deadline = time.monotonic() + 15
            while time.monotonic() < deadline:
                raw, regs = framebuffer(qmp, temp)
                if "PC=fffffe" in regs and raw.count(b"\xff" * 4) >= 512:
                    save_screen(args.output, "xnu", raw)
                    break
                time.sleep(0.3)
            else:
                (args.output / "xnu-registers.txt").write_text(regs)
                save_screen(args.output, "xnu-last", raw)
                raise RuntimeError("XNU kernel PC and framebuffer output were not observed")
        results["xnu"] = {"choice": "B XNU", "high_kernel_pc": True, "framebuffer_output": True}
        print("xnu: PASS Slot B entered the XNU kernel", flush=True)

    if args.entry_keys_image:
        results["entry_keys"] = verify_entry_keys(args.entry_keys_image.resolve(), args.output)

    (args.output / "verification.json").write_text(json.dumps(results, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
