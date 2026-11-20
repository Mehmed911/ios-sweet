#!/usr/bin/env python3
"""Bounds and byte-identity checks for the passive framebuffer observer."""
import hashlib
import unittest
import qemu_frame_witness as witness


class FrameWitness(unittest.TestCase):
    def setUp(self):
        self.fb = {'width': 3, 'height': 2, 'stride': 16}
        self.raw = bytes(range(32))
        self.spec = dict(x=1, y=0, width=2, height=2,
                         sha256=hashlib.sha256(self.raw[4:12] + self.raw[20:28]).hexdigest())

    def test_padding_is_excluded(self):
        pixels, result = witness.observe(self.raw, self.spec, self.fb)
        self.assertEqual(pixels, self.raw[4:12] + self.raw[20:28])
        self.assertTrue(result['matched'])

    def test_wrong_pixels_do_not_match(self):
        self.assertFalse(witness.observe(bytes(32), self.spec, self.fb)[1]['matched'])

    def test_truncated_sample(self):
        with self.assertRaises(ValueError): witness.observe(self.raw[:-1], self.spec, self.fb)

    def test_out_of_bounds(self):
        for changes in ({'x': -1}, {'y': 2}, {'width': 3}, {'height': 0}, {'x': 1 << 64}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                witness.validate({**self.spec, **changes}, self.fb)

    def test_noninteger(self):
        with self.assertRaises(ValueError): witness.validate({**self.spec, 'x': True}, self.fb)

    def test_digest(self):
        with self.assertRaises(ValueError): witness.validate({**self.spec, 'sha256': 'bad'}, self.fb)

    def test_unknown_fields(self):
        with self.assertRaises(ValueError): witness.validate({**self.spec, 'address': 0}, self.fb)

    def test_stride(self):
        with self.assertRaises(ValueError): witness.validate(self.spec, {**self.fb, 'stride': 8})

    def test_sequence(self):
        sequence = [{'name': 'first', **self.spec}, {'name': 'next', **self.spec}]
        self.assertEqual(witness.validate_sequence(sequence, self.fb), sequence)

    def test_sequence_rejects_duplicate(self):
        with self.assertRaises(ValueError):
            witness.validate_sequence([{'name': 'first', **self.spec}] * 2, self.fb)

    def test_sequence_rejects_path_or_extra_fields(self):
        for entry in ({'name': '../file', **self.spec}, {'name': 'ok', **self.spec, 'output': 'file'}):
            with self.subTest(entry=entry), self.assertRaises(ValueError):
                witness.validate_sequence([entry], self.fb)

    def test_sequence_rejects_unbounded_count(self):
        for sequence in ([], [{'name': 'a', **self.spec}] * 9):
            with self.assertRaises(ValueError): witness.validate_sequence(sequence, self.fb)

    def test_explicit_long_profile(self):
        sequence = [{'name': 'frame_' + chr(97 + i), **self.spec} for i in range(16)]
        self.assertEqual(witness.validate_sequence(sequence, self.fb, max_observations=16), sequence)
        with self.assertRaises(ValueError): witness.validate_sequence(sequence, self.fb)
        with self.assertRaises(ValueError): witness.validate_sequence(sequence, self.fb, max_observations=32)
        with self.assertRaises(ValueError): witness.validate_sequence(sequence + [{'name': 'last', **self.spec}], self.fb, max_observations=16)


unittest.main()
