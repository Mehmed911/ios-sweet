#!/usr/bin/env python3
"""Exercise the MT6897 read-only provider and its XNU mapping adapter locally.

All grants and register values in executable tests are synthetic. Saved Android
resource evidence is audited separately and never converted to an XNU grant.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import re
import runpy
import shutil
import subprocess

REPO = Path(__file__).resolve().parent.parent
DRIVERS, XNU = REPO / "duchamp/drivers", REPO / "duchamp/xnu"
COMMON = [DRIVERS / "ufs_register_snapshot.c", DRIVERS / "mt6897_ufs_observer.c"]
UNIT = [*COMMON, XNU / "mt6897_ufs_observer_xnu.c", DRIVERS / "test_mt6897_ufs_observer.c"]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def command(args, log, timeout=45):
    result = subprocess.run([str(arg) for arg in args], capture_output=True, text=True,
                            stdin=subprocess.DEVNULL, timeout=timeout)
    log.write_text(result.stdout + result.stderr)
    if result.returncode:
        raise RuntimeError(f"Command failed ({result.returncode}); see {log}")
    return result.stdout


def native(args, out):
    flags = [args.clang, "-std=c11", "-O1", "-g", "-Wall", "-Wextra", "-Werror",
             "-fsanitize=address,undefined", "-fno-omit-frame-pointer", "-I" + str(DRIVERS)]
    exe = out / "unit.native"
    command([*flags, "-I" + str(XNU), "-DMT6897_UFS_OBSERVER_XNU_TEST", *UNIT, "-o", exe],
            out / "native-build.log")
    log = command([exe], out / "native.log")
    race = out / "races.native"
    command([*flags, "-pthread", *COMMON, DRIVERS / "test_mt6897_ufs_observer_race.c", "-o", race],
            out / "race-build.log")
    race_log = command([race], out / "races.log")
    assert "UFS OBSERVER RACE PASS cases=4" in race_log
    return log


def arm(args, out):
    previous = runpy.run_path(str(REPO / "tools/test-duchamp-ufs-register-snapshot.py"))
    linker, elf = out / "model.ld", out / "model.elf"
    linker.write_text(previous["LINKER"])
    command([args.clang, "--target=aarch64-none-elf", "-std=c11", "-O2", "-ffreestanding",
             "-fno-builtin", "-mgeneral-regs-only", "-mstrict-align", "-Wall", "-Wextra", "-Werror",
             "-DMT6897_MODEL_FREESTANDING", "-DMT6897_UFS_OBSERVER_XNU_TEST",
             "-I" + str(DRIVERS), "-I" + str(XNU), "-nostdlib", "-fuse-ld=lld", "-Wl,-T," + str(linker),
             DRIVERS / "test_mt6897_model_start.S", DRIVERS / "test_mt6897_model_runtime.c",
             *UNIT, "-o", elf], out / "arm-build.log")
    events = out / "trace-events"
    events.write_text("ufs_mmio_read\nufs_mmio_write\nufs_exec_scsi_cmd\n")
    log = command([args.qemu, "-M", "virt,gic-version=3,highmem-ecam=off", "-cpu", "cortex-a76",
                   "-m", "64M", "-smp", "1", "-nodefaults", "-display", "none", "-monitor", "none",
                   "-serial", "stdio", "-nic", "none", "-semihosting-config", "enable=on,target=native",
                   "-kernel", elf, "-device", "ufs,id=ufs0,addr=04.0,mcq=on,mcq-maxq=8",
                   "-trace", f"events={events},file={out / 'ufs.trace'}"], out / "qemu.log")
    assert log.endswith("MT6897 ARM64 MODEL PASS\n")
    assert not (out / "ufs.trace").read_text().strip()
    return log


def real_headers(args, out):
    api = runpy.run_path(str(REPO / "tools/xnu-cc.py"))
    fn = api["run"]
    fn.__globals__["CLANG"] = shutil.which(args.clang)
    commands = api["commands"](str(args.xnu_log))
    dirs = api["component_dirs"](str(args.xnu_buildtree))
    objects = out / "xnu-objects"
    objects.mkdir(exist_ok=True)
    os.environ["XNU_CC_OBJDIR"] = str(objects)
    sources = {"mt6897_ufs_observer.c": DRIVERS / "mt6897_ufs_observer.c",
               "mt6897_ufs_observer_xnu.c": XNU / "mt6897_ufs_observer_xnu.c"}
    results = {}
    for name, path in sources.items():
        original = api["CI_DXB"] + "/xnu/bsd/dev/" + name
        kind, flags = api["template_for"](original, commands)
        flags = [str(path) if arg == original else arg for arg in flags]
        flags = ["-I" + str(DRIVERS), "-I" + str(XNU), *flags]
        _, code, stderr = fn((original, (kind, flags)), str(args.xnu_buildtree), dirs)
        (objects / (name + ".log")).write_text(stderr)
        if code:
            raise RuntimeError(f"Real XNU header compile failed: {name}; see {objects}")
        obj = objects / ("bsd__dev__" + name + ".o")
        imports = command(["llvm-nm", "--undefined-only", obj], objects / (name + ".imports"))
        results[name] = dict(sha256=digest(obj), imports=imports.splitlines())
    imports = results["mt6897_ufs_observer_xnu.c"]["imports"]
    assert any("_ml_io_map_with_prot" in line for line in imports)
    assert not any(re.search(r"smc|[Dd]cache|dma|ml_probe_read|ml_nofault_copy", line) for line in imports)
    return results


def saved_evidence(args):
    layout = runpy.run_path(str(REPO / "tools/test-duchamp-ufs-register-snapshot.py"))["pinned_layout"]
    profile = layout(args.dtb, args.xiaomi_sources)
    saved = json.loads(args.resource_bindings.read_text())
    hci = saved["linux_runtime"]["bindings"]["ufs_hci"]
    assert hci["linux_driver_binding_proven"] and not hci["xnu_delegation_proven"]
    assert not saved["authorization"]["physical_backend_enabled"]
    source = (args.xiaomi_sources / "ufs-mediatek.c").read_text()
    assert "ufshcd_setup_clock(true)" in source and "pm_runtime_get_sync(host->phy_dev)" in source
    return dict(profile=profile, evidence_sha256=digest(args.resource_bindings),
                saved_capture=saved["capture"], android_runtime_status=hci["runtime_status"],
                xnu_read_grant_proven=False, physical_capture_allowed=False,
                reason="Saved Linux state does not establish powered/access-pinned MMIO at XNU entry. "
                       "No trusted physical read-grant producer is registered.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    for name in ("dtb", "xiaomi-sources", "resource-bindings", "xnu-buildtree", "xnu-log"):
        parser.add_argument("--" + name, type=lambda p: Path(p).resolve(), required=True)
    parser.add_argument("--clang", default="clang")
    parser.add_argument("--qemu", default="qemu-system-aarch64")
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    evidence = saved_evidence(args)
    with ThreadPoolExecutor(max_workers=3) as pool:
        host_job, arm_job, xnu_job = (pool.submit(fn, args, out) for fn in (native, arm, real_headers))
        host, guest, objects = host_job.result(), arm_job.result(), xnu_job.result()
    assert re.findall(r"(?m)^UFS OBSERVER case=.*$", host) == re.findall(r"(?m)^UFS OBSERVER case=.*$", guest)
    for log in (host, guest):
        assert "UFS OBSERVER PASS cases=25 physical_access=0" in log
        assert "UFS OBSERVER authority_failures=318 revocations=318 no_later_read=1" in log
    files = [*UNIT, DRIVERS / "ufs_register_snapshot.h", DRIVERS / "mt6897_ufs_observer.h",
             XNU / "mt6897_ufs_observer_xnu.h", DRIVERS / "test_mt6897_ufs_observer_race.c",
             DRIVERS / "test_mt6897_model_start.S", DRIVERS / "test_mt6897_model_runtime.c",
             Path(__file__).resolve()]
    artifacts = ("unit.native", "races.native", "model.elf", "native.log", "qemu.log",
                 "races.log", "ufs.trace")
    report = dict(passed=True, cases=25, denied_authority_positions=318, revoked_positions=318,
        concurrency_cases=4, sanitizers="ASan/UBSan", arm64_qemu=True, real_xnu_objects=objects,
        full_kernel_rebuild=False, actual_xnu_execution=False,
        scope="Standalone tests of the provider and XNU adapter with RAM mapping shims. "
              "VM_PROT_READ requests are checked, not hardware MMU protection or real MT6897 MMIO.",
        evidence=evidence, unrelated_qemu_ufs_trace_empty=True, phone_access=False,
        physical_mmio=False, firmware_calls=0, ufs_commands=0, flash=False, partition_write=False,
        artifact_sha256={name: digest(out / name) for name in artifacts},
        source_sha256={str(path.relative_to(REPO)): digest(path) for path in files})
    (out / "verification.json").write_text(json.dumps(report, indent=2) + "\n")
    print("MT6897 observer binding PASS: 25 cases, 318 denials, 318 revocations, 4 races; "
          "ARM64 QEMU and real XNU-header compile. Physical capture remains disabled.")


if __name__ == "__main__":
    main()
