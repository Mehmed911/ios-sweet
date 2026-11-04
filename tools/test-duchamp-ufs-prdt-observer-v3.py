#!/usr/bin/env python3
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "duchamp/diagnostics/ufs-prdt-observer-v3/duchamp_ufs_prdt_observer_v3.c"
README = ROOT / "duchamp/diagnostics/ufs-prdt-observer-v3/README.md"


class UfsPrdtObserverV3Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SOURCE.read_text(encoding="utf-8")
        cls.readme = README.read_text(encoding="utf-8")

    def test_target_and_abi_are_pinned(self):
        for value in (
            '"mediatek,mt8183-ufshci"',
            '"duchamp"',
            '"mt6897"',
            "gcf2c2dc91b9e-ab11782407",
        ):
            self.assertIn(value, self.source)

    def test_map_capture_is_exactly_one_bounded_range(self):
        for value in (
            "DUCHAMP_DMA_RANGE_COUNT 1U",
            "map[DUCHAMP_DMA_RANGE_COUNT].size",
            "cpu_start - dma_start != offset",
            "dma_range_cpu_start=0x%016llx",
            "dma_range_dma_start=0x%016llx",
            "dma_range_size=0x%016llx",
            "dma_range_offset=0x%016llx",
            "dma_range_identity=%u",
        ):
            self.assertIn(value, self.source)

    def test_direct_and_inverse_translation_are_compared(self):
        for value in (
            "sg_dma_address(sg)",
            "sg_phys(sg)",
            "phys_to_dma(hba->dev, original_phys)",
            "dma_to_phys(hba->dev, dma_address)",
            "raw_dma_phys_matches",
            "raw_dma_phys_mismatches",
            "observed_direct_identity_route=%u",
        ):
            self.assertIn(value, self.source)

    def test_swiotlb_state_and_segments_are_bounded(self):
        for value in (
            "READ_ONCE(swiotlb->nslabs)",
            "READ_ONCE(swiotlb->force_bounce)",
            "is_swiotlb_buffer(hba->dev, translated_phys)",
            "swiotlb_segments",
            "no_swiotlb_observed=%u",
        ):
            self.assertIn(value, self.source)

    def test_report_is_root_read_only_and_coherent(self):
        self.assertIn(
            "DEVICE_ATTR(sweet_ufs_prdt_observation_v3, 0400", self.source
        )
        self.assertIn("static DEFINE_SPINLOCK(duchamp_stats_lock)", self.source)
        self.assertIn("snapshot = duchamp_stats", self.source)
        self.assertIn("coherent_snapshot=1", self.source)
        self.assertNotIn("DEVICE_ATTR_RW", self.source)
        self.assertNotIn("DEVICE_ATTR_WO", self.source)
        self.assertNotIn("module_param", self.source)

    def test_runtime_change_rejects_observation(self):
        self.assertIn("duchamp_dma_contract_stable(hba->dev)", self.source)
        self.assertIn("update.runtime_contract_changes = 1", self.source)
        self.assertIn("update.rejected_calls = 1", self.source)

        callback = self.source.split(
            "static void duchamp_observe_ufs_prdt_v3", 1
        )[1].split("static u64 duchamp_min_or_zero", 1)[0]
        self.assertNotIn("duchamp_direct_contract_matches", callback)
        self.assertIn("dev_iommu_fwspec_get(dev)", self.source)

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

    def test_no_kernel_pointer_is_exposed(self):
        self.assertNotRegex(self.source, r"%p(?:x|K|S|s|B)?")

    def test_documentation_requires_separate_live_approval(self):
        self.assertIn("fresh explicit approval", self.readme)
        self.assertIn("Do not copy or load", self.readme)
        self.assertIn("local build and verification only", self.readme)


if __name__ == "__main__":
    unittest.main(verbosity=2)
