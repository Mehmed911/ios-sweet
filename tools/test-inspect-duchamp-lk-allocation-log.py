#!/usr/bin/env python3
"""Targeted consistency tests derived from a locally captured real OEM log."""
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest


p = argparse.ArgumentParser()
p.add_argument("--log", type=Path, required=True)
p.add_argument("--capture", type=Path, required=True)
args = p.parse_args()
spec = importlib.util.spec_from_file_location("observer", Path(__file__).with_name("inspect-duchamp-lk-allocation-log.py"))
observer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(observer)
raw, receipt = args.log.read_bytes(), json.loads(args.capture.read_text())


class Observations(unittest.TestCase):
    def test_actual_android_a_log(self):
        r = observer.inspect(raw, receipt)
        self.assertTrue(r["observation_consistent"])
        self.assertEqual(r["slot_observed"], "_a")
        self.assertEqual(r["mb_avb_allocations"][0]["start"], 0x334a00000)
        self.assertEqual(r["mb_avb_allocations"][0]["end_exclusive"], 0x33d600000)
        self.assertEqual([x["index"] for x in r["producer_boot_index_messages"]], [794, 794])
        self.assertFalse(r["physical_access_authorized"])
        self.assertFalse(r["complete_slot_b_handoff_established"])
        self.assertFalse(r["firmware_origin_authenticated"])
        bb = r["blackbox_printed_metadata"]
        self.assertTrue(bb["metadata_consistent"])
        self.assertEqual(bb["ring_capacity_from_pinned_code"], 5)
        self.assertEqual(bb["printed_content_headers"][0]["cursor_before_write"], 4)
        self.assertFalse(bb["historical_record_recovered"])
        self.assertFalse(bb["record_freshness_established"])

    def test_wrong_slot_label(self):
        c = copy.deepcopy(receipt)
        next(x for x in c["commands"] if x["name"] == "slot")["text"] = "_b"
        self.assertFalse(observer.inspect(raw, c)["observation_consistent"])

    def test_different_acquisition_boot(self):
        c = copy.deepcopy(receipt)
        next(x for x in c["commands"] if x["name"] == "boot_after")["sha256"] = "0" * 64
        self.assertFalse(observer.inspect(raw, c)["observation_consistent"])

    def test_changed_raw_bytes(self):
        self.assertFalse(observer.inspect(raw + b"altered", receipt)["observation_consistent"])

    def changed(self, old, new):
        b = raw.replace(old, new)
        self.assertNotEqual(raw, b)
        c = copy.deepcopy(receipt)
        rec = next(x for x in c["commands"] if x["name"] == "lk_log")
        rec.update(bytes=len(b), sha256=hashlib.sha256(b).hexdigest())
        return observer.inspect(b, c)

    def test_missing_allocation_even_with_updated_checksum(self):
        self.assertFalse(self.changed(b"name:mb_avb", b"name:unknown")["observation_consistent"])

    def test_mismatched_release_even_with_updated_checksum(self):
        self.assertFalse(self.changed(b"start 0x334a00000 size:", b"start 0x334a01000 size:")["observation_consistent"])

    def test_duplicate_alloc_even_with_updated_checksum(self):
        allocation = next(x for x in raw.split(b"\n") if b"name:mb_avb" in x)
        self.assertFalse(self.changed(allocation, allocation + b"\n" + allocation)["observation_consistent"])

    def test_interval_overflow(self):
        with self.assertRaises(ValueError):
            observer.interval((1 << 64) - 4096, 8192)

    def test_permission_error_is_not_an_allocation_log(self):
        self.assertFalse(observer.inspect(b"head: /proc/pl_lk: Permission denied\n", receipt)["observation_consistent"])

    def test_corrupted_blackbox_magic_with_updated_checksum(self):
        self.assertFalse(self.changed(b"0x56775af41bcde0f0", b"0x56775af41bcde0f1")["observation_consistent"])

    def test_invalid_ring_cursor_with_updated_checksum(self):
        self.assertFalse(self.changed(b"dump_count=4", b"dump_count=6")["observation_consistent"])

    def test_conflicting_boot_generation_with_updated_checksum(self):
        self.assertFalse(self.changed(b"boot_index=31a", b"boot_index=319")["observation_consistent"])

    def test_missing_blackbox_identity_with_updated_checksum(self):
        self.assertFalse(self.changed(b"boot_index=31a", b"unknown_id=31a")["observation_consistent"])

    def test_invalid_record_stride_with_updated_checksum(self):
        self.assertFalse(self.changed(b"dump_size=0x800000", b"dump_size=0x900000")["observation_consistent"])

    def test_missing_acquisition_boot_id(self):
        c = copy.deepcopy(receipt)
        c["commands"] = [x for x in c["commands"] if x["name"] != "boot_before"]
        self.assertFalse(observer.inspect(raw, c)["observation_consistent"])

    def test_consistent_old_generation_is_not_trusted_history(self):
        b = raw.replace(b"boot_index=31a", b"boot_index=319").replace(b"boot_index = 794", b"boot_index = 793")
        c = copy.deepcopy(receipt)
        rec = next(x for x in c["commands"] if x["name"] == "lk_log")
        rec.update(bytes=len(b), sha256=hashlib.sha256(b).hexdigest())
        r = observer.inspect(b, c)
        self.assertFalse(r["blackbox_printed_metadata"]["record_freshness_established"])
        self.assertFalse(r["blackbox_printed_metadata"]["origin_authenticated"])
        self.assertFalse(r["blackbox_printed_metadata"]["historical_record_recovered"])
        self.assertFalse(r["complete_slot_b_handoff_established"])


unittest.main(argv=[__file__])
