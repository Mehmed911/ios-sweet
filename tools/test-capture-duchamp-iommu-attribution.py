#!/usr/bin/env python3
"""Tests for bounded per-thread IOMMU attribution capture parsing."""

import importlib.util
from pathlib import Path
import unittest


REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "tools/capture-duchamp-iommu-attribution.py"
SPEC = importlib.util.spec_from_file_location("iommu_attribution", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class IommuAttributionTests(unittest.TestCase):
    def test_only_positive_rows_are_retained(self):
        text = "\n".join((
            "vdec,100,101,12,iommu:map,1,/sec,",
            "dd,200,200,0,iommu:map,0,/sec,",
            "worker,300,301,2,iommu:unmap,1,/sec,",
            "worker,300,301,0,swiotlb:swiotlb_bounced,0,/sec,",
        ))
        rows = MODULE.parse_rows(text)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["event"], "iommu:map")
        self.assertEqual(rows[0]["count"], 12)

    def test_missing_event_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "missing per-thread events"):
            MODULE.parse_rows("vdec,100,101,12,iommu:map,1,/sec,")

    def test_iommu_format_has_no_device_field(self):
        text = """field:u64 iova; offset:8; size:8; signed:0;
field:u64 paddr; offset:16; size:8; signed:0;
field:size_t size; offset:24; size:8; signed:0;
"""
        fields = MODULE.parse_iommu_format(text)
        self.assertEqual(fields, ["iova", "paddr", "size"])
        self.assertNotIn("dev_name", fields)


if __name__ == "__main__":
    unittest.main(verbosity=2)
