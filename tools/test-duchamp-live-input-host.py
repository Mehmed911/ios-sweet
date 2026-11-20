#!/usr/bin/env python3
"""Adversarial local input transport tests, with a mocked QMP endpoint."""
import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch
import urllib.request
import urllib.error
from duchamp_live_input import Viewer


class HostTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='duchamp-host-input-')
        self.root = Path(self.tmp.name)
        memory = self.root / 'ram'
        memory.write_bytes(bytes(160 * 96 * 4))
        self.status = 0
        self.commands = []

        def qmp(_path, command, args):
            self.commands.append((command, args))
            if command == 'human-monitor-command':
                return '000000000a003e70: 0x%08x' % self.status
            return {}
        self.mock = patch('duchamp_live_input.qmp', qmp)
        self.mock.start()
        runtime = dict(memory=str(memory), ram_bytes=memory.stat().st_size, ram_base=0,
                       qmp='mock', framebuffer=dict(base=0, stride=640), canvas=dict(x=0, y=0, width=160, height=96))
        self.viewer = Viewer(runtime, self.root / 'viewer')

    def tearDown(self):
        self.viewer.close()
        self.mock.stop()
        self.tmp.cleanup()

    def connect(self):
        self.status = 15
        return self.viewer.action('/connect', {})['id']

    def inputs(self):
        return [a for cmd, a in self.commands if cmd == 'input-send-event']

    def test_not_ready_cannot_connect_or_emit(self):
        with self.assertRaises(ValueError):
            self.viewer.action('/connect', {})
        self.assertFalse(self.inputs())

    def test_mapping_readonly(self):
        with self.assertRaises(TypeError):
            self.viewer.memory[0] = 1

    def test_coordinate_boundaries(self):
        sid = self.connect()
        self.viewer.action('/event', dict(id=sid, seq=1, x=159, y=95, left=True, origin='browser-pointer'))
        self.assertEqual([e['data']['value'] for e in self.inputs()[-1]['events'][:2]], [32767, 32767])
        self.assertTrue(self.inputs()[-1]['events'][2]['data']['down'])

    def test_malformed_values_no_device_event(self):
        sid = self.connect()
        base = dict(id=sid, seq=1, x=0, y=0, left=False, origin='browser-pointer')
        for key, value in (('x', -1), ('x', 160), ('y', 96), ('x', True), ('y', 1.0),
                           ('left', 1), ('seq', 2), ('seq', True), ('id', 'old'), ('origin', 'unknown')):
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                self.viewer.action('/event', dict(base, **{key: value}))
        self.assertFalse(self.inputs())

    def test_replay_rejected(self):
        sid = self.connect()
        request = dict(id=sid, seq=1, x=0, y=0, left=False, origin='browser-pointer')
        self.viewer.action('/event', request)
        with self.assertRaises(ValueError):
            self.viewer.action('/event', request)
        self.assertEqual(len(self.inputs()), 1)

    def test_disconnect_releases_and_rejects_stale(self):
        sid = self.connect()
        self.viewer.action('/event', dict(id=sid, seq=1, x=20, y=20, left=True, origin='browser-pointer'))
        self.viewer.action('/disconnect', dict(id=sid))
        self.assertFalse(self.inputs()[-1]['events'][2]['data']['down'])
        fresh = self.connect()
        self.assertNotEqual(sid, fresh)
        with self.assertRaises(ValueError):
            self.viewer.action('/heartbeat', dict(id=sid))

    def test_driver_disconnect_no_event(self):
        sid = self.connect()
        self.status = 0
        with self.assertRaises(ValueError):
            self.viewer.action('/event', dict(id=sid, seq=1, x=20, y=20, left=True, origin='browser-pointer'))
        self.assertFalse(self.inputs())

    def test_watchdog_releases(self):
        sid = self.connect()
        self.viewer.action('/event', dict(id=sid, seq=1, x=20, y=20, left=True, origin='browser-pointer'))
        self.viewer.last = time.monotonic() - 4
        deadline = time.monotonic() + 2
        while self.viewer.id and time.monotonic() < deadline:
            time.sleep(.02)
        self.assertIsNone(self.viewer.id)
        self.assertFalse(self.inputs()[-1]['events'][2]['data']['down'])

    def test_http_token_origin_and_body_limit(self):
        base = self.viewer.url.split('/#')[0]
        for headers, body, code in (({}, b'{}', 403),
                ({'X-Input-Token': self.viewer.token, 'Origin': 'https://untrusted.example'}, b'{}', 403),
                ({'X-Input-Token': self.viewer.token}, b' ' * 513, 400)):
            with self.assertRaises(urllib.error.HTTPError) as error:
                urllib.request.urlopen(urllib.request.Request(base + '/connect', body, headers, method='POST'))
            self.assertEqual(error.exception.code, code)
            error.exception.close()
        self.assertFalse(self.inputs())


if __name__ == '__main__':
    unittest.main(verbosity=2)
