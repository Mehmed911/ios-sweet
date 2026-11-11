#!/usr/bin/env python3
"""Run the synthetic BL31/XNU handoff policy against a read-only QEMU UFS device."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile

REPO = Path(__file__).resolve().parent.parent
DRIVERS = REPO / "duchamp/drivers"
LUN, LBA, BLOCK_BYTES = 2, 276480, 4096
CASES = [
    ("missing_bl31", 1), ("missing_xnu_entry", 1), ("different_boot_id", 1),
    ("both_records_from_older_boot", 1), ("different_image_id", 5),
    ("before_final_bl31_exit", 5), ("missing_hce_sample", 2), ("hce_enabled", 2),
    ("missing_queue_snapshot", 2), ("legacy_transfer_pending", 2), ("task_pending", 2),
    ("mcq_sample_incomplete", 2), ("mcq_completion_pending", 2), ("mcq_work_outstanding", 2),
    ("missing_dma_grant", 3), ("missing_cache_grant", 4),
    ("missing_dma_owner", 3), ("missing_cache_owner", 4),
    ("missing_controller_grant", 5), ("same_boot_with_complete_evidence", 0),
]
ROW = re.compile(
    r"UFS HANDOFF case=(\d+) refusal=(\d+) dispatch=(\d+) pci=(\d+) "
    r"mmio=(\d+) dma=(\d+) reads=(\d+) bytes=(\d+)"
)
LINKER = """ENTRY(_start)
SECTIONS {
 . = 0x40200000;
 .text : { *(.text.boot) *(.text*) }
 .rodata : { *(.rodata*) }
 .data : { *(.data*) }
 . = ALIGN(4096);
 .bss (NOLOAD) : { _bss_start = .; *(.bss*) *(COMMON) . = ALIGN(16); _bss_end = .; }
 . += 0x40000; _stack_top = .;
}
"""


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def verify_log(stdout):
    lines = stdout.splitlines()
    if len(lines) != len(CASES) + 1 or lines[-1] != "MT6897 ARM64 MODEL PASS":
        raise ValueError(f"Unexpected QEMU output: {stdout}")
    records = {}
    for index, (line, (name, expected)) in enumerate(zip(lines, CASES), 1):
        match = ROW.fullmatch(line)
        if not match:
            raise ValueError(f"Unexpected case output: {line}")
        case, refusal, dispatch, pci, mmio, dma, reads, size = map(int, match.groups())
        if case != index or refusal != expected:
            raise ValueError(f"Unexpected verdict for {name}: {line}")
        if expected and any((dispatch, pci, mmio, dma, reads, size)):
            raise ValueError(f"Denied case performed I/O: {name}: {line}")
        if not expected and not (dispatch == pci == reads == 1 and mmio and dma and size == BLOCK_BYTES):
            raise ValueError(f"Positive control did not read one block: {line}")
        records[name] = dict(refusal=refusal, dispatches=dispatch, pci_entries=pci,
                             mmio_callbacks=mmio, dma_callbacks=dma, reads=reads, bytes=size)
    return records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--clang", default="clang")
    parser.add_argument("--qemu", default="qemu-system-aarch64")
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True)
    with tempfile.TemporaryDirectory(prefix="duchamp-ufs-handoff-") as folder:
        scratch = Path(folder)
        linker, elf, media = (scratch / name for name in ("model.ld", "model.elf", "synthetic.raw"))
        linker.write_text(LINKER)
        sources = ["test_mt6897_model_start.S", "test_mt6897_model_runtime.c",
                   "mt6897_ufs_gate.c", "mt6897_ufs_provider.c", "ufs_readonly.c",
                   "test_mt6897_ufs_handoff_qemu.c"]
        subprocess.run([args.clang, "-target", "aarch64-none-elf", "-std=c11", "-O2",
                        "-ffreestanding", "-fno-builtin", "-mgeneral-regs-only", "-mstrict-align",
                        "-Wall", "-Wextra", "-Werror", "-DMT6897_MODEL_FREESTANDING",
                        "-DDUCHAMP_QEMU_UFS_HANDOFF_TEST", "-nostdlib", "-fuse-ld=lld",
                        "-Wl,-T," + str(linker), *(str(DRIVERS / file) for file in sources),
                        "-o", str(elf)], check=True, timeout=30)
        block = bytes((i * 17 + 3) & 255 for i in range(BLOCK_BYTES))
        with media.open("xb") as stream:
            stream.truncate((LBA + 2) * BLOCK_BYTES)
            stream.seek(LBA * BLOCK_BYTES)
            stream.write(block)
        before = digest(media)
        trace_events = scratch / "trace-events"
        trace_events.write_text("ufs_exec_scsi_cmd\nscsi_req_parsed_lba\n")
        trace_path = output / "qemu-ufs.trace"
        command = [args.qemu, "-M", "virt,gic-version=3,highmem-ecam=off", "-cpu", "cortex-a76",
                   "-m", "64M", "-smp", "1", "-nodefaults", "-display", "none",
                   "-monitor", "none", "-serial", "stdio", "-nic", "none",
                   "-semihosting-config", "enable=on,target=native", "-kernel", str(elf),
                   "-drive", f"file={media},format=raw,if=none,id=lu2,readonly=on",
                   "-device", "ufs,id=ufs0,addr=04.0,mcq=off",
                   "-device", f"ufs-lu,bus=ufs0,drive=lu2,lun={LUN}",
                   "-trace", f"events={trace_events},file={trace_path}"]
        result = subprocess.run(command, text=True, capture_output=True, timeout=25)
        (output / "qemu.log").write_text(result.stdout + result.stderr)
        result.check_returncode()
        records = verify_log(result.stdout)
        trace = trace_path.read_text()
        scsi_commands = [(int(lun, 16), int(opcode, 16)) for lun, opcode in re.findall(
            r"^ufs_exec_scsi_cmd slot \d+, lun (0x[0-9a-f]+), opcode (0x[0-9a-f]+)$", trace, re.M)]
        read_lbas = [(int(lun), int(lba)) for lun, lba in re.findall(
            r"^scsi_req_parsed_lba target \d+ lun (\d+) tag \d+ command 136 lba (\d+)$", trace, re.M)]
        if (scsi_commands.count((LUN, 0x88)) != 1 or read_lbas != [(LUN, LBA)] or
                any(lun != LUN or opcode not in (0x9e, 0x88) for lun, opcode in scsi_commands)):
            raise ValueError(f"Unexpected controller traffic: {trace}")
        if digest(media) != before:
            raise ValueError("Synthetic UFS image changed")
        report = dict(passed=True, scope="Synthetic boot records on ARM64 QEMU virt. No actual BL31, XNU or phone.",
                      qemu=subprocess.check_output([args.qemu, "--version"], text=True).splitlines()[0],
                      elf_sha256=digest(elf), read_only_image_sha256=before, image_unchanged=True,
                      fixture=dict(lun=LUN, lba=LBA, bytes=BLOCK_BYTES,
                                   synthetic_block_sha256=hashlib.sha256(block).hexdigest()),
                      cases=records, denied_cases=len(CASES) - 1, successful_virtual_reads=1,
                      scsi_opcodes=[hex(opcode) for _, opcode in scsi_commands],
                      traced_read=dict(lun=LUN, lba=LBA, opcode="READ(16)"),
                      phone_access=False, physical_ufs_read=False, flash=False, partition_write=False)
        (output / "verification.json").write_text(json.dumps(report, indent=2) + "\n")
    print(f"QEMU UFS handoff PASS: {report['denied_cases']} denied cases, one verified virtual read")


if __name__ == "__main__":
    main()
