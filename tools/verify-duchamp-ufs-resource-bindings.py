#!/usr/bin/env python3
"""Verify the pinned read-only Duchamp UFS resource-binding capture."""

import argparse
import hashlib
import json
from pathlib import Path


REPORT_VERSION = 1
CAPTURE_SHA256 = "aaecd9757df5291eeab90ade83cba46d4be73cf57d710ac0bb5e60f6977119f7"

EXPECTED_DRIVERS = {
    "emi_slb_observer": "/sys/bus/platform/drivers/emislb_driver",
    "ufs_hci": "/sys/bus/platform/drivers/ufshcd-mtk",
    "ufs_phy": "/sys/bus/platform/drivers/ufs_mtk_phy",
    "topckgen": "/sys/bus/platform/drivers/clk-mt6897",
    "ufs_clock_ao": "/sys/bus/platform/drivers/clk-mt6897-peri",
    "ufs_clock_reset_pdn": "/sys/bus/platform/drivers/clk-mt6897-peri",
    "dvfsrc": "/sys/bus/platform/drivers/mtk-dvfsrc",
    "secure_power_controller": "/sys/bus/platform/drivers/mtk-scpsys-mt6897",
}

FALSE_BOUNDARY = (
    "system_cache_exclusive_owner_proven",
    "ufs_cache_maintenance_reachability_proven",
    "runtime_smc_effect_proven",
    "firewall_state_or_ufs_grant_proven",
    "xnu_mmio_clock_reset_phy_regulator_irq_delegation_proven",
    "installed_firmware_byte_equivalence_proven",
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def verify_capture(raw):
    require(hashlib.sha256(raw).hexdigest() == CAPTURE_SHA256,
            "resource-binding capture hash differs")
    try:
        report = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("resource-binding capture is not UTF-8 JSON") from error

    require(report.get("report_version") == REPORT_VERSION and
            report.get("passed") is True,
            "resource-binding capture did not pass")
    target = report.get("target", {})
    require(target.get("device") == "duchamp" and
            target.get("soc") == "mt6897" and
            target.get("active_slot") == "_a",
            "resource-binding capture target differs")

    runtime = report.get("linux_runtime", {})
    bindings = runtime.get("bindings", {})
    require(set(bindings) == set(EXPECTED_DRIVERS),
            "resource-binding set differs")
    for resource_id, expected_driver in EXPECTED_DRIVERS.items():
        binding = bindings[resource_id]
        require(binding.get("driver") == expected_driver and
                binding.get("linux_driver_binding_proven") is True and
                binding.get("exclusive_owner_proven") is False and
                binding.get("xnu_delegation_proven") is False,
                resource_id + " binding proof differs")

    hw_voter = runtime.get("hw_voter", {})
    require(hw_voter.get("compatibles") == ["mediatek,mt6897-hwv", "syscon"] and
            hw_voter.get("driver") is None and
            hw_voter.get("syscon_declaration_observed") is True and
            hw_voter.get("standalone_driver_binding_proven") is False and
            hw_voter.get("xnu_delegation_proven") is False,
            "hardware-voter boundary differs")

    regulators = runtime.get("regulators", {})
    require(set(regulators) == {"mt6363_vemc", "8_vbuck3", "dvfsrc-vcore"},
            "regulator set differs")
    require(regulators["mt6363_vemc"].get("state") == "enabled" and
            regulators["mt6363_vemc"].get("microvolts") == 2500000 and
            regulators["8_vbuck3"].get("state") == "enabled" and
            regulators["8_vbuck3"].get("microvolts") == 1193750 and
            regulators["dvfsrc-vcore"].get("microvolts") == 800000 and
            all(value.get("xnu_delegation_proven") is False
                for value in regulators.values()),
            "regulator observation differs")

    interrupts = runtime.get("ufs_interrupts", [])
    require(len(interrupts) == 9 and
            tuple(row.get("gic_hwirq") for row in interrupts) ==
                (200, 209, 210, 211, 212, 213, 214, 215, 216) and
            all(row.get("trigger") == "Level" and
                row.get("handler") == "ufshcd" for row in interrupts),
            "UFS IRQ-handler binding differs")
    require(runtime.get("provider_bindings_proven") is True and
            runtime.get("ufs_irq_handler_binding_proven") is True and
            len(runtime.get("ufs_supplier_links", [])) == 13,
            "Linux runtime attribution differs")

    boundary = report.get("proof_boundary", {})
    for key in (
        "linux_current_provider_bindings_proven",
        "linux_ufs_regulator_state_observed",
        "linux_ufs_irq_handler_binding_proven",
        "slb_and_scmi_coordination_modules_loaded",
        "firewall_and_protection_modules_loaded",
    ):
        require(boundary.get(key) is True, key + " was not proven")
    for key in FALSE_BOUNDARY:
        require(boundary.get(key) is False, key + " was overclaimed")

    authorization = report.get("authorization", {})
    require(authorization == {
        "physical_backend_enabled": False,
        "mmio_callbacks": 0,
        "smc_callbacks": 0,
        "dma_callbacks": 0,
        "ufs_commands": 0,
        "interrupt_reconfiguration_callbacks": 0,
    }, "capture authorized a physical callback")
    safety = report.get("safety", {})
    require(safety.get("phone_read") is True and
            safety.get("phone_write") is False and
            safety.get("selinux_policy_change") is False and
            safety.get("module_load") is False and
            safety.get("mmio_access") is False and
            safety.get("smc_execution") is False and
            safety.get("firewall_probe") is False and
            safety.get("block_device_access") is False and
            safety.get("partition_write") is False and
            safety.get("physical_ufs_backend_enabled") is False,
            "capture safety boundary differs")

    return {
        "report_version": REPORT_VERSION,
        "passed": True,
        "verdict": "linux-resource-bindings-observed-xnu-delegation-denied",
        "capture": {
            "sha256": CAPTURE_SHA256,
            "active_slot": target["active_slot"],
            "provider_bindings": len(bindings),
            "regulators": len(regulators),
            "ufs_irq_handlers": len(interrupts),
        },
        "proofs": dict(boundary),
        "authorization": dict(authorization),
        "safety": {
            "offline_verification": True,
            "phone_access_by_verifier": False,
            "mmio_access": False,
            "smc_execution": False,
            "physical_ufs_backend_enabled": False,
        },
        "scope": (
            "pinned read-only Linux provider attribution; no XNU delegation, "
            "cache owner, SMC effect, firewall grant or firmware byte match"
        ),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("capture", type=Path)
    parser.add_argument("--compact", action="store_true")
    args = parser.parse_args()
    try:
        result = verify_capture(args.capture.read_bytes())
    except (OSError, ValueError) as error:
        parser.exit(1, "resource-binding verification failed: " + str(error) + "\n")
    print(json.dumps(result, sort_keys=True,
                     separators=(",", ":") if args.compact else None,
                     indent=None if args.compact else 2))


if __name__ == "__main__":
    main()
