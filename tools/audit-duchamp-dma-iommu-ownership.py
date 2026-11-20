#!/usr/bin/env python3
"""Build a fail-closed Duchamp UFS DMA/IOMMU/firmware evidence report.

The command consumes only pinned local captures and source receipts.  It does
not contact the phone, execute firmware, issue an SMC, access MMIO or enable a
physical backend.  A successful audit means that the evidence was internally
consistent; it does not mean that physical UFS access from XNU is safe.
"""

import argparse
import hashlib
import json
from pathlib import Path
import re
import struct

import duchamp_saved_ufs as saved


HCCAP_64AS = 1 << 24
RTFF_MTCMOS_CAP = 1 << 9
EXPECTED_HCCAP = 0x55C7051F
EXPECTED_MTK_CAPS = 0x6C0
EXPECTED_ATF_SHA256 = (
    "716222a632e4a0623a2e467e17f1d36f38a37f79a1c026447fe724e75e90e07e"
)
EXPECTED_PROBE_ARTIFACT_SHA256 = (
    "96cd9bf422f8924c1c11b33c92d042ec0ea7fb864e756712fe45e5261be27518"
)
EXPECTED_PROBE_KERNEL = "6.1.57-android14-11-gcf2c2dc91b9e-ab11782407"
EXPECTED_PROBE_VERMAGIC = (
    "6.1.57-android14-11-maybe-dirty SMP preempt mod_unload modversions aarch64"
)
EXPECTED_STREAMING_MASK = "0xffffffffffffffff"
EXPECTED_COHERENT_MASK = "0xffffffffffffffff"
EXPECTED_BUS_DMA_LIMIT = "0x0000000fffffffff"

EXPECTED_DMA_WORDS = {
    0x12A34: 0x360000CA,  # Test controller 64-address capability.
    0x12A3C: 0x92800001,  # x1 = DMA_BIT_MASK(64).
    0x12A44: 0x94000000,  # dma_set_mask relocation.
    0x12A48: 0x34002FA0,  # Success branches to the 64-bit coherent path.
    0x12A50: 0x12800001,  # w1 = DMA_BIT_MASK(32).
    0x12A58: 0x94000000,  # dma_set_mask fallback relocation.
    0x12A5C: 0x35003380,  # Fallback failure branches to init error.
    0x12A64: 0x12800001,  # 32-bit coherent request.
    0x12A68: 0x94000000,  # dma_set_coherent_mask relocation.
    0x12A6C: 0xAA1303E0,  # Return value is not tested; init continues.
    0x12A70: 0x940001CA,  # Continue to ufshcd_memory_alloc().
    0x1303C: 0xAA1703E0,
    0x13040: 0x92800001,  # 64-bit coherent request.
    0x13044: 0x17FFFE89,  # Branch back to dma_set_coherent_mask.
    0x130CC: 0x2A0003F7,  # Preserve fallback error for init failure.
}

EXPECTED_DMA_FRAGMENT_SHA256 = {
    "dma": "da798be9d4f6093314c2272f698466cd43b852a3b43944f20eea7a0ce2f318a3",
    "dma64": "f71cde82307cc5ec7e1427ab1dc6589849fcc0605de21eeafe8618f8d431437c",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def receipt(path):
    raw = Path(path).read_bytes()
    return {"bytes": len(raw), "sha256": sha256(raw)}


def read_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("invalid JSON input: " + str(path)) from error


def verify_runtime_probe(probe):
    """Validate the pinned read-only UFS-device probe and return its contract."""
    require(probe.get("report_version") == 1, "runtime probe report version differs")

    target = probe.get("target", {})
    require(target.get("device") == "duchamp", "runtime probe device differs")
    require(target.get("soc") == "mt6897", "runtime probe SoC differs")
    require(target.get("kernel") == EXPECTED_PROBE_KERNEL,
            "runtime probe kernel differs")

    artifact = probe.get("artifact", {})
    require(artifact.get("name") == "duchamp_dma_iommu_probe.ko",
            "runtime probe artifact name differs")
    require(artifact.get("bytes") == 278200, "runtime probe artifact size differs")
    require(artifact.get("sha256") == EXPECTED_PROBE_ARTIFACT_SHA256,
            "runtime probe artifact hash differs")
    require(artifact.get("vermagic") == EXPECTED_PROBE_VERMAGIC,
            "runtime probe vermagic differs")
    require(artifact.get("this_module_bytes") == 1088,
            "runtime probe struct module size differs")
    require(artifact.get("this_module_relocation_offsets") == [368, 984],
            "runtime probe init/exit relocations differ")

    execution = probe.get("execution", {})
    for key in (
        "module_loaded",
        "two_reads_completed",
        "reads_identical",
        "module_unloaded",
        "staged_file_removed",
    ):
        require(execution.get(key) is True, "runtime probe execution differs: " + key)
    require(execution.get("cleanup_status") == "clean",
            "runtime probe cleanup was not clean")
    require(execution.get("kernel_taint_before") == 12805,
            "runtime probe pre-load taint differs")
    require(execution.get("kernel_taint_during") == 12805,
            "runtime probe changed kernel taint")

    contract = probe.get("contract", {})
    expected = {
        "contract_version": 1,
        "streaming_mask_pointer_present": True,
        "streaming_dma_mask": EXPECTED_STREAMING_MASK,
        "streaming_dma_mask_bits": 64,
        "coherent_dma_mask": EXPECTED_COHERENT_MASK,
        "coherent_dma_mask_bits": 64,
        "bus_dma_limit": EXPECTED_BUS_DMA_LIMIT,
        "bus_dma_limit_bits": 36,
        "dma_mask_is_coherent_mask": False,
        "dma_range_map_present": True,
        "dma_coherent": False,
        "dma_ops_present": False,
        "device_dma_ops_present": False,
        "dma_ops_bypass_supported": False,
        "dma_ops_bypass": False,
        "swiotlb_pool_present": True,
        "iommu_private_present": False,
        "iommu_group_present": False,
        "iommu_fwspec_present": False,
        "iommu_fwspec_ops_present": False,
        "iommu_fwspec_fwnode_present": False,
        "iommu_fwspec_num_ids": 0,
        "iommu_fwspec_first_id": 0,
        "iommu_fwspec_last_id": 0,
        "iommu_domain_present": False,
        "iommu_domain_type": 0,
        "iommu_domain_is_dma": False,
    }
    require(contract == expected, "runtime probe contract differs")

    safety = probe.get("safety", {})
    for key in (
        "partition_access",
        "boot_partition_modified",
        "storage_command_issued_by_probe",
        "dma_mapping_issued_by_probe",
        "iommu_mapping_or_attachment_issued_by_probe",
        "mmio_access_issued_by_probe",
        "smc_issued_by_probe",
        "selinux_changed",
    ):
        require(safety.get(key) is False, "runtime probe safety contract differs: " + key)

    return contract


def decode_imm19_target(pc, word):
    immediate = (word >> 5) & 0x7FFFF
    if immediate & (1 << 18):
        immediate -= 1 << 19
    return pc + immediate * 4


def decode_imm26_target(pc, word):
    immediate = word & 0x03FFFFFF
    if immediate & (1 << 25):
        immediate -= 1 << 26
    return pc + immediate * 4


def inspect_saved_dma_client(module_path):
    raw = saved.pinned(module_path, saved.UFS_SHA)
    elf = saved.Elf(raw)
    text = elf.section_data(elf.sections[".text"])

    for offset, expected in EXPECTED_DMA_WORDS.items():
        actual = struct.unpack_from("<I", text, offset)[0]
        require(actual == expected, f"saved UFS DMA instruction differs at 0x{offset:x}")

    elf.call(0x12A44, "dma_set_mask")
    elf.call(0x12A58, "dma_set_mask")
    elf.call(0x12A68, "dma_set_coherent_mask")

    _, fragments = elf.fragments()
    fragment_receipts = {
        item["name"]: item for item in fragments if item["name"] in {"dma", "dma64"}
    }
    for name, expected in EXPECTED_DMA_FRAGMENT_SHA256.items():
        require(name in fragment_receipts, "missing saved DMA fragment: " + name)
        require(
            fragment_receipts[name]["sha256"] == expected,
            "saved DMA fragment differs: " + name,
        )

    require(decode_imm19_target(0x12A48, EXPECTED_DMA_WORDS[0x12A48]) == 0x1303C,
            "64-bit success target differs")
    require(decode_imm19_target(0x12A5C, EXPECTED_DMA_WORDS[0x12A5C]) == 0x130CC,
            "32-bit failure target differs")
    require(decode_imm26_target(0x13044, EXPECTED_DMA_WORDS[0x13044]) == 0x12A68,
            "64-bit coherent target differs")
    require(decode_imm26_target(0x12A70, EXPECTED_DMA_WORDS[0x12A70]) == 0x13198,
            "post-mask allocation target differs")

    return {
        "module": {"bytes": len(raw), "sha256": sha256(raw)},
        "fragments": fragment_receipts,
        "control_flow": {
            "controller_64as_selects_64_bit_attempt": True,
            "streaming_64_bit_attempt_first": True,
            "streaming_32_bit_fallback_on_failure": True,
            "fallback_failure_exits_initialization": True,
            "coherent_setter_called_after_streaming_success": True,
            "coherent_setter_return_checked": False,
        },
    }


def parse_config(text):
    enabled = set()
    disabled = set()
    for line in text.splitlines():
        if line.startswith("CONFIG_") and line.endswith("=y"):
            enabled.add(line[:-2])
        match = re.fullmatch(r"# (CONFIG_[A-Z0-9_]+) is not set", line)
        if match:
            disabled.add(match.group(1))
    return enabled, disabled


def parse_iomem(text):
    regions = []
    pattern = re.compile(
        r"^\s*([0-9a-fA-F]+)-([0-9a-fA-F]+)\s*:\s*(.*?)\s*$"
    )
    for line in text.splitlines():
        match = pattern.match(line)
        if match:
            regions.append(
                {
                    "start": int(match.group(1), 16),
                    "end": int(match.group(2), 16),
                    "owner": match.group(3),
                }
            )
    return regions


def covering_region(regions, addresses):
    matches = [
        region
        for region in regions
        if all(region["start"] <= address <= region["end"] for address in addresses)
    ]
    require(len(matches) == 1, "expected one Linux resource covering firmware MMIO")
    return matches[0]


def verify_sources(repo, source_dir, client_audit):
    source_receipts = saved.sources(repo, source_dir)
    require(client_audit.get("audit_complete") is True, "saved client audit incomplete")
    require(
        client_audit.get("source_receipts") == source_receipts,
        "saved client/source receipts differ",
    )

    required = {
        "drivers/of/device.c": (
            'iommu = of_iommu_configure(dev, np, id);',
            "arch_setup_dma_ops(dev, dma_start, size, iommu, coherent);",
            "platform bus notifier",
        ),
        "drivers/iommu/of_iommu.c": (
            'of_parse_phandle_with_args(master_np, "iommus"',
            "if (!err && dev->bus && !device_iommu_mapped(dev))",
        ),
        "arch/arm64/mm/dma-mapping.c": (
            "if (iommu)",
            "iommu_setup_dma_ops(dev, dma_base, dma_base + size - 1);",
            "xen_setup_dma_ops(dev);",
        ),
        "kernel/dma/direct.c": (
            "u64 dma_limit = min_not_zero(dma_mask, dev->bus_dma_limit);",
            "min_not_zero(dev->coherent_dma_mask, dev->bus_dma_limit);",
            "if (mask >= DMA_BIT_MASK(32))",
            "return 1;",
        ),
        "kernel/dma/mapping.c": (
            "if (likely(!ops))",
            "addr = dma_direct_map_page(dev, page, offset, size, dir, attrs);",
            "if (!dev->dma_mask || !dma_supported(dev, mask))",
            "*dev->dma_mask = mask;",
            "dev->coherent_dma_mask = mask;",
        ),
        "include/linux/dma-direct.h": (
            "return end <= min_not_zero(*dev->dma_mask, dev->bus_dma_limit);",
        ),
    }
    for relative, needles in required.items():
        text = (Path(source_dir) / relative).read_text(encoding="utf-8")
        for needle in needles:
            require(needle in text, f"pinned source contract differs: {relative}: {needle}")
    return source_receipts


def audit(shell, runtime, probe, client_audit, firmware, iomem_text, config_text,
          dma_client, source_receipts):
    probe_contract = verify_runtime_probe(probe)
    require(client_audit.get("physical_backend_enabled") is False,
            "saved client audit unexpectedly enables the physical backend")
    require(client_audit.get("physical_dma_route_verified") is False,
            "saved client audit unexpectedly promotes the physical DMA route")
    require(client_audit["saved_client"]["module_sha256"] == saved.UFS_SHA,
            "saved client audit module receipt differs")
    require(dma_client["module"]["sha256"] == saved.UFS_SHA,
            "inspected DMA client module receipt differs")
    expected_flow = {
        "controller_64as_selects_64_bit_attempt": True,
        "streaming_64_bit_attempt_first": True,
        "streaming_32_bit_fallback_on_failure": True,
        "fallback_failure_exits_initialization": True,
        "coherent_setter_called_after_streaming_success": True,
        "coherent_setter_return_checked": False,
    }
    require(dma_client.get("control_flow") == expected_flow,
            "inspected DMA client control flow differs")

    require(shell.get("passed") is True, "shell runtime report did not pass")
    target = shell.get("target", {})
    require(target.get("device") == "duchamp", "runtime device is not duchamp")
    require(target.get("hardware") == "mt6897", "runtime hardware is not mt6897")
    require(shell.get("reference_dtb_sha256") == saved.FDT_SHA,
            "runtime DTB receipt differs")

    hccap = shell["runtime_ufs_contract"]["hccap"]["proc_debug"]
    hccap_value = int(hccap["effective_host_capabilities"], 16)
    mtk_caps = int(hccap["mtk_caps"], 16)
    require(hccap_value == EXPECTED_HCCAP, "runtime HCCAP differs")
    require(bool(hccap_value & HCCAP_64AS), "runtime HCCAP lacks 64AS")
    require(hccap.get("supports_64_bit_addressing") is True,
            "runtime HCCAP parser disagrees about 64AS")
    require(mtk_caps == EXPECTED_MTK_CAPS, "runtime MediaTek UFS caps differ")
    require(shell["runtime"]["ufs"]["total_delta"] > 0,
            "no runtime UFS interrupt progress in shell report")
    require(shell["firmware"]["installed_ufs_module"]["state"] == "Live",
            "runtime UFS module is not live")

    runtime_result = runtime.get("result", {})
    require(runtime_result.get("passed") is True, "runtime topology report did not pass")
    runtime_ufs = runtime["runtime"]["ufs"]
    installed = runtime_ufs["installed_module"]
    saved_module = installed["saved_vendor_module"]
    require(saved_module.get("sha256") == saved.UFS_SHA,
            "runtime saved-module receipt differs")
    require(saved_module.get("build_id_match_verified") is True,
            "running/saved UFS module build IDs do not match")
    require(runtime_ufs.get("android_runtime_delivery_observed") is True,
            "runtime UFS delivery was not observed")

    dma = runtime["dma"]
    require(dma.get("dt_iommu_binding_declared") is False,
            "UFS DT unexpectedly declares an IOMMU")
    require(dma.get("linux_sysfs_iommu_group_attached") is False,
            "UFS unexpectedly has a Linux IOMMU group")
    require(dma.get("linux_iommu_supplier_links") == [],
            "UFS unexpectedly has an IOMMU supplier link")
    ufs_ancestry = {entry["path"]: entry for entry in dma["ufs_ancestry"]}
    ufs_node = ufs_ancestry["/soc/ufshci@112b0000"]
    soc_node = ufs_ancestry["/soc"]
    require(ufs_node.get("iommus_present") is False, "UFS iommus property appeared")
    require(ufs_node.get("iommu_map_present") is False,
            "UFS iommu-map property appeared")
    require(ufs_node.get("dma_coherent_present") is False,
            "UFS dma-coherent property appeared")
    direct_windows = soc_node.get("dma_ranges", [])
    require(
        direct_windows == [{
            "bytes": "0x1000000000",
            "child_bus_start": "0x0",
            "identity": True,
            "parent_bus_start": "0x0",
        }],
        "UFS inherited DMA window differs",
    )

    enabled, disabled = parse_config(config_text)
    for symbol in (
        "CONFIG_ARM64_PA_BITS_48",
        "CONFIG_ZONE_DMA32",
        "CONFIG_IOMMU_SUPPORT",
        "CONFIG_IOMMU_DMA",
        "CONFIG_OF_IOMMU",
        "CONFIG_SWIOTLB",
    ):
        require(symbol in enabled, "required kernel config differs: " + symbol)
    require("CONFIG_XEN" in disabled, "CONFIG_XEN is not proven disabled")
    require("CONFIG_DMA_API_DEBUG" in disabled,
            "DMA API debug config state differs")

    require(firmware.get("passed") is True, "captured firmware audit did not pass")
    require(firmware["atf"]["sha256"] == EXPECTED_ATF_SHA256,
            "captured ATF receipt differs")
    require(firmware["service"]["name"] == "MTK_SIP_KERNEL_UFS_CONTROL",
            "captured UFS firmware service differs")
    require(firmware["service"]["fast64_function_id"] == "0xc2000276",
            "captured UFS firmware function ID differs")
    require(firmware["selectors"]["mtcmos"]["value"] == 512,
            "captured MTCMOS selector differs")
    require(firmware["selectors"]["refclk"]["value"] == 8,
            "captured REFCLK selector differs")
    require(firmware["selectors"]["mcq"]["value"] == 1024,
            "captured MCQ selector differs")
    require(firmware["claims"]["captured_bl31_mtcmos_mmio_paths_verified"] is True,
            "captured BL31 MTCMOS path was not verified")
    require(firmware["claims"]["runtime_smc_return_effect_contract_verified"] is False,
            "firmware report unexpectedly promotes runtime effects")
    require(firmware["claims"]["physical_resource_ownership_verified"] is False,
            "firmware report unexpectedly promotes resource ownership")

    firmware_addresses = [
        int(firmware["mtcmos_mmio"]["unlock_register"], 16),
        *[int(value, 16) for value in firmware["mtcmos_mmio"]["control_registers"]],
    ]
    linux_power_region = covering_region(parse_iomem(iomem_text), firmware_addresses)
    require("power-controller" in linux_power_region["owner"],
            "overlapping Linux resource is not the power controller")

    runtime_contract = shell["runtime_ufs_contract"]
    require(runtime_contract["streaming_dma_mask_bits"]["value"] is None,
            "streaming DMA mask unexpectedly captured; update the audit")
    require(runtime_contract["coherent_dma_mask_bits"]["value"] is None,
            "coherent DMA mask unexpectedly captured; update the audit")
    require(runtime_contract["dma_ops"]["value"] is None,
            "DMA ops unexpectedly captured; update the audit")
    require(runtime_contract["iommu_fwspec"]["value"] is None,
            "IOMMU fwspec unexpectedly captured; update the audit")
    require(runtime_contract["iommu_domain"]["value"] is None,
            "IOMMU domain unexpectedly captured; update the audit")

    return {
        "report_version": 2,
        "audit_passed": True,
        "target": {"device": "duchamp", "soc": "mt6897"},
        "runtime_probe": {
            "artifact": probe["artifact"],
            "execution": probe["execution"],
            "contract_version": probe_contract["contract_version"],
        },
        "dma_masks": {
            "controller_hccap": f"0x{hccap_value:08x}",
            "controller_64_bit_addressing_supported": True,
            "saved_client_control_flow": dma_client,
            "requested_streaming_sequence_bits": [64, 32],
            "effective_streaming_mask": probe_contract["streaming_dma_mask"],
            "effective_streaming_mask_bits": probe_contract["streaming_dma_mask_bits"],
            "effective_coherent_mask": probe_contract["coherent_dma_mask"],
            "effective_coherent_mask_bits": probe_contract["coherent_dma_mask_bits"],
            "bus_dma_limit": probe_contract["bus_dma_limit"],
            "bus_dma_limit_bits": probe_contract["bus_dma_limit_bits"],
            "effective_bus_address_ceiling": probe_contract["bus_dma_limit"],
            "effective_bus_address_ceiling_bits": probe_contract["bus_dma_limit_bits"],
            "streaming_and_coherent_mask_share_pointer": probe_contract[
                "dma_mask_is_coherent_mask"
            ],
            "dma_range_map_present": probe_contract["dma_range_map_present"],
            "dma_coherent": probe_contract["dma_coherent"],
            "coherent_setter_result_was_ignored_by_saved_client": True,
            "exact_masks_proven": True,
            "addressability_classification": (
                "both live masks are 64-bit, while the direct-DMA capability and "
                "allocation checks cap addresses at the 36-bit bus_dma_limit"
            ),
        },
        "iommu_route": {
            "dt_iommus_present": False,
            "dt_iommu_map_present": False,
            "linux_iommu_group_attached": False,
            "linux_iommu_supplier_link_observed": False,
            "inherited_identity_dma_window": direct_windows[0],
            "pinned_of_default_path_selects_iommu_ops": False,
            "runtime_dma_ops_state_observed": True,
            "runtime_dma_ops_present": probe_contract["dma_ops_present"],
            "runtime_device_dma_ops_present": probe_contract[
                "device_dma_ops_present"
            ],
            "runtime_dma_ops_bypass_supported": probe_contract[
                "dma_ops_bypass_supported"
            ],
            "runtime_dma_ops_bypass": probe_contract["dma_ops_bypass"],
            "runtime_iommu_private_present": probe_contract[
                "iommu_private_present"
            ],
            "runtime_iommu_group_present": probe_contract["iommu_group_present"],
            "runtime_iommu_fwspec_state_observed": True,
            "runtime_iommu_fwspec_present": probe_contract["iommu_fwspec_present"],
            "runtime_iommu_domain_state_observed": True,
            "runtime_iommu_domain_present": probe_contract["iommu_domain_present"],
            "linux_iommu_attachment_absent_at_observation": True,
            "custom_dma_ops_pointer_excluded_at_observation": True,
            "custom_platform_dma_fixup_excluded": False,
            "linux_dma_api_path": "generic dma-direct",
            "device_swiotlb_pool_present": probe_contract["swiotlb_pool_present"],
            "swiotlb_transfer_observed": False,
            "physical_iommu_bypass_verified": False,
            "classification": (
                "Linux selected its generic dma-direct path and exposed no UFS IOMMU "
                "attachment at observation; dma_range_map remains present, and this "
                "does not prove physical firewall bypass or identity addresses"
            ),
        },
        "firmware_ownership": {
            "runtime_mtk_caps": f"0x{mtk_caps:08x}",
            "runtime_rtff_mtcmos_cap_observed": bool(mtk_caps & RTFF_MTCMOS_CAP),
            "ufs_sip_service": firmware["service"],
            "selectors": {
                "refclk": 8,
                "mtcmos": 512,
                "mcq": 1024,
            },
            "captured_bl31_mtcmos_mmio": firmware["mtcmos_mmio"],
            "linux_overlapping_resource": {
                "start": f"0x{linux_power_region['start']:08x}",
                "end": f"0x{linux_power_region['end']:08x}",
                "owner": linux_power_region["owner"],
            },
            "delegated_firmware_control_contract_present": True,
            "runtime_smc_execution_observed": False,
            "runtime_physical_effect_observed": False,
            "exclusive_linux_ownership_proven": False,
            "exclusive_firmware_ownership_proven": False,
            "ownership_classification": (
                "overlapping Linux resource reservation and captured BL31 direct-MMIO "
                "control path; treat as a shared/delegated boundary"
            ),
        },
        "kernel_config": {
            "arm64_pa_bits": 48,
            "zone_dma32": True,
            "iommu_support": True,
            "iommu_dma": True,
            "of_iommu": True,
            "swiotlb": True,
            "xen": False,
            "dma_api_debug": False,
        },
        "source_receipts": source_receipts,
        "verdict": {
            "proven": [
                "the live controller advertises UFSHCI 64-bit addressing",
                "the matching saved UFS client tries a 64-bit streaming mask then a 32-bit fallback",
                "the live streaming and coherent DMA masks are both 0xffffffffffffffff",
                "the live bus_dma_limit is 0x0000000fffffffff, imposing a 36-bit DMA address ceiling",
                "get_dma_ops() and dev->dma_ops were both null, selecting the pinned kernel's generic dma-direct path",
                "no Linux IOMMU private object, group, fwspec or domain was attached to UFS at observation",
                "a device SWIOTLB pool pointer was present, without evidence that a transfer used it",
                "the live MediaTek UFS caps include RTFF-MTCMOS",
                "the matching client, captured BL31 dispatcher and MTCMOS MMIO path agree on the UFS SiP contract",
                "Linux reserves the same power-controller range touched by the captured BL31 MTCMOS path",
            ],
            "not_proven": [
                "whether any UFS transfer uses SWIOTLB or another bounce path",
                "physical DMA identity, firewall permissions or secure-world translation",
                "cache-maintenance ownership and correctness for a non-coherent device",
                "whether a platform fixup changed fields other than the observed DMA-ops pointer",
                "exclusive Linux or firmware ownership of the overlapping power-controller region",
                "runtime SMC effects or safe physical UFS access from XNU",
            ],
            "physical_xnu_ufs_ready": False,
            "physical_backend_enabled": False,
        },
        "safety": {
            "audit_execution_offline": True,
            "runtime_probe_evidence_included": True,
            "adb_access_by_this_tool": False,
            "temporary_phone_staging_occurred_during_probe_session": True,
            "probe_module_loaded_and_unloaded": True,
            "probe_cleanup_verified": True,
            "partition_access": False,
            "boot_partition_modified": False,
            "storage_command_by_probe": False,
            "dma_mapping_by_probe": False,
            "iommu_mapping_or_attachment_by_probe": False,
            "firmware_execution_by_probe": False,
            "smc_execution_by_probe": False,
            "mmio_access_by_probe": False,
        },
        "scope": (
            "pinned runtime captures, one successful read-only UFS-device kernel probe, "
            "exact saved UFS client instructions, pinned GKI source bodies and captured "
            "BL31 static paths; audit success is not physical-UFS or phone readiness"
        ),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--shell-report", type=Path, required=True)
    parser.add_argument("--runtime-report", type=Path, required=True)
    parser.add_argument("--probe-report", type=Path, required=True)
    parser.add_argument("--client-audit", type=Path, required=True)
    parser.add_argument("--firmware-audit", type=Path, required=True)
    parser.add_argument("--saved-contract", type=Path, required=True)
    parser.add_argument("--sources", type=Path, required=True)
    parser.add_argument("--iomem", type=Path, required=True)
    args = parser.parse_args()

    if args.output.exists():
        parser.error("preserve existing output")

    repo = Path(__file__).resolve().parent.parent
    shell = read_json(args.shell_report)
    runtime = read_json(args.runtime_report)
    probe = read_json(args.probe_report)
    client_audit = read_json(args.client_audit)
    firmware = read_json(args.firmware_audit)
    source_receipts = verify_sources(repo, args.sources, client_audit)
    module_path = args.saved_contract / "ufs-mediatek-mod.ko"
    dma_client = inspect_saved_dma_client(module_path)
    config_path = args.saved_contract / "kernel.config"
    iomem_text = args.iomem.read_text(encoding="utf-8")
    config_text = config_path.read_text(encoding="utf-8")

    result = audit(
        shell,
        runtime,
        probe,
        client_audit,
        firmware,
        iomem_text,
        config_text,
        dma_client,
        source_receipts,
    )
    result["input_receipts"] = {
        "shell_report": receipt(args.shell_report),
        "runtime_report": receipt(args.runtime_report),
        "probe_report": receipt(args.probe_report),
        "client_audit": receipt(args.client_audit),
        "firmware_audit": receipt(args.firmware_audit),
        "iomem": receipt(args.iomem),
        "kernel_config": receipt(config_path),
        "saved_ufs_module": receipt(module_path),
    }

    args.output.mkdir(parents=True, exist_ok=False)
    output = args.output / "result.json"
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
