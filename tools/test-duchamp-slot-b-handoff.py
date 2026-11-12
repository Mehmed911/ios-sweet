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
# Leave the first MiB of RAM for the FDT that QEMU installs automatically.
STUB_PA, IMAGE_PA, FDT_PA, MAILBOX_PA = 0x40100000, 0x40200000, 0x48000000, 0x49000000
RECORD = struct.Struct("<IIQ8I2Q")
CASES = ("matched", "different_boot", "missing_bl31", "missing_queues", "busy_queue",
         "missing_dma", "missing_cache")
BOOT_ARGS = ("debug=0xc serial=3 cpus=1 keepsyms=1 -enable_kprintf_spam -noprogress "
             "rd=qufs0 rootrw=0 sweet-qemu-ufs=1 sweet_console_fb=1 sweet-qemu-ufs-probe=1 "
             "sweet-qemu-boot-id=0x0000000000000000 sweet-qemu-ufs-handoff=1")


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2) + "\n")


def build_image(args, output):
    tree_raw = args.adt.read_bytes()
    tree, end = adt.parse(tree_raw)
    assert end == len(tree_raw)
    qemu_ufs.validate_tree(tree)
    chosen = qemu_ufs.child(tree, "chosen")
    assert chosen.prop("qemu-bl31-ufs") is None
    chosen.props.append(("qemu-bl31-ufs", 0, bytes(RECORD.size)))
    tree_path = output / "boot.adt"
    tree_path.write_bytes(adt.serialize(tree))
    payload, _ = mkpayload.build(args.kernel, tree_path, BOOT_ARGS)
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


def check_case(name, output, ids, payload, loaders, disk, qemu, seconds, symbols, checkpoint):
    same_boot, proof, busy, verdict = PROBE["CASES"][name]
    folder = output / name
    folder.mkdir()
    entry_id = ids[name]
    record_id = 0 if same_boot is None else entry_id if same_boot else ids["matched"]
    record = (RECORD.pack(1, proof, record_id, 1, 0, busy, 0, 0, 0, 0, 0, 5, 6)
              if record_id else bytes(RECORD.size))
    mailbox = folder / "mailbox.bin"
    mailbox.write_bytes(struct.pack("<8sQ", b"QEMUBL31", entry_id) + record)
    entry_loaders = [*loaders, "-device", f"loader,file={mailbox},addr={MAILBOX_PA:#x},force-raw=on"]
    disk_path, disk_hash, expected_hash = disk
    options, media = qemu_ufs.runner_options(payload, disk_path, "cortex-a76", "duchamp")
    assert media["readonly"] and media["no_ramdisk"] and media["sha256"] == disk_hash
    log, screen, block, result = PROBE["boot_to_probe"](
        payload, folder, options, qemu, seconds, symbols, checkpoint,
        inherited=False, pending=False, compare_record=None, entry_loaders=entry_loaders)

    seen = set(re.findall(r"UFS XNU=([0-9a-f]{16}) BL31=([0-9a-f]{16}) V=(\d+)", screen, re.I))
    assert seen == {(f"{entry_id:016x}", f"{record_id:016x}", str(verdict))}, (name, seen)
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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("kernel", "ci-receipt", "adt", "fdt", "slot-b", "reference", "backup", "output"):
        parser.add_argument("--" + name, type=lambda value: Path(value).resolve(), required=True)
    parser.add_argument("--seconds", type=int, default=120)
    parser.add_argument("--jobs", type=int, choices=(1, 2, 3), default=3)
    args = parser.parse_args()
    qemu = shutil.which("qemu-system-aarch64")
    if qemu is None:
        parser.error("qemu-system-aarch64 is required")
    build = json.loads(args.ci_receipt.read_text(encoding="utf-8-sig"))
    sha256 = PROBE["sha256"]
    assert build["conclusion"] == "success" and sha256(args.kernel) == build["sha256"]
    original_hash = sha256(args.slot_b)
    block, reference = PROBE["load_reference"](args.reference, args.backup)
    symbols = PROBE["symbols"](args.kernel)
    assert {"_duchamp_qemu_ufs_handoff_enter", "_duchamp_qemu_ufs_handoff_probe_lease"} <= symbols.keys()
    checkpoint = PROBE["probe_checkpoint"](args.kernel)
    args.output.mkdir(parents=True)
    payload, loaders, image, unpacked = build_image(args, args.output)
    image_hash = sha256(image)
    ids = {name: secrets.randbits(62) | (1 << 62) for name in CASES}
    assert len(set(ids.values())) == len(ids)
    disk = PROBE["fixture"](args.output / "android-reference.raw", block)
    try:
        with ThreadPoolExecutor(max_workers=args.jobs) as workers:
            futures = {name: workers.submit(check_case, name, args.output, ids, payload, loaders,
                                            disk, qemu, args.seconds, symbols, checkpoint)
                       for name in CASES}
            results = {}
            for name, future in futures.items():
                results[name] = future.result()
                print(name, json.dumps(results[name]), flush=True)
        assert sha256(disk[0]) == disk[1]
    finally:
        disk[0].unlink()
    assert sha256(args.slot_b) == original_hash and sha256(image) == image_hash
    write_json(args.output / "verification.json", dict(
        passed=True, qemu_only=True, synthetic_bl31=True, actual_xnu=True, phone_access=False,
        original_slot_b_sha256=original_hash, image=image.name, image_size=image.stat().st_size,
        image_sha256=image_hash, booted_image_sha256=sha256(unpacked), build=build,
        android_reference_sha256=reference["block_sha256"], cases=results))


if __name__ == "__main__":
    main()
