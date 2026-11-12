#!/usr/bin/env python3
"""Repack a saved Slot B header and exercise the QEMU-only BL31 receiver."""

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import re
import runpy
import secrets
import shutil
import struct
import subprocess
import sys

import adt
import mkpayload
import qemu_ufs

TOOLS = Path(__file__).resolve().parent
SHIM = TOOLS.parent / "duchamp/bootshim"
PROBE = runpy.run_path(str(TOOLS / "test-duchamp-ufs-probe-xnu.py"))
ROOT = PROBE["handoff"]
# Leave the first MiB of RAM for the FDT that QEMU installs automatically.
STUB_PA, IMAGE_PA, FDT_PA, MAILBOX_PA = 0x40100000, 0x40200000, 0x48000000, 0x49000000
RECORD = struct.Struct("<IIQ8I2Q")
CASES = ("matched", "different_boot", "missing_bl31", "missing_queues", "busy_queue",
         "missing_dma", "missing_cache")
BOOT_ARGS = ("debug=0xc serial=3 cpus=1 keepsyms=1 -enable_kprintf_spam -noprogress "
             "rd=qufs0 rootrw=0 sweet-qemu-ufs=1 sweet_console_fb=1 "
             "sweet-qemu-boot-id=0x0000000000000000 sweet-qemu-ufs-handoff=1")


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2) + "\n")


def build_image(args, output, adt_path, *, gpt):
    tree_raw = adt_path.read_bytes()
    tree, end = adt.parse(tree_raw)
    assert end == len(tree_raw)
    assert (qemu_ufs.validate_tree(tree) is not None) == gpt
    chosen = qemu_ufs.child(tree, "chosen")
    assert chosen.prop("qemu-bl31-ufs") is None
    chosen.props.append(("qemu-bl31-ufs", 0, bytes(RECORD.size)))
    tree_path = output / "boot.adt"
    tree_path.write_bytes(adt.serialize(tree))
    cmdline = BOOT_ARGS if gpt else BOOT_ARGS + " sweet-qemu-ufs-probe=1"
    payload, _ = mkpayload.build(args.kernel, tree_path, cmdline)
    payload_path = output / "payload.bin"
    payload_path.write_bytes(payload)

    shim_output = output / "shim"
    flags = dict(PAYLOAD=str(payload_path), SHIM_OUT=str(shim_output), MATERIALIZE="1",
                 READY="1", JUMP="1", QEMU_BL31_RECEIVER="1")
    with (output / "build.log").open("w") as log:
        guard = subprocess.run(["sh", str(SHIM / "build.sh")],
                               env=dict(os.environ, **flags, QEMU_ONLY=""), text=True,
                               capture_output=True)
        assert guard.returncode == 2 and "isolated QEMU-only" in guard.stderr, guard.stderr
        log.write(guard.stderr)
        log.flush()
        subprocess.run(["sh", str(SHIM / "build.sh")], env=dict(os.environ, **flags, QEMU_ONLY="1"),
                       stdout=log, stderr=subprocess.STDOUT, check=True)
        image = output / "slot-b-bl31-qemu-only.img"
        subprocess.run([sys.executable, str(SHIM / "pack_boot.py"), "--stock-boot", str(args.slot_b),
                        "--kernel", str(shim_output / "Image"), "--out", str(image), "--lz4-legacy"],
                       stdout=log, stderr=subprocess.STDOUT, check=True)

    container = image.read_bytes()
    original = args.slot_b.read_bytes()
    size, = struct.unpack_from("<I", container, 8)
    assert original[:8] == container[:8] == b"ANDROID!"
    assert container[12:1584] == original[12:1584]
    assert len(container) == ((4096 + size + 4095) & ~4095) and len(container) < len(original)
    assert not any(container[4096 + size:])
    compressed = container[4096:4096 + size]
    assert compressed.startswith(bytes.fromhex("02214c18"))
    kernel = subprocess.check_output(["lz4", "-d", "-c"], input=compressed)
    assert kernel == (shim_output / "Image").read_bytes()
    assert kernel[56:60] == b"ARM\x64" and IMAGE_PA + len(kernel) <= FDT_PA
    assert FDT_PA + args.fdt.stat().st_size <= MAILBOX_PA
    unpacked = output / "Image-from-slot-b"
    unpacked.write_bytes(kernel)
    stub = output / "entry-stub.bin"
    stub.write_bytes(PROBE["sweet"]["stub"](FDT_PA, IMAGE_PA))
    loaders = []
    for path, address in ((stub, STUB_PA), (unpacked, IMAGE_PA), (args.fdt, FDT_PA)):
        loaders.extend(["-device", f"loader,file={path},addr={address:#x},force-raw=on"])
    loaders.extend(["-device", f"loader,addr={STUB_PA:#x},cpu-num=0"])
    return payload, loaders, image, unpacked


def load_mailbox(name, folder, ids, loaders):
    same_boot, proof, busy, verdict = ROOT["CASES"][name]
    entry_id = ids[name]
    record_id = 0 if same_boot is None else entry_id if same_boot else ids["matched"]
    record = (RECORD.pack(1, proof, record_id, 1, 0, busy, 0, 0, 0, 0, 0, 5, 6)
              if record_id else bytes(RECORD.size))
    mailbox = folder / "mailbox.bin"
    mailbox.write_bytes(struct.pack("<8sQ", b"QEMUBL31", entry_id) + record)
    entry_loaders = [*loaders, "-device", f"loader,file={mailbox},addr={MAILBOX_PA:#x},force-raw=on"]
    return entry_loaders, entry_id, record_id, verdict


def check_ids(name, screen, entry_id, record_id, verdict):
    seen = set(re.findall(r"UFS XNU=([0-9a-f]{16}) BL31=([0-9a-f]{16}) V=(\d+)", screen, re.I))
    assert seen == {(f"{entry_id:016x}", f"{record_id:016x}", str(verdict))}, (name, seen)


def check_case(name, output, ids, payload, loaders, disk, qemu, seconds, symbols, checkpoint):
    folder = output / name
    folder.mkdir()
    entry_loaders, entry_id, record_id, verdict = load_mailbox(name, folder, ids, loaders)
    disk_path, disk_hash, expected_hash = disk
    options, media = qemu_ufs.runner_options(payload, disk_path, "cortex-a76", "duchamp")
    assert media["readonly"] and media["no_ramdisk"] and media["sha256"] == disk_hash
    log, screen, block, result = PROBE["boot_to_probe"](
        payload, folder, options, qemu, seconds, symbols, checkpoint,
        inherited=False, pending=False, compare_record=None, entry_loaders=entry_loaders)

    check_ids(name, screen, entry_id, record_id, verdict)
    traffic = (folder / "ufs.trace").read_text().splitlines()
    match = re.findall(PROBE["START"] + r"([0-9a-f]{64})(?![0-9a-f])", log)
    read_commands = [line for line in traffic if line.startswith("ufs_exec_scsi_cmd ")
                     and line.endswith("opcode 0x88")]
    if verdict == 1:
        assert result["stop_marker"] == PROBE["DONE"] and match == [expected_hash]
        assert hashlib.sha256(block).hexdigest() == expected_hash
        assert len(read_commands) == 1 and ", lun 0x2," in read_commands[0], read_commands
        read_tags = re.findall(r"^scsi_req_parsed_lba target 0 lun 2 tag (\d+) command 136 lba "
                               rf"{qemu_ufs.PROBE_LBA}$", "\n".join(traffic), re.M)
        assert len(read_tags) == 1, read_tags
        assert (f"scsi_req_parsed target 0 lun 2 tag {read_tags[0]} command 136 dir 1 length "
                f"{qemu_ufs.PROBE_BYTES}") in traffic
    else:
        assert result["stop_marker"] == PROBE["BLOCKED"] and not match and not traffic and not any(block)
    return dict(entry_boot_id=hex(entry_id), bl31_boot_id=hex(record_id), verdict=verdict,
                stop_marker=result["stop_marker"], sha256=match[0] if match else None,
                ufs_trace_events=len(traffic), read16=len(read_commands),
                elapsed_seconds=result["elapsed_host_seconds"])


def check_gpt_case(name, output, ids, loaders, disk, args, qemu):
    folder = output / name
    folder.mkdir()
    entry_loaders, entry_id, record_id, verdict = load_mailbox(name, folder, ids, loaders)
    disk_path, disk_hash, gpt = disk
    screen, trace, result, metadata = ROOT["run_guest"](
        folder, output / "payload.bin", args.kernel, disk_path, qemu, args.seconds,
        entry_loaders=entry_loaders)
    check_ids(name, screen, entry_id, record_id, verdict)
    assert metadata["readonly"] and metadata["no_ramdisk"] and metadata["sha256"] == disk_hash
    assert metadata["gpt"] == {key: gpt[key] for key in ("sector_bytes", "root_guid")}
    read_pass = "DUCHAMP UFS PID1 READ PASS" in screen
    write_refused = "DUCHAMP UFS WRITE OPEN REFUSED EROFS" in screen
    read_lbas = [int(lba) for lba in re.findall(
        r"^scsi_req_parsed_lba target \d+ lun 0 tag \d+ command 136 lba (\d+)$", trace, re.M)]
    if verdict == 1:
        assert result["status"] == "no_panic_observed", (name, result)
        assert result["stop_marker"] == ROOT["HEARTBEAT"] and read_pass and write_refused, (name, result)
        assert "DUCHAMP UFS ROOT DEVICE MATCH" in screen and "DUCHAMP UFS HFS FILE BYTES MATCH" in screen
        # QEMU's UFS logical block is 4096 bytes even for a 512-byte GPT fixture.
        first = gpt["root_offset"]
        end = first + gpt["root_bytes"]
        assert 0 in read_lbas and any(first <= 4096 * lba < end for lba in read_lbas), read_lbas
        commands = set(re.findall(r"^ufs_exec_scsi_cmd slot \d+, lun (\S+), opcode (\S+)$", trace, re.M))
        assert commands == {("0x0", "0x9e"), ("0x0", "0x88")}, commands
    else:
        assert result["stop_marker"] == ROOT["DENIED"] and not read_pass and not trace.strip(), (name, result)
    return dict(entry_boot_id=hex(entry_id), bl31_boot_id=hex(record_id), verdict=verdict,
                stop_marker=result["stop_marker"], pid1_read_pass=read_pass, write_refused=write_refused,
                ufs_trace_events=len(trace.splitlines()), read16=len(read_lbas),
                elapsed_seconds=result["elapsed_host_seconds"])


def check_matrix(args, ids, check):
    with ThreadPoolExecutor(max_workers=args.jobs) as workers:
        futures = {name: workers.submit(check, name) for name in CASES}
        results = {}
        for name, future in futures.items():
            results[name] = future.result()
            print(name, json.dumps(results[name]), flush=True)
        return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("kernel", "ci-receipt", "fdt", "slot-b", "output"):
        parser.add_argument("--" + name, type=lambda value: Path(value).resolve(), required=True)
    for name in ("adt", "reference", "backup", "gpt-fixture"):
        parser.add_argument("--" + name, type=lambda value: Path(value).resolve())
    parser.add_argument("--seconds", type=int, default=120)
    parser.add_argument("--jobs", type=int, choices=(1, 2, 3), default=3)
    args = parser.parse_args()
    if args.gpt_fixture and any((args.adt, args.reference, args.backup)):
        parser.error("--gpt-fixture supplies its own ADT and replaces the one-block reference")
    if not args.gpt_fixture and not all((args.adt, args.reference, args.backup)):
        parser.error("the one-block test requires --adt, --reference and --backup")
    qemu = shutil.which("qemu-system-aarch64")
    if qemu is None:
        parser.error("qemu-system-aarch64 is required")
    build = json.loads(args.ci_receipt.read_text(encoding="utf-8-sig"))
    sha256 = PROBE["sha256"]
    assert build["conclusion"] == "success" and sha256(args.kernel) == build["sha256"]
    original_hash = sha256(args.slot_b)
    symbols = PROBE["symbols"](args.kernel)
    assert {"_duchamp_qemu_ufs_handoff_enter", "_duchamp_qemu_ufs_handoff_probe_lease"} <= symbols.keys()
    gpt = args.gpt_fixture is not None
    adt_path = args.gpt_fixture / "qemu-ufs.adt" if gpt else args.adt
    if gpt:
        disk_path = args.gpt_fixture / "root.gpt.raw"
        manifest = json.loads((args.gpt_fixture / "fixture.json").read_text())
        assert manifest["no_ramdisk"] and manifest["readonly_backend"]
        assert manifest["init_source_sha256"] == sha256(TOOLS / "duchamp-ufs-init.S")
        for path in (disk_path, adt_path):
            assert sha256(path) == manifest["sha256"][path.name]
    args.output.mkdir(parents=True)
    payload, loaders, image, unpacked = build_image(args, args.output, adt_path, gpt=gpt)
    image_hash = sha256(image)
    ids = {name: secrets.randbits(62) | (1 << 62) for name in CASES}
    assert len(set(ids.values())) == len(ids)
    if gpt:
        disk = disk_path, manifest["sha256"][disk_path.name], manifest["gpt"]
        results = check_matrix(args, ids, lambda name: check_gpt_case(
            name, args.output, ids, loaders, disk, args, qemu))
        assert sha256(disk_path) == disk[1]
        report = dict(gpt=manifest["gpt"], readonly_disk_sha256=disk[1])
    else:
        checkpoint = PROBE["probe_checkpoint"](args.kernel)
        block, reference = PROBE["load_reference"](args.reference, args.backup)
        disk = PROBE["fixture"](args.output / "android-reference.raw", block)
        try:
            results = check_matrix(args, ids, lambda name: check_case(
                name, args.output, ids, payload, loaders, disk, qemu, args.seconds, symbols, checkpoint))
            assert sha256(disk[0]) == disk[1]
        finally:
            disk[0].unlink()
        report = dict(android_reference_sha256=reference["block_sha256"])
    assert sha256(args.slot_b) == original_hash and sha256(image) == image_hash
    write_json(args.output / "verification.json", dict(
        passed=True, qemu_only=True, synthetic_bl31=True, actual_xnu=True, phone_access=False,
        original_slot_b_sha256=original_hash, image=image.name, image_size=image.stat().st_size,
        image_sha256=image_hash, booted_image_sha256=sha256(unpacked), build=build,
        cases=results, **report))


if __name__ == "__main__":
    main()
