#!/usr/bin/env python3
"""Boot a full CI XNU and verify its one-block QEMU UFS probe against Android."""

import argparse
import concurrent.futures
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
    "inherited_controller": handoff["CASES"]["matched"],
    **handoff["CASES"],
    "changed_byte": (True, 0x3f, 0, 1),
    "missing_handoff_opt_in": (None, 0, 0, None),
}
DONE = "DUCHAMP UFS PROBE DONE"
BLOCKED = "DUCHAMP UFS PROBE BLOCKED"
FAILED = "DUCHAMP UFS PROBE FAILED"
START = "DUCHAMP UFS PROBE SHA256 "


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


def seed_firmware_ufs(endpoint):
    """Program QEMU's legacy transfer list while the XNU CPU is paused."""
    bar = qemu_ufs.BAR[0]
    pci = qemu_ufs.ECAM[0] + (4 << 15)
    list_pa = 0x60000000  # Guest RAM below the XNU memory window.
    setup_trace = []

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
                return int(reply[1], 0) if len(reply) == 2 else None

            assert command(f"readl {pci:#x}") == 0x00131b36
            bar_type = command(f"readl {pci + 0x10:#x}") & 15
            assert bar_type in (0, 4)
            command(f"writel {pci + 0x10:#x} {bar:#x}")
            if bar_type == 4:
                command(f"writel {pci + 0x14:#x} 0")
            command(f"writew {pci + 4:#x} 2")
            for offset, value in ((0x34, 1), (0x90, 0x16), (0x50, list_pa),
                                  (0x54, 0), (0x60, 1)):
                command(f"writel {bar + offset:#x} {value:#x}")
                setup_trace.append(f"ufs_mmio_write addr {offset:#x} data {value:#x} size 4")
            registers = {}
            for name, offset in (("HCE", 0x34), ("HCS", 0x30), ("UTRLBA", 0x50),
                                 ("UTRLBAU", 0x54), ("UTRLDBR", 0x58), ("UTRLRSR", 0x60)):
                value = command(f"readl {bar + offset:#x}")
                registers[name] = value
                setup_trace.append(f"ufs_mmio_read addr {offset:#x} data {value:#x} size 4")
            assert registers["HCE"] == 1 and registers["HCS"] & 3 == 3
            assert (registers["UTRLBA"], registers["UTRLBAU"]) == (list_pa, 0)
            assert (registers["UTRLDBR"], registers["UTRLRSR"]) == (0, 1)

            # Restore the PCI entry condition required by qu_prepare, leaving
            # the emulated HCI and its list running. XNU will map the BAR again.
            command(f"writew {pci + 4:#x} 0")
            pci_command = command(f"readw {pci + 4:#x}")
            assert pci_command == 0
    return dict(queue_mode="legacy", registers=registers, pci_command=pci_command,
                setup_trace=setup_trace)


def boot_to_probe(payload, folder, options, qemu, seconds, names, checkpoint,
                  *, inherited_controller):
    """Stop at the compiled terminal loop and capture the kernel's BSD log."""
    run = folder / "run"
    run.mkdir()
    frame = sweet["FRAMEBUFFERS"]["duchamp"]
    base, image, args, entry = sweet["build_image"](payload, frame)
    ram_size = max(4, -(-(base + struct.unpack_from("<Q", payload, 0x40)[0] - 0x40000000) // (1 << 30)))
    trace = folder / "ufs.trace"
    events = folder / "trace-events"
    events.write_text("ufs_mmio_read\nufs_mmio_write\nufs_exec_scsi_cmd\n"
                      "scsi_req_parsed_lba\nscsi_req_parsed\n")
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
        if inherited_controller:
            cmd.extend(["-qtest", f"unix:{firmware},server=on,wait=off",
                        "-qtest-log", str(folder / "firmware-qtest.log")])
        ring, block = scratch / "msgbuf", scratch / "block"
        gdb = scratch / "capture.gdb"
        gdb.write_text(f"""set architecture aarch64
target remote {debug}
hbreak *{checkpoint:#x}
continue
if $pc != {checkpoint:#x}
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
                        not inherited_controller or firmware.exists()
                    ):
                        break
                    if process.poll() is not None:
                        raise RuntimeError("QEMU exited before opening its sockets")
                    time.sleep(0.05)
                else:
                    raise RuntimeError("QEMU socket startup timed out")
                if inherited_controller:
                    state = seed_firmware_ufs(firmware)
                    (folder / "firmware-state.json").write_text(json.dumps(state, indent=2) + "\n")
                receipt = subprocess.run(["gdb-multiarch", "-q", "-nx", "-batch", "-x", str(gdb)],
                                         text=True, capture_output=True, timeout=seconds)
                (run / "gdb.log").write_text(receipt.stdout + receipt.stderr)
                receipt.check_returncode()
                marker = re.search(rf"PROBE PC={checkpoint:#x} RING size=(\d+) next=(\d+)", receipt.stdout)
                assert marker, receipt.stdout
                size, index = map(int, marker.groups())
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
    inherited_controller = name == "inherited_controller"
    entry_id = ids[name]
    bl31_id = 0 if same_boot is None else entry_id if same_boot else ids["matched"]
    folder = output / name
    folder.mkdir()
    tree, end = adt.parse(tree_raw)
    assert end == len(tree_raw)
    chosen = qemu_ufs.child(tree, "chosen")
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
                                               checkpoint, inherited_controller=inherited_controller)
    (folder / "run/ufs-input.json").write_text(json.dumps(metadata, indent=2) + "\n")
    seen = set(re.findall(r"UFS XNU=([0-9a-f]{16}) BL31=([0-9a-f]{16}) V=(\d+)", screen, re.I))
    assert seen == (set() if verdict is None else {(f"{entry_id:016x}", f"{bl31_id:016x}", str(verdict))}), (name, seen)
    hashes = set(re.findall(START + r"([0-9a-f]{64})(?![0-9a-f])", log, re.I))
    assert metadata["readonly"] and metadata["no_ramdisk"] and metadata["sha256"] == disk_hash
    assert metadata["probe"] == {"lun": qemu_ufs.PROBE_LUN, "lba": qemu_ufs.PROBE_LBA,
                                 "bytes": qemu_ufs.PROBE_BYTES}
    traffic = (folder / "ufs.trace").read_text()
    inherited_result = {}
    if inherited_controller:
        state = json.loads((folder / "firmware-state.json").read_text())
        setup_trace = state.pop("setup_trace")
        events = traffic.splitlines()
        assert events[:len(setup_trace)] == setup_trace, events
        guest_events = events[len(setup_trace):]
        (folder / "guest-ufs.trace").write_text("\n".join(guest_events) + "\n")
        # The admitted synthetic lease reaches dufs_start. A single HCE=1
        # read proves the guard was exercised after PCI setup.
        assert guest_events == ["ufs_mmio_read addr 0x34 data 0x1 size 4"], guest_events
        assert result["stop_marker"] == FAILED and f"{FAILED} status=-5" in log, log
        assert not hashes and not any(block)
        traffic = "\n".join(guest_events)
        inherited_result = dict(firmware_state=state, controller_mmio_reads=1,
                                controller_mmio_writes=0, scsi_commands=0, provider_status=-5)
    commands = re.findall(r"^ufs_exec_scsi_cmd slot \d+, lun (0x[0-9a-f]+), opcode (0x[0-9a-f]+)$",
                          traffic, re.M)
    reads = re.findall(r"^scsi_req_parsed_lba target \d+ lun (\d+) tag \d+ command 136 lba (\d+)$",
                       traffic, re.M)
    transfers = [int(n) for n in re.findall(
        r"^scsi_req_parsed target \d+ lun 2 tag \d+ command 136 dir 1 length (\d+)$", traffic, re.M)]
    if verdict == 1 and not inherited_controller:
        assert result["stop_marker"] == DONE and hashes == {expected_hash}, (name, result, hashes)
        assert hashlib.sha256(block).hexdigest() == expected_hash
        assert commands.count(("0x2", "0x88")) == 1 and reads == [("2", "276480")], (name, commands, reads)
        assert transfers == [qemu_ufs.PROBE_BYTES], (name, transfers)
        assert all(lun == "0x2" and opcode in ("0x9e", "0x88") for lun, opcode in commands)
    elif not inherited_controller:
        assert result["stop_marker"] == BLOCKED and not hashes and not traffic.strip(), (name, result, hashes)
        assert not any(block)
    return dict(entry_boot_id=hex(entry_id), bl31_boot_id=hex(bl31_id), verdict=verdict,
                stop_marker=result["stop_marker"], sha256=next(iter(hashes), None),
                controller_trace_events=len(traffic.splitlines()), read16=len(reads),
                bytes_read=sum(transfers),
                elapsed_seconds=result["elapsed_host_seconds"], **inherited_result)


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
