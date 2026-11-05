#!/usr/bin/env python3
"""Build a fail-closed MT6897 UFS resource-ownership candidate.

The assessment binds the exact saved Duchamp DTB to the pinned runtime and
captured-BL31 reports.  Device Tree declarations and static firmware dispatch
paths are inventory evidence only: they do not delegate MMIO, interrupt,
clock, reset, regulator, PHY, DMA, or storage ownership to XNU.

No positive physical receipt can be produced from the currently saved
evidence.  The tool performs no phone, MMIO, SMC, DMA, UFS, network, fastboot,
or partition operation.
"""

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys


REPORT_VERSION = 3
FDT_SHA256 = "9c49589f70044127be8941a9ea5537977f440ccd5ac15cfd24e120c8a1181d29"
RUNTIME_SHA256 = "71236c08c0354ff0733d44a64e505d117dfd4594e370bedd81fad3ec93d1bf4d"
FIRMWARE_SHA256 = "65e4a5cdd2085c2e2bb48ad9829109f8e39b7a260669074ab59427419b5d110c"
LIVE_RUNTIME_SHA256 = "fb1fa60b1b6df4f50f7794520be959ba7997f9433cea0f23dc818df9b5681660"
FIRMWARE_IDENTITY_SHA256 = (
    "1a9060eec770e72f70d1e51b2d0e8b86ab5be45b0ccd6ca73ca6b345171dcba2"
)
FIRMWARE_SIP_ABI_SHA256 = (
    "54c963ea6895717b937c1793685f2ebd70c48f9969ff168b2e63d6621accf103"
)
RESOURCE_BINDINGS_SHA256 = (
    "aaecd9757df5291eeab90ade83cba46d4be73cf57d710ac0bb5e60f6977119f7"
)

UFS_SERVICE_ID = "0xc2000276"
UFS_SELECTORS = {"refclk": 8, "mtcmos": 512, "mcq": 1024}

MMIO_RESOURCES = (
    ("ufs_hci", "/soc/ufshci@112b0000", 0x112B0000, 0x3000, "xnu-direct"),
    ("ufs_phy", "/soc/ufsphy@112a0000", 0x112A0000, 0x10000, "xnu-direct"),
    ("topckgen", "/syscon@10000000", 0x10000000, 0x1000, "shared-clock"),
    ("clock_hw_voter", "/syscon@10320000", 0x10320000, 0x2000, "shared-clock"),
    ("ufscfg_ao", "/syscon@112b8000", 0x112B8000, 0x1000, "shared-clock"),
    ("ufscfg_pdn", "/syscon@112bb000", 0x112BB000, 0x1000, "shared-clock-reset"),
    ("secure_power_controller", "/power-controller@1c001000", 0x1C001000,
     0x1000, "firmware-mediated"),
    ("mphy_glb_dig", "/soc/peri-ufs-glb-dig@11fa0000", 0x11FA0000,
     0x1000, "ufs-named-unlinked"),
    ("mphy_glb_ana", "/soc/peri-ufs-glb-ana@11fa1000", 0x11FA1000,
     0x1000, "ufs-named-unlinked"),
    ("mphy_glb_mib", "/soc/peri-ufs-glb-mib@11fa2000", 0x11FA2000,
     0x1000, "ufs-named-unlinked"),
    ("mphy_glb_pll", "/soc/peri-ufs-glb-pll@11fa3000", 0x11FA3000,
     0x1000, "ufs-named-unlinked"),
    ("mphy_glb_cdr", "/soc/peri-ufs-glb-cdr@11fa4000", 0x11FA4000,
     0x1000, "ufs-named-unlinked"),
    ("mphy_ln_dig_tx", "/soc/peri-ufs-ln-dig-tx@11fa8000", 0x11FA8000,
     0x1000, "ufs-named-unlinked"),
    ("mphy_ln_ana_tx", "/soc/peri-ufs-ln-ana-tx@11fa9000", 0x11FA9000,
     0x1000, "ufs-named-unlinked"),
    ("mphy_ln_dig_rx", "/soc/peri-ufs-ln-dig-rx@11faa000", 0x11FAA000,
     0x1000, "ufs-named-unlinked"),
    ("mphy_ln_ana_rx", "/soc/peri-ufs-ln-ana-rx@11fab000", 0x11FAB000,
     0x1000, "ufs-named-unlinked"),
)

EXPECTED_CLOCKS = (
    ("ufs_sel", "/syscon@10000000", 42),
    ("ufs_sel_min_src", "/syscon@10000000", 118),
    ("ufs_sel_max_src", "/syscon@10000000", 172),
    ("ufs_fde", "/syscon@10000000", 41),
    ("ufs_fde_min_src", "/syscon@10000000", 139),
    ("ufs_fde_max_src", "/syscon@10000000", 117),
    ("unipro_tx_sym", "/syscon@112b8000", 0),
    ("unipro_rx_sym0", "/syscon@112b8000", 1),
    ("unipro_rx_sym1", "/syscon@112b8000", 2),
    ("unipro_sysclk", "/syscon@112b8000", 3),
    ("ufshci_ufs", "/syscon@112bb000", 0),
    ("ufshci_aes", "/syscon@112bb000", 1),
)

EXPECTED_RESETS = (
    ("unipro_rst", "/syscon@112bb000/reset-controller", 0),
    ("crypto_rst", "/syscon@112bb000/reset-controller", 1),
    ("hci_rst", "/syscon@112bb000/reset-controller", 2),
)

EXPECTED_INTERRUPTS = (
    (0, 168, 4, 0),
    (0, 177, 4, 0),
    (0, 178, 4, 0),
    (0, 179, 4, 0),
    (0, 180, 4, 0),
    (0, 181, 4, 0),
    (0, 182, 4, 0),
    (0, 183, 4, 0),
    (0, 184, 4, 0),
)

EXPECTED_GIC_HWIRQS = (200, 209, 210, 211, 212, 213, 214, 215, 216)

EXPECTED_SUPPLIES = {
    "dvfsrc-vcore-supply": "/soc/dvfsrc@1c00f000/dvfsrc-vcore",
    "vcc-supply": "/soc/spmi@1cc04000/pmic@4/regulators/vemc",
    "vccq-supply": "/soc/spmi@1cc04000/mt6319@8/mt6319-8-regulator/8-vbuck3",
}

RUNTIME_PROOFS = (
    "installed_firmware_identity",
    "firmware_effect_contract",
    "secure_power_arbitration",
    "mmio_resource_delegation",
    "clock_and_hw_voter_ownership",
    "reset_ownership",
    "phy_ownership",
    "regulator_ownership",
    "ufs_interrupt_ownership",
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def load_json(path, expected_sha256, label):
    raw = path.read_bytes()
    require(sha256(raw) == expected_sha256, label + " hash differs")
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(label + " is not valid UTF-8 JSON") from error
    require(isinstance(value, dict), label + " is not a JSON object")
    return value, len(raw)


def load_tree(repo, raw):
    parser_path = repo / "tools/inspect-duchamp-hardware.py"
    spec = importlib.util.spec_from_file_location(
        "duchamp_resource_ownership_fdt", parser_path
    )
    require(spec is not None and spec.loader is not None,
            "cannot load bounded FDT parser")
    module = importlib.util.module_from_spec(spec)
    sys.dont_write_bytecode = True
    spec.loader.exec_module(module)
    return module.Fdt(raw), parser_path


def exact_node(tree, path):
    node = tree.nodes.get(path)
    require(node is not None, "missing required DT node: " + path)
    return node


def exact_register(tree, resource_id, path, base, size, ownership_class):
    node = exact_node(tree, path)
    registers = tree.registers(node)
    expected = [{
        "bus_address": hex(base),
        "physical_address": hex(base),
        "bytes": hex(size),
    }]
    require(registers == expected, resource_id + " register declaration differs")
    return {
        "id": resource_id,
        "path": path,
        "base": hex(base),
        "bytes": hex(size),
        "ownership_class": ownership_class,
        "declaration_proven": True,
        "host_dependency_link_proven": ownership_class != "ufs-named-unlinked",
        "runtime_owner": "unproven",
        "xnu_physical_access_authorized": False,
    }


def exact_references(tree, node, key, count_key, names_key, expected):
    entries = tree.references(node, key, count_key, names_key)
    observed = tuple(
        (entry.get("name"), entry["provider"], entry["args"][0])
        for entry in entries
    )
    require(observed == expected, key + " declaration differs")
    return [{"name": name, "provider": provider, "id": identifier,
             "runtime_owner": "unproven", "authorized": False}
            for name, provider, identifier in observed]


def evaluate_receipt(proofs):
    require(set(proofs) == set(RUNTIME_PROOFS), "runtime proof set differs")
    require(all(isinstance(value, bool) for value in proofs.values()),
            "runtime proof values must be booleans")
    blockers = [name for name in RUNTIME_PROOFS if not proofs[name]]
    issuable = not blockers
    return {
        "type": "mt6897-ufs-resource-ownership-v1",
        "status": "issuable" if issuable else "denied",
        "receipt_issuable": issuable,
        "blockers": blockers,
        "payload": ({"proofs": dict(proofs)} if issuable else None),
    }


def build_report(repo, fdt_path, runtime_path, firmware_path,
                 live_runtime_path, firmware_identity_path,
                 firmware_sip_abi_path, resource_bindings_path):
    fdt_raw = fdt_path.read_bytes()
    require(sha256(fdt_raw) == FDT_SHA256, "DTB hash differs")
    runtime, runtime_bytes = load_json(
        runtime_path, RUNTIME_SHA256, "runtime evidence"
    )
    firmware, firmware_bytes = load_json(
        firmware_path, FIRMWARE_SHA256, "firmware evidence"
    )
    live_runtime, live_runtime_bytes = load_json(
        live_runtime_path, LIVE_RUNTIME_SHA256, "live runtime evidence"
    )
    firmware_identity, firmware_identity_bytes = load_json(
        firmware_identity_path, FIRMWARE_IDENTITY_SHA256,
        "firmware identity evidence"
    )
    firmware_sip_abi, firmware_sip_abi_bytes = load_json(
        firmware_sip_abi_path, FIRMWARE_SIP_ABI_SHA256,
        "firmware SiP ABI evidence"
    )
    resource_bindings, resource_bindings_bytes = load_json(
        resource_bindings_path, RESOURCE_BINDINGS_SHA256,
        "resource-binding evidence"
    )
    require(runtime.get("report_version") == 2 and
            runtime.get("audit_passed") is True,
            "runtime evidence did not pass")
    require(runtime.get("target") == {"device": "duchamp", "soc": "mt6897"},
            "runtime target differs")
    require(firmware.get("report_version") == 1 and
            firmware.get("passed") is True,
            "firmware evidence did not pass")
    require(live_runtime.get("report_version") == 2 and
            live_runtime.get("result", {}).get("passed") is True,
            "live runtime evidence did not pass")
    identity_proofs = firmware_identity.get("proofs", {})
    identity_safety = firmware_identity.get("safety", {})
    require(firmware_identity.get("report_version") == 1 and
            firmware_identity.get("passed") is True and
            firmware_identity.get("verdict") ==
            "installed-bl31-runtime-identity-matched",
            "firmware identity evidence did not pass")
    require(identity_proofs.get(
                "installed_firmware_identity_proven") is True and
            identity_proofs.get(
                "installed_binary_byte_equivalence_proven") is False and
            identity_proofs.get(
                "runtime_smc_effect_contract_proven") is False and
            identity_proofs.get(
                "physical_resource_ownership_proven") is False,
            "firmware identity evidence overclaims its scope")
    require(identity_safety.get("offline_inputs_only") is True and
            identity_safety.get("phone_access_by_this_tool") is False and
            identity_safety.get("smc_execution") is False and
            identity_safety.get("mmio_access") is False and
            identity_safety.get("partition_access") is False and
            identity_safety.get("physical_ufs_backend_enabled") is False,
            "firmware identity evidence safety differs")
    sip_proofs = firmware_sip_abi.get("proofs", {})
    sip_safety = firmware_sip_abi.get("safety", {})
    sip_client = firmware_sip_abi.get("client", {})
    sip_client_abi = sip_client.get("abi", {})
    sip_firmware = firmware_sip_abi.get("firmware", {})
    require(firmware_sip_abi.get("report_version") == 1 and
            firmware_sip_abi.get("passed") is True and
            firmware_sip_abi.get("verdict") ==
                "running-client-build-id-to-captured-bl31-static-sip-abi-matched" and
            sip_proofs.get("running_client_build_id_match_proven")
                is True and
            sip_proofs.get("running_client_byte_equivalence_proven")
                is False and
            sip_proofs.get("saved_client_smc_call_relocations_proven")
                is True and
            sip_proofs.get("saved_client_function_id_and_selectors_proven")
                is True and
            sip_proofs.get("captured_bl31_service_dispatch_proven")
                is True and
            sip_proofs.get("installed_bl31_runtime_identity_matched")
                is True and
            sip_proofs.get("static_end_to_end_sip_abi_proven") is True,
            "firmware SiP ABI evidence did not pass")
    require(sip_client.get("saved_module_sha256") ==
                "7043e1109b4c356a914fdc92ffbe463c0c43cb27342f6ccce1517a2086b02493" and
            sip_client.get("running_gnu_build_id") ==
                "df7eecc22450fb6e6eceaaef4b3fe8ceb46b2a84" and
            sip_client.get("running_to_saved_build_id_note_byte_match")
                is True and
            sip_client_abi.get("function_id") == UFS_SERVICE_ID and
            sip_client_abi.get("selectors") == UFS_SELECTORS and
            sip_firmware.get("fast64_function_id") == UFS_SERVICE_ID and
            sip_firmware.get("selectors") == UFS_SELECTORS and
            sip_firmware.get("running_bl31_identity") ==
                firmware_identity.get("identity"),
            "firmware SiP ABI payload differs")
    require(sip_proofs.get(
                "installed_binary_byte_equivalence_proven") is False and
            sip_proofs.get(
                "runtime_smc_effect_contract_proven") is False and
            sip_proofs.get("firewall_state_proven") is False and
            sip_proofs.get("xnu_firmware_abi_authorized") is False and
            sip_proofs.get("physical_resource_ownership_proven") is False,
            "firmware SiP ABI evidence overclaims its scope")
    require(sip_safety.get("offline_inputs_only") is True and
            sip_safety.get("phone_access_by_this_tool") is False and
            sip_safety.get("smc_execution") is False and
            sip_safety.get("mmio_access") is False and
            sip_safety.get("firewall_probe") is False and
            sip_safety.get("partition_access") is False and
            sip_safety.get("physical_ufs_backend_enabled") is False,
            "firmware SiP ABI evidence safety differs")
    binding_target = resource_bindings.get("target", {})
    binding_runtime = resource_bindings.get("linux_runtime", {})
    binding_boundary = resource_bindings.get("proof_boundary", {})
    binding_authorization = resource_bindings.get("authorization", {})
    binding_safety = resource_bindings.get("safety", {})
    require(resource_bindings.get("report_version") == 1 and
            resource_bindings.get("passed") is True and
            binding_target.get("device") == "duchamp" and
            binding_target.get("soc") == "mt6897" and
            binding_target.get("active_slot") == "_a",
            "resource-binding evidence did not pass")
    require(binding_runtime.get("provider_bindings_proven") is True and
            binding_runtime.get("ufs_irq_handler_binding_proven") is True and
            len(binding_runtime.get("bindings", {})) == 8 and
            len(binding_runtime.get("regulators", {})) == 3 and
            len(binding_runtime.get("ufs_interrupts", [])) == 9,
            "resource-binding runtime attribution differs")
    for key in (
        "linux_current_provider_bindings_proven",
        "linux_ufs_regulator_state_observed",
        "linux_ufs_irq_handler_binding_proven",
        "slb_and_scmi_coordination_modules_loaded",
        "firewall_and_protection_modules_loaded",
    ):
        require(binding_boundary.get(key) is True,
                "resource-binding proof missing: " + key)
    for key in (
        "system_cache_exclusive_owner_proven",
        "ufs_cache_maintenance_reachability_proven",
        "runtime_smc_effect_proven",
        "firewall_state_or_ufs_grant_proven",
        "xnu_mmio_clock_reset_phy_regulator_irq_delegation_proven",
        "installed_firmware_byte_equivalence_proven",
    ):
        require(binding_boundary.get(key) is False,
                "resource-binding evidence overclaims: " + key)
    require(binding_authorization == {
                "physical_backend_enabled": False,
                "mmio_callbacks": 0,
                "smc_callbacks": 0,
                "dma_callbacks": 0,
                "ufs_commands": 0,
                "interrupt_reconfiguration_callbacks": 0,
            }, "resource-binding evidence authorized a physical callback")
    require(binding_safety.get("phone_read") is True and
            binding_safety.get("phone_write") is False and
            binding_safety.get("selinux_policy_change") is False and
            binding_safety.get("module_load") is False and
            binding_safety.get("mmio_access") is False and
            binding_safety.get("smc_execution") is False and
            binding_safety.get("firewall_probe") is False and
            binding_safety.get("block_device_access") is False and
            binding_safety.get("partition_write") is False and
            binding_safety.get("physical_ufs_backend_enabled") is False,
            "resource-binding evidence safety differs")
    live_safety = live_runtime.get("safety", {})
    require(live_safety.get("offline_analysis_only") is True and
            live_safety.get("read_only_inputs") is True and
            live_safety.get("phone_write") is False and
            live_safety.get("partition_access") is False and
            live_safety.get("mmio_access") is False,
            "live runtime evidence safety differs")

    tree, parser_path = load_tree(repo, fdt_raw)
    root = exact_node(tree, "/")
    require(root.strings("model") == ["MT6897"], "DTB model differs")

    resources = [exact_register(tree, *spec) for spec in MMIO_RESOURCES]
    gic = exact_node(tree, "/interrupt-controller")
    gic_registers = tree.registers(gic)
    require(gic_registers == [
        {"bus_address": "0xc400000", "physical_address": "0xc400000",
         "bytes": "0x40000"},
        {"bus_address": "0xc440000", "physical_address": "0xc440000",
         "bytes": "0x200000"},
    ], "GIC register declaration differs")
    for resource_id, register in zip(("gicd", "gicr"), gic_registers):
        resources.append({
            "id": resource_id,
            "path": gic.path,
            "base": register["physical_address"],
            "bytes": register["bytes"],
            "ownership_class": "interrupt-provider",
            "declaration_proven": True,
            "host_dependency_link_proven": True,
            "runtime_owner": "unproven",
            "xnu_physical_access_authorized": False,
        })
    host = exact_node(tree, "/soc/ufshci@112b0000")
    clocks = exact_references(
        tree, host, "clocks", "#clock-cells", "clock-names", EXPECTED_CLOCKS
    )
    resets = exact_references(
        tree, host, "resets", "#reset-cells", "reset-names", EXPECTED_RESETS
    )
    interrupts = tree.interrupts(host)
    observed_interrupts = tuple(tuple(entry["args"]) for entry in interrupts)
    require(observed_interrupts == EXPECTED_INTERRUPTS,
            "UFS interrupt declaration differs")
    require(all(entry["provider"] == "/interrupt-controller" for entry in interrupts),
            "UFS interrupt provider differs")
    live_ufs = live_runtime.get("runtime", {}).get("ufs", {})
    require(tuple(live_ufs.get("dt_spi_ids", [])) ==
            tuple(entry[1] for entry in EXPECTED_INTERRUPTS),
            "live UFS DT SPI mapping differs")
    require(tuple(live_ufs.get("expected_gic_hwirqs", [])) ==
            EXPECTED_GIC_HWIRQS,
            "live UFS GIC HWIRQ mapping differs")
    rows = live_ufs.get("irq_rows", [])
    require(len(rows) == len(EXPECTED_INTERRUPTS),
            "live UFS IRQ row count differs")
    require(tuple(row.get("hwirq") for row in rows) == EXPECTED_GIC_HWIRQS and
            all(row.get("name") == "ufshcd" and
                row.get("controller") == "GICv3" and
                row.get("trigger") == "Level" for row in rows),
            "live UFS IRQ routing differs")
    irq_total_delta = sum(row.get("total_delta", -1) for row in rows)
    require(irq_total_delta == live_ufs.get("total_delta") == 47 and
            live_ufs.get("android_runtime_delivery_observed") is True and
            live_ufs.get("xnu_phone_delivery_observed") is False,
            "live UFS IRQ delivery evidence differs")
    interrupt_manifest = [{
        "provider": entry["provider"],
        "specifier": entry["args"],
        "linux_gic_hwirq": row["hwirq"],
        "linux_irq": row["linux_irq"],
        "linux_mapping_proven": True,
        "linux_delivery_observed": row["total_delta"] > 0,
        "linux_delivery_delta": row["total_delta"],
        "xnu_delivery_proven": False,
        "runtime_owner": "unproven",
        "authorized": False,
    } for entry, row in zip(interrupts, rows)]

    phys = tree.references(host, "phys", "#phy-cells")
    require(len(phys) == 1 and phys[0]["provider"] == "/soc/ufsphy@112a0000"
            and phys[0]["args"] == [], "UFS PHY reference differs")
    supplies = {}
    for name, expected_path in EXPECTED_SUPPLIES.items():
        provider = tree.provider(host.scalar(name))
        require(provider.path == expected_path, name + " provider differs")
        supplies[name] = {
            "provider": provider.path,
            "runtime_owner": "unproven",
            "authorized": False,
        }
    require("dma-coherent" not in host.props,
            "saved UFS node unexpectedly became DMA coherent")
    require("iommus" not in host.props and "iommu-map" not in host.props,
            "saved UFS node unexpectedly gained an IOMMU binding")

    topckgen = exact_node(tree, "/syscon@10000000")
    require("hw-voter-regmap" in topckgen.props,
            "topckgen lacks hw-voter-regmap")
    hw_voter = tree.provider(topckgen.scalar("hw-voter-regmap"))
    require(hw_voter.path == "/syscon@10320000",
            "topckgen hardware-voter provider differs")

    service = firmware.get("service", {})
    selectors = firmware.get("selectors", {})
    claims = firmware.get("claims", {})
    firmware_mmio = firmware.get("mtcmos_mmio", {})
    require(service.get("fast64_function_id") == UFS_SERVICE_ID,
            "firmware UFS service ID differs")
    require({name: selectors.get(name, {}).get("value")
             for name in UFS_SELECTORS} == UFS_SELECTORS,
            "firmware selector values differ")
    require(claims.get("captured_bl31_ufs_service_descriptor_verified") is True and
            claims.get("saved_client_function_id_dispatch_verified") is True and
            claims.get("captured_bl31_mtcmos_mmio_paths_verified") is True,
            "captured firmware static path is incomplete")
    require(claims.get("runtime_smc_return_effect_contract_verified") is False and
            claims.get("physical_resource_ownership_verified") is False and
            claims.get("direct_xnu_mtcmos_mmio_authorized") is False,
            "firmware evidence unexpectedly promoted physical ownership")
    require(firmware_mmio.get("unlock_register") == "0x1c001000" and
            firmware_mmio.get("control_registers") == ["0x1c001e10", "0x1c001e14"] and
            firmware_mmio.get("safe_xnu_direct_readback_authorized") is False,
            "firmware MTCMOS resource boundary differs")
    identity_capture = firmware_identity.get("capture", {})
    require(identity_capture.get("tee_a_sha256") ==
            firmware.get("tee_a", {}).get("sha256") and
            identity_capture.get("atf_sha256") ==
            firmware.get("atf", {}).get("sha256"),
            "firmware identity/static audit capture differs")

    runtime_firmware = runtime.get("firmware_ownership", {})
    require(runtime_firmware.get("runtime_rtff_mtcmos_cap_observed") is True,
            "runtime RTFF-MTCMOS capability was not observed")
    require(runtime_firmware.get("ufs_sip_service", {}).get(
        "fast64_function_id") == UFS_SERVICE_ID,
        "runtime/static UFS service disagreement")
    require(runtime_firmware.get("selectors") == UFS_SELECTORS,
            "runtime/static selector disagreement")
    require(runtime_firmware.get("runtime_smc_execution_observed") is False and
            runtime_firmware.get("runtime_physical_effect_observed") is False and
            runtime_firmware.get("exclusive_linux_ownership_proven") is False and
            runtime_firmware.get("exclusive_firmware_ownership_proven") is False,
            "runtime evidence unexpectedly promoted physical ownership")
    overlap = runtime_firmware.get("linux_overlapping_resource", {})
    require(overlap.get("start") == "0x1c001000" and
            overlap.get("end") == "0x1c001fff",
            "runtime power-controller overlap differs")

    proofs = {name: False for name in RUNTIME_PROOFS}
    proofs["installed_firmware_identity"] = True
    receipt = evaluate_receipt(proofs)
    return {
        "report_version": REPORT_VERSION,
        "passed": True,
        "target": {"device": "duchamp", "soc": "mt6897", "engine": "ufs"},
        "declarations": {
            "exact_saved_dtb_manifest_proven": True,
            "mmio": resources,
            "unlinked_ufs_named_mmio": [
                entry["id"] for entry in resources
                if entry["ownership_class"] == "ufs-named-unlinked"
            ],
            "clocks": clocks,
            "resets": resets,
            "interrupts": interrupt_manifest,
            "phy": {
                "provider": phys[0]["provider"],
                "runtime_owner": "unproven",
                "authorized": False,
            },
            "supplies": supplies,
            "dma_coherent": False,
            "iommu_binding_present": False,
            "clock_hw_voter": hw_voter.path,
        },
        "firmware_contract": {
            "captured_bl31_artifact_pinned": True,
            "static_service_dispatch_proven": True,
            "installed_client_binary_identity_proven": True,
            "static_end_to_end_sip_abi_proven": True,
            "static_abi_scope": (
                "installed UFS client build ID and raw SMC call sites matched "
                "to captured BL31 dispatch with runtime identity strings"
            ),
            "service_id": UFS_SERVICE_ID,
            "selectors": UFS_SELECTORS,
            "rtff_mtcmos_capability_observed": True,
            "secure_power_overlap": {
                "start": "0x1c001000",
                "end": "0x1c001fff",
                "classification": "shared/delegated boundary",
            },
            "installed_firmware_identity_proven": True,
            "identity_match_strength": "runtime identity strings",
            "installed_binary_byte_equivalence_proven": False,
            "runtime_effect_contract_proven": False,
            "exclusive_owner_proven": False,
            "direct_xnu_secure_power_mmio_authorized": False,
        },
        "runtime_observations": {
            "linux_ufs_irq_mapping_proven": True,
            "linux_ufs_irq_delivery_observed": True,
            "linux_ufs_irq_total_delta": irq_total_delta,
            "linux_ufs_irq_rows_with_delivery": sum(
                row["total_delta"] > 0 for row in rows
            ),
            "xnu_ufs_irq_delivery_observed": False,
            "xnu_ufs_irq_delegation_proven": False,
            "ufs_interrupt_ownership_proven": False,
            "linux_resource_provider_bindings_proven": True,
            "linux_ufs_regulator_state_observed": True,
            "linux_ufs_irq_handler_binding_proven": True,
            "linux_slb_scmi_coordination_modules_loaded": True,
            "linux_firewall_protection_modules_loaded": True,
            "system_cache_exclusive_owner_proven": False,
            "ufs_cache_maintenance_reachability_proven": False,
            "firewall_state_or_ufs_grant_proven": False,
            "xnu_resource_delegation_proven": False,
        },
        "runtime_proofs": proofs,
        "ownership_receipt": receipt,
        "authorization": {
            "physical_backend_enabled": False,
            "mmio_callbacks": 0,
            "smc_callbacks": 0,
            "dma_callbacks": 0,
            "ufs_commands": 0,
            "interrupt_reconfiguration_callbacks": 0,
        },
        "inputs": {
            "fdt": {"sha256": FDT_SHA256, "bytes": len(fdt_raw)},
            "runtime_evidence": {
                "sha256": RUNTIME_SHA256, "bytes": runtime_bytes,
            },
            "firmware_evidence": {
                "sha256": FIRMWARE_SHA256, "bytes": firmware_bytes,
            },
            "live_runtime_evidence": {
                "sha256": LIVE_RUNTIME_SHA256, "bytes": live_runtime_bytes,
            },
            "firmware_identity_evidence": {
                "sha256": FIRMWARE_IDENTITY_SHA256,
                "bytes": firmware_identity_bytes,
            },
            "firmware_sip_abi_evidence": {
                "sha256": FIRMWARE_SIP_ABI_SHA256,
                "bytes": firmware_sip_abi_bytes,
            },
            "resource_binding_evidence": {
                "sha256": RESOURCE_BINDINGS_SHA256,
                "bytes": resource_bindings_bytes,
            },
            "bounded_parser": str(parser_path.relative_to(repo)).replace("\\", "/"),
        },
        "safety": {
            "local_files_only": True,
            "phone_access": False,
            "network_access": False,
            "adb_access": False,
            "fastboot_access": False,
            "mmio_access": False,
            "smc_execution": False,
            "dma_or_ufs_commands": False,
            "partition_access": False,
            "physical_backend_enabled": False,
        },
        "scope": (
            "offline declaration and static installed-client-to-BL31 ABI "
            "inventory only; a denied receipt is the expected safe result "
            "until independent runtime effect and ownership proofs exist"
        ),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--fdt", type=Path, required=True)
    parser.add_argument("--runtime-evidence", type=Path, required=True)
    parser.add_argument("--firmware-evidence", type=Path, required=True)
    parser.add_argument("--live-runtime-evidence", type=Path, required=True)
    parser.add_argument("--firmware-identity-evidence", type=Path,
                        required=True)
    parser.add_argument("--firmware-sip-abi-evidence", type=Path,
                        required=True)
    parser.add_argument("--resource-binding-evidence", type=Path,
                        required=True)
    args = parser.parse_args()

    repo = Path(__file__).resolve().parent.parent
    output = args.output.resolve()
    require(not output.exists(), "preserve existing output: " + str(output))
    output.parent.mkdir(parents=True, exist_ok=True)
    report = build_report(
        repo,
        args.fdt.resolve(strict=True),
        args.runtime_evidence.resolve(strict=True),
        args.firmware_evidence.resolve(strict=True),
        args.live_runtime_evidence.resolve(strict=True),
        args.firmware_identity_evidence.resolve(strict=True),
        args.firmware_sip_abi_evidence.resolve(strict=True),
        args.resource_binding_evidence.resolve(strict=True),
    )
    descriptor = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(json.dumps({
        "passed": True,
        "output": str(output),
        "receipt_issuable": report["ownership_receipt"]["receipt_issuable"],
        "physical_backend_enabled": False,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
