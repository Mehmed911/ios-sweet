#!/usr/bin/env python3
"""Unit tests for the fail-closed Duchamp phone-layout verifier."""

import importlib.util
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest


REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "tools" / "verify-duchamp-phone-layout.py"
SPEC = importlib.util.spec_from_file_location(
    "verify_duchamp_phone_layout", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def contract_fixture():
    return {
        "report_version": 1,
        "result": "PASS",
        "decision": "offline-layout-documented-phone-execution-blocked",
        "inputs": {
            name: {"sha256": digest}
            for name, digest in MODULE.EXPECTED_HASHES.items()
        },
        "lk": {
            "self_bootstrap_mapping": {
                "physical_base": MODULE.LK_PHYSICAL_BASE,
                "runtime_pc_register_captured": False,
            },
            "linux_handoff": {
                "smc_function_id": MODULE.LK_SMC_FUNCTION_ID,
                "kernel_target_is_fixed_in_lk_binary": False,
                "fdt_target_is_fixed_in_lk_binary": False,
            },
        },
        "android_image_contract": {
            "load_address": MODULE.IMAGE_BASE,
            "runtime_entry_pc_captured": False,
        },
        "fdt_handoff": {
            "address": MODULE.FDT_ADDRESS,
            "incoming_x0_value_captured": False,
            "dtb_self_describes_physical_address": False,
        },
        "phone_layout": {
            "image_base": MODULE.IMAGE_BASE,
            "image_ceiling_exclusive": MODULE.FDT_ADDRESS,
            "expected_entry_x0": MODULE.FDT_ADDRESS,
            "execution_authorized": False,
        },
        "claims": {
            "phone_layout_preflight_permitted": True,
            "phone_execution_ready": False,
            "android_image_runtime_entry_pc_captured": False,
            "fdt_incoming_x0_captured": False,
        },
        "safety": {
            "phone_access": False,
            "adb_access": False,
            "fastboot_access": False,
            "partition_write": False,
            "flash": False,
            "mmio_access": False,
            "firmware_execution": False,
            "jump_to_xnu": False,
        },
    }


class PhoneLayoutVerifierTests(unittest.TestCase):
    def test_valid_contract_stays_execution_blocked(self):
        result = MODULE.validate_contract(contract_fixture())
        self.assertTrue(result["contract_valid"])
        self.assertFalse(result["execution_authorized"])

    def test_runtime_claim_or_execution_authorization_is_rejected(self):
        contract = contract_fixture()
        contract["fdt_handoff"]["incoming_x0_value_captured"] = True
        with self.assertRaisesRegex(ValueError, "FDT corroboration"):
            MODULE.validate_contract(contract)

        contract = contract_fixture()
        contract["phone_layout"]["execution_authorized"] = True
        with self.assertRaisesRegex(ValueError, "phone-layout boundary"):
            MODULE.validate_contract(contract)

    def test_wrong_artifact_receipt_is_rejected(self):
        contract = contract_fixture()
        contract["inputs"]["lk"]["sha256"] = "00" * 32
        with self.assertRaisesRegex(ValueError, "lk receipt"):
            MODULE.validate_contract(contract)

    def test_arm64_image_header_is_bounded(self):
        raw = bytearray(64)
        struct.pack_into("<QQQ", raw, 8, 0, len(raw), 0xA)
        raw[56:60] = b"ARM\x64"
        result = MODULE.inspect_arm64_image(bytes(raw))
        self.assertEqual(result["bytes"], 64)
        struct.pack_into("<Q", raw, 16, 65)
        with self.assertRaisesRegex(ValueError, "header size"):
            MODULE.inspect_arm64_image(bytes(raw))

    def test_existing_output_is_preserved(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "result.json"
            output.write_text("keep", encoding="utf-8")
            process = subprocess.run(
                [sys.executable, str(SCRIPT), "--contract", "missing",
                 "--json-out", str(output)],
                capture_output=True, text=True)
            self.assertEqual(process.returncode, 2)
            self.assertIn("preserve existing output", process.stderr)
            self.assertEqual(output.read_text(encoding="utf-8"), "keep")


if __name__ == "__main__":
    unittest.main(verbosity=2)
