#!/usr/bin/env python3
"""Exercise the real XNU read-only observer on an MT6897-shaped QEMU RAM bank.

No physical grant, phone action, kernel patch/replay or storage write. ivshmem
only supplies stable bytes; it does not implement MT6897 UFS/firmware behavior.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from pathlib import Path
import re
import runpy
import secrets
import shutil
import struct
import subprocess
import sys

import adt
import mt6897_ufs_model
from duchamp_ufs_xnu_replay import digest, symbols

TOOLS = Path(__file__).resolve().parent
SLOT = runpy.run_path(str(TOOLS / "test-duchamp-slot-b-handoff.py"))
ROOT = SLOT["ROOT"]
CASES = {"cold": 1, "disabled": 2, "different_boot": 3, "missing_power": 4,
         "missing_clocks": 5, "revoke_before_map": 6, "revoke_mid_read": 7,
         "revoke_before_publish": 8, "inherited_pending": 9, "default_off": 0,
         "wrong_device_profile": 1}


def register_bank(profile, pending):
    assert int(profile["hci"]["physical_address"], 16) == 0x112b0000
    assert int(profile["hci"]["bytes"], 16) == 0x3000
    assert profile["mcq_stride"] == 0x30
    assert profile["mcq_register_offsets"][0]["SQD"] == 0x2800
    raw = bytearray(0x4000)  # PCI BAR size must be a power of two.
    def put(offset, value):
        struct.pack_into("<I", raw, offset, value)
    put(0, 0x55c7051f); put(4, 0x20007); put(8, 0x400)
    if pending:
        put(0x34, 1); put(0x300, 1)
        for i in range(8):
            c = 0x400 + i * 0x40
            put(c, 0x8000001f); put(c + 4, 0x60002000 + i * 0x1000)
            put(c + 0x20, 0x8000001f); put(c + 0x24, 0x60003000 + i * 0x1000)
        put(profile["mcq_register_offsets"][7]["SQD"] + 4, 32)
    return raw


def check_case(args, name, folder, image, profile, qemu):
    scenario = CASES[name]
    loaders, container, payload = image
    bank = folder / "register-bank.bin"
    expected_bank = register_bank(profile, scenario == 9)
    if not args.verify_existing:
        bank.write_bytes(expected_bank)
    assert bank.read_bytes() == expected_bank
    bank_sha = digest(expected_bank)
    wrapper = folder / "qemu-with-bank"
    wrapper_text = f"""#!{sys.executable}
import os,sys
qemu={qemu!r}
args=sys.argv[1:]
if '-M' in args:
    args += ['-object', 'memory-backend-file,id=observer_bank,size=16K,share=on,mem-path={bank}',
             '-device', 'ivshmem-plain,memdev=observer_bank,addr=05.0']
os.execv(qemu,[qemu,*args])
"""
    if args.verify_existing:
        assert wrapper.read_text() == wrapper_text
        mailbox = (folder / "mailbox.bin").read_bytes()
        assert mailbox[:8] == b"QEMUBL31"
        boot, = struct.unpack_from("<Q", mailbox, 8)
        record, = struct.unpack_from("<Q", mailbox, 24)
        version, proof = struct.unpack_from("<II", mailbox, 16)
        assert version == 1 and proof == 0x3f and boot == record and boot
        assert mailbox == struct.pack("<8sQ", b"QEMUBL31", boot) + SLOT["RECORD"].pack(
            1, 0x3f, boot, 1, 0, 0, 0, 0, 0, 0, 0, 5, 6)
        trace = (folder / "ufs.trace").read_text()
        result = json.loads((folder / "run/result.json").read_text())
        metadata = json.loads((folder / "run/ufs-input.json").read_text())
        screen = "\n".join(p.read_text() for p in [*sorted((folder / "run/frames").glob("*.txt")),
                                                   folder / "run/fb.txt"])
    else:
        wrapper.write_text(wrapper_text)
        wrapper.chmod(0o755)
        boot = secrets.randbits(62) | 1 << 62
        entry, boot, record, _ = SLOT["load_mailbox"]("matched", folder, {"matched": boot}, loaders)
        screen, trace, result, metadata = ROOT["run_guest"](
            folder, payload, args.kernel, args.fixture / "root.gpt.raw", str(wrapper), args.seconds,
            entry_loaders=entry, extra_events=("ufs_mcq_complete_req",), capture_kernel_log=True)
    log = (folder / "run/kernel-log.txt").read_text()
    # The old framebuffer-only early mark may scroll away before the first
    # frame. Positive root preparation logs it again; early denials do not.
    # Their observer marker uses the validated handoff getter, which returns
    # nonzero only after the kernel accepted matching entry/record IDs.
    if "UFS XNU=" in screen + log:
        SLOT["check_ids"](name, screen + log, boot, record, 1)
    assert metadata["readonly"] and metadata["no_ramdisk"], name
    assert digest(bank.read_bytes()) == bank_sha, (name, "register bank was modified")
    marker = re.findall(r"SWEET OBSERVER case=(\d+) status=(-?\d+) maps=(\d+) reads=(\d+) "
                        r"checks=(\d+) unchanged=(\d+) flags=([0-9a-f]+) boot=([0-9a-f]{16}) pass=(\d+)", log)
    observation = None
    if scenario and name != "wrong_device_profile":
        assert len(marker) == 1, (name, marker, log[-4000:])
        case, status, maps, reads, checks, unchanged = map(int, marker[0][:6])
        flags, seen_boot, passed = int(marker[0][6], 16), int(marker[0][7], 16), int(marker[0][8])
        assert case == scenario and seen_boot == boot and passed == 1, (name, marker)
        expected_status = 0 if scenario in (1, 9) else -2 if scenario == 2 else -4 if scenario < 6 else -8
        expected_reads = 316 if scenario in (1, 8, 9) else 98 if scenario == 7 else 0
        expected_maps = int(scenario in (1, 7, 8, 9))
        assert (status, reads, maps, unchanged, flags) == (
            expected_status, expected_reads, expected_maps, int(bool(expected_status)), 0x39 if scenario == 9 else 0)
        protection = re.findall(r"SWEET OBSERVER RO read=([0-9a-f]{16}) write=([0-9a-f]{16}) pass=(\d+)", log)
        if maps:
            assert len(protection) == 1 and protection[0][2] == "1", (name, protection)
            read_par, write_par = (int(v, 16) for v in protection[0][:2])
            assert not read_par & 1 and write_par & 1
            assert read_par & 0x0000fffffffff000 == 0x112b0000
        else:
            assert not protection
        if not status:
            queues = re.findall(r"SWEET OBSERVER q=(\d+) sq=([0-9a-f]+)/([0-9a-f]+) cq=([0-9a-f]+)/([0-9a-f]+)", log)
            assert len(queues) == 8
            assert [[int(v, 16) for v in row[1:]] for row in queues] == [
                [0, 32 if scenario == 9 and i == 7 else 0, 0, 0] for i in range(8)]
        observation = dict(status=status, maps=maps, reads=reads, authority_checks=checks,
                           output_unchanged=bool(unchanged), blockers=hex(flags),
                           read_only_translation_verified=bool(protection))
    else:
        assert not marker and "SWEET OBSERVER RO" not in log
    if scenario in (0, 1) and name != "wrong_device_profile":
        assert result["stop_marker"] == ROOT["HEARTBEAT"], (name, result)
        assert "DUCHAMP UFS PID1 READ PASS" in screen + log
        assert "DUCHAMP UFS WRITE OPEN REFUSED EROFS" in screen + log
        assert re.search(r"ufs_exec_scsi_cmd .*opcode 0x88", trace)
        assert set(re.findall(r"ufs_exec_scsi_cmd .*opcode (0x[0-9a-f]+)", trace)) <= {"0x88", "0x9e"}
    else:
        assert not trace.strip(), (name, trace[:600])
        error = 6 if name == "wrong_device_profile" else 1
        assert f"DUCHAMP QEMU backend selftest failed: {error}" in screen + log
        assert ROOT["HEARTBEAT"] not in screen + log
    return dict(passed=True, scenario=scenario, boot_id=hex(boot), observer=observation,
                virtual_ufs_events=len(trace.splitlines()), register_bank_sha256=bank_sha,
                register_bank_unchanged=True, stop_marker=result["stop_marker"],
                elapsed_host_seconds=result["elapsed_host_seconds"],
                local_container_sha256=digest(container.read_bytes()))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for option in ("kernel", "slot-b", "fdt", "fixture", "mt6897-sources", "output"):
        ap.add_argument("--" + option, type=lambda x: Path(x).resolve(), required=True)
    ap.add_argument("--full-build-sha256", required=True)
    ap.add_argument("--ci-run", type=int, required=True)
    ap.add_argument("--ci-head", required=True)
    ap.add_argument("--case", choices=CASES, action="append")
    ap.add_argument("--jobs", type=int, choices=(1, 2, 3), default=2)
    ap.add_argument("--seconds", type=int, default=100)
    ap.add_argument("--verify-existing", action="store_true",
                    help="recheck saved guest executions without writing inputs or restarting QEMU")
    args = ap.parse_args()
    if not args.verify_existing:
        args.output.mkdir(parents=True, exist_ok=False)
    kernel_sha = digest(args.kernel.read_bytes())
    assert kernel_sha == args.full_build_sha256
    artifact = args.kernel.parent
    assert (artifact / "SOURCE-COMMIT.txt").read_text().strip() == args.ci_head
    sums = dict((name.removeprefix("*"), checksum) for checksum, name in
                (line.split(None, 1) for line in (artifact / "SHA256SUMS").read_text().splitlines()))
    assert sums[args.kernel.name] == kernel_sha
    assert {"_duchamp_qemu_ufs_observer_test", "_mt6897_ufs_xnu_observer_bind",
            "_mt6897_ufs_observer_capture", "_ml_io_map_with_prot"} <= symbols(args.kernel).keys()
    fixture_manifest = json.loads((args.fixture / "fixture.json").read_text())
    for n in ("root.gpt.raw", "qemu-ufs.adt"):
        assert digest((args.fixture / n).read_bytes()) == fixture_manifest["sha256"][n]
    slot_sha = digest(args.slot_b.read_bytes())
    profile, _ = mt6897_ufs_model.load_profile(args.fdt, args.mt6897_sources)
    tree, end = adt.parse((args.fixture / "qemu-ufs.adt").read_bytes())
    assert end == (args.fixture / "qemu-ufs.adt").stat().st_size
    assert all(n.name != "duchamp-qemu-observer" for n in tree.children)
    node = adt.Node()
    node.props = [("name", 0, b"duchamp-qemu-observer\0"),
                  ("compatible", 0, b"qemu,mt6897-register-bank-v1\0")]
    tree.children.append(node)
    base_tree = adt.serialize(tree)
    cases = args.case or list(CASES)
    assert len(cases) == len(set(cases))
    images = {}
    for name in cases:
        folder = args.output / ("image-" + name)
        if not args.verify_existing:
            folder.mkdir()
        tree, _ = adt.parse(base_tree)
        if name == "wrong_device_profile":
            tree.children[-1].props[-1] = ("compatible", 0, b"qemu,wrong-device\0")
        tree_path = folder / "observer.adt"
        if args.verify_existing:
            assert tree_path.read_bytes() == adt.serialize(tree)
        else:
            tree_path.write_bytes(adt.serialize(tree))
        flags = " sweet-qemu-ufs-mcq=1 sweet-qemu-ufs-snapshot=1"
        if CASES[name]:
            flags += f" sweet-qemu-ufs-observer-test={CASES[name]}"
        if args.verify_existing:
            loaders, image = None, folder / "slot-b-bl31-qemu-only.img"
            expected_payload, _ = SLOT["mkpayload"].build(
                args.kernel, folder / "boot.adt", SLOT["BOOT_ARGS"] + flags)
            assert (folder / "payload.bin").read_bytes() == expected_payload
        else:
            _, loaders, image, _ = SLOT["build_image"](args, folder, tree_path, gpt=True, extra_boot_args=flags)
        images[name] = (loaders, image, folder / "payload.bin")
    qemu = shutil.which("qemu-system-aarch64")
    assert qemu
    results = {}
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        jobs = {}
        for name in cases:
            folder = args.output / name
            if not args.verify_existing:
                folder.mkdir()
            jobs[pool.submit(check_case, args, name, folder, images[name], profile, qemu)] = name
        for future in as_completed(jobs):
            name = jobs[future]
            results[name] = future.result()
            SLOT["write_json"](args.output / name / "verification.json", results[name])
            print(name, json.dumps(results[name]), flush=True)
    assert digest(args.kernel.read_bytes()) == kernel_sha
    assert digest(args.slot_b.read_bytes()) == slot_sha
    assert digest((args.fixture / "root.gpt.raw").read_bytes()) == fixture_manifest["sha256"]["root.gpt.raw"]
    report = dict(passed=True, full_matrix=set(cases) == set(CASES), cases=results,
                  rechecked_saved_executions=args.verify_existing,
                  actual_xnu_execution=True, full_kernel_rebuild=True, replay_hooks_applied=False,
                  ci_run=args.ci_run, ci_head=args.ci_head, kernel_sha256=kernel_sha,
                  source_inputs_sha256=digest((artifact / "SOURCE-INPUTS.txt").read_bytes()),
                  model_profile=profile, simulated_authority=True, physical_capture_allowed=False,
                  phone_access=False, partition_write=False, readonly_disk_unchanged=True)
    SLOT["write_json"](args.output / "verification.json", report)


if __name__ == "__main__":
    main()
