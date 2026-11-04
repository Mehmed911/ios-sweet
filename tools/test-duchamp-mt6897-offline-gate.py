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
        repo / "duchamp/drivers/duchamp_counter_probe.h",
        repo / "duchamp/drivers/duchamp_timer_probe.h",
        repo / "duchamp/drivers/duchamp_timer_boot.h",
        repo / "duchamp/drivers/duchamp_psci_boot.h",
        repo / "duchamp/drivers/test_duchamp_counter_probe.c",
        repo / "duchamp/drivers/test_duchamp_timer_probe.c",
        repo / "duchamp/drivers/mt6897-platform-sources.json",
        repo / "duchamp/drivers/test_mt6897_ufs_topckgen.c",
        repo / "duchamp/drivers/test_mt6897_ufs_gate.c",
        repo / "duchamp/xnu/mt6897_ufs_cache_backend.c",
        repo / "duchamp/xnu/mt6897_ufs_cache_backend.h",
        repo / "duchamp/xnu/test_mt6897_ufs_cache_backend.c",
        repo / "duchamp/drivers/ufs_readonly.c",
        repo / "duchamp/drivers/ufs_readonly.h",
        repo / "tools/check-duchamp-fdt.sh",
        repo / "tools/inspect-duchamp-hardware.py",
        repo / "tools/assess-mt6897-ufs-dma-map.py",
        repo / "tools/test-mt6897-ufs-dma-map.py",
        repo / "tools/interpret-duchamp-prdt-v3-observation.py",
        repo / "tools/test-interpret-duchamp-prdt-v3-observation.py",
        repo / "duchamp/diagnostics/ufs-prdt-observer-v3/PHONE-RESULT-2026-11-04.json",
        repo / "tools/assess-mt6897-ufs-resource-ownership.py",
        repo / "tools/test-mt6897-ufs-resource-ownership.py",
        repo / "tools/report-duchamp-mt6897-ownership.py",
        repo / "tools/test-report-duchamp-mt6897-ownership.py",
        repo / "tools/test-duchamp-psci-boot.py",
        repo / "tools/stage-duchamp-counter-probe.py",
        repo / "tools/test-duchamp-counter-probe-stage.py",
        repo / "tools/test-duchamp-counter-probe.py",
        repo / "tools/stage-duchamp-timer-probe.py",
        repo / "tools/test-duchamp-timer-probe-stage.py",
        repo / "tools/test-duchamp-timer-probe.py",
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
    parser.add_argument("--runtime-evidence", type=Path, required=True)
    parser.add_argument("--firmware-evidence", type=Path, required=True)
    parser.add_argument("--prdt-evidence", type=Path, required=True)
    parser.add_argument("--prdt-v3-evidence", type=Path, required=True)
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
    runtime_evidence = args.runtime_evidence.resolve()
    firmware_evidence = args.firmware_evidence.resolve()
    prdt_evidence = args.prdt_evidence.resolve()
    prdt_v3_evidence = args.prdt_v3_evidence.resolve()
    if sha256(fdt) != FDT_SHA256:
        parser.error("saved Duchamp DTB provenance differs")

    before = tracked_inputs(repo)
    input_hashes = {
        "fdt": sha256(fdt),
        "template": sha256(template),
        "board": sha256(repo / "duchamp/board.toml"),
        "runtime_evidence": sha256(runtime_evidence),
        "firmware_evidence": sha256(firmware_evidence),
        "prdt_evidence": sha256(prdt_evidence),
        "prdt_v3_evidence": sha256(prdt_v3_evidence),
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
        "counter_stage": [
            sys.executable,
            str(repo / "tools/test-duchamp-counter-probe-stage.py"),
        ],
        "counter_probe": [
            sys.executable,
            str(repo / "tools/test-duchamp-counter-probe.py"),
            str(output / "counter-probe"),
        ],
        "timer_probe_stage": [
            sys.executable,
            str(repo / "tools/test-duchamp-timer-probe-stage.py"),
        ],
        "timer_probe": [
            sys.executable,
            str(repo / "tools/test-duchamp-timer-probe.py"),
            str(output / "timer-probe"),
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
        "ufs_activation_gate": [
            sys.executable,
            str(repo / "tools/test-mt6897-ufs-gate.py"),
            str(output / "ufs-activation-gate"),
            "--fdt", str(fdt),
            "--runtime-evidence", str(runtime_evidence),
            "--firmware-evidence", str(firmware_evidence),
            "--prdt-evidence", str(prdt_evidence),
        ],
        "ufs_cache_contract": [
            sys.executable,
            str(repo / "tools/test-mt6897-ufs-cache.py"),
            str(output / "ufs-cache-contract"),
        ],
        "ufs_cache_backend": [
            sys.executable,
            str(repo / "tools/test-mt6897-ufs-cache-backend.py"),
            str(output / "ufs-cache-backend"),
        ],
        "ufs_dma_route_contract": [
            sys.executable,
            str(repo / "tools/test-mt6897-ufs-dma-route.py"),
            str(output / "ufs-dma-route-contract"),
        ],
        "ufs_dma_map_model_tests": [
            sys.executable,
            str(repo / "tools/test-mt6897-ufs-dma-map.py"),
        ],
        "ufs_dma_map_candidate": [
            sys.executable,
            str(repo / "tools/assess-mt6897-ufs-dma-map.py"),
            str(output / "ufs-dma-map-candidate/result.json"),
            "--fdt", str(fdt),
            "--runtime-evidence", str(runtime_evidence),
            "--prdt-evidence", str(prdt_evidence),
            "--prdt-v3-evidence", str(prdt_v3_evidence),
        ],
        "ufs_resource_ownership_tests": [
            sys.executable,
            str(repo / "tools/test-mt6897-ufs-resource-ownership.py"),
        ],
        "ufs_resource_ownership": [
            sys.executable,
            str(repo / "tools/assess-mt6897-ufs-resource-ownership.py"),
            str(output / "ufs-resource-ownership/result.json"),
            "--fdt", str(fdt),
            "--runtime-evidence", str(runtime_evidence),
            "--firmware-evidence", str(firmware_evidence),
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
        counter_probe = load_pass(output / "counter-probe/result.json")
        timer_probe = load_pass(output / "timer-probe/result.json")
        gic = load_pass(output / "gic/result.json")
        psci = load_pass(output / "psci/result.json")
        timer_frequency = load_pass(output / "timer-frequency/result.json")
        power = load_pass(output / "power-dma/result.json")
        providers = load_pass(output / "providers/result.json")
        clocks = load_pass(output / "ufs-clocks/result.json")
        topckgen = load_pass(output / "ufs-topckgen/result.json")
        polling = load_pass(output / "ufs-polling/result.json")
        activation_gate = load_pass(output / "ufs-activation-gate/result.json")
        cache_contract = load_pass(output / "ufs-cache-contract/result.json")
        cache_backend = load_pass(output / "ufs-cache-backend/result.json")
        dma_route_contract = load_pass(
            output / "ufs-dma-route-contract/result.json"
        )
        dma_map_candidate = load_pass(
            output / "ufs-dma-map-candidate/result.json"
        )
        resource_ownership = load_pass(
            output / "ufs-resource-ownership/result.json"
        )
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
        current_ufs = activation_gate.get("current_duchamp_evidence", {})
        if activation_gate.get("evidence_bound") is not True:
            raise ValueError("UFS activation gate was not bound to saved evidence")
        activation_receipts = activation_gate.get("input_receipts", {})
        compiled_receipts = activation_gate.get("compiled_receipts", {})
        if activation_receipts.get("fdt", {}).get("sha256") != FDT_SHA256:
            raise ValueError("UFS activation gate input FDT receipt differs")
        if compiled_receipts.get("fdt") != FDT_SHA256:
            raise ValueError("compiled UFS gate FDT receipt differs")
        activation_concurrency = activation_gate.get("concurrency", {})
        if (activation_concurrency.get("verifier_calls") != 1 or
                activation_concurrency.get(
                    "simultaneous_second_authorization") !=
                    "terminal fail-closed"):
            raise ValueError("UFS activation gate concurrency proof differs")
        activation_provider = activation_gate.get("provider", {})
        if (activation_provider.get("denied_dispatches") != 0 or
                activation_provider.get("native_model_dispatches") != 6 or
                activation_provider.get("concurrent_fault_before_dispatch") !=
                "terminal fail-closed" or
                activation_provider.get("freestanding_arm64_compile") is not True or
                activation_provider.get("arm64_matches_native") is not True or
                activation_provider.get("physical_backend") != "disabled"):
            raise ValueError("UFS lease-provider fail-closed proof differs")
        if activation_gate.get("freestanding_arm64_compile") is not True:
            raise ValueError("UFS activation gate did not compile for ARM64")
        activation_arm64 = activation_gate.get("arm64_model", {})
        if (activation_arm64.get("passed") is not True or
                activation_arm64.get("same_output_as_native") is not True):
            raise ValueError("UFS activation gate ARM64 model did not match native")
        if current_ufs.get("decision") != "denied":
            raise ValueError("current Duchamp UFS evidence was not denied")
        cache_current = cache_contract.get("current_duchamp_evidence", {})
        cache_native = cache_contract.get("native", {})
        cache_arm64 = cache_contract.get("arm64_qemu_model", {})
        cache_concurrency = cache_contract.get("concurrency", {})
        cache_policy = cache_contract.get("contract", {})
        if (cache_current.get("activation_lease_available") is not False or
                cache_current.get("cache_callbacks") != 0 or
                cache_current.get(
                    "physical_cache_maintenance_authorized") is not False):
            raise ValueError("UFS cache contract promoted current Duchamp evidence")
        if (cache_native.get("current_duchamp_callbacks") != 0 or
                cache_native.get("synthetic_model_handoffs") != 6 or
                cache_arm64.get("passed") is not True or
                cache_arm64.get("same_output_as_native") is not True):
            raise ValueError("UFS cache contract model proof differs")
        if (cache_concurrency.get("checks", 0) <= 0 or
                cache_concurrency.get("fault_before_cache_callback") is not True or
                cache_concurrency.get("range_callbacks") != 0):
            raise ValueError("UFS cache contract concurrency proof differs")
        if (cache_policy.get("default_closed") is not True or
                cache_policy.get("lease_checked_at_bind_and_every_transition")
                is not True or
                cache_policy.get("physical_backend") != "disabled"):
            raise ValueError("UFS cache contract fail-closed policy differs")
        cache_safety = cache_contract.get("safety", {})
        for key in ("phone_access", "adb_access", "fastboot_access",
                    "mmio_access", "smc_execution", "dma_access",
                    "cache_instruction_execution_by_contract",
                    "partition_access"):
            if cache_safety.get(key) is not False:
                raise ValueError("unsafe UFS cache-contract action: " + key)
        cache_backend_native = cache_backend.get("native", {})
        cache_backend_arm64 = cache_backend.get("arm64_qemu_model", {})
        cache_backend_object = cache_backend.get("production_arm64_object", {})
        cache_backend_policy = cache_backend.get("contract", {})
        if (cache_backend_native.get("checks", 0) <= 0 or
                cache_backend_arm64.get("passed") is not True or
                cache_backend_arm64.get("same_checks_as_native") is not True or
                cache_backend_object.get("undefined_imports") != [
                    "CleanPoC_DcacheRegion", "FlushPoC_DcacheRegion"] or
                cache_backend_object.get("dsb_sy_present") is not True or
                cache_backend_object.get("isb_present") is not True or
                cache_backend_policy.get("exact_receipt_pinned") is not True or
                cache_backend_policy.get("default_activation") != "none"):
            raise ValueError("XNU UFS cache backend proof differs")
        cache_backend_safety = cache_backend.get("safety", {})
        for key in ("phone_access", "adb_access", "fastboot_access",
                    "mmio_access", "smc_execution", "dma_access",
                    "partition_access", "production_cache_primitive_executed"):
            if cache_backend_safety.get(key) is not False:
                raise ValueError("unsafe XNU UFS cache-backend action: " + key)
        dma_route_native = dma_route_contract.get("native", {})
        dma_route_arm64 = dma_route_contract.get("arm64_qemu_model", {})
        dma_route_concurrency = dma_route_contract.get("concurrency", {})
        dma_route_policy = dma_route_contract.get("contract", {})
        dma_route_scope = dma_route_contract.get("scope", {})
        if (dma_route_native.get("current_duchamp_callbacks") != 0 or
                dma_route_native.get("synthetic_direct_mappings") != 3 or
                dma_route_native.get("synthetic_bounce_mappings") != 3 or
                dma_route_arm64.get("passed") is not True or
                dma_route_arm64.get("same_output_as_native") is not True):
            raise ValueError("UFS DMA-route model proof differs")
        if (dma_route_concurrency.get("checks", 0) <= 0 or
                dma_route_concurrency.get(
                    "fault_before_route_callback") is not True or
                dma_route_concurrency.get(
                    "active_clear_before_cpu_owned_publish") is not True or
                dma_route_concurrency.get("copy_callbacks") != 0):
            raise ValueError("UFS DMA-route concurrency proof differs")
        if (dma_route_policy.get("default_closed") is not True or
                dma_route_policy.get(
                    "lease_checked_at_bind_and_every_transition") is not True or
                dma_route_policy.get("immutable_receipt_fingerprint") is not True or
                dma_route_policy.get(
                    "unique_boot_local_route_instance_id") is not True or
                dma_route_policy.get(
                    "unique_per_route_operation_id") is not True or
                dma_route_policy.get("physical_backend") != "disabled"):
            raise ValueError("UFS DMA-route fail-closed policy differs")
        for key in ("phone_access", "mmio", "cache_instruction", "dma",
                    "ufs_command"):
            if dma_route_scope.get(key) is not False:
                raise ValueError("unsafe UFS DMA-route action: " + key)
        dma_map_translation = dma_map_candidate.get("candidate", {})
        dma_map_bounce = dma_map_candidate.get("bounce", {})
        dma_map_safety = dma_map_candidate.get("safety", {})
        if (dma_map_translation.get(
                "static_dt_translation_model_proven") is not True or
                dma_map_translation.get(
                    "runtime_dma_range_entries_proven") is not True or
                dma_map_translation.get(
                    "raw_dma_equals_cpu_pa_proven") is not True or
                dma_map_translation.get(
                    "forward_and_inverse_translation_proven") is not True or
                dma_map_translation.get(
                    "direct_route_receipt_issuable") is not True or
                dma_map_translation.get("receipt_scope") !=
                    "observed Linux UFS address route" or
                dma_map_bounce.get("disposition") !=
                    "inactive-not-forced-no-bounce-observed" or
                dma_map_bounce.get("swiotlb_pool_present") is not True or
                dma_map_bounce.get("swiotlb_pool_active") is not False or
                dma_map_bounce.get("swiotlb_force_bounce") is not False or
                dma_map_bounce.get("sample_no_swiotlb") is not True or
                dma_map_bounce.get("sample_segments") != 34162 or
                dma_map_bounce.get("bounded_window_segments") != 29452 or
                dma_map_bounce.get(
                    "observed_direct_route_proven") is not True or
                dma_map_bounce.get(
                    "global_bounce_disposition_proven") is not False or
                dma_map_bounce.get(
                    "bounce_route_receipt_issuable") is not False):
            raise ValueError("UFS DMA-map live evidence differs")
        for key in ("phone_access", "mmio_access", "smc_execution",
                    "dma_or_ufs_commands", "partition_access",
                    "physical_backend_enabled"):
            if dma_map_safety.get(key) is not False:
                raise ValueError("unsafe UFS DMA-map candidate action: " + key)
        resource_receipt = resource_ownership.get("ownership_receipt", {})
        resource_authorization = resource_ownership.get("authorization", {})
        resource_declarations = resource_ownership.get("declarations", {})
        resource_firmware = resource_ownership.get("firmware_contract", {})
        resource_safety = resource_ownership.get("safety", {})
        expected_resource_blockers = [
            "installed_firmware_identity",
            "firmware_effect_contract",
            "secure_power_arbitration",
            "mmio_resource_delegation",
            "clock_and_hw_voter_ownership",
            "reset_ownership",
            "phy_ownership",
            "regulator_ownership",
            "ufs_interrupt_ownership",
        ]
        if (resource_receipt.get("status") != "denied" or
                resource_receipt.get("receipt_issuable") is not False or
                resource_receipt.get("payload") is not None or
                resource_receipt.get("blockers") != expected_resource_blockers):
            raise ValueError("UFS resource-ownership receipt was not denied")
        if (resource_declarations.get(
                "exact_saved_dtb_manifest_proven") is not True or
                len(resource_declarations.get("mmio", [])) != 18 or
                len(resource_declarations.get(
                    "unlinked_ufs_named_mmio", [])) != 9 or
                len(resource_declarations.get("clocks", [])) != 12 or
                len(resource_declarations.get("resets", [])) != 3 or
                len(resource_declarations.get("interrupts", [])) != 9 or
                resource_declarations.get("clock_hw_voter") !=
                "/syscon@10320000" or
                resource_declarations.get("dma_coherent") is not False or
                resource_declarations.get("iommu_binding_present") is not False):
            raise ValueError("UFS resource declaration manifest differs")
        if (resource_firmware.get("static_service_dispatch_proven") is not True or
                resource_firmware.get("service_id") != "0xc2000276" or
                resource_firmware.get("runtime_effect_contract_proven") is not False or
                resource_firmware.get("exclusive_owner_proven") is not False or
                resource_firmware.get(
                    "direct_xnu_secure_power_mmio_authorized") is not False):
            raise ValueError("UFS firmware/resource ownership proof differs")
        if resource_authorization != {
                "physical_backend_enabled": False,
                "mmio_callbacks": 0,
                "smc_callbacks": 0,
                "dma_callbacks": 0,
                "ufs_commands": 0,
                "interrupt_reconfiguration_callbacks": 0,
        }:
            raise ValueError("UFS resource ownership enabled a callback")
        for key in ("phone_access", "network_access", "adb_access",
                    "fastboot_access", "mmio_access", "smc_execution",
                    "dma_or_ufs_commands", "partition_access",
                    "physical_backend_enabled"):
            if resource_safety.get(key) is not False:
                raise ValueError("unsafe UFS resource-ownership action: " + key)
        if current_ufs.get("blockers") != [
            "firmware_effect_contract",
            "resource_ownership",
            "cache_maintenance_ownership",
            "direct_address_translation",
            "bounce_disposition",
        ]:
            raise ValueError("current Duchamp UFS blocker set changed")
        if current_ufs.get("blocker_mask") != "0x000100000000040e":
            raise ValueError("current Duchamp UFS blocker mask changed")
        for key in ("verifier_calls", "hardware_calls", "mmio_calls",
                    "smc_calls", "dma_calls"):
            if current_ufs.get(key) != 0:
                raise ValueError("UFS activation gate side effect: " + key)
        for key in ("hardware_access", "mmio_access", "smc_execution",
                    "dma_access", "phone_access"):
            if current_ufs.get(key) is not False:
                raise ValueError("UFS activation gate safety changed: " + key)
        if psci.get("physical_psci_authorized") is not False:
            raise ValueError("PSCI gate unexpectedly authorized physical CPU_ON")
        if psci.get("smc_executed") is not False:
            raise ValueError("PSCI gate unexpectedly executed an SMC")
        if counter_probe.get("architected_register_reads_executed") is not True:
            raise ValueError("counter probe did not read the architected counter")
        if counter_probe.get("qemu_cntfrq_hz") != 62500000:
            raise ValueError("counter probe observed an unexpected QEMU frequency")
        for key in ("timer_register_writes", "gic_access", "smc_execution",
                    "phone_access"):
            if counter_probe.get(key) is not False:
                raise ValueError("counter-probe safety claim changed: " + key)
        if timer_probe.get("architected_timer_expiry_executed") is not True:
            raise ValueError("timer probe did not observe architected expiry")
        if timer_probe.get("qemu_cntfrq_hz") != 62500000:
            raise ValueError("timer probe observed an unexpected QEMU frequency")
        if timer_probe.get("timer_register_writes") is not True:
            raise ValueError("timer probe did not execute its expected writes")
        if timer_probe.get("timer_irq_masked") is not True:
            raise ValueError("timer probe did not keep the IRQ masked")
        for key in ("timer_irq_delivery_tested", "gic_access", "smc_execution",
                    "phone_access"):
            if timer_probe.get(key) is not False:
                raise ValueError("timer-probe safety claim changed: " + key)
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
            "pre_gic_counter": {
                "stage_tests_passed": components["counter_stage"]["passed"],
                "native": counter_probe["native_checks"],
                "arm64": counter_probe["arm64_checks"],
                "architected_register_reads_executed": counter_probe[
                    "architected_register_reads_executed"
                ],
                "qemu_cntfrq_hz": counter_probe["qemu_cntfrq_hz"],
                "timer_register_writes": counter_probe["timer_register_writes"],
                "gic_access": counter_probe["gic_access"],
                "smc_execution": counter_probe["smc_execution"],
                "phone_access": counter_probe["phone_access"],
            },
            "pre_gic_timer_expiry": {
                "stage_tests_passed": components["timer_probe_stage"]["passed"],
                "native": timer_probe["native_checks"],
                "arm64": timer_probe["arm64_checks"],
                "architected_timer_expiry_executed": timer_probe[
                    "architected_timer_expiry_executed"
                ],
                "qemu_cntfrq_hz": timer_probe["qemu_cntfrq_hz"],
                "deadline_ticks": timer_probe["qemu_deadline_ticks"],
                "elapsed_ticks": timer_probe["qemu_elapsed_ticks"],
                "timer_irq_masked": timer_probe["timer_irq_masked"],
                "timer_irq_delivery_tested": timer_probe[
                    "timer_irq_delivery_tested"
                ],
                "gic_access": timer_probe["gic_access"],
                "smc_execution": timer_probe["smc_execution"],
                "phone_access": timer_probe["phone_access"],
            },
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
            "ufs_activation_gate": {
                "native_checks": activation_gate["native"]["checks"],
                "concurrency_checks": activation_concurrency["checks"],
                "compiled_receipts_match_saved_inputs": True,
                "freestanding_arm64_compile": activation_gate[
                    "freestanding_arm64_compile"
                ],
                "arm64_model_checks": activation_arm64["checks"],
                "arm64_matches_native": activation_arm64[
                    "same_output_as_native"
                ],
                "evidence_bound": activation_gate["evidence_bound"],
                "current_decision": current_ufs["decision"],
                "current_blockers": current_ufs["blockers"],
                "verifier_calls": current_ufs["verifier_calls"],
                "hardware_access": current_ufs["hardware_access"],
                "lease_provider": {
                    "native_checks": activation_provider["native_checks"],
                    "concurrency_checks": activation_provider[
                        "concurrency_checks"
                    ],
                    "operation_classes": activation_provider[
                        "native_model_dispatches"
                    ],
                    "denied_dispatches": activation_provider[
                        "denied_dispatches"
                    ],
                    "concurrent_fault_before_dispatch": activation_provider[
                        "concurrent_fault_before_dispatch"
                    ],
                    "arm64_matches_native": activation_provider[
                        "arm64_matches_native"
                    ],
                },
                "physical_backend": "disabled",
            },
            "ufs_cache_contract": {
                "native_checks": cache_native["checks"],
                "current_duchamp_callbacks": cache_native[
                    "current_duchamp_callbacks"
                ],
                "synthetic_model_handoffs": cache_native[
                    "synthetic_model_handoffs"
                ],
                "concurrency_checks": cache_concurrency["checks"],
                "fault_before_cache_callback": cache_concurrency[
                    "fault_before_cache_callback"
                ],
                "arm64_model_checks": cache_arm64["checks"],
                "arm64_matches_native": cache_arm64[
                    "same_output_as_native"
                ],
                "lease_checked_at_bind_and_every_transition": cache_policy[
                    "lease_checked_at_bind_and_every_transition"
                ],
                "physical_backend": cache_policy["physical_backend"],
            },
            "ufs_cache_backend": {
                "native_checks": cache_backend_native["checks"],
                "arm64_model_checks": cache_backend_arm64["checks"],
                "arm64_matches_native": cache_backend_arm64[
                    "same_checks_as_native"
                ],
                "production_imports": cache_backend_object[
                    "undefined_imports"
                ],
                "dsb_sy_present": cache_backend_object["dsb_sy_present"],
                "isb_present": cache_backend_object["isb_present"],
                "cache_line_size": 64,
                "default_activation": cache_backend_policy[
                    "default_activation"
                ],
                "full_xnu_qemu_execution": "separate gate",
                "physical_backend": "disabled",
            },
            "ufs_dma_route_contract": {
                "native_checks": dma_route_native["checks"],
                "current_duchamp_callbacks": dma_route_native[
                    "current_duchamp_callbacks"
                ],
                "synthetic_direct_mappings": dma_route_native[
                    "synthetic_direct_mappings"
                ],
                "synthetic_bounce_mappings": dma_route_native[
                    "synthetic_bounce_mappings"
                ],
                "concurrency_checks": dma_route_concurrency["checks"],
                "fault_before_route_callback": dma_route_concurrency[
                    "fault_before_route_callback"
                ],
                "active_clear_before_cpu_owned_publish":
                    dma_route_concurrency[
                        "active_clear_before_cpu_owned_publish"
                    ],
                "unique_boot_local_route_instance_id": dma_route_policy[
                    "unique_boot_local_route_instance_id"
                ],
                "unique_per_route_operation_id": dma_route_policy[
                    "unique_per_route_operation_id"
                ],
                "arm64_model_checks": dma_route_arm64["checks"],
                "arm64_matches_native": dma_route_arm64[
                    "same_output_as_native"
                ],
                "physical_backend": dma_route_policy["physical_backend"],
            },
            "ufs_dma_map_candidate": {
                "model_tests_passed": components[
                    "ufs_dma_map_model_tests"
                ]["passed"],
                "windows": dma_map_translation["windows"],
                "static_dt_translation_model_proven": dma_map_translation[
                    "static_dt_translation_model_proven"
                ],
                "runtime_dma_range_entries_proven": dma_map_translation[
                    "runtime_dma_range_entries_proven"
                ],
                "raw_dma_equals_cpu_pa_proven": dma_map_translation[
                    "raw_dma_equals_cpu_pa_proven"
                ],
                "forward_and_inverse_translation_proven":
                    dma_map_translation[
                        "forward_and_inverse_translation_proven"
                    ],
                "direct_route_receipt_issuable": dma_map_translation[
                    "direct_route_receipt_issuable"
                ],
                "receipt_scope": dma_map_translation["receipt_scope"],
                "swiotlb_pool_present": dma_map_bounce[
                    "swiotlb_pool_present"
                ],
                "swiotlb_pool_active": dma_map_bounce[
                    "swiotlb_pool_active"
                ],
                "swiotlb_force_bounce": dma_map_bounce[
                    "swiotlb_force_bounce"
                ],
                "sample_no_swiotlb": dma_map_bounce[
                    "sample_no_swiotlb"
                ],
                "sample_segments": dma_map_bounce["sample_segments"],
                "bounded_window_segments": dma_map_bounce[
                    "bounded_window_segments"
                ],
                "observed_direct_route_proven": dma_map_bounce[
                    "observed_direct_route_proven"
                ],
                "global_bounce_disposition_proven": dma_map_bounce[
                    "global_bounce_disposition_proven"
                ],
                "bounce_disposition": dma_map_bounce["disposition"],
                "physical_backend": "disabled",
            },
            "ufs_resource_ownership": {
                "model_tests_passed": components[
                    "ufs_resource_ownership_tests"
                ]["passed"],
                "mmio_resources": len(resource_declarations["mmio"]),
                "clocks": len(resource_declarations["clocks"]),
                "resets": len(resource_declarations["resets"]),
                "interrupts": len(resource_declarations["interrupts"]),
                "clock_hw_voter": resource_declarations[
                    "clock_hw_voter"
                ],
                "captured_bl31_static_dispatch": resource_firmware[
                    "static_service_dispatch_proven"
                ],
                "runtime_effect_contract_proven": resource_firmware[
                    "runtime_effect_contract_proven"
                ],
                "receipt_issuable": resource_receipt[
                    "receipt_issuable"
                ],
                "blockers": resource_receipt["blockers"],
                "callbacks": {
                    "mmio": resource_authorization["mmio_callbacks"],
                    "smc": resource_authorization["smc_callbacks"],
                    "dma": resource_authorization["dma_callbacks"],
                    "ufs": resource_authorization["ufs_commands"],
                    "interrupt_reconfiguration": resource_authorization[
                        "interrupt_reconfiguration_callbacks"
                    ],
                },
                "physical_backend": "disabled",
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
        "runtime_evidence": sha256(runtime_evidence),
        "firmware_evidence": sha256(firmware_evidence),
        "prdt_evidence": sha256(prdt_evidence),
        "prdt_v3_evidence": sha256(prdt_v3_evidence),
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
            "ufs_resource_ownership_receipt": (
                "implemented fail-closed; exact MMIO/clock/reset/IRQ/PHY/"
                "regulator manifest passes, but runtime ownership receipt is denied"
            ),
            "ufs_dma_or_iommu_route": (
                "validated for the observed Linux UFS workload: live 64-GiB "
                "identity map, raw DMA equals PA, forward/inverse translation, "
                "and no SWIOTLB segment observed"
            ),
            "ufs_dma_route_contract": (
                "direct-route receipt is evidence-backed for the observed "
                "Linux workload; global future bounce behavior, XNU cache "
                "ownership and firmware/resource ownership remain unverified"
            ),
            "ufs_activation_lease_provider": (
                "implemented fail-closed; no physical lease available"
            ),
            "ufs_noncoherent_cache_contract": (
                "implemented fail-closed; no physical lease or cache callbacks"
            ),
            "ufs_xnu_cache_backend": (
                "generic ARM64 PoC primitives audited; MT6897 outer/system-cache "
                "reachability and ownership remain unverified"
            ),
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
        "scope": (
            "pinned DT/runtime/live-PRDT evidence, host sanitizers and local "
            "ARM64/QEMU models only"
        ),
    }
    if failure is not None:
        report["failure"] = failure
    (output / "result.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if passed else 1)


if __name__ == "__main__":
    main()
