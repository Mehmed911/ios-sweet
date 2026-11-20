#!/usr/bin/env python3
"""Offline phase/range tests; no hardware or boot permissions are produced."""

import unittest

from duchamp_memory_placement import BOOT_PHASES, check_boot_lifetimes


def span(name, start, size, first, last):
    return {"name": name, "role": name, "start": start, "bytes": size,
            "alignment": 0x1000, "length_alignment": 0x1000,
            "first_phase": first, "last_phase": last}


class LifetimeTests(unittest.TestCase):
    def setUp(self):
        self.memory = {"schema_version": 1,
                       "ram_banks": [{"start": 0x1000, "bytes": 0x20000}]}
        self.profile = {"schema_version": 1, "name": "synthetic", "buffers": [
            span("compressed-input", 0x1000, 0x2000, BOOT_PHASES[0], BOOT_PHASES[0]),
            span("decompression-scratch", 0x3000, 0x1000, BOOT_PHASES[0], BOOT_PHASES[0]),
            span("lk-output", 0x4000, 0x3000, BOOT_PHASES[0], BOOT_PHASES[3]),
            span("fdt", 0x8000, 0x1000, BOOT_PHASES[0], BOOT_PHASES[4]),
            span("xnu-window", 0x10000, 0x10000, BOOT_PHASES[3], BOOT_PHASES[4]),
        ], "claims": []}
        self.profile["claims"] = [{**row, "name": "claim-" + row["name"],
                                    "kind": "buffer-claim", "buffer": row["name"]}
                                   for row in self.profile["buffers"]]

    def result(self):
        return check_boot_lifetimes(self.memory, self.profile)

    def findings(self, problem):
        return [row for row in self.result()["findings"] if row["problem"] == problem]

    def test_complete_geometry_never_grants_ownership(self):
        result = self.result()
        self.assertFalse(result["physical_execution_authorized"])
        self.assertEqual(len(result["findings"]), 5)
        self.assertEqual(len(self.findings("unknown-dma-ownership")), 5)

    def test_self_reported_dma_is_not_evidence(self):
        for row in self.profile["buffers"]:
            row["dma_ownership"] = "independently-established"
        self.profile["physical_execution_authorized"] = True
        self.assertEqual(len(self.findings("unknown-dma-ownership")), 5)
        self.assertFalse(self.result()["physical_execution_authorized"])

    def test_modem_overlap(self):
        self.profile["claims"].append({**span("modem", 0x11000, 0x1000,
                                            BOOT_PHASES[0], BOOT_PHASES[4]),
                                       "kind": "excluded-reservation"})
        self.assertEqual(self.findings("overlaps-active-reservation")[0]["region"], "xnu-window")

    def test_decompression_input_output_overlap(self):
        self.profile["buffers"][0]["start"] = 0x4000
        self.assertEqual(self.findings("overlaps-live-buffer")[0]["other"], "lk-output")

    def test_decompression_scratch_overlap(self):
        self.profile["buffers"][1]["start"] = 0x4000
        self.assertEqual(self.findings("overlaps-live-buffer")[0]["other"], "lk-output")

    def test_unknown_decompression_extent(self):
        for index in (0, 1):
            self.profile["buffers"][index]["start"] = None
        self.assertEqual(len(self.findings("unknown-buffer-extent")), 2)

    def test_released_lk_claim_does_not_cover_xnu_entry(self):
        self.profile["claims"][2]["last_phase"] = BOOT_PHASES[0]
        missing = self.findings("missing-claim-during-phase")
        self.assertEqual([row["other"] for row in missing], list(BOOT_PHASES[1:4]))

    def test_reservation_begins_after_first_write(self):
        self.profile["claims"][2]["first_phase"] = BOOT_PHASES[1]
        self.assertEqual(self.findings("missing-claim-during-phase")[0]["other"], BOOT_PHASES[0])

    def test_nonconcurrent_buffer_reuse(self):
        self.profile["buffers"][0]["start"] = 0x10000
        self.assertEqual(self.findings("overlaps-live-buffer"), [])

    def test_one_phase_overlap_is_rejected(self):
        self.profile["buffers"][0].update(start=0x10000, last_phase=BOOT_PHASES[3])
        self.assertTrue(self.findings("overlaps-live-buffer"))

    def test_invalid_lifetime(self):
        for first, last in ((BOOT_PHASES[4], BOOT_PHASES[0]), ("unknown", BOOT_PHASES[0]),
                            (BOOT_PHASES[0], "never")):
            with self.subTest(first=first, last=last), self.assertRaises(ValueError):
                self.profile["buffers"][0].update(first_phase=first, last_phase=last)
                self.result()

    def test_overflow_and_alignment(self):
        for start, size in (((1 << 64) - 0x1000, 0x2000), (0x1001, 0x1000),
                             (0x1000, 0x1001), (-1, 0x1000), (True, 0x1000)):
            with self.subTest(start=start, size=size), self.assertRaises(ValueError):
                self.profile["buffers"][0].update(start=start, bytes=size)
                self.result()

    def test_outside_ram(self):
        self.profile["buffers"][0]["start"] = 0x30000
        self.assertTrue(self.findings("outside-declared-ram"))

    def test_missing_buffer(self):
        self.profile["buffers"].pop(1)
        self.profile["claims"].pop(1)
        self.assertEqual(self.findings("missing-required-lifetime-buffer")[0]["region"],
                         "decompression-scratch")

    def test_duplicate_name(self):
        self.profile["buffers"][1]["name"] = "compressed-input"
        with self.assertRaises(ValueError):
            self.result()

    def test_unknown_claim_target(self):
        self.profile["claims"][0]["buffer"] = "missing"
        with self.assertRaises(ValueError):
            self.result()

    def test_unknown_claim_kind(self):
        self.profile["claims"][0]["kind"] = "grant"
        with self.assertRaises(ValueError):
            self.result()

    def test_unknown_schema(self):
        for version in (2, True, None):
            with self.subTest(version=version), self.assertRaises(ValueError):
                self.profile["schema_version"] = version
                self.result()

    def test_unknown_memory_map_schema(self):
        self.memory["schema_version"] = True
        with self.assertRaises(ValueError):
            self.result()


if __name__ == "__main__":
    unittest.main(verbosity=2)
