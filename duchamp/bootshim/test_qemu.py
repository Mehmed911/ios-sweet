#!/usr/bin/env python3
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
FB_ROWS = 12
FB_HEIGHT = 2712
BAND_HEIGHT = FB_HEIGHT // FB_ROWS
EXPECTED = [
    0xFF00FF00, 0xFF00FF00, 0xFF00FF00, 0xFF00FF00,
    0xFF00FF00, 0xFF00FF00, 0xFF00FF00, 0xFF00FF00,
    0xFF00FFFF, 0xFFFF00FF, 0xFF00FFFF, 0xFFFF00FF,
]
EXCEPTION_EXPECTED = [0xFFFF0000] * FB_ROWS
EXCEPTION_EXPECTED[1] = 0xFFFF00FF
RETURN_EXPECTED = [0xFF00FF00] * 8 + [
    0xFFFF00FF, 0xFF00FFFF, 0xFFFF00FF, 0xFF00FFFF,
]
SLOT_MISSING_EXPECTED = [0xFF00FF00] * 8 + [
    0xFFFF0000, 0xFF00FF00, 0xFF00FF00, 0xFF00FFFF,
]
SLOT_READY_EXPECTED = [0xFF00FF00] * 11 + [0xFFFF00FF]
EARLY_RETURN_EXPECTED = [
    0xFF00FF00, 0xFF00FF00, 0xFF00FF00, 0xFF00FF00,
    0xFF00FF00, 0xFFFF0000, 0xFF00FF00, 0xFF00FF00,
    0xFFFF00FF, 0xFF00FFFF, 0xFFFF00FF, 0xFF00FFFF,
]
LK_RAM_EXPECTED = [0xFF00FF00] * 11 + [0xFF00FFFF]
LK_REPORT_FORMAT = "<Q8I7Q"
LK_REPORT_SIZE = struct.calcsize(LK_REPORT_FORMAT)


def mutation_receipt(data, value=1469598103934665603):
    for byte in data:
        value ^= byte
        value = value * 1099511628211 & 0xFFFFFFFFFFFFFFFF
    return value


def lk_payload_expectations(path):
    data = path.read_bytes()
    if len(data) < 0x2A8 or data[:8] != b"SWEETXNU":
        raise SystemExit(f"invalid SWEETXNU payload: {path}")
    version, segment_count = struct.unpack_from("<II", data, 8)
    if version != 1 or not 1 <= segment_count <= 32:
        raise SystemExit(f"invalid SWEETXNU version/segments: {path}")
    if len(data) < 0x2A8 + segment_count * 32:
        raise SystemExit(f"truncated SWEETXNU segment table: {path}")
    (virt_base, entry_va, _adt_offset, adt_size, kernel_end, phys_base,
     memory_size) = struct.unpack_from("<7Q", data, 0x10)
    if phys_base != 0x1C0000000 or memory_size != 0x20000000:
        raise SystemExit(
            f"unexpected SWEETXNU window: base={phys_base:#x} "
            f"size={memory_size:#x}")
    entry = phys_base + entry_va - virt_base
    adt = phys_base + kernel_end - virt_base
    boot_args = (adt + adt_size + 0x3FFF) & ~0x3FFF
    return {
        "bytes": len(data),
        "segments": segment_count,
        "entry": entry,
        "boot_args": boot_args,
    }


def lk_report_is_final(data):
    if len(data) != LK_REPORT_SIZE:
        return False
    fields = struct.unpack(LK_REPORT_FORMAT, data)
    magic, version, size, result, state, error = fields[:6]
    checksum = fields[-1]
    return (magic == 0x5450524B4C435544 and version == 1 and
            size == LK_REPORT_SIZE and checksum != 0 and
            checksum == mutation_receipt(data[:-8]) and
            (state == 2 or result != 0 or error != 0))


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
    parser.add_argument("--image", type=Path, default=Path("out/Image"))
    parser.add_argument("--pattern",
                        choices=("normal", "exception", "return",
                                 "slot-missing", "slot-ready",
                                 "early-return", "lk-ram", "xnu"),
                        default="normal")
    parser.add_argument("--dtb", type=Path)
    parser.add_argument("--memory", default="4G")
    parser.add_argument("--wait", type=float, default=0.5)
    parser.add_argument("--capture", type=Path)
    parser.add_argument("--slot-pa", type=lambda value: int(value, 0))
    parser.add_argument("--expect-slot-stub", type=lambda value: int(value, 0))
    parser.add_argument("--expect-slot-checkpoint", type=lambda value: int(value, 0),
                        default=0)
    parser.add_argument("--expect-slot-delta", type=lambda value: int(value, 0))
    parser.add_argument("--return-record-pa", type=lambda value: int(value, 0))
    parser.add_argument("--return-log-pa", type=lambda value: int(value, 0))
    parser.add_argument("--expect-return-reason", type=lambda value: int(value, 0))
    parser.add_argument("--expect-no-return", action="store_true",
                        help="require the XNU return record to remain zero")
    parser.add_argument("--lk-report-pa", type=lambda value: int(value, 0))
    parser.add_argument("--expect-lk-generation",
                        type=lambda value: int(value, 0))
    parser.add_argument("--lk-payload", type=Path)
    parser.add_argument("--exception-record-pa",
                        type=lambda value: int(value, 0))
    parser.add_argument("--expect-no-exception", action="store_true")
    args = parser.parse_args()
    if args.expect_no_return and args.return_record_pa is None:
        parser.error("--expect-no-return requires --return-record-pa")
    if args.expect_no_return and args.expect_return_reason is not None:
        parser.error("--expect-no-return conflicts with --expect-return-reason")
    if args.return_log_pa is not None and args.return_record_pa is None:
        parser.error("--return-log-pa requires --return-record-pa")
    if args.expect_no_exception and args.exception_record_pa is None:
        parser.error("--expect-no-exception requires --exception-record-pa")
    if args.lk_payload is not None and args.lk_report_pa is None:
        parser.error("--lk-payload requires --lk-report-pa")
    lk_expected = (lk_payload_expectations(args.lk_payload.resolve())
                   if args.lk_payload is not None else None)
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

    with tempfile.TemporaryDirectory(prefix="duchamp-bootshim-") as temp:
        raw = Path(temp) / "marker.raw"
        slot_raw = Path(temp) / "return-slot.raw"
        return_raw = Path(temp) / "return-record.raw"
        return_log_raw = Path(temp) / "return-log.raw"
        lk_report_raw = Path(temp) / "lk-ram-report.raw"
        exception_raw = Path(temp) / "exception-record.raw"
        qemu_stderr = Path(temp) / "qemu.stderr"
        command = [
            qemu, "-M", "virt,gic-version=3", "-cpu", "cortex-a76",
            "-smp", "1", "-m", args.memory, "-nodefaults", "-nographic",
            "-kernel", str(image), "-no-reboot",
            "-qmp", f"tcp:127.0.0.1:{port},server,nowait",
        ]
        if args.dtb:
            command += ["-dtb", str(args.dtb.resolve())]
        stderr_stream = qemu_stderr.open("w", encoding="utf-8")
        process = subprocess.Popen(
            command, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
            stderr=stderr_stream, text=True)
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
                stderr_stream.close()
                detail = qemu_stderr.read_text(errors="replace").strip()
                raise RuntimeError(
                    "QMP did not become ready" +
                    (f": {detail}" if detail else ""))
            with connection, connection.makefile("rwb") as stream:
                json.loads(stream.readline())
                qmp_call(stream, "qmp_capabilities")
                if args.lk_report_pa is not None:
                    deadline = time.time() + args.wait
                    while True:
                        qmp_call(stream, "pmemsave", val=args.lk_report_pa,
                                 size=LK_REPORT_SIZE,
                                 filename=str(lk_report_raw))
                        if lk_report_is_final(lk_report_raw.read_bytes()):
                            break
                        if time.time() >= deadline:
                            break
                        time.sleep(0.05)
                else:
                    time.sleep(args.wait)
                qmp_call(stream, "stop")
                qmp_call(stream, "pmemsave", val=FB_BASE,
                         size=FB_STRIDE * FB_HEIGHT, filename=str(raw))
                if args.slot_pa is not None:
                    qmp_call(stream, "pmemsave", val=args.slot_pa,
                             size=32, filename=str(slot_raw))
                if args.return_record_pa is not None:
                    qmp_call(stream, "pmemsave", val=args.return_record_pa,
                             size=104, filename=str(return_raw))
                if args.return_log_pa is not None:
                    qmp_call(stream, "pmemsave", val=args.return_log_pa,
                             size=65536, filename=str(return_log_raw))
                if args.lk_report_pa is not None:
                    qmp_call(stream, "pmemsave", val=args.lk_report_pa,
                             size=96, filename=str(lk_report_raw))
                if args.exception_record_pa is not None:
                    qmp_call(stream, "pmemsave", val=args.exception_record_pa,
                             size=40, filename=str(exception_raw))
                stream.write(b'{"execute":"quit"}\n')
                stream.flush()
            process.wait(timeout=5)
            stderr_stream.close()
        finally:
            if process.poll() is None:
                process.kill()
                process.wait()
            if not stderr_stream.closed:
                stderr_stream.close()

        data = raw.read_bytes()
        if args.capture:
            args.capture.write_bytes(data)
        if args.slot_pa is not None:
            magic, stub, checkpoint, delta = struct.unpack(
                "<8sQQQ", slot_raw.read_bytes())
            if magic != b"XNULDRST" or stub == 0 or stub & 3:
                raise SystemExit(
                    f"invalid return slot: magic={magic!r} stub={stub:#x}")
            if (args.expect_slot_stub is not None and
                    stub != args.expect_slot_stub):
                raise SystemExit(
                    f"return stub={stub:#x} expected={args.expect_slot_stub:#x}")
            if checkpoint != args.expect_slot_checkpoint:
                raise SystemExit(
                    f"checkpoint={checkpoint:#x} "
                    f"expected={args.expect_slot_checkpoint:#x}")
            if (args.expect_slot_delta is not None and
                    delta != args.expect_slot_delta):
                raise SystemExit(
                    f"phys-virt={delta:#x} "
                    f"expected={args.expect_slot_delta:#x}")
            print("bootshim-return-slot-memory: PASS "
                  f"pa={args.slot_pa:#x} stub={stub:#x} delta={delta:#x}")
        if args.return_record_pa is not None:
            return_data = return_raw.read_bytes()
            if args.expect_no_return:
                if any(return_data):
                    raise SystemExit(
                        "XNU unexpectedly returned to the bootshim: "
                        f"record={return_data.hex()}")
                print("bootshim-xnu-no-return-record: PASS "
                      f"pa={args.return_record_pa:#x}")
                return_data = None
            if return_data is None:
                fields = None
            else:
                fields = struct.unpack("<QIIII10Q", return_data)
        else:
            fields = None
        if fields is not None:
            (magic, version, size, result, _reserved, reason, code, elr, far,
             log_pa, log_length, copied, head, tail, checksum) = fields
            if copied > 65536 or copied != head + tail or copied > log_length:
                raise SystemExit(
                    "invalid XNU return log lengths: "
                    f"length={log_length} copied={copied} "
                    f"head={head} tail={tail}")
            if copied and args.return_log_pa is None:
                raise SystemExit(
                    "XNU return record contains a log but --return-log-pa "
                    "was not supplied")
            expected_return_checksum = mutation_receipt(return_data[:-8])
            if copied:
                saved_log = return_log_raw.read_bytes()
                expected_return_checksum = mutation_receipt(
                    saved_log[:copied], expected_return_checksum)
            if (magic != 0x4455434858524554 or version != 1 or size != 104 or
                    result != 0 or _reserved != 0 or code == 0 or
                    checksum != expected_return_checksum):
                raise SystemExit(
                    "invalid XNU return record: "
                    f"magic={magic:#x} version={version} size={size} "
                    f"result={result} reserved={_reserved} code={code:#x} "
                    f"checksum={checksum:#x} "
                    f"expected={expected_return_checksum:#x}")
            if (args.expect_return_reason is not None and
                    reason != args.expect_return_reason):
                raise SystemExit(
                    f"return reason={reason:#x} "
                    f"expected={args.expect_return_reason:#x}")
            print("bootshim-xnu-early-return-record: PASS "
                  f"pa={args.return_record_pa:#x} reason={reason:#x} "
                  f"esr={code:#x} elr={elr:#x} far={far:#x} "
                  f"log_pa={log_pa:#x} log_length={log_length} "
                  f"copied={copied}")
        if args.exception_record_pa is not None:
            kind, esr, elr, far, sp = struct.unpack(
                "<5Q", exception_raw.read_bytes())
            if args.expect_no_exception and any((kind, esr, elr, far, sp)):
                raise SystemExit(
                    "bootshim exception: "
                    f"kind={kind} esr={esr:#x} elr={elr:#x} "
                    f"far={far:#x} sp={sp:#x}")
            if any((kind, esr, elr, far, sp)):
                print("bootshim-exception-record: PRESENT "
                      f"kind={kind} esr={esr:#x} elr={elr:#x} "
                      f"far={far:#x} sp={sp:#x}")
            else:
                print("bootshim-exception-record: CLEAR "
                      f"pa={args.exception_record_pa:#x}")
        if args.lk_report_pa is not None:
            report_data = lk_report_raw.read_bytes()
            fields = struct.unpack(LK_REPORT_FORMAT, report_data)
            (magic, version, size, result, state, error, detail,
             prepare_result, reserved, generation, bytes_read, source_reads,
             entry, boot_args, segment_count, checksum) = fields
            expected_checksum = mutation_receipt(report_data[:-8])
            if (magic != 0x5450524B4C435544 or version != 1 or size != 96 or
                    result != 0 or state != 2 or error != 0 or detail != 0 or
                    prepare_result != 0 or reserved != 0 or bytes_read == 0 or
                    source_reads == 0 or entry == 0 or boot_args == 0 or
                    segment_count == 0 or checksum != expected_checksum):
                raise SystemExit(
                    "invalid LK RAM report: "
                    f"magic={magic:#x} version={version} size={size} "
                    f"result={result} state={state} error={error} "
                    f"detail={detail} prepare={prepare_result} "
                    f"generation={generation:#x} bytes={bytes_read} "
                    f"reads={source_reads} entry={entry:#x} "
                    f"boot_args={boot_args:#x} segments={segment_count} "
                    f"checksum={checksum:#x} expected={expected_checksum:#x}")
            if (args.expect_lk_generation is not None and
                    generation != args.expect_lk_generation):
                raise SystemExit(
                    f"LK generation={generation:#x} "
                    f"expected={args.expect_lk_generation:#x}")
            if lk_expected is not None:
                actual = {
                    "bytes": bytes_read,
                    "segments": segment_count,
                    "entry": entry,
                    "boot_args": boot_args,
                }
                if actual != lk_expected:
                    raise SystemExit(
                        f"LK report/payload mismatch: actual={actual} "
                        f"expected={lk_expected}")
            print("bootshim-lk-ram-report: PASS "
                  f"pa={args.lk_report_pa:#x} generation={generation:#x} "
                  f"bytes={bytes_read} reads={source_reads} "
                  f"entry={entry:#x} boot_args={boot_args:#x} "
                  f"segments={segment_count}")
        if args.pattern == "xnu":
            words = struct.unpack(f"<{len(data) // 4}I", data)
            white = sum(value == 0xFFFFFFFF for value in words)
            if white < 512:
                raise SystemExit(f"XNU stage-0 marker missing: white_pixels={white}")
            print(f"bootshim-qemu-xnu-entry: PASS white_pixels={white}")
            return
        if args.pattern == "normal":
            expected_rows = EXPECTED
        elif args.pattern == "return":
            expected_rows = RETURN_EXPECTED
        elif args.pattern == "slot-missing":
            expected_rows = SLOT_MISSING_EXPECTED
        elif args.pattern == "slot-ready":
            expected_rows = SLOT_READY_EXPECTED
        elif args.pattern == "early-return":
            expected_rows = EARLY_RETURN_EXPECTED
        elif args.pattern == "lk-ram":
            expected_rows = LK_RAM_EXPECTED
        else:
            expected_rows = EXCEPTION_EXPECTED
        for row, expected in enumerate(expected_rows):
            offset = (row * BAND_HEIGHT + BAND_HEIGHT // 2) * FB_STRIDE
            first = struct.unpack_from("<I", data, offset)[0]
            last = struct.unpack_from("<I", data, offset + (FB_WIDTH - 1) * 4)[0]
            padding = struct.unpack_from("<I", data, offset + FB_WIDTH * 4)[0]
            if first != expected or last != expected or padding != 0:
                raise SystemExit(
                    f"row {row}: first={first:#010x} last={last:#010x} "
                    f"padding={padding:#010x} expected={expected:#010x}")
    print("bootshim-qemu-test: PASS")


if __name__ == "__main__":
    main()
