#!/usr/bin/env python3
"""Run the saved-DTB MT6897 offline gates in parallel; never access a phone."""

import argparse
import concurrent.futures
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time


FDT_SHA256 = "9c49589f70044127be8941a9ea5537977f440ccd5ac15cfd24e120c8a1181d29"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tracked_inputs(repo):
    paths = [
        repo / "duchamp/board.toml",
        repo / "duchamp/drivers/duchamp_gic_boot.h",
        repo / "duchamp/drivers/duchamp_timer_boot.h",
        repo / "duchamp/drivers/duchamp_psci_boot.h",
        repo / "duchamp/drivers/mt6897-platform-sources.json",
        repo / "duchamp/drivers/test_mt6897_ufs_topckgen.c",
        repo / "duchamp/drivers/ufs_readonly.c",
        repo / "duchamp/drivers/ufs_readonly.h",
        repo / "tools/check-duchamp-fdt.sh",
        repo / "tools/inspect-duchamp-hardware.py",
        repo / "tools/report-duchamp-mt6897-ownership.py",
        repo / "tools/test-report-duchamp-mt6897-ownership.py",
        repo / "tools/test-duchamp-psci-boot.py",
        repo / "tools/test-duchamp-timer-boot.py",
        Path(__file__).resolve(),
    ]
    paths.extend(sorted((repo / "duchamp/drivers").glob("mt6897*.[ch]")))
    paths.extend(sorted((repo / "tools").glob("test-mt6897-*.py")))
    paths.extend(sorted((repo / "tools").glob("test-duchamp-gic-boot.py")))
    paths.extend(sorted((repo / "tools").glob("test-duchamp-ufs-poll.py")))
    paths.extend(sorted((repo / "tools").glob("test-duchamp-boot-profile.py")))
    return {str(path.relative_to(repo)): sha256(path) for path in dict.fromkeys(paths)}


def decoded(value):
    if isinstance(value, bytes):
        return value.decode(errors="replace")
    return value or ""


def run_component(name, command, log_dir, timeout_seconds):
    started = time.monotonic()
    try:
        result = subprocess.run(
            command, capture_output=True, text=True, timeout=timeout_seconds
        )
        returncode = result.returncode
        stdout = result.stdout
        stderr = result.stderr
        failure = None
    except subprocess.TimeoutExpired as error:
        returncode = 124
        stdout = decoded(error.stdout)
        stderr = decoded(error.stderr)
        failure = f"timeout after {timeout_seconds} seconds"
    except OSError as error:
        returncode = 127
        stdout = ""
        stderr = str(error) + "\n"
        failure = str(error)
    elapsed = time.monotonic() - started
    log = log_dir / (name + ".log")
    log.write_text(stdout + stderr)
    component = {
        "name": name,
        "passed": returncode == 0,
        "returncode": returncode,
        "seconds": round(elapsed, 3),
        "command": command,
        "log": str(log),
    }
    if failure is not None:
        component["failure"] = failure
    return component


def load_pass(path):
    result = json.loads(path.read_text())
    if result.get("passed") is not True:
        raise ValueError("component did not report a pass: " + str(path))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--fdt", type=Path, required=True)
    parser.add_argument("--template", type=Path, required=True)
    parser.add_argument("--boot-sources", type=Path, required=True)
    parser.add_argument("--platform-sources", type=Path, required=True)
    parser.add_argument("--backend-sources", type=Path, required=True)
    parser.add_argument("--jobs", type=int, default=7)
    parser.add_argument("--timeout-seconds", type=int, default=120)
    args = parser.parse_args()

    output = args.output.resolve()
    if output.exists():
        parser.error("preserve existing output")
    if args.jobs < 1:
        parser.error("--jobs must be positive")
    if args.timeout_seconds < 1:
        parser.error("--timeout-seconds must be positive")

    repo = Path(__file__).resolve().parent.parent
    fdt = args.fdt.resolve()
    template = args.template.resolve()
    boot_sources = args.boot_sources.resolve()
    platform_sources = args.platform_sources.resolve()
    backend_sources = args.backend_sources.resolve()
    if sha256(fdt) != FDT_SHA256:
        parser.error("saved Duchamp DTB provenance differs")

    before = tracked_inputs(repo)
    input_hashes = {
        "fdt": sha256(fdt),
        "template": sha256(template),
        "board": sha256(repo / "duchamp/board.toml"),
    }
    started = time.monotonic()
    output.mkdir(parents=True)
    log_dir = output / "logs"
    log_dir.mkdir()

    hardware = output / "hardware.json"
    inspect_command = [
        sys.executable,
        str(repo / "tools/inspect-duchamp-hardware.py"),
        str(fdt),
        str(hardware),
    ]
    inspect_result = run_component(
        "hardware", inspect_command, log_dir, args.timeout_seconds
    )
    if not inspect_result["passed"]:
        report = {
            "passed": False,
            "failure": "saved-DTB hardware inspection failed",
            "components": {"hardware": inspect_result},
            "physical_device_access": False,
        }
        (output / "result.json").write_text(json.dumps(report, indent=2) + "\n")
        raise SystemExit(1)

    commands = {
        "fdt_preflight": ["bash", str(repo / "tools/check-duchamp-fdt.sh"), str(fdt)],
        "boot_profile": [
            sys.executable,
            str(repo / "tools/test-duchamp-boot-profile.py"),
            "--fdt", str(fdt),
            "--template", str(template),
            "--sources", str(boot_sources),
        ],
        "gic": [
            sys.executable,
            str(repo / "tools/test-duchamp-gic-boot.py"),
            str(output / "gic"),
        ],
        "psci": [
            sys.executable,
            str(repo / "tools/test-duchamp-psci-boot.py"),
            str(output / "psci"),
        ],
        "timer_frequency": [
            sys.executable,
            str(repo / "tools/test-duchamp-timer-boot.py"),
            str(output / "timer-frequency"),
        ],
        "power_dma": [
            sys.executable,
            str(repo / "tools/test-mt6897-platform.py"),
            str(output / "power-dma"),
            "--fdt", str(fdt),
            "--sources", str(platform_sources),
        ],
        "providers": [
            sys.executable,
            str(repo / "tools/test-mt6897-backends.py"),
            str(output / "providers"),
            "--fdt", str(fdt),
            "--sources", str(backend_sources),
        ],
        "ufs_clocks": [
            sys.executable,
            str(repo / "tools/test-mt6897-ufs-clocks.py"),
            str(output / "ufs-clocks"),
            "--hardware-report", str(hardware),
        ],
        "ufs_topckgen": [
            sys.executable,
            str(repo / "tools/test-mt6897-ufs-topckgen.py"),
            str(output / "ufs-topckgen"),
            "--hardware-report", str(hardware),
        ],
        "ufs_polling": [
            sys.executable,
            str(repo / "tools/test-duchamp-ufs-poll.py"),
            str(output / "ufs-polling"),
        ],
        "ownership": [
            sys.executable,
            str(repo / "tools/report-duchamp-mt6897-ownership.py"),
            str(fdt),
            "--compact",
        ],
    }

    components = {"hardware": inspect_result}
    with concurrent.futures.ThreadPoolExecutor(
        max_workers=min(args.jobs, len(commands))
    ) as executor:
        futures = {
            executor.submit(
                run_component, name, command, log_dir, args.timeout_seconds
            ): name
            for name, command in commands.items()
        }
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            components[result["name"]] = result

    failure = None
    evidence = {}
    try:
        if not all(component["passed"] for component in components.values()):
            failed = sorted(name for name, value in components.items() if not value["passed"])
            raise ValueError("failed components: " + ", ".join(failed))
        hardware_result = json.loads(hardware.read_text())
        gic = load_pass(output / "gic/result.json")
        psci = load_pass(output / "psci/result.json")
        timer_frequency = load_pass(output / "timer-frequency/result.json")
        power = load_pass(output / "power-dma/result.json")
        providers = load_pass(output / "providers/result.json")
        clocks = load_pass(output / "ufs-clocks/result.json")
        topckgen = load_pass(output / "ufs-topckgen/result.json")
        polling = load_pass(output / "ufs-polling/result.json")
        ownership = json.loads(
            Path(components["ownership"]["log"]).read_text(encoding="utf-8")
        )
        observed_hashes = {
            hardware_result["fdt_sha256"],
            power["saved_dtb"]["fdt_sha256"],
            providers["saved_dtb"]["fdt_sha256"],
        }
        if observed_hashes != {FDT_SHA256}:
            raise ValueError("component DTB provenance disagreement")
        if power.get("physical_backend_enabled") is not False:
            raise ValueError("power/DMA test unexpectedly enabled a physical backend")
        if providers.get("physical_backend_enabled") is not False:
            raise ValueError("provider test unexpectedly enabled a physical backend")
        if psci.get("physical_psci_authorized") is not False:
            raise ValueError("PSCI gate unexpectedly authorized physical CPU_ON")
        if psci.get("smc_executed") is not False:
            raise ValueError("PSCI gate unexpectedly executed an SMC")
        if timer_frequency.get("architected_register_read_executed") is not False:
            raise ValueError("timer model unexpectedly read CNTFRQ")
        if timer_frequency.get("physical_timer_enabled") is not False:
            raise ValueError("timer model unexpectedly enabled a physical timer")
        if power["saved_dtb"].get("physical_dma_route_verified") is not False:
            raise ValueError("physical DMA route was incorrectly promoted")
        if providers["saved_dtb"].get("installed_firmware_verified") is not False:
            raise ValueError("installed firmware was incorrectly promoted")
        top_safety = topckgen.get("safety", {})
        if top_safety.get("callback_only") is not True:
            raise ValueError("topckgen model is not callback-only")
        for key in ("direct_mmio_backend", "phone_access", "pll_control",
                    "firmware_ownership_claimed"):
            if top_safety.get(key) is not False:
                raise ValueError("topckgen safety claim changed: " + key)
        if topckgen.get("saved_fdt_topckgen_references") != {
            "ufs_sel": 42,
            "ufs_sel_min_src": 118,
            "ufs_sel_max_src": 172,
            "ufs_fde": 41,
            "ufs_fde_min_src": 139,
            "ufs_fde_max_src": 117,
        }:
            raise ValueError("topckgen saved-DTB references changed")
        separate_topckgen = clocks.get("separate_topckgen_references", [])
        if separate_topckgen != list(topckgen["saved_fdt_topckgen_references"]):
            raise ValueError("leaf/topckgen component reference disagreement")
        for name, category in ownership["categories"].items():
            if category.get("runtime_owner") != "unproven":
                raise ValueError(f"{name} ownership was incorrectly promoted")
            if category.get("physical_access_tested") is not False:
                raise ValueError(f"{name} physical access was incorrectly promoted")
        ufs_route = ownership["categories"]["ufs"]["ufs_dma_route"]
        if ufs_route.get("verified") is not False:
            raise ValueError("ownership report promoted the UFS DMA route")
        evidence = {
            "boot_profile_tests": 21,
            "gic": {
                "native": gic["native_checks"],
                "arm64": gic["arm64_model_checks"],
                "actual_qemu_gicr": gic["actual_qemu_gicr_checks"],
            },
            "psci": {
                "native": psci["native_checks"],
                "arm64": psci["arm64_checks"],
                "physical_psci_authorized": psci["physical_psci_authorized"],
                "smc_executed": psci["smc_executed"],
            },
            "timer_frequency": {
                "native": timer_frequency["native_checks"],
                "arm64": timer_frequency["arm64_checks"],
                "architected_register_read_executed": timer_frequency["architected_register_read_executed"],
                "physical_timer_enabled": timer_frequency["physical_timer_enabled"],
            },
            "power_dma": {
                "power": power["power_checks"],
                "dma": power["dma_checks"],
                "arm64_reproduced": power["arm64_model"]["same_checks_as_native"],
            },
            "providers": {
                "native": providers["native_checks"],
                "raw_smc": providers["raw_smc_checks"],
                "arm64_matches_native": providers["arm64_checks"] == providers["native_checks"],
            },
            "ufs_clocks": {
                "leaf_mapping_from_saved_fdt": clocks.get("captured_fdt_leaf_mapping_verified"),
                "topckgen_references_covered_by_separate_model": separate_topckgen,
            },
            "ufs_topckgen": {
                "native_checks": topckgen["native_checks"],
                "freestanding_arm64_compile": topckgen["freestanding_arm64_compile"],
                "callback_only": top_safety["callback_only"],
                "physical_backend": "disabled",
            },
            "ufs_polling": {
                "native": polling["native_checks"],
                "arm64": polling["arm64_checks"],
            },
            "ownership": {
                "dtb_sha256": ownership["dtb"]["sha256"],
                "categories": sorted(ownership["categories"]),
                "runtime_owners": "unproven",
                "physical_access_tested": False,
                "ufs_dma_route_verified": ufs_route["verified"],
            },
        }
    except (KeyError, OSError, ValueError, json.JSONDecodeError) as error:
        failure = str(error)

    after = tracked_inputs(repo)
    inputs_unchanged = before == after and input_hashes == {
        "fdt": sha256(fdt),
        "template": sha256(template),
        "board": sha256(repo / "duchamp/board.toml"),
    }
    passed = failure is None and inputs_unchanged
    if not inputs_unchanged and failure is None:
        failure = "source or saved input changed during the gate"

    report = {
        "passed": passed,
        "seconds": round(time.monotonic() - started, 3),
        "input_sha256": input_hashes,
        "inputs_unchanged": inputs_unchanged,
        "components": dict(sorted(components.items())),
        "evidence": evidence,
        "remaining_physical_blockers": {
            "runtime_timer_and_interrupt_delivery": "unverified",
            "gic_and_firmware_resource_ownership": "unverified",
            "installed_firmware_contract": "unverified",
            "ufs_dma_or_iommu_route": "unverified",
            "ufs_topckgen_physical_backend": "disabled",
            "physical_ufs_backend": "disabled",
            "secondary_cpu_start_and_power": "unverified",
            "mali_acceleration": "not implemented",
        },
        "safety": {
            "physical_device_access": False,
            "mmio_access": False,
            "flash_or_partition_write": False,
            "phone_execution_authorized": False,
        },
        "scope": "saved-DTB parsing, host sanitizers and local ARM64/QEMU models only",
    }
    if failure is not None:
        report["failure"] = failure
    (output / "result.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if passed else 1)


if __name__ == "__main__":
    main()
