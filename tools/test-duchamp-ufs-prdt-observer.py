#!/usr/bin/env python3
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "duchamp/diagnostics/ufs-prdt-observer/duchamp_ufs_prdt_observer.c"
README = ROOT / "duchamp/diagnostics/ufs-prdt-observer/README.md"
CONFIG = ROOT / "research/mt6897-contract/saved-v1/kernel.config"


class UfsPrdtObserverTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SOURCE.read_text(encoding="utf-8")
        cls.readme = README.read_text(encoding="utf-8")
        cls.config = CONFIG.read_text(encoding="utf-8")

    def test_target_and_kernel_are_pinned(self):
        for value in (
            '"mediatek,mt8183-ufshci"',
            '"duchamp"',
            '"mt6897"',
            "gcf2c2dc91b9e-ab11782407",
        ):
            self.assertIn(value, self.source)

    def test_required_vendor_hook_configuration_is_present(self):
        for value in (
            "CONFIG_ANDROID_VENDOR_HOOKS=y",
            "CONFIG_TRACEPOINTS=y",
            "CONFIG_SCSI_UFS_VARIABLE_SG_ENTRY_SIZE=y",
            "CONFIG_NEED_SG_DMA_LENGTH=y",
        ):
            self.assertIn(value, self.config)

    def test_hook_is_registered_and_unregistered(self):
        self.assertIn("register_trace_android_vh_ufs_fill_prdt(", self.source)
        self.assertGreaterEqual(
            self.source.count("unregister_trace_android_vh_ufs_fill_prdt("), 2
        )
        self.assertIn("duchamp_observe_ufs_prdt", self.source)
        self.assertGreaterEqual(
            self.source.count("tracepoint_synchronize_unregister();"), 2
        )

    def test_report_is_root_read_only(self):
        self.assertIn(
            "DEVICE_ATTR(sweet_ufs_prdt_observation, 0400", self.source
        )
        self.assertNotIn("DEVICE_ATTR_RW", self.source)
        self.assertNotIn("DEVICE_ATTR_WO", self.source)
        self.assertNotIn("module_param", self.source)

    def test_callback_is_bounded_and_filters_exact_device(self):
        self.assertIn("hba->dev != READ_ONCE(duchamp_ufs_dev)", self.source)
        self.assertIn("segments > DUCHAMP_MAX_PRDT_SEGMENTS", self.source)
        self.assertIn("segments > READ_ONCE(hba->host->sg_tablesize)", self.source)
        self.assertIn("DUCHAMP_MAX_PRDT_ENTRY_SIZE", self.source)

    def test_observer_compares_all_route_layers(self):
        for expression in (
            "sg_dma_address(sg)",
            "sg_dma_len(sg)",
            "lrbp->ucd_prdt_ptr",
            "dma_to_phys(hba->dev, dma_address)",
            "is_swiotlb_buffer(hba->dev, translated_phys)",
            "sg_phys(sg)",
            "DUCHAMP_UFS_DMA_LIMIT",
        ):
            self.assertIn(expression, self.source)
        for expression in (
            "duchamp_direct_contract_matches",
            "iommu_get_domain_for_dev(dev)",
            "dev_iommu_fwspec_get(dev)",
            "READ_ONCE(dev->bus_dma_limit)",
        ):
            self.assertIn(expression, self.source)

    def test_report_is_a_coherent_fail_closed_snapshot(self):
        self.assertIn("static DEFINE_SPINLOCK(duchamp_stats_lock)", self.source)
        self.assertIn("snapshot = duchamp_stats", self.source)
        self.assertIn("coherent_snapshot=1", self.source)
        self.assertIn("observation_complete=%u", self.source)
        self.assertIn("!snapshot.rejected_calls", self.source)
        self.assertIn("!snapshot.runtime_contract_changes", self.source)
        self.assertIn("all_segments_within_bus_limit=%u", self.source)

    def test_hook_error_is_never_modified(self):
        self.assertIn("READ_ONCE(*err)", self.source)
        self.assertNotRegex(self.source, r"\*err\s*=")

    def test_forbidden_active_operations_are_absent(self):
        forbidden = (
            r"\bdma_alloc_[A-Za-z0-9_]*\s*\(",
            r"\bdma_map_[A-Za-z0-9_]*\s*\(",
            r"\bdma_unmap_[A-Za-z0-9_]*\s*\(",
            r"\biommu_attach[A-Za-z0-9_]*\s*\(",
            r"\biommu_map[A-Za-z0-9_]*\s*\(",
            r"\bioremap[A-Za-z0-9_]*\s*\(",
            r"\breadl\s*\(",
            r"\bwritel\s*\(",
            r"\barm_smccc[A-Za-z0-9_]*\s*\(",
            r"\bscsi_execute[A-Za-z0-9_]*\s*\(",
            r"\bsubmit_bio[A-Za-z0-9_]*\s*\(",
        )
        for pattern in forbidden:
            self.assertNotRegex(self.source, pattern)

    def test_no_kernel_pointer_format_is_exposed(self):
        self.assertNotRegex(self.source, r"%p(?:x|K|S|s|B)?")

    def test_documentation_requires_new_phone_approval(self):
        self.assertIn("fresh explicit approval", self.readme)
        self.assertIn("Do not copy or load", self.readme)
        self.assertIn("does not prove physical DMA behavior", self.readme)


if __name__ == "__main__":
    unittest.main(verbosity=2)
