#!/usr/bin/env python3
"""Build and test the callback-only MT6897 UFS topckgen model offline."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess


VENDOR_REPOSITORY = "mt6897-devs/android_kernel_device_modules_6.1"
VENDOR_COMMIT = "a805f95d61dbf0b2959c9262acc626893114321d"
SOURCE_PINS = {
    "drivers/clk/mediatek/clk-mt6897.c":
        "8c5474b19206b410ce19d2e29f221cca5a57401c",
    "drivers/clk/mediatek/clk-mux.c":
        "dc747d04daf417c1b76b4dea6a5f5814db6f9a02",
    "drivers/clk/mediatek/clk-mux.h":
        "6c29d77878fc3b12b9c52871f64e41cc157a880b",
    "include/dt-bindings/clock/mt6897-clk.h":
        "ad626fb71eae5c3e6ef02d08e7c8e723adcc239f",
}
FDT_SHA256 = "9c49589f70044127be8941a9ea5537977f440ccd5ac15cfd24e120c8a1181d29"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(command, commands, output, **kwargs):
    commands.append(command)
    (output / "commands.json").write_text(json.dumps(commands, indent=2) + "\n")
    return subprocess.run(command, check=True, **kwargs)


def verify_manifest(path):
    manifest = json.loads(path.read_text())
    vendor = manifest["vendor"]
    if vendor["repository"] != VENDOR_REPOSITORY or vendor["commit"] != VENDOR_COMMIT:
        raise ValueError("unexpected vendor source revision")
    actual = {entry["path"]: entry["git_blob"] for entry in vendor["files"]}
    for source, blob in SOURCE_PINS.items():
        if actual.get(source) != blob:
            raise ValueError("missing or changed topckgen source pin: " + source)
    return manifest


def verify_hardware_report(path):
    report = json.loads(path.read_text())
    if report.get("fdt_sha256") != FDT_SHA256:
        raise ValueError("unexpected captured-DTB provenance")
    expected = {
        "ufs_sel": 42,
        "ufs_sel_min_src": 118,
        "ufs_sel_max_src": 172,
        "ufs_fde": 41,
        "ufs_fde_min_src": 139,
        "ufs_fde_max_src": 117,
    }
    observed = {}
    for clock in report["nodes"]["ufs"]["clocks"]:
        if clock.get("name") not in expected:
            continue
        if clock.get("provider") != "/syscon@10000000":
            raise ValueError("unexpected topckgen provider")
        if clock.get("provider_reg_cells") != [0, 0x10000000, 0, 0x1000]:
            raise ValueError("unexpected topckgen FDT resource")
        args = clock.get("args", [])
        if len(args) != 1:
            raise ValueError("unexpected topckgen clock specifier")
        observed[clock["name"]] = args[0]
    if observed != expected:
        raise ValueError("saved-DTB UFS topckgen references changed")
    return observed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--hardware-report", type=Path)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    repo = Path(__file__).resolve().parent.parent
    drivers = repo / "duchamp/drivers"
    source = drivers / "mt6897_ufs_topckgen.c"
    header = drivers / "mt6897_ufs_topckgen.h"
    test_source = drivers / "test_mt6897_ufs_topckgen.c"
    manifest_path = drivers / "mt6897-platform-sources.json"
    manifest = verify_manifest(manifest_path)
    text = source.read_text()
    if "volatile" in text or "MTUFS_TOPCKGEN_BASE" in text:
        raise ValueError("implementation contains a direct-address/MMIO path")
    commands = []
    binary = output / "topckgen-tests"
    compile_command = [
        "clang", "-std=c11", "-O1", "-g", "-Wall", "-Wextra", "-Werror",
        "-fsanitize=address,undefined", "-fno-omit-frame-pointer",
        str(source), str(test_source), "-o", str(binary),
    ]
    run(compile_command, commands, output)
    native = run([str(binary)], commands, output, capture_output=True, text=True)
    (output / "sanitizer.log").write_text(native.stdout + native.stderr)
    match = re.fullmatch(
        r"(\d+) MT6897 UFS topckgen callback-model checks passed; "
        r"no MMIO backend\n", native.stdout)
    if not match:
        raise RuntimeError("unexpected native test output")
    obj = output / "mt6897_ufs_topckgen.arm64.o"
    run([
        "clang", "-target", "aarch64-none-elf", "-std=c11", "-O2",
        "-ffreestanding", "-fno-builtin", "-mgeneral-regs-only",
        "-Wall", "-Wextra", "-Werror", "-c", str(source), "-o", str(obj),
    ], commands, output)
    imports = run(
        ["llvm-nm", "--undefined-only", str(obj)], commands, output,
        capture_output=True, text=True).stdout.strip()
    if imports:
        raise RuntimeError("unexpected freestanding imports: " + imports)
    hardware = None
    if args.hardware_report:
        hardware = verify_hardware_report(args.hardware_report.resolve())
    source_paths = [source, header, test_source, manifest_path, Path(__file__).resolve()]
    result = {
        "passed": True,
        "native_checks": int(match.group(1)),
        "sanitizers": "ASan + UBSan",
        "freestanding_arm64_compile": True,
        "arm64_undefined_imports": [],
        "arm64_object_sha256": sha256(obj),
        "source_manifest": {
            "repository": manifest["vendor"]["repository"],
            "commit": manifest["vendor"]["commit"],
            "verified_git_blobs": SOURCE_PINS,
        },
        "saved_fdt_topckgen_references": hardware,
        "source_sha256": {
            str(path.relative_to(repo)): sha256(path) for path in source_paths
        },
        "safety": {
            "callback_only": True,
            "direct_mmio_backend": False,
            "phone_access": False,
            "pll_control": False,
            "firmware_ownership_claimed": False,
            "readback_bounded_by_time_and_poll_count": True,
        },
        "scope": "host register model and freestanding ARM64 compile only",
    }
    (output / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
