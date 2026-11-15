#!/usr/bin/env python3
"""Exercise the isolated metadata capture in native mocks and the ARM64 bootshim."""

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import os
from pathlib import Path
import subprocess
import sys


SHIM = Path(__file__).resolve().parent
DTS = """\
/dts-v1/;
/ {
    compatible = "mediatek,MT6897";
    #address-cells = <2>;
    #size-cells = <2>;
    chosen { };
    soc {
        #address-cells = <2>;
        #size-cells = <2>;
        ranges;
        ufshci@112b0000 {
            reg = <0 0x112b0000 0 0x3000>;
            clocks = <1>;
            phys = <2>;
            power-domains = <3>;
            resets = <4>;
            vcc-supply = <5>;
            vccq-supply = <6>;
            mediatek,ufs-rtff-mtcmos;
        };
    };
};
"""


def run(args, log, **kw):
    result = subprocess.run(args, cwd=SHIM, stdin=subprocess.DEVNULL,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, timeout=40, **kw)
    log.write_text(result.stdout)
    if result.returncode:
        raise RuntimeError(f"{args[0]} failed with {result.returncode}, see {log}")
    return result.stdout


def edit_dtb(dtb, options, node, property_name, *values):
    subprocess.run(["fdtput", *options, dtb, node, property_name, *values],
                   check=True, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=10)


def fixture(base, path, slot, extension=None, omit=()):
    path.write_bytes(base.read_bytes())
    if slot:
        edit_dtb(path, ("-t", "s"), "/chosen", "bootargs", slot)
    if extension:
        edit_dtb(path, ("-t", "s"), "/chosen", "bootargs_ext", extension)
    for key in omit:
        edit_dtb(path, ("-d",), "/soc/ufshci@112b0000", key)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=lambda value: Path(value).resolve())
    parser.add_argument("--contract", required=True, type=lambda value: Path(value).resolve())
    parser.add_argument("--saved-duchamp-fdt", type=lambda value: Path(value).resolve())
    args = parser.parse_args()
    out = args.output
    out.mkdir(parents=True)
    env = dict(os.environ, SHIM_OUT=str(out / "bootshim"), PHONE_CAPTURE="1",
               PHONE_CONTRACT=str(args.contract), UFS_HANDOFF_PROBE="1")
    run(["sh", "build.sh"], out / "bootshim-build.log", env=env)
    image = out / "bootshim/Image"
    elf = out / "bootshim/duchamp-diagnostic.elf"
    symbols = subprocess.check_output(["llvm-nm", str(elf)], text=True).splitlines()

    def guest_pa(symbol):
        values = [int(row.split()[0], 16) for row in symbols if row.split()[-1] == symbol]
        if len(values) != 1:
            raise RuntimeError(f"missing or ambiguous ELF symbol {symbol}")
        return hex(0x40200000 + values[0])

    dts, generic = out / "fixture.dts", out / "fixture.dtb"
    dts.write_text(DTS)
    run(["dtc", "-q", "-I", "dts", "-O", "dtb", "-o", str(generic), str(dts)], out / "dtc.log")
    binary = out / "test-handoff-evidence"
    run(["clang", "-std=c11", "-O1", "-g", "-Wall", "-Wextra", "-Werror",
         "-fsanitize=address,undefined", "test_ufs_handoff_evidence.c",
         "ufs_handoff_evidence.c", "-o", str(binary)], out / "native-build.log")

    cases = [
        ("b_declared", "androidboot.slot_suffix=_b", None, (), 2, 0xff),
        ("wrong_slot_a", "androidboot.slot_suffix=_a", None, (), 1, 0xff),
        ("conflicting_hints", "androidboot.slot_suffix=_b", "androidboot.slot_suffix=_a", (), 3, 0xff),
        ("slot_missing", "different.androidboot.slot_suffix=_b", None, (), 0, 0xff),
        ("invalid_slot", "androidboot.slot_suffix=_bextra", None, (), 3, 0xff),
        ("clock_missing", "androidboot.slot_suffix=_b", None, ("clocks",), 2, 0xfd),
        ("power_missing", None, "androidboot.slot_suffix=_b",
         ("power-domains", "mediatek,ufs-rtff-mtcmos"), 2, 0xe7),
    ]
    dtbs = []
    for name, slot, extension, omit, expected_slot, declarations in cases:
        path = out / f"{name}.dtb"
        fixture(generic, path, slot, extension, omit)
        dtbs.append((name, path, expected_slot, declarations))
    if args.saved_duchamp_fdt:
        # The saved final Android FDT contains the HCI, clocks, PHY, RTFF,
        # resets and rails, and carries no recognized slot hint.
        dtbs.append(("saved_duchamp", args.saved_duchamp_fdt, 0, 0xf7))

    def check(case):
        name, dtb, slot, declarations = case
        values = (str(slot), hex(declarations))
        before = hashlib.sha256(dtb.read_bytes()).digest()
        run([str(binary), str(dtb), *values], out / f"{name}-native.log")
        qemu_args = [sys.executable, "test_qemu.py", "--image", str(image),
                     "--dtb", str(dtb), "--pattern", "pc-x0", "--wait", "4",
                     "--capture-record-pa", guest_pa("duchamp_bootshim_phone_capture_record"),
                     "--ufs-handoff-record-pa", guest_pa("duchamp_bootshim_ufs_handoff_record"),
                     "--expect-ufs-fdt", *values]
        log = run(qemu_args, out / f"{name}-qemu.log")
        if "bootshim-ufs-handoff-receiver: PASS" not in log:
            raise RuntimeError(f"missing QEMU success marker for {name}")
        if hashlib.sha256(dtb.read_bytes()).digest() != before:
            raise RuntimeError(f"input FDT changed for {name}")
        print(f"{name}: native and bootshim QEMU PASS", flush=True)

    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(check, dtbs))


if __name__ == "__main__":
    main()
