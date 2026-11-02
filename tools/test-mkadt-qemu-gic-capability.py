#!/usr/bin/env python3
"""Keep QEMU's exact GIC capability out of every phone ADT."""

import unittest

import mkadt


def child(parent, name):
    matches = [node for node in parent.children if node.name == name]
    if len(matches) != 1:
        raise AssertionError(f"expected one {name} node, found {len(matches)}")
    return matches[0]


def prop(node, name):
    matches = [value for key, flags, value in node.props
               if key == name and flags == 0]
    if len(matches) > 1:
        raise AssertionError(f"duplicate {name} property")
    return matches[0] if matches else None


class QemuGicCapabilityTest(unittest.TestCase):
    def test_qemu_gets_exact_capability(self):
        tree = mkadt.build(seed=bytes(64), qemu=True, duchamp_window=True)
        gic = child(child(tree, "arm-io"), "gic")
        self.assertEqual(
            prop(gic, "duchamp,gic-mmio-auth-v1"),
            mkadt.u64(
                mkadt.QEMU_GICD,
                mkadt.GICD_SIZE,
                mkadt.QEMU_GICR,
                mkadt.GICR_SIZE,
            ),
        )

    def test_phone_never_gets_qemu_capability(self):
        for kwargs in ({}, {"duchamp_window": True}, {"highmem": True}):
            with self.subTest(kwargs=kwargs):
                tree = mkadt.build(seed=bytes(64), **kwargs)
                gic = child(child(tree, "arm-io"), "gic")
                self.assertIsNone(prop(gic, "duchamp,gic-mmio-auth-v1"))


if __name__ == "__main__":
    unittest.main()
