#!/usr/bin/env python3
"""Combine pinned Duchamp evidence into a fail-closed phone-readiness report.

This tool reads existing local JSON reports only.  A successful exit means the
evidence is internally consistent; it does not authorize phone execution,
physical MMIO, DMA, UFS, fastboot, or a partition write.
"""

import argparse
import hashlib
import json
from pathlib import Path


FDT_SHA256 = "9c49589f70044127be8941a9ea5537977f440ccd5ac15cfd24e120c8a1181d29"
UFS_MODULE_SHA256 = (
    "7043e1109b4c356a914fdc92ffbe463c0c43cb27342f6ccce1517a2086b02493"
)
UFS_MODULE_BUILD_ID = "df7eecc22450fb6e6eceaaef4b3fe8ceb46b2a84"
UFS_HWIRQS = [200, 209, 210, 211, 212, 213, 214, 215, 216]
CANDIDATE_SHA256 = "a83f0792ccd883c19a8225641b4e96090fb08673375e71fe93123e0dafddfaa8"
CANDIDATE_BYTES = 64 * 1024 * 1024


def require(condition, message):
    if not condition:
        raise ValueError(message)


def value(mapping, *path):
    current = mapping
    for key in path:
        if not isinstance(current, dict) or key not in current:
            raise ValueError("missing evidence field: " + ".".join(path))
        current = current[key]
    return current


def validate_live(report):
    require(value(report, "report_version") == 1, "unsupported live report version")
    require(value(report, "result", "passed") is True, "live report did not pass")
    require(
        value(report, "fdt", "reference_sha256") == FDT_SHA256,
        "live report reference DTB differs",
    )
    require(
        value(report, "fdt", "critical_topology_matches_reference") is True,
        "live critical topology differs",
    )
    require(value(report, "fdt", "added_nodes") == [], "live FDT added nodes")
    require(value(report, "fdt", "removed_nodes") == [], "live FDT removed nodes")

    timer = value(report, "runtime", "timer")
    require(timer.get("android_runtime_delivery_observed") is True, "Android timer delivery missing")
    require(timer.get("xnu_phone_delivery_observed") is False, "unexpected XNU timer promotion")
    require(timer.get("clocksource") == "arch_sys_counter", "unexpected clocksource")
    require(timer.get("clockevent") == "arch_sys_timer", "unexpected clockevent")
    require(timer.get("gic_hwirq") == 27, "unexpected timer HWIRQ")
    require(isinstance(timer.get("total_delta"), int) and timer["total_delta"] > 0,
            "timer counter did not advance")

    ufs = value(report, "runtime", "ufs")
    require(ufs.get("android_runtime_delivery_observed") is True, "Android UFS delivery missing")
    require(ufs.get("xnu_phone_delivery_observed") is False, "unexpected XNU UFS promotion")
    require(ufs.get("driver") == "/sys/bus/platform/drivers/ufshcd-mtk",
            "unexpected UFS driver")
    require(ufs.get("expected_gic_hwirqs") == UFS_HWIRQS, "unexpected UFS HWIRQs")
    require(isinstance(ufs.get("total_delta"), int) and ufs["total_delta"] > 0,
            "UFS counters did not advance")
    module = value(ufs, "installed_module")
    saved_module = value(module, "saved_vendor_module")
    require(module.get("name") == "ufs_mediatek_mod" and module.get("state") == "Live",
            "installed UFS module identity differs")
    require(module.get("gnu_build_id") == UFS_MODULE_BUILD_ID,
            "installed UFS module build ID differs")
    require(saved_module.get("sha256") == UFS_MODULE_SHA256,
            "saved UFS module hash differs")
    require(saved_module.get("gnu_build_id") == UFS_MODULE_BUILD_ID,
            "saved UFS module build ID differs")
    require(saved_module.get("build_id_match_verified") is True,
            "installed/saved UFS build ID match missing")
    require(saved_module.get("source_commit_match_verified") is False,
            "unexpected UFS source-build promotion")
    require(module.get("local_source_commit_match_verified") is False,
            "unexpected local source-build promotion")

    firmware = value(report, "firmware")
    require(firmware.get("installed_scmi_identity_observed") is True,
            "installed SCMI identity missing")
    require(firmware.get("installed_ufs_client_binary_identity_verified") is True,
            "installed UFS client binary identity missing")
    for key in (
        "installed_ufs_sip_abi_verified",
        "installed_ufs_sip_effect_contract_verified",
        "xnu_firmware_abi_verified",
        "physical_resource_ownership_verified",
    ):
        require(firmware.get(key) is False, "unexpected firmware promotion: " + key)

    dma = value(report, "dma")
    windows = dma.get("dt_direct_dma_windows")
    require(
        windows == [{
            "path": "/soc",
            "child_bus_start": "0x0",
            "parent_bus_start": "0x0",
            "bytes": "0x1000000000",
            "identity": True,
        }],
        "direct DMA window differs",
    )
    require(dma.get("dt_iommu_binding_declared") is False, "unexpected DT IOMMU binding")
    require(dma.get("linux_sysfs_iommu_group_attached") is False,
            "unexpected Linux IOMMU group")
    require(dma.get("linux_iommu_supplier_links") == [], "unexpected IOMMU supplier")
    for key in ("physical_dma_bypass_verified", "coherency_verified", "xnu_dma_ready"):
        require(dma.get(key) is False, "unexpected DMA promotion: " + key)

    safety = value(report, "safety")
    require(safety.get("offline_analysis_only") is True, "live report was not offline-only")
    require(safety.get("read_only_inputs") is True, "live report inputs were not read-only")
    for key in ("adb_access_by_this_tool", "mmio_access", "phone_write", "partition_access"):
        require(safety.get(key) is False, "unsafe live-report action: " + key)
    return {
        "android_timer_irq_delivery": True,
        "android_ufs_irq_delivery": True,
        "critical_live_fdt_topology": True,
        "direct_identity_dma_window_bytes": 1 << 36,
        "linux_ufs_iommu_attachment_observed": False,
        "installed_ufs_module_binary_identity": True,
    }


def validate_offline_gate(report):
    require(report.get("passed") is True, "offline gate did not pass")
    require(report.get("inputs_unchanged") is True, "offline gate inputs changed")
    require(value(report, "input_sha256", "fdt") == FDT_SHA256,
            "offline gate DTB differs")
    safety = value(report, "safety")
    for key in ("physical_device_access", "mmio_access", "flash_or_partition_write",
                "phone_execution_authorized"):
        require(safety.get(key) is False, "unsafe offline-gate action: " + key)
    blockers = value(report, "remaining_physical_blockers")
    require(blockers.get("installed_firmware_contract") == "unverified",
            "unexpected offline firmware promotion")
    require(blockers.get("physical_ufs_backend") == "disabled",
            "physical UFS backend was enabled")
    require(blockers.get("ufs_topckgen_physical_backend") == "disabled",
            "physical topckgen backend was enabled")
    return True


def validate_saved_audit(report):
    require(report.get("audit_complete") is True, "saved UFS audit incomplete")
    require(value(report, "input_sha256", "fdt") == FDT_SHA256,
            "saved UFS audit DTB differs")
    require(value(report, "modules", "ufs-mediatek-mod.ko", "sha256") == UFS_MODULE_SHA256,
            "saved UFS audit module differs")
    require(report.get("dma_window_bytes") == 1 << 36, "saved DMA window differs")
    for key in ("source_binary_equivalence_verified", "physical_dma_route_verified",
                "installed_firmware_contract_verified", "physical_backend_enabled"):
        require(report.get(key) is False, "unexpected saved-audit promotion: " + key)
    return True


def validate_client_audit(report):
    require(report.get("audit_complete") is True, "firmware client audit incomplete")
    client = value(report, "saved_client")
    require(client.get("module_sha256") == UFS_MODULE_SHA256,
            "firmware client module differs")
    query = value(client, "mcq_query")
    require(query.get("function_id") == "0xc2000276" and query.get("selector") == 1024,
            "firmware client MCQ request differs")
    require(client.get("offsets_are_runtime_addresses") is False,
            "static offsets were promoted to runtime addresses")
    for key in ("installed_firmware_contract_verified", "physical_dma_route_verified",
                "physical_backend_enabled"):
        require(report.get(key) is False, "unexpected client-audit promotion: " + key)
    return True


def validate_contract_model(report):
    require(report.get("passed") is True, "saved contract model did not pass")
    require(report.get("saved_module_sha256") == UFS_MODULE_SHA256,
            "contract model module differs")
    require(report.get("test_sources_unchanged") is True,
            "contract model sources changed")
    for key in ("physical_backend_enabled", "installed_firmware_contract_verified",
                "physical_dma_route_verified"):
        require(report.get(key) is False, "unexpected contract-model promotion: " + key)
    return True


def validate_candidate(manifest, image_receipt):
    require(manifest.get("branch") == "duchamp-bootstrap", "candidate branch differs")
    require(value(manifest, "inputs", "live_fdt_sha256") == FDT_SHA256,
            "candidate DTB differs")
    outputs = value(manifest, "outputs")
    require(outputs.get("candidate_sha256") == CANDIDATE_SHA256,
            "candidate manifest hash differs")
    require(outputs.get("candidate_size") == CANDIDATE_BYTES,
            "candidate manifest size differs")
    require(image_receipt == {"bytes": CANDIDATE_BYTES, "sha256": CANDIDATE_SHA256},
            "candidate image does not match its pinned manifest")
    checks = value(manifest, "checks")
    for key in (
        "payload_source_rebuild_phone",
        "payload_source_rebuild_qemu",
        "bootshim_host_entry_guard",
        "handoff_ready",
        "xnu_return_contract",
        "payload_preflight",
        "materializer",
        "return_slot",
        "embedded_payload_match_phone",
        "embedded_payload_match_qemu",
        "phone_elf_no_relocations",
        "phone_elf_no_unresolved_symbols",
        "qemu_elf_no_relocations",
        "qemu_elf_no_unresolved_symbols",
        "qemu_xnu_jump",
        "avb_none_verified",
        "lz4_decompressed_match",
        "offline_gate_v18",
    ):
        require(checks.get(key) is True, "candidate check missing: " + key)
    require(checks.get("phone_elf_indirect_branch_count") == 1,
            "candidate phone branch count differs")
    require(checks.get("qemu_elf_indirect_branch_count") == 1,
            "candidate QEMU branch count differs")
    require(isinstance(checks.get("qemu_white_pixels"), int)
            and checks["qemu_white_pixels"] > 0, "candidate QEMU XNU pixels missing")
    safety = value(manifest, "safety")
    for key in ("phone_write", "fastboot_used", "partition_access",
                "physical_mmio_executed", "physical_ufs_enabled",
                "phone_execution_authorized"):
        require(safety.get(key) is False, "unsafe candidate action: " + key)
    return True


def assess(live, offline, saved, client, contract, candidate, candidate_receipt):
    observed = validate_live(live)
    validate_offline_gate(offline)
    validate_saved_audit(saved)
    validate_client_audit(client)
    validate_contract_model(contract)
    validate_candidate(candidate, candidate_receipt)
    blockers = [
        {
            "id": "xnu_phone_timer_irq_delivery",
            "verified": False,
            "needed": "bounded diagnostic execution proving XNU timer and IRQ delivery",
        },
        {
            "id": "installed_firmware_effect_contract",
            "verified": False,
            "needed": "matched BL31 identity plus UFS SiP return/effect semantics",
        },
        {
            "id": "physical_resource_ownership",
            "verified": False,
            "needed": "exclusive GIC/UFS/PHY/clock/reset ownership for XNU",
        },
        {
            "id": "runtime_ufs_dma_contract",
            "verified": False,
            "needed": "HCCAP, effective masks, dma_ops/fwspec/domain/SWIOTLB and cache ownership",
        },
        {
            "id": "xnu_physical_ufs_backend",
            "verified": False,
            "needed": "reviewed backend that remains disabled until all earlier contracts pass",
        },
    ]
    return {
        "evidence_validated": True,
        "safe_offline_stage_complete": True,
        "assessment": "blocked",
        "diagnostic_candidate_prepared": True,
        "physical_phone_execution_authorized": False,
        "full_system_boot_ready": False,
        "physical_ufs_backend_authorized": False,
        "observed": observed,
        "remaining_blockers": blockers,
        "next_safe_work": [
            "add read-only runtime capture fields for UFS HCCAP and effective DMA masks",
            "identify the installed BL31 image/build before modeling UFS SiP effects",
            "keep the MT6897 physical UFS provider disabled",
        ],
        "safety": {
            "local_json_inputs_only": True,
            "adb_access": False,
            "phone_write": False,
            "fastboot_access": False,
            "partition_access": False,
            "mmio_access": False,
            "smc_execution": False,
        },
        "scope": (
            "evidence consistency and fail-closed readiness assessment only; "
            "not authorization for a phone trial"
        ),
    }


def read_report(path):
    raw = path.read_bytes()
    if len(raw) > 64 * 1024 * 1024:
        raise ValueError("JSON evidence file is too large: " + str(path))
    report = json.loads(raw)
    if not isinstance(report, dict):
        raise ValueError("JSON evidence root is not an object: " + str(path))
    return report, {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def file_receipt(path):
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as stream:
        while True:
            block = stream.read(1024 * 1024)
            if not block:
                break
            size += len(block)
            digest.update(block)
    return {"bytes": size, "sha256": digest.hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--live-report", type=Path, required=True)
    parser.add_argument("--offline-gate", type=Path, required=True)
    parser.add_argument("--saved-audit", type=Path, required=True)
    parser.add_argument("--client-audit", type=Path, required=True)
    parser.add_argument("--contract-model", type=Path, required=True)
    parser.add_argument("--candidate-manifest", type=Path, required=True)
    parser.add_argument("--candidate-image", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("preserve existing output")
    paths = {
        "live_report": args.live_report,
        "offline_gate": args.offline_gate,
        "saved_audit": args.saved_audit,
        "client_audit": args.client_audit,
        "contract_model": args.contract_model,
        "candidate_manifest": args.candidate_manifest,
    }
    try:
        loaded = {name: read_report(path.resolve()) for name, path in paths.items()}
        reports = {name: item[0] for name, item in loaded.items()}
        candidate_receipt = file_receipt(args.candidate_image.resolve())
        result = assess(
            reports["live_report"],
            reports["offline_gate"],
            reports["saved_audit"],
            reports["client_audit"],
            reports["contract_model"],
            reports["candidate_manifest"],
            candidate_receipt,
        )
        receipts = {name: item[1] for name, item in loaded.items()}
        receipts["candidate_image"] = candidate_receipt
        for name, path in paths.items():
            require(read_report(path.resolve())[1] == receipts[name],
                    "evidence changed during assessment: " + name)
        require(file_receipt(args.candidate_image.resolve()) == candidate_receipt,
                "candidate image changed during assessment")
        result["input_receipts"] = receipts
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as error:
        parser.exit(1, "phone readiness assessment failed: " + str(error) + "\n")
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
