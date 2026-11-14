#!/usr/bin/env python3
"""Verify the passive MT6897 UFS observer on the host and on ARM64 QEMU.

The MT6897 register-array fixture is not MT6897 hardware emulation. The separate
PCI test reads QEMU's actual UFS controller using its own runtime register map.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import re
import subprocess

import mt6897_ufs_model

REPO = Path(__file__).resolve().parent.parent
DRIVERS = REPO / "duchamp/drivers"
SOURCES = [DRIVERS / name for name in ("ufs_register_snapshot.c", "test_ufs_register_snapshot.c")]
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
    return hashlib.sha256(path.read_bytes()).hexdigest()


def command(args, log):
    result = subprocess.run([str(arg) for arg in args], stdin=subprocess.DEVNULL,
                            capture_output=True, text=True, timeout=40)
    log.write_text(result.stdout + result.stderr)
    if result.returncode:
        raise RuntimeError(f"Command failed ({result.returncode}); see {log}")
    return result.stdout


def pinned_layout(dtb, sources):
    profile, _ = mt6897_ufs_model.load_profile(dtb, sources)
    header = (DRIVERS / "ufs_register_snapshot.h").read_text()

    def constant(name):
        return int(re.search(rf"\b{name}\s*=\s*(0x[\da-f]+|\d+)\b", header)[1], 0)

    assert constant("DUFS_MTK_HCI_BASE") == int(profile["hci"]["physical_address"], 16)
    assert constant("DUFS_MTK_HCI_BYTES") == int(profile["hci"]["bytes"], 16)
    assert constant("DUFS_MCQ_STRIDE") == profile["mcq_stride"]
    assert constant("DUFS_MCQ_MAX_QUEUES") == len(profile["mcq_gic_intids"]) == 8
    for i, expected in enumerate(profile["mcq_register_offsets"]):
        base = constant("DUFS_MTK_MCQ_RUNTIME") + i * constant("DUFS_MCQ_STRIDE")
        assert expected == dict(SQD=base, SQIS=base + constant("DUFS_MCQ_SQ_IS"),
                               CQD=base + constant("DUFS_MCQ_CQ_HEAD"),
                               CQIS=base + constant("DUFS_MCQ_CQ_IS"))
    xiaomi = (sources / "ufs-mediatek.c").read_text()
    stride = re.search(r"(?m)^#define MCQ_QCFG_SIZE\s+(0x[\da-fA-F]+)", xiaomi)
    assert constant("DUFS_MCQ_CONFIG_STRIDE") == int(stride[1], 16)
    assert '#define MCQ_QUEUE_OFFSET(c) ((((c) >> 16) & 0xFF) * 0x200)' in xiaomi
    return profile


def build_host(args, output):
    binary = output / "snapshot.native"
    command([args.clang, "-std=c11", "-O1", "-g", "-Wall", "-Wextra", "-Werror",
             "-fsanitize=address,undefined", "-fno-omit-frame-pointer", *SOURCES, "-o", binary],
            output / "native-build.log")
    return command([binary], output / "native.log")


def build_arm(args, output):
    linker, elf = output / "snapshot.ld", output / "snapshot.elf"
    linker.write_text(LINKER)
    command([args.clang, "--target=aarch64-none-elf", "-std=c11", "-O2", "-ffreestanding",
             "-fno-builtin", "-mgeneral-regs-only", "-mstrict-align", "-Wall", "-Wextra", "-Werror",
             "-DMT6897_MODEL_FREESTANDING", "-DDUCHAMP_SNAPSHOT_QEMU_DEVICE",
             "-nostdlib", "-fuse-ld=lld", "-Wl,-T," + str(linker),
             DRIVERS / "test_mt6897_model_start.S", DRIVERS / "test_mt6897_model_runtime.c",
             *SOURCES, "-o", elf], output / "arm-build.log")
    events = output / "trace-events"
    events.write_text("ufs_mmio_read\nufs_mmio_write\nufs_exec_scsi_cmd\n"
                      "ufs_mcq_create_sq\nufs_mcq_create_cq\nufs_mcq_complete_req\n"
                      "ufs_err_dma_read_req_upiu\nufs_err_dma_write_cq\n")
    return command([args.qemu, "-M", "virt,gic-version=3,highmem-ecam=off", "-cpu", "cortex-a76",
                    "-m", "64M", "-smp", "1", "-nodefaults", "-display", "none",
                    "-monitor", "none", "-serial", "stdio", "-nic", "none",
                    "-semihosting-config", "enable=on,target=native", "-kernel", elf,
                    "-device", "ufs,id=ufs0,addr=04.0,mcq=on,mcq-maxq=8",
                    "-trace", f"events={events},file={output / 'ufs.trace'}"], output / "qemu.log")


def build_apple(args, output):
    obj = output / "snapshot.apple-arm64.o"
    command([args.clang, "--target=arm64-apple-macos14.0", "-std=c11", "-O2", "-ffreestanding",
             "-fno-builtin", "-mgeneral-regs-only", "-Wall", "-Wextra", "-Werror",
             "-c", SOURCES[0], "-o", obj], output / "apple-build.log")
    return digest(obj)


def verify_trace(output, qemu_log):
    lines = (output / "ufs.trace").read_text().splitlines()
    reg = re.compile(r"ufs_mmio_(read|write) addr (0x[\da-f]+) data (0x[\da-f]+) size (\d+)")
    entries = [match.groups() for line in lines if (match := reg.fullmatch(line))]
    writes = [(i, int(addr, 16), int(value, 16), int(size))
              for i, (kind, addr, value, size) in enumerate(entries) if kind == "write"]
    # These eight writes ONLY construct the inherited firmware fixture between
    # the cold observation and the inherited observation. Neither capture writes.
    expected = [(0x34, 1), (0x300, 1), (0x424, 0x43001000), (0x428, 0),
                (0x420, 0x8000001f), (0x404, 0x43000000), (0x408, 0), (0x400, 0x8000001f)]
    assert [(addr, value) for _, addr, value, _ in writes] == expected
    assert all(size == 4 for _, _, _, size in writes)
    assert [index for index, _, _, _ in writes] == list(range(316, 324))
    assert len(entries) == 640 and sum(kind == "read" for kind, *_ in entries) == 632
    assert "ufs_exec_scsi_cmd" not in "\n".join(lines)
    assert "ufs_mcq_complete_req" not in "\n".join(lines)
    assert "ufs_err_dma_" not in "\n".join(lines)
    assert "UFS DEVICE cold blockers=0 reads=316" in qemu_log
    assert "UFS DEVICE inherited blockers=41 reads=316" in qemu_log
    assert "UFS DEVICE different_boot denied=1 reads=0" in qemu_log
    for name, start in (("cold", 0), ("inherited", 324)):
        for sample, offset in (("first", 0), ("last", 158)):
            values = entries[start + offset:start + offset + 158]
            assert len(values) == 158 and all(kind == "read" for kind, *_ in values)
            record = dict(boot_id="0x5678", profile="QEMU PCI UFS", base="0x10000000",
                          observation_only=True, ownership_granted=False,
                          dma_granted=False, cache_granted=False,
                          registers={addr: value for _, addr, value, _ in values})
            (output / f"{name}-{sample}.json").write_text(json.dumps(record, indent=2) + "\n")
    return dict(mmio_reads=632, fixture_only_writes=8, observer_writes=0,
                scsi_commands=0, completions=0, dma_faults=0, inherited_blockers=41,
                different_boot_reads=0, pci_bus_mastering=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--dtb", type=Path, required=True)
    parser.add_argument("--xiaomi-sources", type=Path, required=True)
    parser.add_argument("--clang", default="clang")
    parser.add_argument("--qemu", default="qemu-system-aarch64")
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    profile = pinned_layout(args.dtb, args.xiaomi_sources)
    with ThreadPoolExecutor(max_workers=3) as pool:
        host_job = pool.submit(build_host, args, output)
        arm_job = pool.submit(build_arm, args, output)
        apple_job = pool.submit(build_apple, args, output)
        host, arm, apple = host_job.result(), arm_job.result(), apple_job.result()
    host_rows = re.findall(r"(?m)^UFS SNAPSHOT case=.*$", host)
    assert len(host_rows) == 30 and host_rows == re.findall(r"(?m)^UFS SNAPSHOT case=.*$", arm)
    for text in (host, arm):
        assert "UFS SNAPSHOT failures=316 output_unchanged=1" in text
        assert "UFS SNAPSHOT revocations=316 no_later_read=1" in text
        assert "UFS SNAPSHOT PASS cases=30" in text
    assert arm.endswith("MT6897 ARM64 MODEL PASS\n")
    trace = verify_trace(output, arm)
    files = SOURCES + [DRIVERS / "ufs_register_snapshot.h", Path(__file__).resolve()]
    report = dict(passed=True, scope="Passive observer, register-array MT6897 fixtures and actual QEMU PCI UFS. "
                  "Standalone ARM64 guest; not XNU execution or MT6897 hardware emulation.",
                  profile=profile, model_cases=30, read_error_positions=316, revocation_positions=316,
                  sanitizers="ASan and UBSan", arm64_qemu=True,
                  apple_arm64_object_sha256=apple, xnu_full_build=False,
                  qemu=subprocess.check_output([args.qemu, "--version"], text=True).splitlines()[0],
                  trace=trace, source_sha256={str(p.relative_to(REPO)): digest(p) for p in files},
                  authority="Read permission is synthetic. Samples never confer ownership or DMA/cache grants.",
                  phone_access=False, physical_ufs_read=False, flash=False, partition_write=False)
    (output / "verification.json").write_text(json.dumps(report, indent=2) + "\n")
    print("UFS register snapshot PASS: 30 cases, 316 read errors and 316 revocations, "
          "ASan/UBSan and ARM64 QEMU; zero observer writes/SCSI")


if __name__ == "__main__":
    main()
