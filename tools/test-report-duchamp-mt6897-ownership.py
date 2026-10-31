#!/usr/bin/env python3
"""Focused tests for the offline Duchamp MT6897 ownership report."""

import ast
import importlib.util
import os
from pathlib import Path
import unittest


REPO = Path(__file__).resolve().parent.parent
DEFAULT_DTB = REPO.parent / "phone-fdt.bin"


def load_report_module():
    path = REPO / "tools/report-duchamp-mt6897-ownership.py"
    spec = importlib.util.spec_from_file_location("duchamp_ownership_report", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class OwnershipReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_report_module()
        cls.dtb = Path(os.environ.get("DUCHAMP_SAVED_DTB", DEFAULT_DTB))
        cls.raw = cls.dtb.read_bytes()
        cls.report = cls.module.build_report(cls.raw, REPO)

    def test_exact_saved_dtb_and_read_only_safety(self):
        self.assertEqual(
            self.report["dtb"]["sha256"], self.module.EXPECTED_DTB_SHA256
        )
        self.assertEqual(self.report["dtb"]["bytes"], 485760)
        self.assertEqual(self.report["dtb"]["model"], "MT6897")
        safety = self.report["safety"]
        self.assertTrue(safety["offline_only"])
        self.assertTrue(safety["read_only_inputs"])
        for key in (
            "mmio_access",
            "adb_access",
            "fastboot_access",
            "phone_access",
            "partition_access",
            "network_access",
            "subprocess_execution",
        ):
            self.assertFalse(safety[key], key)

    def test_every_category_has_uniform_resource_fields(self):
        self.assertEqual(
            set(self.report["categories"]),
            {"gic", "timer", "firmware", "power", "iommu", "ufs"},
        )
        for category in self.report["categories"].values():
            self.assertEqual(category["runtime_owner"], "unproven")
            self.assertFalse(category["physical_access_tested"])
            self.assertTrue(category["nodes"])
            for node in category["nodes"]:
                self.assertEqual(set(node["resources"]), set(self.module.RESOURCE_KEYS))
                self.assertIn("value", node["status"])
                self.assertIsInstance(node["compatibles"], list)
                self.assertIsInstance(node["roles"], list)

    def test_gic_and_timer_declarations_are_separate_from_runtime_proof(self):
        gic = self.report["categories"]["gic"]
        primary = next(node for node in gic["nodes"] if node["path"] == "/interrupt-controller")
        self.assertIn("arm,gic-v3", primary["compatibles"])
        self.assertTrue(primary["resources"]["reg"]["present"])
        self.assertTrue(primary["resources"]["interrupts"]["present"])

        timer = self.report["categories"]["timer"]
        paths = {node["path"] for node in timer["nodes"]}
        self.assertIn("/timer", paths)
        self.assertIn("/soc/systimer@1cc10000", paths)
        arch = next(node for node in timer["nodes"] if node["path"] == "/timer")
        self.assertIn("arm,armv8-timer", arch["compatibles"])
        self.assertTrue(arch["resources"]["interrupts"]["present"])

    def test_firmware_and_power_evidence_remain_unproven(self):
        firmware = self.report["categories"]["firmware"]
        psci = next(node for node in firmware["nodes"] if node["path"] == "/psci")
        scmi = next(
            node for node in firmware["nodes"] if node["path"] == "/firmware/scmi"
        )
        self.assertEqual(psci["details"]["method"], ["smc"])
        self.assertTrue(scmi["details"]["mboxes"]["present"])
        self.assertTrue(scmi["details"]["shmem"]["present"])

        power_paths = {
            node["path"] for node in self.report["categories"]["power"]["nodes"]
        }
        self.assertIn("/power-controller@1c001000", power_paths)
        self.assertIn("/soc/spmi@1cc04000", power_paths)

    def test_iommu_exists_but_ufs_route_is_not_declared_or_proven(self):
        iommu = self.report["categories"]["iommu"]
        iommu_paths = {node["path"] for node in iommu["nodes"]}
        self.assertIn("/soc/iommu@1e802000", iommu_paths)
        self.assertIn("/soc/iommu@1e810000", iommu_paths)

        ufs = self.report["categories"]["ufs"]
        host = next(node for node in ufs["nodes"] if node["path"] == "/soc/ufshci@112b0000")
        self.assertTrue(host["resources"]["reg"]["present"])
        self.assertTrue(host["resources"]["interrupts"]["present"])
        self.assertTrue(host["resources"]["clocks"]["present"])
        self.assertTrue(host["resources"]["resets"]["present"])
        self.assertFalse(host["resources"]["power_domains"]["present"])
        self.assertFalse(host["resources"]["iommus"]["present"])
        route = ufs["ufs_dma_route"]
        self.assertFalse(route["verified"])
        self.assertFalse(route["dtb_iommu_binding_declared_on_host_or_ancestors"])
        self.assertIn("absence does not prove direct/bypass DMA", route["reason"])

    def test_source_manifests_match_the_same_saved_dtb(self):
        evidence = self.report["source_evidence"]
        self.assertTrue(evidence["parser"]["reused"])
        self.assertEqual(len(evidence["manifests"]), 3)
        for manifest in evidence["manifests"]:
            if manifest["captured_fdt_sha256"]:
                self.assertTrue(manifest["matches_report_dtb"], manifest["path"])
        for category, sources in evidence["local_sources"].items():
            self.assertTrue(sources, category)
            for source in sources:
                self.assertTrue(source["present"], source["path"])
                self.assertFalse(source["ownership_proof"])

    def test_modified_blob_is_rejected_before_interpretation(self):
        with self.assertRaisesRegex(ValueError, "provenance mismatch"):
            self.module.build_report(self.raw + b"changed", REPO)

    def test_tool_has_no_external_or_filesystem_write_api(self):
        path = REPO / "tools/report-duchamp-mt6897-ownership.py"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imports = set()
        calls = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    calls.append(node.func.attr)
                elif isinstance(node.func, ast.Name):
                    calls.append(node.func.id)
        self.assertTrue(
            imports.isdisjoint(
                {"subprocess", "socket", "urllib", "http", "requests", "winreg"}
            )
        )
        self.assertTrue(
            set(calls).isdisjoint(
                {
                    "open",
                    "write_text",
                    "write_bytes",
                    "mkdir",
                    "touch",
                    "unlink",
                    "rename",
                    "chmod",
                }
            )
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
