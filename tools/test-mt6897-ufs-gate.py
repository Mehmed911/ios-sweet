#!/usr/bin/env python3
"""Test the MT6897 UFS activation gate against pinned local evidence only.

The output directory is published only after every evidence, native sanitizer,
and freestanding AArch64 check succeeds. Existing output is never overwritten.
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path


REPORT_VERSION = 1
GATE_API_VERSION = 2
FDT_SHA256 = "9c49589f70044127be8941a9ea5537977f440ccd5ac15cfd24e120c8a1181d29"
EXPECTED_BLOCKERS = [
    "firmware_effect_contract",
    "resource_ownership",
    "cache_maintenance_ownership",
    "direct_address_translation",
    "bounce_disposition",
]
EXPECTED_BLOCKER_MASK = (
    (1 << 1) |  # MT6897_UFS_E_FIRMWARE_EFFECT_CONTRACT
    (1 << 2) |  # MT6897_UFS_E_RESOURCE_OWNERSHIP
    (1 << 3) |  # MT6897_UFS_E_CACHE_MAINTENANCE_OWNERSHIP
    (1 << 10) |  # MT6897_UFS_E_DIRECT_ADDRESS_TRANSLATION
    (1 << 48)  # MT6897_UFS_BLOCK_BOUNCE_DISPOSITION
)
PINNED_REPORTS = {
    "runtime": {
        "path": Path("research/mt6897-dma-ownership/live-20261101-v2/result.json"),
        "sha256": "71236c08c0354ff0733d44a64e505d117dfd4594e370bedd81fad3ec93d1bf4d",
    },
    "firmware": {
        "path": Path("research/mt6897-firmware-live/20261101-v1/ufs-sip-audit-v2.json"),
        "sha256": "65e4a5cdd2085c2e2bb48ad9829109f8e39b7a260669074ab59427419b5d110c",
    },
    "prdt": {
        "path": Path("research/mt6897-dma-ownership/prdt-interpretation-20261101-v1/interpretation.json"),
        "sha256": "1e4c735d316004c83f9db71538186357112c7567daecd12be52ba24e74ea4018",
    },
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha256_bytes(raw):
    return hashlib.sha256(raw).hexdigest()


def sha256_file(path):
    return sha256_bytes(path.read_bytes())


def mapping(value, name):
    require(isinstance(value, dict), name + " is not an object")
    return value


def exact_path(left, right):
    return os.path.normcase(str(left)) == os.path.normcase(str(right))


def load_pinned_report(repo, supplied, label):
    pin = PINNED_REPORTS[label]
    expected = (repo / pin["path"]).resolve(strict=True)
    actual = supplied.resolve(strict=True)
    require(exact_path(actual, expected), label + " evidence is not the pinned saved report")
    raw = actual.read_bytes()
    digest = sha256_bytes(raw)
    require(digest == pin["sha256"], label + " evidence hash differs")
    try:
        report = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(label + " evidence is not valid UTF-8 JSON") from error
    mapping(report, label + " evidence")
    return report, {
        "path": str(pin["path"]).replace("\\", "/"),
        "bytes": len(raw),
        "sha256": digest,
    }


def validate_runtime(report):
    require(report.get("report_version") == 2, "unsupported runtime evidence version")
    require(report.get("audit_passed") is True, "runtime evidence audit did not pass")
    require(report.get("target") == {"device": "duchamp", "soc": "mt6897"},
            "runtime evidence target differs")

    masks = mapping(report.get("dma_masks"), "runtime dma_masks")
    require(masks.get("effective_streaming_mask") == "0xffffffffffffffff" and
            masks.get("effective_streaming_mask_bits") == 64,
            "runtime streaming DMA mask differs")
    require(masks.get("effective_coherent_mask") == "0xffffffffffffffff" and
            masks.get("effective_coherent_mask_bits") == 64,
            "runtime coherent DMA mask differs")
    require(masks.get("bus_dma_limit") == "0x0000000fffffffff" and
            masks.get("bus_dma_limit_bits") == 36,
            "runtime bus DMA limit differs")
    require(masks.get("exact_masks_proven") is True and
            masks.get("dma_coherent") is False and
            masks.get("dma_range_map_present") is True,
            "runtime DMA classification differs")

    route = mapping(report.get("iommu_route"), "runtime iommu_route")
    expected_false = (
        "dt_iommus_present",
        "dt_iommu_map_present",
        "runtime_dma_ops_present",
        "runtime_device_dma_ops_present",
        "runtime_iommu_private_present",
        "runtime_iommu_group_present",
        "runtime_iommu_fwspec_present",
        "runtime_iommu_domain_present",
        "swiotlb_transfer_observed",
        "physical_iommu_bypass_verified",
    )
    for field in expected_false:
        require(route.get(field) is False, "runtime route unexpectedly promoted: " + field)
    require(route.get("runtime_dma_ops_state_observed") is True and
            route.get("runtime_iommu_fwspec_state_observed") is True and
            route.get("runtime_iommu_domain_state_observed") is True and
            route.get("linux_iommu_attachment_absent_at_observation") is True,
            "runtime route observation is incomplete")
    require(route.get("linux_dma_api_path") == "generic dma-direct",
            "runtime Linux DMA path differs")
    require(route.get("device_swiotlb_pool_present") is True,
            "runtime SWIOTLB pool observation differs")

    ownership = mapping(report.get("firmware_ownership"), "runtime firmware_ownership")
    for field in (
        "runtime_smc_execution_observed",
        "runtime_physical_effect_observed",
        "exclusive_linux_ownership_proven",
        "exclusive_firmware_ownership_proven",
    ):
        require(ownership.get(field) is False,
                "runtime ownership unexpectedly promoted: " + field)

    verdict = mapping(report.get("verdict"), "runtime verdict")
    require(verdict.get("physical_xnu_ufs_ready") is False and
            verdict.get("physical_backend_enabled") is False,
            "runtime evidence unexpectedly authorizes physical UFS")
    not_proven = verdict.get("not_proven")
    require(isinstance(not_proven, list), "runtime not_proven is not a list")
    for text in (
        "whether any UFS transfer uses SWIOTLB or another bounce path",
        "physical DMA identity, firewall permissions or secure-world translation",
        "cache-maintenance ownership and correctness for a non-coherent device",
        "runtime SMC effects or safe physical UFS access from XNU",
    ):
        require(text in not_proven, "runtime evidence lost blocker: " + text)

    safety = mapping(report.get("safety"), "runtime safety")
    require(safety.get("audit_execution_offline") is True and
            safety.get("adb_access_by_this_tool") is False,
            "runtime audit safety differs")
    for field in (
        "partition_access",
        "boot_partition_modified",
        "storage_command_by_probe",
        "dma_mapping_by_probe",
        "iommu_mapping_or_attachment_by_probe",
        "firmware_execution_by_probe",
        "smc_execution_by_probe",
        "mmio_access_by_probe",
    ):
        require(safety.get(field) is False, "unsafe runtime evidence action: " + field)

    return {
        "streaming_dma_mask_bits": 64,
        "coherent_dma_mask_bits": 64,
        "bus_dma_limit_bits": 36,
        "linux_dma_api_path": "generic dma-direct",
        "linux_iommu_attached": False,
        "device_swiotlb_pool_present": True,
        "swiotlb_transfer_observed": False,
        "physical_dma_bypass_verified": False,
        "physical_xnu_ufs_ready": False,
    }


def validate_firmware(report):
    require(report.get("report_version") == 1, "unsupported firmware evidence version")
    require(report.get("passed") is True, "firmware evidence did not pass")
    atf = mapping(report.get("atf"), "firmware atf")
    atf_sha256 = atf.get("sha256")
    require(isinstance(atf_sha256, str) and
            re.fullmatch(r"[0-9a-f]{64}", atf_sha256) is not None,
            "firmware ATF receipt is invalid")
    service = mapping(report.get("service"), "firmware service")
    require(service.get("name") == "MTK_SIP_KERNEL_UFS_CONTROL" and
            service.get("fast64_function_id") == "0xc2000276",
            "firmware UFS service differs")
    selectors = mapping(report.get("selectors"), "firmware selectors")
    require(mapping(selectors.get("refclk"), "refclk selector").get("value") == 8,
            "firmware REFCLK selector differs")
    require(mapping(selectors.get("mtcmos"), "mtcmos selector").get("value") == 512,
            "firmware MTCMOS selector differs")
    require(mapping(selectors.get("mcq"), "mcq selector").get("value") == 1024,
            "firmware MCQ selector differs")

    claims = mapping(report.get("claims"), "firmware claims")
    for field in (
        "captured_bl31_ufs_service_descriptor_verified",
        "saved_client_function_id_dispatch_verified",
        "saved_refclk_selector_dispatch_verified",
        "saved_mtcmos_selector_dispatch_verified",
        "saved_mcq_selector_dispatch_verified",
        "mtcmos_body_present_in_captured_binary",
        "known_selector_common_zero_return_present",
        "captured_bl31_mtcmos_mmio_paths_verified",
    ):
        require(claims.get(field) is True, "firmware static claim differs: " + field)
    for field in (
        "zero_reply_proves_physical_effect",
        "direct_xnu_mtcmos_mmio_authorized",
        "runtime_smc_return_effect_contract_verified",
        "physical_resource_ownership_verified",
        "xnu_physical_ufs_ready",
    ):
        require(claims.get(field) is False,
                "firmware evidence unexpectedly promoted: " + field)

    mtcmos = mapping(report.get("mtcmos_mmio"), "firmware mtcmos_mmio")
    require(mtcmos.get("safe_xnu_direct_readback_authorized") is False,
            "firmware evidence authorized direct XNU readback")
    safety = mapping(report.get("safety"), "firmware safety")
    require(safety.get("local_file_only") is True, "firmware audit was not local-only")
    for field in (
        "firmware_executed",
        "smc_execution",
        "mmio_access",
        "adb_access_by_this_tool",
        "phone_write",
        "partition_write",
        "fastboot_access",
    ):
        require(safety.get(field) is False, "unsafe firmware evidence action: " + field)

    return {
        "atf_sha256": atf_sha256,
        "function_id": "0xc2000276",
        "common_zero_return_present": True,
        "runtime_effect_contract_verified": False,
        "physical_resource_ownership_verified": False,
        "safe_xnu_direct_readback_authorized": False,
        "physical_xnu_ufs_ready": False,
    }


def validate_prdt(report):
    require(report.get("report_version") == 1, "unsupported PRDT evidence version")
    require(report.get("verdict") == "validated-limited-prdt-evidence",
            "PRDT evidence verdict differs")
    proven = mapping(report.get("proven"), "PRDT proven")
    for field in (
        "all_observed_extents_within_36bit_bus_limit",
        "dma_direct_no_iommu_contract_pinned_at_snapshots",
        "inverse_dma_translation_returns_original_scatterlist_phys",
        "no_swiotlb_observed_in_sample",
        "observer_cleanup_verified",
        "prdt_matches_mapped_scatterlist",
    ):
        require(proven.get(field) is True, "PRDT proven claim differs: " + field)
    not_proven = mapping(report.get("not_proven"), "PRDT not_proven")
    for field in (
        "live_dma_range_map_is_identity",
        "physical_firewall_bypass",
        "raw_dma_address_equals_cpu_physical",
        "read_workload_caused_every_observed_command",
        "xnu_cache_ownership",
        "xnu_gic_or_ufs_ownership",
        "xnu_physical_ufs_ready",
    ):
        require(not_proven.get(field) is False,
                "PRDT evidence unexpectedly promoted: " + field)
    observation = mapping(report.get("observation"), "PRDT observation")
    require(observation.get("bus_dma_limit") == (1 << 36) - 1 and
            observation.get("commands_delta") == 371 and
            observation.get("segments_delta") == 17437,
            "PRDT observation counters differ")
    safety = mapping(report.get("safety"), "PRDT safety")
    require(safety.get("local_file_only") is True, "PRDT interpretation was not local-only")
    for field in ("adb_access", "mmio_access", "partition_access", "phone_write", "smc_execution"):
        require(safety.get(field) is False, "unsafe PRDT evidence action: " + field)

    return {
        "commands_delta": 371,
        "segments_delta": 17437,
        "no_swiotlb_observed_in_sample": True,
        "bounce_disposition_proven": False,
        "raw_dma_address_equals_cpu_physical": False,
        "live_dma_range_map_is_identity": False,
        "physical_firewall_bypass": False,
        "xnu_cache_ownership": False,
        "xnu_resource_ownership": False,
        "xnu_physical_ufs_ready": False,
    }


def parse_gate_api(header_text):
    version = re.search(
        r"^\s*#define\s+MT6897_UFS_GATE_EVIDENCE_VERSION\s+UINT32_C\((\d+)\)",
        header_text,
        re.MULTILINE,
    )
    require(version is not None, "gate evidence version definition is missing")
    require(int(version.group(1)) == GATE_API_VERSION,
            "gate API version 2 is required")
    helper = re.search(
        r"mt6897_ufs_gate_duchamp_known_evidence\s*\(\s*uint64_t\s+boot_generation\s*\)",
        header_text,
        re.MULTILINE,
    )
    require(helper is not None,
            "gate API v2 helper must take uint64_t boot_generation")
    return GATE_API_VERSION


def receipt_extractor_source():
    return r'''#include "mt6897_ufs_gate.h"
#include <stdint.h>
#include <stdio.h>

static void print_hash(const uint8_t value[32])
{
    unsigned index;
    for (index = 0; index < 32; ++index) {
        (void)printf("%02x", value[index]);
    }
}

int main(void)
{
    struct mt6897_ufs_gate_evidence evidence =
        mt6897_ufs_gate_duchamp_known_evidence(UINT64_C(0x202611030001));

    (void)printf("fdt="); print_hash(evidence.fdt_sha256);
    (void)printf(" firmware="); print_hash(evidence.firmware_sha256);
    (void)printf(" firmware_audit=");
    print_hash(evidence.firmware_audit_sha256);
    (void)printf(" runtime="); print_hash(evidence.runtime_dma_report_sha256);
    (void)printf(" prdt="); print_hash(evidence.prdt_report_sha256);
    (void)printf(" hci_base=0x%llx hci_size=0x%llx"
        " phy_base=0x%llx phy_size=0x%llx"
        " dma_size=0x%llx dma_limit=0x%llx dma_bits=%u"
        " service=0x%x refclk=%u mtcmos=%u mcq=%u\n",
        (unsigned long long)evidence.ufs_hci_base,
        (unsigned long long)evidence.ufs_hci_size,
        (unsigned long long)evidence.ufs_phy_base,
        (unsigned long long)evidence.ufs_phy_size,
        (unsigned long long)evidence.dma_size,
        (unsigned long long)evidence.dma_limit,
        evidence.dma_address_bits, evidence.firmware_service_id,
        evidence.firmware_refclk_selector,
        evidence.firmware_mtcmos_selector,
        evidence.firmware_mcq_selector);
    return 0;
}
'''


def parse_compiled_receipts(stdout):
    lines = [line.strip() for line in stdout.splitlines() if line.strip()]
    require(len(lines) == 1, "compiled receipt extractor output differs")
    pairs = re.findall(r"\b([a-z_]+)=([0-9a-fx]+)\b", lines[0])
    values = {}
    for key, value in pairs:
        require(key not in values, "duplicate compiled receipt: " + key)
        values[key] = value
    required = {
        "fdt", "firmware", "firmware_audit", "runtime", "prdt",
        "hci_base", "hci_size", "phy_base", "phy_size", "dma_size",
        "dma_limit", "dma_bits", "service", "refclk", "mtcmos", "mcq",
    }
    require(set(values) == required, "compiled receipt fields differ")
    for name in ("fdt", "firmware", "firmware_audit", "runtime", "prdt"):
        require(re.fullmatch(r"[0-9a-f]{64}", values[name]) is not None,
                "compiled " + name + " receipt is invalid")
    return values


def integer_value(value, name):
    try:
        return int(value, 0)
    except (TypeError, ValueError) as error:
        raise ValueError("invalid integer in current-evidence line: " + name) from error


def zero_value(value, name):
    normalized = value.lower()
    if normalized not in ("false", "no"):
        try:
            require(int(normalized, 0) == 0,
                    name + " was not zero/false in current-evidence line")
        except ValueError as error:
            raise ValueError(
                name + " was not zero/false in current-evidence line") from error
    return 0


def keyed_value(fields, aliases, name, required=True):
    matches = [fields[alias] for alias in aliases if alias in fields]
    if not matches:
        if required:
            raise ValueError("current-evidence line is missing " + name)
        return None
    require(len(matches) == 1,
            "current-evidence line has ambiguous " + name)
    return matches[0]


def parse_current_evidence_line(stdout):
    candidates = [
        line.strip() for line in stdout.splitlines()
        if "duchamp" in line.lower() and "boot_generation=" in line.lower() and
        ("blockers=" in line.lower() or "blocker_mask=" in line.lower())
    ]
    require(len(candidates) == 1,
            "expected one machine-readable current Duchamp denial line")
    line = candidates[0]
    pairs = re.findall(
        r"\b([A-Za-z][A-Za-z0-9_-]*)="
        r"(0[xX][0-9A-Fa-f]+|-?[0-9]+|[A-Za-z][A-Za-z0-9_-]*)",
        line,
    )
    fields = {}
    for key, value in pairs:
        normalized = key.lower().replace("-", "_")
        require(normalized not in fields,
                "current-evidence line has duplicate field: " + normalized)
        fields[normalized] = value
    decision = keyed_value(fields, ("decision",), "decision", False)
    result = keyed_value(fields, ("result",), "result", False)
    require("denied" in line.lower() or
            (decision is not None and decision.lower() == "denied") or
            (result is not None and integer_value(result, "result") == -1),
            "current Duchamp line does not report denial")

    generation_text = keyed_value(
        fields, ("boot_generation", "generation"), "boot_generation")
    generation = integer_value(generation_text, "boot_generation")
    require(generation > 0, "current evidence used a zero boot generation")

    blockers_text = keyed_value(
        fields, ("blockers", "blocker_mask"), "blockers")
    blockers = integer_value(blockers_text, "blockers")
    require(blockers == EXPECTED_BLOCKER_MASK,
            "current Duchamp blocker mask differs")

    verifier_text = keyed_value(
        fields, ("verifier", "verifier_calls"), "verifier calls")
    verifier_calls = zero_value(verifier_text, "verifier calls")
    mmio_text = keyed_value(
        fields, ("mmio", "mmio_calls", "mmio_access"), "MMIO calls")
    smc_text = keyed_value(
        fields, ("smc", "smc_calls", "smc_execution"), "SMC calls")
    dma_text = keyed_value(
        fields, ("dma", "dma_calls", "dma_access"), "DMA calls")
    hardware_text = keyed_value(
        fields, ("hardware", "hardware_calls", "hardware_access"), "hardware calls")
    phone_text = keyed_value(
        fields, ("phone", "phone_access"), "phone access")

    mmio_calls = zero_value(mmio_text, "MMIO calls")
    smc_calls = zero_value(smc_text, "SMC calls")
    dma_calls = zero_value(dma_text, "DMA calls")
    hardware_calls = zero_value(hardware_text, "hardware calls")
    phone_access = bool(zero_value(phone_text, "phone access"))
    require(hardware_calls == 0 and mmio_calls == 0 and smc_calls == 0 and
            dma_calls == 0 and phone_access is False,
            "current Duchamp gate test reported a side effect")

    return {
        "line": line,
        "boot_generation": generation,
        "blocker_mask": "0x%016x" % blockers,
        "verifier_calls": verifier_calls,
        "hardware_calls": hardware_calls,
        "hardware_access": bool(hardware_calls),
        "mmio_calls": mmio_calls,
        "mmio_access": bool(mmio_calls),
        "smc_calls": smc_calls,
        "smc_execution": bool(smc_calls),
        "dma_calls": dma_calls,
        "dma_access": bool(dma_calls),
        "phone_access": phone_access,
    }


def run_command(command, commands, directory, name, env=None):
    result = subprocess.run(
        command,
        cwd=directory,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=120,
        check=False,
    )
    (directory / (name + ".stdout.txt")).write_text(result.stdout, encoding="utf-8")
    (directory / (name + ".stderr.txt")).write_text(result.stderr, encoding="utf-8")
    commands.append({
        "name": name,
        "command": [str(item) for item in command],
        "returncode": result.returncode,
    })
    if result.returncode != 0:
        raise RuntimeError(name + " failed with exit code " + str(result.returncode))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--fdt", type=Path, required=True)
    parser.add_argument("--runtime-evidence", type=Path, required=True)
    parser.add_argument("--firmware-evidence", type=Path, required=True)
    parser.add_argument("--prdt-evidence", type=Path, required=True)
    args = parser.parse_args()

    output = args.output.resolve()
    if output.exists():
        parser.error("preserve existing output")
    repo = Path(__file__).resolve().parent.parent
    drivers = repo / "duchamp/drivers"
    gate_source = drivers / "mt6897_ufs_gate.c"
    gate_header = drivers / "mt6897_ufs_gate.h"
    test_source = drivers / "test_mt6897_ufs_gate.c"
    concurrency_source = drivers / "test_mt6897_ufs_gate_concurrency.c"
    provider_source = drivers / "mt6897_ufs_provider.c"
    provider_header = drivers / "mt6897_ufs_provider.h"
    provider_test_source = drivers / "test_mt6897_ufs_provider.c"
    provider_concurrency_source = (
        drivers / "test_mt6897_ufs_provider_concurrency.c"
    )
    script = Path(__file__).resolve()
    model_runtime = drivers / "test_mt6897_model_runtime.c"
    model_start = drivers / "test_mt6897_model_start.S"
    sources = [
        gate_source, gate_header, test_source, concurrency_source,
        provider_source, provider_header, provider_test_source,
        provider_concurrency_source,
        model_runtime, model_start, script
    ]
    for source in sources:
        require(source.is_file(), "missing gate test input: " + str(source))

    fdt = args.fdt.resolve(strict=True)
    fdt_raw = fdt.read_bytes()
    fdt_digest = sha256_bytes(fdt_raw)
    require(fdt_digest == FDT_SHA256, "saved Duchamp FDT receipt differs")
    fdt_receipt = {
        "path": str(fdt),
        "bytes": len(fdt_raw),
        "sha256": fdt_digest,
    }
    runtime_report, runtime_receipt = load_pinned_report(
        repo, args.runtime_evidence, "runtime")
    firmware_report, firmware_receipt = load_pinned_report(
        repo, args.firmware_evidence, "firmware")
    prdt_report, prdt_receipt = load_pinned_report(
        repo, args.prdt_evidence, "prdt")
    evidence = {
        "runtime": validate_runtime(runtime_report),
        "firmware": validate_firmware(firmware_report),
        "prdt": validate_prdt(prdt_report),
    }
    gate_api_version = parse_gate_api(gate_header.read_text(encoding="utf-8"))

    source_before = {
        str(path.relative_to(repo)).replace("\\", "/"): sha256_file(path)
        for path in sources
    }
    input_before = {
        "fdt": fdt_receipt["sha256"],
        "runtime": runtime_receipt["sha256"],
        "firmware": firmware_receipt["sha256"],
        "prdt": prdt_receipt["sha256"],
    }

    clang = shutil.which("clang")
    llvm_nm = shutil.which("llvm-nm")
    qemu = shutil.which("qemu-system-aarch64")
    require(clang is not None, "clang is required")
    require(llvm_nm is not None, "llvm-nm is required")
    require(qemu is not None, "qemu-system-aarch64 is required")

    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(
        prefix="." + output.name + ".tmp-", dir=str(output.parent)))
    published = False
    try:
        commands = []
        extractor_source = temporary / "extract-mt6897-ufs-receipts.c"
        extractor_source.write_text(receipt_extractor_source(), encoding="utf-8")
        extractor = temporary / "extract-mt6897-ufs-receipts"
        extractor_compile = [
            clang,
            "-std=c11",
            "-O2",
            "-Wall",
            "-Wextra",
            "-Werror",
            "-I",
            str(drivers),
            str(gate_source),
            str(extractor_source),
            "-o",
            str(extractor),
        ]
        run_command(extractor_compile, commands, temporary, "receipt-compile")
        compiled_receipts = parse_compiled_receipts(run_command(
            [str(extractor)], commands, temporary, "receipt-extract").stdout)
        require(compiled_receipts["fdt"] == fdt_receipt["sha256"],
                "compiled gate FDT receipt differs from supplied FDT")
        require(compiled_receipts["firmware"] ==
                evidence["firmware"]["atf_sha256"],
                "compiled gate firmware receipt differs from firmware report")
        require(compiled_receipts["firmware_audit"] ==
                firmware_receipt["sha256"],
                "compiled gate firmware-audit receipt differs")
        require(compiled_receipts["runtime"] == runtime_receipt["sha256"],
                "compiled gate runtime-DMA receipt differs")
        require(compiled_receipts["prdt"] == prdt_receipt["sha256"],
                "compiled gate PRDT receipt differs")
        expected_resources = {
            "hci_base": "0x112b0000",
            "hci_size": "0x3000",
            "phy_base": "0x112a0000",
            "phy_size": "0x10000",
            "dma_size": "0x1000000000",
            "dma_limit": "0xfffffffff",
            "dma_bits": "36",
            "service": evidence["firmware"]["function_id"],
            "refclk": "8",
            "mtcmos": "512",
            "mcq": "1024",
        }
        for field, expected_value in expected_resources.items():
            require(compiled_receipts[field] == expected_value,
                    "compiled gate resource differs: " + field)

        native = temporary / "mt6897-ufs-gate-test"
        native_compile = [
            clang,
            "-std=c11",
            "-O1",
            "-g",
            "-Wall",
            "-Wextra",
            "-Werror",
            "-fsanitize=address,undefined",
            "-fno-sanitize-recover=all",
            "-fno-omit-frame-pointer",
            str(gate_source),
            str(test_source),
            "-o",
            str(native),
        ]
        run_command(native_compile, commands, temporary, "native-compile")
        sanitizer_env = os.environ.copy()
        sanitizer_env["ASAN_OPTIONS"] = "halt_on_error=1"
        sanitizer_env["UBSAN_OPTIONS"] = "halt_on_error=1:print_stacktrace=1"
        native_result = run_command(
            [str(native)], commands, temporary, "native-test", sanitizer_env)
        summary = re.search(
            r"(?m)^(\d+) MT6897 UFS lease-gate checks passed; "
            r"no MMIO/SMC/DMA calls\s*$",
            native_result.stdout,
        )
        require(summary is not None, "unexpected native gate-test summary")
        native_checks = int(summary.group(1))
        require(native_checks > 0, "native gate test reported no checks")
        current = parse_current_evidence_line(native_result.stdout)
        output_lines = [
            line for line in native_result.stdout.splitlines() if line.strip()
        ]
        require(len(output_lines) == 2,
                "unexpected extra native gate-test output")

        concurrency = temporary / "mt6897-ufs-gate-concurrency-test"
        concurrency_compile = [
            clang,
            "-std=c11",
            "-O1",
            "-g",
            "-Wall",
            "-Wextra",
            "-Werror",
            "-fsanitize=address,undefined",
            "-fno-sanitize-recover=all",
            "-fno-omit-frame-pointer",
            "-pthread",
            "-DMT6897_UFS_GATE_TEST_HOOKS",
            str(gate_source),
            str(concurrency_source),
            "-o",
            str(concurrency),
        ]
        run_command(concurrency_compile, commands, temporary,
                    "concurrency-compile")
        concurrency_result = run_command(
            [str(concurrency)], commands, temporary, "concurrency-test",
            sanitizer_env)
        concurrency_summary = re.search(
            r"(?m)^(\d+) MT6897 UFS concurrent authorization checks passed; "
            r"verifier_calls=1 no MMIO/SMC/DMA calls\s*$",
            concurrency_result.stdout,
        )
        require(concurrency_summary is not None,
                "unexpected concurrent gate-test summary")
        concurrency_checks = int(concurrency_summary.group(1))
        require(concurrency_checks > 0,
                "concurrent gate test reported no checks")

        provider_native = temporary / "mt6897-ufs-provider-test"
        provider_native_compile = [
            clang,
            "-std=c11",
            "-O1",
            "-g",
            "-Wall",
            "-Wextra",
            "-Werror",
            "-fsanitize=address,undefined",
            "-fno-sanitize-recover=all",
            "-fno-omit-frame-pointer",
            str(gate_source),
            str(provider_source),
            str(provider_test_source),
            "-o",
            str(provider_native),
        ]
        run_command(provider_native_compile, commands, temporary,
                    "provider-native-compile")
        provider_native_result = run_command(
            [str(provider_native)], commands, temporary,
            "provider-native-test", sanitizer_env)
        provider_summary = re.search(
            r"(?m)^(\d+) MT6897 UFS lease-provider checks passed; "
            r"model_dispatches=(\d+) denied_dispatches=(\d+)\s*$",
            provider_native_result.stdout,
        )
        require(provider_summary is not None,
                "unexpected native provider-test summary")
        provider_checks = int(provider_summary.group(1))
        provider_model_dispatches = int(provider_summary.group(2))
        provider_denied_dispatches = int(provider_summary.group(3))
        require(provider_checks > 0, "provider test reported no checks")
        require(provider_model_dispatches == 6,
                "provider model did not cover all operation classes")
        require(provider_denied_dispatches == 0,
                "denied provider operation reached a callback")

        provider_concurrency = (
            temporary / "mt6897-ufs-provider-concurrency-test"
        )
        provider_concurrency_compile = [
            clang,
            "-std=c11",
            "-O1",
            "-g",
            "-Wall",
            "-Wextra",
            "-Werror",
            "-fsanitize=address,undefined",
            "-fno-sanitize-recover=all",
            "-fno-omit-frame-pointer",
            "-pthread",
            "-DMT6897_UFS_PROVIDER_TEST_HOOKS",
            str(gate_source),
            str(provider_source),
            str(provider_concurrency_source),
            "-o",
            str(provider_concurrency),
        ]
        run_command(provider_concurrency_compile, commands, temporary,
                    "provider-concurrency-compile")
        provider_concurrency_result = run_command(
            [str(provider_concurrency)], commands, temporary,
            "provider-concurrency-test", sanitizer_env)
        provider_concurrency_summary = re.search(
            r"(?m)^(\d+) MT6897 UFS concurrent provider checks passed; "
            r"fault_before_dispatch=1 dispatches=0\s*$",
            provider_concurrency_result.stdout,
        )
        require(provider_concurrency_summary is not None,
                "unexpected concurrent provider-test summary")
        provider_concurrency_checks = int(
            provider_concurrency_summary.group(1)
        )
        require(provider_concurrency_checks > 0,
                "concurrent provider test reported no checks")

        arm64_object = temporary / "mt6897_ufs_gate.arm64.o"
        arm64_compile = [
            clang,
            "-target",
            "aarch64-none-elf",
            "-std=c11",
            "-O2",
            "-ffreestanding",
            "-fno-builtin",
            "-mgeneral-regs-only",
            "-Wall",
            "-Wextra",
            "-Werror",
            "-c",
            str(gate_source),
            "-o",
            str(arm64_object),
        ]
        run_command(arm64_compile, commands, temporary, "arm64-compile")
        imports = run_command(
            [llvm_nm, "--undefined-only", str(arm64_object)],
            commands,
            temporary,
            "arm64-imports",
        ).stdout.strip()
        require(imports == "", "unexpected freestanding imports: " + imports)

        provider_arm64_object = temporary / "mt6897_ufs_provider.arm64.o"
        provider_arm64_compile = [
            clang,
            "-target",
            "aarch64-none-elf",
            "-std=c11",
            "-O2",
            "-ffreestanding",
            "-fno-builtin",
            "-mgeneral-regs-only",
            "-Wall",
            "-Wextra",
            "-Werror",
            "-c",
            str(provider_source),
            "-o",
            str(provider_arm64_object),
        ]
        run_command(provider_arm64_compile, commands, temporary,
                    "provider-arm64-compile")
        provider_import_text = run_command(
            [llvm_nm, "--undefined-only", str(provider_arm64_object)],
            commands,
            temporary,
            "provider-arm64-imports",
        ).stdout
        provider_imports = sorted(
            line.split()[-1] for line in provider_import_text.splitlines()
            if line.split()
        )
        require(provider_imports == [
            "mt6897_ufs_gate_fault",
            "mt6897_ufs_gate_lease_check",
        ], "unexpected provider imports: " + ", ".join(provider_imports))

        linker = temporary / "model.ld"
        linker.write_text(
            "ENTRY(_start)\nSECTIONS { . = 0x40200000;\n"
            " .text : { *(.text.boot) *(.text*) }\n"
            " .rodata : { *(.rodata*) }\n"
            " .data : { *(.data*) }\n . = ALIGN(4096);\n"
            " .bss (NOLOAD) : { _bss_start = .; *(.bss*) *(COMMON) "
            ". = ALIGN(16); _bss_end = .; }\n"
            " . += 0x40000; _stack_top = .;\n}\n",
            encoding="utf-8",
        )
        arm64_elf = temporary / "mt6897-ufs-gate-model.arm64.elf"
        arm64_link = [
            clang,
            "-target", "aarch64-none-elf",
            "-std=c11",
            "-O2",
            "-ffreestanding",
            "-fno-builtin",
            "-mgeneral-regs-only",
            "-mstrict-align",
            "-Wall", "-Wextra", "-Werror",
            "-DMT6897_MODEL_FREESTANDING",
            "-nostdlib",
            "-fuse-ld=lld",
            "-Wl,-T," + str(linker),
            str(model_start),
            str(model_runtime),
            str(gate_source),
            str(test_source),
            "-o", str(arm64_elf),
        ]
        run_command(arm64_link, commands, temporary, "arm64-model-link")
        arm64_result = run_command([
            qemu,
            "-M", "virt",
            "-cpu", "cortex-a76",
            "-smp", "1",
            "-m", "64M",
            "-nographic",
            "-monitor", "none",
            "-serial", "stdio",
            "-nic", "none",
            "-semihosting-config", "enable=on,target=native",
            "-kernel", str(arm64_elf),
        ], commands, temporary, "arm64-model-test")
        require(native_result.stdout in arm64_result.stdout,
                "ARM64 model did not reproduce the native gate checks")
        require("MT6897 ARM64 MODEL PASS" in arm64_result.stdout,
                "ARM64 model did not report a pass")

        provider_arm64_elf = (
            temporary / "mt6897-ufs-provider-model.arm64.elf"
        )
        provider_arm64_link = [
            clang,
            "-target", "aarch64-none-elf",
            "-std=c11",
            "-O2",
            "-ffreestanding",
            "-fno-builtin",
            "-mgeneral-regs-only",
            "-mstrict-align",
            "-Wall", "-Wextra", "-Werror",
            "-DMT6897_MODEL_FREESTANDING",
            "-nostdlib",
            "-fuse-ld=lld",
            "-Wl,-T," + str(linker),
            str(model_start),
            str(model_runtime),
            str(gate_source),
            str(provider_source),
            str(provider_test_source),
            "-o", str(provider_arm64_elf),
        ]
        run_command(provider_arm64_link, commands, temporary,
                    "provider-arm64-model-link")
        provider_arm64_result = run_command([
            qemu,
            "-M", "virt",
            "-cpu", "cortex-a76",
            "-smp", "1",
            "-m", "64M",
            "-nographic",
            "-monitor", "none",
            "-serial", "stdio",
            "-nic", "none",
            "-semihosting-config", "enable=on,target=native",
            "-kernel", str(provider_arm64_elf),
        ], commands, temporary, "provider-arm64-model-test")
        require(provider_native_result.stdout in provider_arm64_result.stdout,
                "ARM64 model did not reproduce native provider checks")
        require("MT6897 ARM64 MODEL PASS" in provider_arm64_result.stdout,
                "ARM64 provider model did not report a pass")

        source_after = {
            str(path.relative_to(repo)).replace("\\", "/"): sha256_file(path)
            for path in sources
        }
        input_after = {
            "fdt": sha256_file(fdt),
            "runtime": sha256_file(args.runtime_evidence.resolve(strict=True)),
            "firmware": sha256_file(args.firmware_evidence.resolve(strict=True)),
            "prdt": sha256_file(args.prdt_evidence.resolve(strict=True)),
        }
        require(source_after == source_before, "gate sources changed during the test")
        require(input_after == input_before, "evidence changed during the test")

        result = {
            "report_version": REPORT_VERSION,
            "passed": True,
            "gate_api_version": gate_api_version,
            "evidence_bound": True,
            "input_receipts": {
                "fdt": fdt_receipt,
                "runtime": runtime_receipt,
                "firmware": firmware_receipt,
                "prdt": prdt_receipt,
            },
            "compiled_receipts": compiled_receipts,
            "validated_evidence": evidence,
            "current_duchamp_evidence": {
                "decision": "denied",
                "boot_generation": current["boot_generation"],
                "blockers": EXPECTED_BLOCKERS,
                "blocker_mask": current["blocker_mask"],
                "verifier_calls": current["verifier_calls"],
                "hardware_calls": current["hardware_calls"],
                "hardware_access": current["hardware_access"],
                "mmio_calls": current["mmio_calls"],
                "mmio_access": current["mmio_access"],
                "smc_calls": current["smc_calls"],
                "smc_execution": current["smc_execution"],
                "dma_calls": current["dma_calls"],
                "dma_access": current["dma_access"],
                "phone_access": current["phone_access"],
            },
            "native": {
                "checks": native_checks,
                "sanitizers": "ASan + UBSan",
                "current_evidence_line": current["line"],
            },
            "concurrency": {
                "checks": concurrency_checks,
                "sanitizers": "ASan + UBSan",
                "verifier_calls": 1,
                "simultaneous_second_authorization": "terminal fail-closed",
            },
            "provider": {
                "native_checks": provider_checks,
                "native_model_dispatches": provider_model_dispatches,
                "denied_dispatches": provider_denied_dispatches,
                "concurrency_checks": provider_concurrency_checks,
                "concurrent_fault_before_dispatch": "terminal fail-closed",
                "freestanding_arm64_compile": True,
                "arm64_checks": provider_checks,
                "arm64_matches_native": True,
                "arm64_object_sha256": sha256_file(provider_arm64_object),
                "arm64_elf_sha256": sha256_file(provider_arm64_elf),
                "physical_backend": "disabled",
            },
            "freestanding_arm64_compile": True,
            "arm64_undefined_imports": [],
            "arm64_object_sha256": sha256_file(arm64_object),
            "arm64_model": {
                "passed": True,
                "checks": native_checks,
                "same_output_as_native": True,
                "elf_sha256": sha256_file(arm64_elf),
                "scope": (
                    "actual ARM64 CPU execution under QEMU virt with MMU/cache "
                    "off and no MediaTek peripheral emulation"
                ),
            },
            "source_sha256": source_before,
            "sources_unchanged": True,
            "evidence_unchanged": True,
            "safety": {
                "local_files_only": True,
                "verifier_calls": 0,
                "hardware_calls": 0,
                "hardware_access": False,
                "mmio_calls": 0,
                "mmio_access": False,
                "smc_calls": 0,
                "smc_execution": False,
                "dma_calls": 0,
                "dma_access": False,
                "provider_denied_dispatches": provider_denied_dispatches,
                "phone_access": False,
                "adb_access": False,
                "fastboot_access": False,
                "network_access": False,
                "partition_access": False,
            },
            "scope": (
                "pinned saved-evidence validation, native sanitizer execution, "
                "freestanding AArch64 compilation, and ARM64 QEMU policy-model "
                "execution plus lease-guarded provider dispatch checks only; "
                "no physical UFS authorization"
            ),
        }
        (temporary / "commands.json").write_text(
            json.dumps(commands, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        (temporary / "result.json").write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        require(not output.exists(), "preserve existing output")
        temporary.rename(output)
        published = True
        print(json.dumps(result, indent=2, sort_keys=True))
    finally:
        if not published and temporary.exists():
            shutil.rmtree(temporary)


if __name__ == "__main__":
    main()
