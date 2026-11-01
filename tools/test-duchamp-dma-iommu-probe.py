#!/usr/bin/env python3
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "duchamp/diagnostics/dma-iommu-probe/duchamp_dma_iommu_probe.c"
README = ROOT / "duchamp/diagnostics/dma-iommu-probe/README.md"
CONFIG = ROOT / "research/mt6897-contract/saved-v1/kernel.config"


class DmaIommuProbeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = PROBE.read_text(encoding="utf-8")
        cls.readme = README.read_text(encoding="utf-8")
        cls.config = CONFIG.read_text(encoding="utf-8")

    def test_target_is_pinned_to_captured_ufs_device_and_kernel(self):
        self.assertIn('"mediatek,mt8183-ufshci"', self.source)
        self.assertIn('"duchamp"', self.source)
        self.assertIn('"mt6897"', self.source)
        self.assertIn("gcf2c2dc91b9e-ab11782407", self.source)

    def test_captured_kernel_supports_required_read_only_interfaces(self):
        for item in (
            "CONFIG_MODULES=y",
            "CONFIG_MODULE_UNLOAD=y",
            "CONFIG_MODVERSIONS=y",
            "CONFIG_IOMMU_API=y",
            "CONFIG_IOMMU_SUPPORT=y",
            "CONFIG_OF_IOMMU=y",
            "CONFIG_IOMMU_DMA=y",
        ):
            self.assertIn(item, self.config)

    def test_interface_is_one_read_only_sysfs_attribute(self):
        self.assertIn("DEVICE_ATTR_RO(sweet_dma_iommu_contract)", self.source)
        self.assertNotIn("DEVICE_ATTR_RW", self.source)
        self.assertNotIn("DEVICE_ATTR_WO", self.source)
        self.assertNotIn("module_param", self.source)
        self.assertIn("device_create_file(", self.source)
        self.assertIn("device_remove_file(", self.source)

    def test_exact_masks_and_route_state_are_exported(self):
        for name in (
            "streaming_dma_mask",
            "streaming_dma_mask_bits",
            "coherent_dma_mask",
            "coherent_dma_mask_bits",
            "dma_ops_present",
            "device_dma_ops_present",
            "swiotlb_pool_present",
            "iommu_fwspec_present",
            "iommu_fwspec_num_ids",
            "iommu_domain_present",
            "iommu_domain_type",
        ):
            self.assertIn(f'"{name}=', self.source)

    def test_probe_uses_referenced_device_and_public_iommu_api(self):
        for call in (
            "of_find_compatible_node(",
            "of_find_device_by_node(",
            "get_dma_ops(",
            "dev_iommu_fwspec_get(",
            "iommu_get_domain_for_dev(",
            "sysfs_emit(",
            "put_device(",
        ):
            self.assertIn(call, self.source)

    def test_no_raw_kernel_pointer_is_exported(self):
        self.assertNotRegex(self.source, r"%p(?:x|K|S|s|B)?")
        self.assertNotIn("unsigned long)ops", self.source)
        self.assertNotIn("unsigned long)domain", self.source)

    def test_forbidden_mutating_or_hardware_operations_are_absent(self):
        forbidden_calls = (
            r"\bdma_alloc_[A-Za-z0-9_]*\s*\(",
            r"\bdma_map_[A-Za-z0-9_]*\s*\(",
            r"\bdma_set_mask\s*\(",
            r"\bdma_set_coherent_mask\s*\(",
            r"\biommu_attach[A-Za-z0-9_]*\s*\(",
            r"\biommu_map[A-Za-z0-9_]*\s*\(",
            r"\bioremap[A-Za-z0-9_]*\s*\(",
            r"\breadl\s*\(",
            r"\bwritel\s*\(",
            r"\barm_smccc[A-Za-z0-9_]*\s*\(",
            r"\bufs_mtk_smc[A-Za-z0-9_]*\s*\(",
            r"\bscsi_execute[A-Za-z0-9_]*\s*\(",
            r"\bplatform_driver_register\s*\(",
        )
        for pattern in forbidden_calls:
            self.assertNotRegex(self.source, pattern)

    def test_documentation_requires_separate_phone_authorization(self):
        self.assertIn("separate explicit approval", self.readme)
        self.assertIn("Do not copy or load", self.readme)
        self.assertIn("does **not** allocate or map DMA memory", self.readme)


if __name__ == "__main__":
    unittest.main(verbosity=2)
