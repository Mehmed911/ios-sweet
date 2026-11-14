#!/usr/bin/env python3
"""Boot XNU from a read-only GPT through QEMU MCQ and verify fault isolation."""

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

import mt6897_ufs_model
from duchamp_ufs_xnu_replay import branch, digest, macho_segments, symbols

TOOLS = Path(__file__).resolve().parent
SLOT = runpy.run_path(str(TOOLS / "test-duchamp-slot-b-handoff.py"))
ROOT = SLOT["ROOT"]
SOURCE = TOOLS.parent / "duchamp/xnu/qemu_ufs_mcq.c"
BASE_SHA256 = "57ba8b32dd1b7a5ed7c70ed65d7a4aec107d12b85147f236c439cd309672fda0"
BIND_CALL = 0xfffffe00074df9e4
TEXT = 0xfffffe0007b479a0
STATE = 0xfffffe0007b95000
CONSTANTS = STATE + 128
TEXT_SIZE = 0xfffffe0007b48000 - TEXT
STATE_SIZE = 128
CONSTANTS_SIZE = 256
EVENTS = ("ufs_mcq_create_sq", "ufs_mcq_create_cq", "ufs_mcq_complete_req",
          "ufs_process_db", "ufs_err_dma_read_req_upiu", "ufs_err_dma_read_prdt",
          "ufs_err_dma_read_sq", "ufs_err_dma_write_cq", "ufs_err_dma_write_rsp_upiu")
CASES = {
    "matched": (0, "matched", None),
    "dma_outside_pool": (1, "matched", "DUCHAMP MCQ DMA REJECTED"),
    "missing_sq_sync": (2, "matched", "DUCHAMP MCQ CACHE SYNC REQUIRED"),
    "device_dma_fault": (3, "matched", None),
    "missing_dma_grant": (0, "missing_dma", None),
    "missing_cache_grant": (0, "missing_cache", None),
    "inherited_mcq": (0, "mcq_mode", None),
}


def build_kernel(base, output):
    raw = bytearray(base.read_bytes())
    assert digest(raw) == BASE_SHA256, "unexpected baseline kernel"
    names = symbols(base)
    segments = list(macho_segments(raw))

    def offset(va, size, segment, *, padding=False):
        for name, start, _, pos, length, ranges in segments:
            if name == segment and start <= va and va + size <= start + length:
                if padding:
                    assert not any(lo < va + size and va < hi for lo, hi in ranges if lo != hi)
                    assert not any(va <= address < va + size for address in names.values())
                return pos + va - start
        raise ValueError(f"{va:#x} is outside file-backed {segment}")

    defs = ("dufs_bind", "PE_parse_boot_argn", "sweet_early_mark", "memcpy")
    layout = output / "mcq.ld"
    layout.write_text("\n".join(f"{name} = {names['_' + name]:#x};" for name in defs) + f"""
SECTIONS {{
  .replay {TEXT:#x} : {{ *(.text*) }}
  .state {STATE:#x} (NOLOAD) : {{ *(.bss*) }}
  .constants {CONSTANTS:#x} : {{ *(.rodata*) }}
  /DISCARD/ : {{ *(.comment) *(.eh_frame*) }}
}}
ASSERT(SIZEOF(.state) <= {STATE_SIZE}, "MCQ state exceeds the pinned gap")
ASSERT(SIZEOF(.constants) <= {CONSTANTS_SIZE}, "MCQ constants exceed the pinned gap")
ASSERT(SIZEOF(.replay) <= {TEXT_SIZE}, "MCQ code exceeds the pinned gap")
""")
    elf = output / "mcq.elf"
    subprocess.run(["clang", "--target=aarch64-none-elf", "-Oz", "-ffreestanding", "-fno-builtin",
                    "-fno-stack-protector", "-mgeneral-regs-only", "-fomit-frame-pointer", "-fno-jump-tables",
                    "-fno-unwind-tables", "-fno-asynchronous-unwind-tables", "-Wall", "-Wextra",
                    "-Werror", "-DDUCHAMP_PINNED_QEMU_MCQ_REPLAY", "-nostdlib", "-fuse-ld=lld",
                    "-Wl,-e,dufs_mcq_bind", "-Wl,-T," + str(layout), "-I",
                    str(TOOLS.parent / "duchamp/drivers"), str(SOURCE), "-o", str(elf)], check=True)
    sizes = {}
    for section, address, segment in (("replay", TEXT, "__TEXT_EXEC"),
                                      ("constants", CONSTANTS, "__DATA")):
        path = output / f"mcq.{section}"
        subprocess.run(["llvm-objcopy", "-O", "binary", "--only-section=." + section, elf, path],
                       check=True)
        blob = path.read_bytes()
        pos = offset(address, len(blob), segment, padding=True)
        assert blob and not any(raw[pos:pos + len(blob)])
        raw[pos:pos + len(blob)] = blob
        sizes[section] = len(blob)
    data_pos = offset(STATE, STATE_SIZE, "__DATA", padding=True)
    assert not any(raw[data_pos:data_pos + STATE_SIZE])
    hook = offset(BIND_CALL, 4, "__TEXT_EXEC")
    assert struct.unpack_from("<I", raw, hook)[0] == branch(BIND_CALL, names["_dufs_bind"], True)
    struct.pack_into("<I", raw, hook, branch(BIND_CALL, symbols(elf)["dufs_mcq_bind"], True))
    kernel = output / "kernel.qemu-mcq"
    kernel.write_bytes(raw)
    return kernel, {"baseline_sha256": BASE_SHA256, "replay_sha256": digest(raw),
                    "source_sha256": digest(SOURCE.read_bytes()), "replay_bytes": sizes["replay"],
                    "baseline_ci_run": 43115466836, "full_kernel_rebuild": False}


def check_case(name, folder, profile, records, images, kernel, disk, qemu, seconds, snapshot=False):
    fault, handoff, marker = CASES[name]
    loaders, image, payload = images[fault]
    ids = {handoff: secrets.randbits(62) | 1 << 62}
    entry_loaders, entry_id, record_id, verdict = SLOT["load_mailbox"](
        handoff, folder, ids, loaders, records)
    screen, trace, result, metadata = ROOT["run_guest"](
        folder, payload, kernel, disk, qemu, seconds,
        entry_loaders=entry_loaders, extra_events=EVENTS, capture_kernel_log=snapshot)
    SLOT["check_ids"](name, screen, entry_id, record_id, verdict)
    assert metadata["readonly"] and metadata["no_ramdisk"] and metadata["gpt"] == profile
    assert metadata["mcq"] == {"max_queues": 8, "fault": fault}
    if snapshot and verdict == 1:
        expected = f"DUCHAMP UFS SNAPSHOT boot=0x{entry_id:016x} status=0 reads=316 blockers=0x0"
        kernel_log = (folder / "run/kernel-log.txt").read_text()
        assert expected in kernel_log, (name, "snapshot marker missing from kernel log")
        lines = trace.splitlines()
        assert len(lines) > 316 and all(line.startswith("ufs_mmio_read ") for line in lines[:316])
        first_write = next(i for i, line in enumerate(lines) if line.startswith("ufs_mmio_write "))
        assert first_write >= 316, (name, first_write)
        samples = [lines[:158], lines[158:316]]
        assert samples[0] == samples[1], name
    assert not re.search(r"(?m)^ufs_process_db\b", trace), name
    assert not re.search(r"(?m)^ufs_mmio_write (?:addr )?(0x58|0x60)\b", trace), name
    commands = re.findall(r"(?m)^ufs_exec_scsi_cmd .*opcode (0x[\da-f]+)", trace)
    assert set(commands) <= {"0x9e", "0x88"}, (name, commands)
    completions = len(re.findall(r"(?m)^ufs_mcq_complete_req\b", trace))
    dma_errors = re.findall(r"(?m)^ufs_err_dma_\w+.*$", trace)
    sq_tails = re.findall(r"(?m)^ufs_mmio_write (?:addr )?0x1004\b.*$", trace)
    cq_heads = re.findall(r"(?m)^ufs_mmio_write (?:addr )?0x101c\b.*$", trace)
    assert ("ufs_mcq_create_sq" in trace) == ("ufs_mcq_create_cq" in trace) == (verdict == 1), name
    if name == "matched":
        assert result["stop_marker"] == ROOT["HEARTBEAT"]
        assert "DUCHAMP UFS ROOT DEVICE MATCH" in screen and "DUCHAMP UFS PID1 READ PASS" in screen
        assert "DUCHAMP UFS WRITE OPEN REFUSED EROFS" in screen
        assert completions > 4 and len(sq_tails) == len(cq_heads) == completions
        assert commands.count("0x88") > 4 and not dma_errors
    else:
        assert result["stop_marker"] in (ROOT["DENIED"], "SWEET EARLY PANIC:")
        assert ROOT["HEARTBEAT"] not in screen
        assert not commands and not completions and not cq_heads, name
        if marker:
            assert marker in screen and not sq_tails and not dma_errors, name
            assert "DUCHAMP QUFS root unavailable: 5" in screen
        elif fault == 3:
            assert len(sq_tails) == 1 and len(dma_errors) == 1
            assert "ufs_err_dma_read_req_upiu" in dma_errors[0]
            assert "DUCHAMP QUFS root unavailable: 60" in screen
        else:
            assert not trace.strip(), (name, trace[:600])
    return dict(boot_id=f"0x{entry_id:016x}", handoff_verdict=verdict,
                local_boot_image_sha256=digest(image.read_bytes()),
                stop_marker=result["stop_marker"], elapsed_seconds=result["elapsed_host_seconds"],
                sq_submissions=len(sq_tails), cq_acknowledgements=len(cq_heads),
                mcq_completions=completions, read16=commands.count("0x88"),
                dma_errors=dma_errors, rejection_marker=marker, trace_events=len(trace.splitlines()),
                passive_snapshot=snapshot and verdict == 1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for option in ("kernel", "slot-b", "fdt", "fixture", "mt6897-sources", "output"):
        parser.add_argument("--" + option, type=lambda path: Path(path).resolve(), required=True)
    parser.add_argument("--seconds", type=int, default=90)
    parser.add_argument("--full-build-sha256", help="verify and boot the complete Mach-O without replay hooks")
    parser.add_argument("--ci-run", type=int)
    parser.add_argument("--ci-head")
    parser.add_argument("--jobs", type=int, choices=(1, 2, 3), default=2)
    parser.add_argument("--case", choices=CASES, action="append")
    parser.add_argument("--snapshot", action="store_true", help="run the opt-in passive observer before HCI writes")
    args = parser.parse_args()
    qemu = shutil.which("qemu-system-aarch64")
    if not qemu:
        parser.error("qemu-system-aarch64 is required")
    output = args.output
    output.mkdir(parents=True)
    disk, adt = (args.fixture / name for name in ("root.gpt.raw", "qemu-ufs.adt"))
    manifest = json.loads((args.fixture / "fixture.json").read_text())
    for path in (disk, adt):
        assert digest(path.read_bytes()) == manifest["sha256"][path.name]
    baseline, slot_sha = args.kernel, digest(args.slot_b.read_bytes())
    gpt = manifest["gpt"]
    model, records = mt6897_ufs_model.exercise_model(args.fdt, args.mt6897_sources, disk, gpt)
    SLOT["write_json"](output / "mt6897-model.json", model)
    assert model["mcq_wrap_and_drain"] and model["mcq_test_queue"] == 7
    assert model["profile"]["mcq_stride"] == 0x30
    baseline_sha = digest(baseline.read_bytes())
    if args.full_build_sha256:
        if baseline_sha != args.full_build_sha256:
            parser.error("full-build kernel SHA-256 differs from the artifact receipt")
        required = {"_dufs_mcq_bind", "_duchamp_qemu_ufs_handoff_enter",
                    "_duchamp_qemu_ufs_rootdev"}
        if args.snapshot:
            required |= {"_dufs_snapshot_registers", "_duchamp_qemu_ufs_snapshot_boot_id"}
        missing = required - symbols(baseline).keys()
        if missing:
            parser.error("full-build artifact lacks required XNU UFS symbols: " + ", ".join(sorted(missing)))
        kernel = baseline
        build = dict(kernel_sha256=baseline_sha, ci_run=args.ci_run, ci_head=args.ci_head,
                     source_sha256=digest(SOURCE.read_bytes()), full_kernel_rebuild=True,
                     replay_hooks_applied=False)
    else:
        if args.snapshot:
            parser.error("the snapshot integration requires a complete source-built kernel")
        if args.ci_run is not None or args.ci_head is not None:
            parser.error("CI provenance flags require --full-build-sha256")
        kernel, build = build_kernel(baseline, output)
    args.kernel = kernel
    cases = args.case or list(CASES)
    if len(cases) != len(set(cases)):
        parser.error("select each case only once")
    images = {}
    for fault in sorted({CASES[name][0] for name in cases}):
        folder = output / f"image-{fault}"
        folder.mkdir()
        flags = " sweet-qemu-ufs-mcq=1"
        if args.snapshot:
            flags += " sweet-qemu-ufs-snapshot=1"
        if fault:
            flags += f" sweet-qemu-mcq-fault={fault}"
        _, loaders, image, _ = SLOT["build_image"](args, folder, adt, gpt=True, extra_boot_args=flags)
        images[fault] = (loaders, image, folder / "payload.bin")
    profile = {key: gpt[key] for key in ("sector_bytes", "root_guid")}
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        jobs = {}
        for name in cases:
            folder = output / name
            folder.mkdir()
            future = pool.submit(check_case, name, folder, profile, records, images,
                                 kernel, disk, qemu, args.seconds, args.snapshot)
            jobs[future] = name
        results = {}
        for future in as_completed(jobs):
            name = jobs[future]
            results[name] = future.result()
            SLOT["write_json"](output / name / "verification.json", results[name])
            print(name, json.dumps(results[name]), flush=True)
    assert digest(baseline.read_bytes()) == baseline_sha
    assert digest(args.slot_b.read_bytes()) == slot_sha
    assert digest(disk.read_bytes()) == manifest["sha256"][disk.name]
    report = dict(passed=True, full_matrix=set(cases) == CASES.keys(), build=build,
                  cases=results, qemu=subprocess.check_output([qemu, "--version"], text=True).splitlines()[0],
                  disk_sha256=manifest["sha256"][disk.name], disk_readonly_unchanged=True,
                  synthetic_bl31=True, physical_ufs_authorized=False, phone_access=False)
    SLOT["write_json"](output / "verification.json", report)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
