#!/usr/bin/env python3
"""Malformed host touch transactions must not reach the virtual device."""
import tempfile
import struct
from pathlib import Path
import unittest
from unittest.mock import patch
from duchamp_touch_input import TouchViewer


class TouchHost(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='duchamp-touch-host-')
        root = Path(self.tmp.name)
        ram = root / 'ram'
        data = bytearray(160 * 96 * 4)
        struct.pack_into('<H', data, 0x202, 64)
        ram.write_bytes(data)
        self.ram = ram
        self.queue_address = 0x200
        self.commands = []
        self.status = 15
        self.consumed = 0
        self.queue_size = 64

        def qmp(_, cmd, arguments):
            self.commands.append((cmd, arguments))
            if cmd == 'human-monitor-command':
                return '000000000a003c70: 0x%08x' % self.status
            if cmd == 'x-query-virtio-queue-status':
                self.assertEqual(arguments, {'path': '/machine/peripheral/duchamp-touch', 'queue': 0})
                return dict(name='virtio-input', **{'queue-index': 0, 'vring-num': self.queue_size, 'inuse': 0,
                                                  'vring-avail': self.queue_address, 'last-avail-idx': self.consumed})
            return {}
        self.mock = patch('duchamp_touch_input.qmp', qmp)
        self.mock.start()
        self.viewer = TouchViewer(dict(memory=str(ram), ram_bytes=ram.stat().st_size, ram_base=0, qmp='mock',
                                      framebuffer=dict(base=0, stride=640), canvas=dict(x=0, y=0, width=160, height=96)), root / 'viewer')
        self.sid = self.viewer.action('/connect', {})['id']

    def tearDown(self):
        self.viewer.close()
        self.mock.stop()
        self.tmp.cleanup()

    def inputs(self):
        return [a for c, a in self.commands if c == 'input-send-event']

    def c(self, slot=0, cid=1, phase='begin', x=0, y=95):
        return dict(slot=slot, id=cid, phase=phase, x=x, y=y)

    def send(self, *contacts, seq=1):
        return self.viewer.action('/touch', dict(id=self.sid, seq=seq, contacts=list(contacts), origin='qmp-multitouch-test'))

    def test_two_contacts_single_transaction(self):
        self.send(self.c(), self.c(10, 10, x=159, y=0))
        self.assertEqual(len(self.inputs()), 1)
        self.assertEqual(len(self.inputs()[0]['events']), 6)
        self.assertEqual(set(self.viewer.contacts), {0, 10})
        self.assertEqual(self.inputs()[0]['events'][-2]['data']['value'], 32767)
        self.assertEqual(self.viewer.events[-1]['queue_required'], 9)

    def test_invalid_bounds_do_not_emit(self):
        for key, value in [('slot', 11), ('slot', -1), ('id', 11), ('x', 160), ('y', 96), ('x', True), ('phase', 'unknown')]:
            contact = self.c()
            contact[key] = value
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                self.send(contact)
        self.assertFalse(self.inputs())

    def test_batch_rejected_atomically(self):
        with self.assertRaises(ValueError):
            self.send(self.c(), self.c(1, 2, x=160))
        self.assertFalse(self.inputs())
        self.assertFalse(self.viewer.contacts)

    def test_duplicate_contact_rejected(self):
        for contacts in [(self.c(), self.c()), (self.c(), self.c(1, 1))]:
            with self.assertRaises(ValueError):
                self.send(*contacts)
        self.assertFalse(self.inputs())

    def test_unknown_move_end_cancel(self):
        for phase in ['move', 'end', 'cancel']:
            with self.assertRaises(ValueError):
                self.send(self.c(phase=phase))
        self.assertFalse(self.inputs())

    def test_replay_and_wrong_identity(self):
        self.send(self.c())
        with self.assertRaises(ValueError):
            self.send(self.c())
        with self.assertRaises(ValueError):
            self.send(self.c(cid=2, phase='move'), seq=2)
        self.assertEqual(len(self.inputs()), 1)

    def test_cancel_and_reuse_slot(self):
        self.send(self.c())
        self.send(self.c(phase='cancel'), seq=2)
        self.assertFalse(self.viewer.contacts)
        self.assertEqual(self.inputs()[-1]['events'][0]['data']['tracking-id'], -1)
        self.send(self.c(cid=2), seq=3)

    def test_lost_source_cancels_all(self):
        self.send(self.c(), self.c(1, 2))
        self.viewer.action('/disconnect', dict(id=self.sid))
        self.assertFalse(self.viewer.contacts)
        self.assertEqual(len(self.inputs()[-1]['events']), 2)
        with self.assertRaises(ValueError):
            self.send(self.c(), seq=2)

    def test_disconnected_driver_denies(self):
        self.status = 0
        with self.assertRaises(ValueError):
            self.send(self.c())
        self.assertFalse(self.inputs())

    def test_backpressure_never_submits_partial_report(self):
        self.consumed = 64
        with self.assertRaises(ValueError):
            self.send(self.c())
        self.assertFalse(self.inputs())
        self.assertFalse(self.viewer.contacts)

    def test_untrusted_queue_address_denied(self):
        self.queue_address = 0xfffff000
        with self.assertRaises(ValueError):
            self.send(self.c())
        self.assertFalse(self.inputs())

    def test_failed_cancel_blocks_source_reconnect(self):
        self.send(self.c())
        self.consumed = 64
        result = self.viewer.action('/disconnect', dict(id=self.sid))
        self.assertFalse(result['released'])
        self.assertTrue(result['new_session_required'])
        with self.assertRaises(ValueError):
            self.viewer.action('/connect', {})

    def test_wrong_queue_format_denied(self):
        self.queue_size = 128
        with self.assertRaises(ValueError):
            self.send(self.c())
        self.assertFalse(self.inputs())

    def test_wrapped_queue_index(self):
        self.consumed = 65530
        with self.ram.open('r+b') as f:
            f.seek(0x202)
            f.write(struct.pack('<H', 58))
        self.send(self.c())
        self.assertEqual(self.viewer.events[-1]['queue_available'], 64)

    def test_missing_debug_interface_denied(self):
        with patch('duchamp_touch_input.qmp', side_effect=RuntimeError('CommandNotFound')):
            with self.assertRaises(RuntimeError):
                self.viewer.batch([self.c()], 'qmp-multitouch-test')
        self.assertFalse(self.inputs())


if __name__ == '__main__':
    unittest.main(verbosity=2)
