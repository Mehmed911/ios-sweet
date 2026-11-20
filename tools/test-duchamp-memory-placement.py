#!/usr/bin/env python3
"""Exercise the offline interval checker and its fail-closed decision."""

import unittest

from duchamp_memory_placement import Interval, U64_MAX, check_candidate, checked_range


def region(role, start, size, alignment=0x1000):
    return {"name": role, "role": role, "start": start, "bytes": size,
            "alignment": alignment, "length_alignment": alignment}


class PlacementTests(unittest.TestCase):
    def setUp(self):
        self.memory_map = {
            "schema_version": 1,
            "ram_banks": [region("ram", 0x1000, 0x20000)],
            "fixed_reservations": [],
            "dynamic_requests": [],
        }
        self.candidate = {
            "name": "synthetic",
            "xnu_window": region("xnu-window", 0x10000, 0x10000),
            "regions": [
                region("bootshim", 0x1000, 0x1000),
                region("bootshim-stack", 0x2000, 0x1000),
                region("embedded-payload", 0x3000, 0x2000),
                region("xnu-segment", 0x10000, 0x1000),
                region("md0", 0x11000, 0x1000),
                region("md1", 0x12000, 0x1000),
                region("adt", 0x13000, 0x1000),
                region("boot-args", 0x14000, 0x1000),
                region("xnu-allocator", 0x15000, 0xb000),
            ],
        }

    def report(self):
        return check_candidate(self.memory_map, self.candidate)

    def findings(self, problem):
        return [item["region"] for item in self.report()["structural_findings"]
                if item["problem"] == problem]

    def test_adjacent_ranges_with_no_physical_authorization(self):
        self.assertEqual(self.report()["structural_findings"], [])
        self.assertEqual(self.report()["decision"], "BLOCKED_BY_MEMORY_EVIDENCE")
        self.assertFalse(self.report()["physical_execution_authorized"])

    def test_self_reported_authorization_does_not_grant_access(self):
        self.memory_map["physical_execution_authorized"] = True
        self.candidate["same_boot_firmware_verified"] = True
        self.assertFalse(self.report()["physical_execution_authorized"])

    def test_uint64_input_boundaries(self):
        self.assertEqual(Interval.from_row({"start": U64_MAX - 1, "bytes": 1}).end, U64_MAX)
        for start, size in ((True, 1), (1, True), ("0", 1), (0, 0), (-1, 1), (0, -1),
                            (U64_MAX, 1), (1, U64_MAX), (U64_MAX + 1, 1), (0, U64_MAX + 1)):
            with self.subTest(start=start, size=size), self.assertRaises(ValueError):
                Interval.from_row({"start": start, "bytes": size})

    def test_bad_alignment_or_length(self):
        for row in (region("bad", 0x1800, 0x1000), region("bad", 0x1000, 17),
                    region("bad", 0x1000, 0x1000, 3), region("bad", 0x1000, 0x1000, False)):
            with self.subTest(row=row), self.assertRaises(ValueError):
                checked_range(row)

    def test_adjacent_banks_can_cover_runtime(self):
        self.memory_map["ram_banks"] = [region("ram1", 0x1000, 0x15000),
                                         region("ram2", 0x16000, 0xb000)]
        self.assertEqual(self.findings("outside-declared-ram"), [])

    def test_gap_in_declared_ram(self):
        self.memory_map["ram_banks"] = [region("ram1", 0x1000, 0x14000),
                                         region("ram2", 0x16000, 0xb000)]
        self.assertEqual(self.findings("outside-declared-ram"), ["xnu-allocator", "xnu-window"])

    def test_fixed_no_map_overlap_and_boundary(self):
        self.memory_map["fixed_reservations"] = [
            {**region("no-map", 0x5000, 0x1000), "flags": ["no-map"]},
            {**region("blocked", 0x12000, 0x1000), "flags": ["no-map"]},
        ]
        self.assertEqual(self.findings("intersects-fixed-reservation"), ["md1", "xnu-window"])

    def test_dynamic_request_can_overlap_staging(self):
        self.memory_map["dynamic_requests"] = [
            {"name": "DPMAIF", "allocation_ranges": [region("alloc", 0x2000, 0x2000)]},
        ]
        self.assertEqual(self.findings("intersects-unresolved-dynamic-reservation"),
                         ["bootshim-stack", "embedded-payload"])

    def test_dynamic_without_location_has_no_safe_gap(self):
        self.memory_map["dynamic_requests"] = [{"name": "unknown", "allocation_ranges": []}]
        self.assertEqual(len(self.findings("intersects-unresolved-dynamic-reservation")), 10)

    def test_partial_overlap_rejected(self):
        self.candidate["regions"][4]["bytes"] = 0x2000
        self.assertEqual(self.findings("overlaps-candidate-region"), ["md0"])

    def test_kernel_ramdisk_collision(self):
        self.candidate["regions"][3]["bytes"] = 0x2000
        self.assertEqual(self.findings("overlaps-candidate-region"), ["xnu-segment"])

    def test_destination_outside_window(self):
        self.candidate["regions"][5]["start"] = 0x20000
        self.assertEqual(self.findings("destination-outside-xnu-window"), ["md1"])

    def test_staging_inside_runtime_window(self):
        self.candidate["regions"][2]["start"] = 0x18000
        self.assertEqual(self.findings("staging-intersects-xnu-window"), ["embedded-payload"])

    def test_missing_md1(self):
        self.candidate["regions"].pop(5)
        self.assertEqual(self.findings("missing-required-region"), ["md1"])

    def test_unknown_region_role(self):
        self.candidate["regions"][5]["role"] = "xnu-window"
        self.assertEqual(self.findings("unknown-region-role"), ["md1"])

    def test_unknown_schema(self):
        self.memory_map["schema_version"] = True
        with self.assertRaises(ValueError):
            self.report()


if __name__ == "__main__":
    unittest.main(verbosity=2)
