#!/usr/bin/env python3
"""Exercise the isolated metadata capture in native mocks and the ARM64 bootshim."""

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import struct
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


def run(args, log, *, env=None):
    args = list(map(str, args))
    result = subprocess.run(args, cwd=SHIM, stdin=subprocess.DEVNULL,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, timeout=40, env=env)
    log.write_text(result.stdout)
    receipt = dict(argv=args, cwd=str(SHIM), log=log.name, exit_code=result.returncode)
    if env:
        receipt["diagnostic_env"] = {key: env[key] for key in
                                     ("SHIM_OUT", "PHONE_CAPTURE", "PHONE_CONTRACT", "UFS_HANDOFF_PROBE")}
    log.with_suffix(".command.json").write_text(json.dumps(receipt, indent=2) + "\n")
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
    claims = out / "untrusted-chosen-claims.dtb"
    fixture(generic, claims, "androidboot.slot_suffix=_b sweet-qemu-boot-id=0x1234")
    edit_dtb(claims, ("-t", "s"), "/chosen", "qemu-bl31-ufs", "untrusted")
    edit_dtb(claims, ("-t", "x"), "/soc/ufshci@112b0000", "iommus", "1", "2")
    edit_dtb(claims, (), "/soc/ufshci@112b0000", "dma-coherent")
    dtbs.append(("untrusted_chosen_claims", claims, 2, 0x3ff))

    # Exercise both SHA-256 padding branches and a block-aligned FDT.
    for remainder in (0, 55, 56):
        path = out / f"padding-{remainder}.dtb"
        data = bytearray(generic.read_bytes())
        data.extend(bytes((remainder - len(data)) % 64))
        struct.pack_into(">I", data, 4, len(data))
        path.write_bytes(data)
        dtbs.append((f"padding_{remainder}", path, 0, 0xff))
    if args.saved_duchamp_fdt:
        # The saved final Android FDT contains the HCI, clocks, PHY, RTFF,
        # resets and rails, and carries no recognized slot hint.
        dtbs.append(("saved_duchamp", args.saved_duchamp_fdt, 0, 0xf7))

    def check(case):
        name, dtb, slot, declarations = case
        values = (str(slot), hex(declarations))
        before = hashlib.sha256(dtb.read_bytes()).digest()
        run([binary, dtb, *values, before.hex()], out / f"{name}-native.log")
        qemu_args = [sys.executable, "test_qemu.py", "--image", str(image),
                     "--dtb", str(dtb), "--pattern", "pc-x0", "--wait", "4",
                     "--capture-record-pa", guest_pa("duchamp_bootshim_phone_capture_record"),
                     "--ufs-handoff-record-pa", guest_pa("duchamp_bootshim_ufs_handoff_record"),
                     "--expect-ufs-fdt", *values]
        log = run(qemu_args, out / f"{name}-qemu.log")
        if ("bootshim-ufs-handoff-receiver: PASS" not in log or
                "bootshim-ufs-handoff-digest-framebuffer: PASS" not in log):
            raise RuntimeError(f"missing QEMU success marker for {name}")
        if hashlib.sha256(dtb.read_bytes()).digest() != before:
            raise RuntimeError(f"input FDT changed for {name}")
        print(f"{name}: native and bootshim QEMU PASS", flush=True)

    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(check, dtbs))


if __name__ == "__main__":
    main()
