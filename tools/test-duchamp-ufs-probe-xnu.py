#!/usr/bin/env python3
"""Boot a full CI XNU and verify its one-block QEMU UFS probe against Android."""

import argparse
import concurrent.futures
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import re
import runpy
import secrets
import shutil
import socket
import struct
import subprocess
import sys
import tempfile
import time

import adt
from duchamp_ufs_xnu_replay import symbols
import mkpayload
import qemu_ufs

TOOLS = Path(__file__).resolve().parent
handoff = runpy.run_path(str(TOOLS / "test-duchamp-ufs-handoff-xnu.py"))
sweet = runpy.run_path(str(TOOLS / "qemu-sweet.py"))
CASES = {
    "firmware_xnu_compare": handoff["CASES"]["matched"],
    "inherited_pending": handoff["CASES"]["matched"],
    "inherited_controller": handoff["CASES"]["matched"],
    **handoff["CASES"],
    "changed_byte": (True, 0x3f, 0, 1),
    "missing_handoff_opt_in": (None, 0, 0, None),
}
DONE = "DUCHAMP UFS PROBE DONE"
BLOCKED = "DUCHAMP UFS PROBE BLOCKED"
FAILED = "DUCHAMP UFS PROBE FAILED"
START = "DUCHAMP UFS PROBE SHA256 "
FIRMWARE_LIST = 0x60000000  # Guest RAM below the XNU memory window.
FIRMWARE_REQUEST = "firmware_pending"
FIRMWARE_QUEUE_REGISTERS = (
    ("HCE", 0x34), ("HCS", 0x30), ("UTRLBA", 0x50), ("UTRLBAU", 0x54),
    ("UTRLDBR", 0x58), ("UTRLRSR", 0x60), ("UTMRLDBR", 0x78), ("UTMRLRSR", 0x80),
)


def sha256(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def load_reference(path, backup):
    reference = json.loads(path.read_text())
    assert reference["product"] == "duchamp" and reference["soc"] == "mt6897"
    assert reference["partition"] == "vendor_boot_a" and reference["matched_live_partition"]
    assert reference["matched_saved_partition"] and reference["matched_second_lba_read"]
    lun, lba, size = qemu_ufs.PROBE_LUN, qemu_ufs.PROBE_LBA, qemu_ufs.PROBE_BYTES
    assert (reference["linux_scsi_lun"], reference["linux_lba"],
            reference["linux_logical_block_bytes"], reference["byte_offset"]) == (lun, lba, size, lba * size)
    assert sha256(backup) == reference["saved_vendor_boot_sha256"]
    with backup.open("rb") as stream:
        block = stream.read(size)
    assert len(block) == size and hashlib.sha256(block).hexdigest() == reference["block_sha256"]
    return block, reference


def fixture(path, block):
    size, lba = qemu_ufs.PROBE_BYTES, qemu_ufs.PROBE_LBA
    with path.open("xb") as stream:
        stream.truncate((lba + 2) * size)
        stream.seek(lba * size)
        stream.write(block)
    return path, sha256(path), hashlib.sha256(block).hexdigest()


def probe_checkpoint(kernel):
    code = subprocess.check_output(["llvm-objdump", "-d", "--disassemble-symbols=_qu_probe_stop",
                                    str(kernel)], text=True)
    loops = re.findall(r"(?m)^([0-9a-f]+): d503205f\s+wfe\s*\n[0-9a-f]+: 17ffffff\s+b\s+0x\1\b", code)
    assert len(loops) == 1, code
    return int(loops[0], 16)


@contextmanager
def qtest(endpoint):
    with socket.socket(socket.AF_UNIX) as sock:
        sock.settimeout(5)
        sock.connect(str(endpoint))
        with sock.makefile("rw", encoding="ascii") as stream:
            def command(request):
                stream.write(request + "\n")
                stream.flush()
                reply = stream.readline().strip().split(maxsplit=1)
                if not reply or reply[0] != "OK":
                    raise RuntimeError(f"qtest {request}: {reply}")
                if request.startswith("read "):
                    return bytes.fromhex(reply[1].removeprefix("0x"))
                return int(reply[1], 0) if len(reply) == 2 else None
            yield command


def wait_doorbell(command, expected):
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        if command(f"readl {qemu_ufs.BAR[0] + 0x58:#x}") == expected:
            return
        time.sleep(0.02)
    raise RuntimeError(f"UFS doorbell did not reach {expected}")


def submit_firmware_request(command, *, read):
    """Submit one slot-0 command on the read-only emulated LUN."""
    descriptor_pa = FIRMWARE_LIST + 0x1000
    buffer_pa = FIRMWARE_LIST + 0x2000
    size = qemu_ufs.PROBE_BYTES if read else 0
    descriptor = struct.pack("<8I", 0x15000000 if read else 0x11000000, 0, 0xf, 0,
                             descriptor_pa, 0, (128 << 16) | 128, (256 << 16) | 1 if read else 0)
    upiu = bytearray(1040 if read else 32)
    upiu[:4] = bytes((1, 0x40 if read else 0, qemu_ufs.PROBE_LUN, 2 if read else 1))
    if read:
        struct.pack_into(">I", upiu, 12, size)
        struct.pack_into(">BBQIBB", upiu, 16, 0x88, 0, qemu_ufs.PROBE_LBA, 1, 0, 0)
        struct.pack_into("<4I", upiu, 1024, buffer_pa, 0, 0, size - 1)
    for address, data in ((descriptor_pa, upiu), (FIRMWARE_LIST, descriptor)):
        command(f"write {address:#x} {len(data):#x} 0x{data.hex()}")
    command(f"writel {qemu_ufs.BAR[0] + 0x58:#x} 1")


def finish_firmware_read(command):
    wait_doorbell(command, 0)
    assert command(f"readl {FIRMWARE_LIST + 8:#x}") == 0
    response = command(f"read {FIRMWARE_LIST + 0x1200:#x} 0x10")
    assert response[0] == 0x21 and response[2:4] == bytes((qemu_ufs.PROBE_LUN, 2))
    assert response[6:8] == bytes(2) and response[12:16] == bytes(4)
    size = qemu_ufs.PROBE_BYTES
    block = command(f"read {FIRMWARE_LIST + 0x2000:#x} {size:#x}")
    assert len(block) == size
    return dict(lun=qemu_ufs.PROBE_LUN, lba=qemu_ufs.PROBE_LBA, bytes=size,
                sha256=hashlib.sha256(block).hexdigest(), ocs=0, scsi_status=0)


def seed_firmware_ufs(endpoint, trace, *, hold_read=None, release_after_read=False):
    """Program QEMU's legacy transfer list while the XNU CPU is paused."""
    bar = qemu_ufs.BAR[0]
    pci = qemu_ufs.ECAM[0] + (4 << 15)
    state = {}
    with qtest(endpoint) as command:
        assert command(f"readl {pci:#x}") == 0x00131b36
        bar_type = command(f"readl {pci + 0x10:#x}") & 15
        assert bar_type in (0, 4)
        command(f"writel {pci + 0x10:#x} {bar:#x}")
        if bar_type == 4:
            command(f"writel {pci + 0x14:#x} 0")
        command(f"writew {pci + 4:#x} {6 if hold_read or release_after_read else 2}")
        for offset, value in ((0x34, 1), (0x90, 0x16), (0x50, FIRMWARE_LIST),
                              (0x54, 0), (0x60, 1)):
            command(f"writel {bar + offset:#x} {value:#x}")
        if hold_read or release_after_read:
            # Consume the virtual LUN's power-on UNIT ATTENTION before its read.
            submit_firmware_request(command, read=False)
            wait_doorbell(command, 0)
            assert command(f"readl {FIRMWARE_LIST + 8:#x}") == 0
            if hold_read:
                hold_read()
            submit_firmware_request(command, read=True)
        if hold_read:
            deadline = time.monotonic() + 5
            while "ufs_exec_scsi_cmd slot 0, lun 0x2, opcode 0x88" not in trace.read_text():
                if time.monotonic() >= deadline:
                    raise RuntimeError("Firmware READ(16) was not submitted")
                time.sleep(0.02)
            assert command(f"readl {FIRMWARE_LIST + 8:#x}") == 0xf
        if release_after_read:
            state["firmware_read"] = finish_firmware_read(command)
            # Stop submissions and release the completed firmware list before XNU.
            for offset in (0x60, 0x50, 0x54, 0x34):
                command(f"writel {bar + offset:#x} 0")
        registers = {
            name: command(f"readl {bar + offset:#x}")
            for name, offset in FIRMWARE_QUEUE_REGISTERS
        }
        if release_after_read:
            assert not any(registers.values()), registers
        else:
            assert registers["HCE"] == 1 and registers["HCS"] & 3 == 3
            assert (registers["UTRLBA"], registers["UTRLBAU"]) == (FIRMWARE_LIST, 0)
            assert (registers["UTRLDBR"], registers["UTRLRSR"]) == (int(bool(hold_read)), 1)

        # XNU maps the PCI BAR again without changing the HCI state here.
        command(f"writew {pci + 4:#x} 0")
        pci_command = command(f"readw {pci + 4:#x}")
        assert pci_command == 0
    setup_trace = trace.read_text().splitlines()
    assert setup_trace
    return dict(queue_mode="legacy", registers=registers, pci_command=pci_command,
                setup_trace=setup_trace, **state)


def observe_pending_request(monitor, endpoint, trace, state, checkpoint, seconds):
    """Observe the WFE stop loop before resuming firmware I/O for GDB capture."""
    qmp_channel = runpy.run_path(str(TOOLS / "duchamp-qemu-windows.py"))["qmp_channel"]
    with socket.socket(socket.AF_UNIX) as sock:
        sock.connect(str(monitor))
        qmp = qmp_channel(sock)

        def hmp(command):
            return qmp("human-monitor-command", **{"command-line": command})

        def block_command(command):
            assert not hmp(f'qemu-io duchamp_lu{qemu_ufs.PROBE_LUN} "{command}"')

        try:
            firmware = seed_firmware_ufs(
                endpoint, trace, hold_read=lambda: block_command(f"break read_aio {FIRMWARE_REQUEST}")
            )
            state.update(firmware)
            qmp("cont")
            deadline = time.monotonic() + seconds
            while time.monotonic() < deadline:
                match = re.search(r"\bPC=([0-9a-f]+)", hmp("info registers"), re.I)
                if match and int(match[1], 16) in (checkpoint, checkpoint + 4):
                    break
                time.sleep(0.2)
            else:
                raise RuntimeError("XNU did not reach the probe stop loop with I/O pending")
            state["guest_trace_end"] = len(trace.read_text().splitlines())
            with qtest(endpoint) as command:
                doorbell = command(f"readl {qemu_ufs.BAR[0] + 0x58:#x}")
                ocs = command(f"readl {FIRMWARE_LIST + 8:#x}")
            assert (doorbell, ocs) == (1, 0xf)
            state["at_rejection"] = dict(pc=hex(int(match[1], 16)), UTRLDBR=doorbell, OCS=ocs)
        finally:
            # A debug stop drains QEMU block I/O. Release only after sampling.
            block_command(f"resume {FIRMWARE_REQUEST}")

    with qtest(endpoint) as command:
        wait_doorbell(command, 0)
        ocs = command(f"readl {FIRMWARE_LIST + 8:#x}")
        assert ocs == 0
        state["after_firmware_completion"] = dict(UTRLDBR=0, OCS=ocs)


def boot_to_probe(payload, folder, options, qemu, seconds, names, checkpoint,
                  *, inherited, pending, compare_record):
    """Stop at the compiled terminal loop and capture the kernel's BSD log."""
    run = folder / "run"
    run.mkdir()
    frame = sweet["FRAMEBUFFERS"]["duchamp"]
    base, image, args, entry = sweet["build_image"](payload, frame)
    ram_size = max(4, -(-(base + struct.unpack_from("<Q", payload, 0x40)[0] - 0x40000000) // (1 << 30)))
    trace = folder / "ufs.trace"
    events = folder / "trace-events"
    trace_events = ("ufs_mmio_read\nufs_mmio_write\nufs_exec_scsi_cmd\n"
                    "scsi_req_parsed_lba\nscsi_req_parsed\n")
    compare = compare_record is not None
    observe_firmware = inherited or compare
    if pending or compare:
        trace_events += "ufs_process_db\nufs_complete_req\n"
    if pending:
        options = options.copy()
        drive_index = options.index("-drive") + 1
        options[drive_index] = options[drive_index].replace("file=", "file=blkdebug::", 1)
    events.write_text(trace_events)
    memory = folder / "guest-memory"
    with tempfile.TemporaryDirectory(prefix="ufs-probe-qemu-") as temporary:
        scratch = Path(temporary)
        monitor, debug = scratch / "qmp", scratch / "gdb"
        firmware = scratch / "firmware.sock"
        ram, stub, framebuffer = (scratch / name for name in ("ram", "stub", "fb"))
        ram.write_bytes(image)
        stub_pa = sweet["STUB_PA"]
        stub.write_bytes(sweet["stub"](args, entry))
        cmd = [qemu, "-M", "virt,gic-version=3,highmem-ecam=off,memory-backend=probe_ram",
               "-m", f"{ram_size}G", "-cpu", "cortex-a76", "-smp", "1", "-nodefaults", "-nographic",
               "-object", f"memory-backend-file,id=probe_ram,size={ram_size}G,mem-path={memory},share=on,prealloc=off",
               "-qmp", f"unix:{monitor},server=on,wait=off", "-gdb", f"unix:{debug},server=on,wait=off",
               "-S", "-no-reboot", "-device", f"loader,file={ram},addr={base:#x},force-raw=on",
               "-device", f"loader,file={stub},addr={stub_pa:#x},force-raw=on",
               "-device", f"loader,addr={stub_pa:#x},cpu-num=0",
               "-trace", f"events={events},file={trace}", *options]
        if observe_firmware:
            cmd.extend(["-qtest", f"unix:{firmware},server=on,wait=off",
                        "-qtest-log", str(folder / "firmware-qtest.log")])
        ring, block = scratch / "msgbuf", scratch / "block"
        gdb = scratch / "capture.gdb"
        gdb.write_text(f"""set architecture aarch64
target remote {debug}
if $pc != {checkpoint:#x} && $pc != {checkpoint + 4:#x}
  hbreak *{checkpoint:#x}
  continue
end
if $pc != {checkpoint:#x} && $pc != {checkpoint + 4:#x}
  quit 1
end
set $msg = *(unsigned long long *) {names['_msgbufp']:#x}
set $size = *(unsigned int *) ($msg + 4)
set $next = *(unsigned int *) ($msg + 8)
set $ring = *(unsigned long long *) ($msg + 16)
if *(unsigned int *) $msg != 0x063061 || $size == 0 || $size > 1048576 || $next >= $size
  quit 1
end
printf "PROBE PC=%#lx RING size=%u next=%u\\n", $pc, $size, $next
dump binary memory {ring} $ring ($ring + $size)
dump binary memory {block} {names['_qu_probe_stop.block']:#x} {names['_qu_probe_stop.block'] + qemu_ufs.PROBE_BYTES:#x}
disconnect
""")
        start = time.monotonic()
        with (folder / "runner.log").open("w") as log:
            process = subprocess.Popen(cmd, stdout=log, stderr=log)
            try:
                for _ in range(100):
                    if monitor.exists() and debug.exists() and (
                        not observe_firmware or firmware.exists()
                    ):
                        break
                    if process.poll() is not None:
                        raise RuntimeError("QEMU exited before opening its sockets")
                    time.sleep(0.05)
                else:
                    raise RuntimeError("QEMU socket startup timed out")
                if observe_firmware:
                    state = {}
                    if pending:
                        observe_pending_request(monitor, firmware, trace, state, checkpoint, seconds)
                    else:
                        state = seed_firmware_ufs(firmware, trace, release_after_read=compare)
                    if compare:
                        fields = struct.unpack("<IIQ8I2Q", compare_record)
                        queue_fields = ("HCE", "UTRLDBR", "UTMRLDBR", "UTRLRSR", "UTMRLRSR")
                        measured = tuple(state["registers"][name] for name in queue_fields)
                        assert fields[3:10] == (1, *measured, 0), (fields, measured)
                        state.update(boot_id=hex(fields[2]), record_matches_measured_queues=True,
                                     source="QTest before XNU execution")
                    (folder / "firmware-state.json").write_text(json.dumps(state, indent=2) + "\n")
                receipt = subprocess.run(["gdb-multiarch", "-q", "-nx", "-batch", "-x", str(gdb)],
                                         text=True, capture_output=True, timeout=seconds)
                (run / "gdb.log").write_text(receipt.stdout + receipt.stderr)
                receipt.check_returncode()
                marker = re.search(r"PROBE PC=(0x[0-9a-f]+) RING size=(\d+) next=(\d+)", receipt.stdout)
                assert marker, receipt.stdout
                assert int(marker[1], 16) in (checkpoint, checkpoint + 4)
                size, index = int(marker[2]), int(marker[3])
                data = ring.read_bytes()
                assert len(data) == size
                log_text = (data[index:] + data[:index]).replace(b"\0", b"").decode(errors="replace")
                (run / "kernel-log.txt").write_text(log_text)
                sweet["qmp"](str(monitor), pmemsave=(frame["base"], frame["stride"] * frame["height"],
                                                     str(framebuffer)))
                font = sweet["payload_data"](payload, names["_iso_font"], 256 * 16)
                screen, _ = sweet["decode_screen"](framebuffer.read_bytes(), font, frame)
                (run / "fb.txt").write_text(screen)
                result = dict(checkpoint=hex(checkpoint), elapsed_host_seconds=round(time.monotonic()-start, 3),
                              stop_marker=next((m for m in (DONE, BLOCKED, FAILED) if m in log_text), None))
                (run / "result.json").write_text(json.dumps(result, indent=2) + "\n")
                return log_text, screen, block.read_bytes(), result
            finally:
                if process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()
                memory.unlink(missing_ok=True)


def run_case(name, ids, output, kernel, tree_raw, disk, qemu, seconds, names, checkpoint):
    same_boot, proof, busy, verdict = CASES[name]
    pending = name == "inherited_pending"
    inherited = pending or name == "inherited_controller"
    compare = name == "firmware_xnu_compare"
    entry_id = ids[name]
    bl31_id = 0 if same_boot is None else entry_id if same_boot else ids["matched"]
    folder = output / name
    folder.mkdir()
    tree, end = adt.parse(tree_raw)
    assert end == len(tree_raw)
    chosen = qemu_ufs.child(tree, "chosen")
    record = None
    if bl31_id:
        record = struct.pack("<IIQ8I2Q", 1, proof, bl31_id, 1, 0, busy, 0, 0, 0, 0, 0, 5, 6)
        chosen.props.append(("qemu-bl31-ufs", 0, record))
    adt_path = folder / "boot.adt"
    adt_path.write_bytes(adt.serialize(tree))
    cmdline = ("debug=0xc serial=3 cpus=1 keepsyms=1 -enable_kprintf_spam -noprogress "
               "rd=qufs0 rootrw=0 sweet-qemu-ufs=1 sweet_console_fb=1 sweet-qemu-ufs-probe=1 "
               f"sweet-qemu-boot-id={entry_id:#x}")
    if verdict is not None:
        cmdline += " sweet-qemu-ufs-handoff=1"
    payload, _ = mkpayload.build(kernel, adt_path, cmdline)
    disk_path, disk_hash, expected_hash = disk
    options, metadata = qemu_ufs.runner_options(payload, disk_path, "cortex-a76", "duchamp")
    log, screen, block, result = boot_to_probe(payload, folder, options, qemu, seconds, names,
                                              checkpoint, inherited=inherited, pending=pending,
                                              compare_record=record if compare else None)
    (folder / "run/ufs-input.json").write_text(json.dumps(metadata, indent=2) + "\n")
    seen = set(re.findall(r"UFS XNU=([0-9a-f]{16}) BL31=([0-9a-f]{16}) V=(\d+)", screen, re.I))
    assert seen == (set() if verdict is None else {(f"{entry_id:016x}", f"{bl31_id:016x}", str(verdict))}), (name, seen)
    hashes = set(re.findall(START + r"([0-9a-f]{64})(?![0-9a-f])", log, re.I))
    assert metadata["readonly"] and metadata["no_ramdisk"] and metadata["sha256"] == disk_hash
    assert metadata["probe"] == {"lun": qemu_ufs.PROBE_LUN, "lba": qemu_ufs.PROBE_LBA,
                                 "bytes": qemu_ufs.PROBE_BYTES}
    traffic = (folder / "ufs.trace").read_text()
    firmware_result = {}
    if inherited or compare:
        state = json.loads((folder / "firmware-state.json").read_text())
        setup_trace = state.pop("setup_trace")
        events = traffic.splitlines()
        assert events[:len(setup_trace)] == setup_trace, events
        guest_trace_end = state.pop("guest_trace_end", len(events))
        guest_events = events[len(setup_trace):guest_trace_end]
        if pending or compare:
            firmware_commands = [line for line in setup_trace if line.startswith("ufs_exec_scsi_cmd ")]
            assert firmware_commands == ["ufs_exec_scsi_cmd slot 0, lun 0x2, opcode 0x0",
                                         "ufs_exec_scsi_cmd slot 0, lun 0x2, opcode 0x88"], setup_trace
            assert (f"scsi_req_parsed_lba target 0 lun 2 tag 2 command 136 lba {qemu_ufs.PROBE_LBA}"
                    in setup_trace), setup_trace
            assert (f"scsi_req_parsed target 0 lun 2 tag 2 command 136 dir 1 length {qemu_ufs.PROBE_BYTES}"
                    in setup_trace), setup_trace
            completion = "ufs_complete_req UTRLDBR slot 0"
            assert setup_trace.count(completion) == (2 if compare else 1)
            (folder / "firmware-ufs.trace").write_text("\n".join(setup_trace) + "\n")
        if pending:
            after_guest = events[guest_trace_end:]
            assert after_guest[0] == "ufs_mmio_read addr 0x58 data 0x1 size 4", after_guest
            assert after_guest.count(completion) == 1 and all(
                line == completion or line.startswith("ufs_mmio_read ") for line in after_guest
            ), after_guest
            (folder / "after-xnu-ufs.trace").write_text("\n".join(after_guest) + "\n")
        (folder / "guest-ufs.trace").write_text("\n".join(guest_events) + "\n")
        traffic = "\n".join(guest_events)
        firmware_result["firmware_state"] = state
        if inherited:
            # A single HCE=1 read proves the guard was exercised after PCI setup.
            assert guest_events == ["ufs_mmio_read addr 0x34 data 0x1 size 4"], guest_events
            assert result["stop_marker"] == FAILED and f"{FAILED} status=-5" in log, log
            assert not hashes and not any(block)
            firmware_result.update(controller_mmio_reads=1, controller_mmio_writes=0,
                                   scsi_commands=0, provider_status=-5)
        else:
            assert state["boot_id"] == hex(entry_id) == hex(bl31_id)
            assert state["record_matches_measured_queues"]
            assert state["firmware_read"]["sha256"] == hashlib.sha256(block).hexdigest() == expected_hash
            firmware_result["firmware_xnu_match"] = True
    commands = re.findall(r"^ufs_exec_scsi_cmd slot \d+, lun (0x[0-9a-f]+), opcode (0x[0-9a-f]+)$",
                          traffic, re.M)
    reads = re.findall(r"^scsi_req_parsed_lba target \d+ lun (\d+) tag \d+ command 136 lba (\d+)$",
                       traffic, re.M)
    transfers = [int(n) for n in re.findall(
        r"^scsi_req_parsed target \d+ lun 2 tag \d+ command 136 dir 1 length (\d+)$", traffic, re.M)]
    if verdict == 1 and not inherited:
        assert result["stop_marker"] == DONE and hashes == {expected_hash}, (name, result, hashes)
        assert hashlib.sha256(block).hexdigest() == expected_hash
        assert commands.count(("0x2", "0x88")) == 1 and reads == [("2", "276480")], (name, commands, reads)
        assert transfers == [qemu_ufs.PROBE_BYTES], (name, transfers)
        assert all(lun == "0x2" and opcode in ("0x9e", "0x88") for lun, opcode in commands)
    elif not inherited:
        assert result["stop_marker"] == BLOCKED and not hashes and not traffic.strip(), (name, result, hashes)
        assert not any(block)
    return dict(entry_boot_id=hex(entry_id), bl31_boot_id=hex(bl31_id), verdict=verdict,
                stop_marker=result["stop_marker"], sha256=next(iter(hashes), None),
                controller_trace_events=len(traffic.splitlines()), read16=len(reads),
                bytes_read=sum(transfers),
                elapsed_seconds=result["elapsed_host_seconds"], **firmware_result)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("kernel", "ci-receipt", "adt", "reference", "backup", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--seconds", type=int, default=120)
    parser.add_argument("--jobs", type=int, choices=(1, 2, 3), default=3)
    args = parser.parse_args()
    kernel, output = args.kernel.resolve(), args.output.resolve()
    build = json.loads(args.ci_receipt.read_text(encoding="utf-8-sig"))
    assert build["conclusion"] == "success" and sha256(kernel) == build["sha256"]
    required = {"_duchamp_qemu_ufs_handoff_probe_lease", "_mt6897_ufs_probe_bind",
                "_mt6897_ufs_probe_read", "_arm_init", "_qu_probe_stop.block", "_msgbufp"}
    names = symbols(kernel)
    assert required <= names.keys()
    checkpoint = probe_checkpoint(kernel)
    qemu = shutil.which("qemu-system-aarch64")
    if qemu is None:
        parser.error("qemu-system-aarch64 is required")
    tree_raw = args.adt.read_bytes()
    tree, end = adt.parse(tree_raw)
    assert end == len(tree_raw) and qemu_ufs.validate_tree(tree) is None
    assert qemu_ufs.child(tree, "chosen").prop("qemu-bl31-ufs") is None
    block, reference = load_reference(args.reference, args.backup)
    changed = bytes([block[0] ^ 1]) + block[1:]
    output.mkdir(parents=True)
    ids = {name: secrets.randbits(62) | (1 << 62) for name in CASES}
    assert len(set(ids.values())) == len(ids)
    cases = {}
    with tempfile.TemporaryDirectory(prefix="probe-media-", dir=output) as temporary:
        original = fixture(Path(temporary) / "android-reference.raw", block)
        tampered = fixture(Path(temporary) / "changed-byte.raw", changed)
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as workers:
            futures = {
                workers.submit(run_case, name, ids, output, kernel, tree_raw,
                               tampered if name == "changed_byte" else original, qemu, args.seconds,
                               names, checkpoint): name
                for name in CASES
            }
            for future in concurrent.futures.as_completed(futures):
                name = futures[future]
                cases[name] = future.result()
                print(name, json.dumps(cases[name]), flush=True)
        assert all(sha256(disk[0]) == disk[1] for disk in (original, tampered))
    assert sha256(kernel) == build["sha256"] and sha256(args.backup) == reference["saved_vendor_boot_sha256"]
    assert cases["matched"]["sha256"] == reference["block_sha256"] != cases["changed_byte"]["sha256"]
    report = dict(passed=True, actual_xnu=True, full_kernel_rebuild=True, replay_hooks_applied=False,
                  build=build, synthetic_bl31=True, qemu_only=True, media_unchanged=True,
                  phone_access=False, partition_write=False, android_reference_sha256=reference["block_sha256"],
                  matched_android=True, changed_byte_detected=True,
                  denied_cases=sum(case["stop_marker"] == BLOCKED for case in cases.values()), cases=cases)
    (output / "verification.json").write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
