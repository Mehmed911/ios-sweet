#!/usr/bin/env python3
"""Serve one pinned Duchamp QEMU display and digitizer over Windows loopback."""

import argparse
import io
import json
import os
import subprocess
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from PIL import Image

WIDTH, HEIGHT, STRIDE = 1220, 2712, 4992
FRAMEBUFFER_OFFSET = 0xFCC2F000 - 0x40000000

PAGE = """<!doctype html>
<html lang="ar" dir="rtl"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Duchamp QEMU Fast</title>
<style>
*{box-sizing:border-box}body{margin:0;background:#15191e;color:#eef2f6;font:15px system-ui}
main{height:100dvh;display:grid;grid-template-rows:auto minmax(0,1fr) auto;justify-items:center;gap:10px;padding:12px}
header,footer{text-align:center}header{font-size:17px;font-weight:600}small{display:block;color:#b5c2cf;font-weight:400}
img{height:100%;max-width:100%;aspect-ratio:1220/2712;object-fit:contain;background:#07090c;touch-action:none;user-select:none}
img.ready{cursor:pointer}button{background:#2a3743;color:white;border:0;border-radius:8px;padding:6px 14px;cursor:pointer}
</style>
<main><header>محاكي Duchamp <small id="status">جارٍ تشغيل المحاكي…</small></header>
<img id="display" alt="شاشة المحاكي" draggable="false"><footer><button id="stop">إيقاف المحاكي</button></footer></main>
<script>
const display = document.getElementById('display'), status = document.getElementById('status');
let ready = false, pointer = null, lastMove = 0, lastUrl, frameVersion = '', sending = Promise.resolve();
async function refresh() {
  try {
    const response = await fetch('/frame?after='+frameVersion, {cache:'no-store'});
    ready = response.headers.get('X-Guest-Ready') === '1';
    display.classList.toggle('ready', ready);
    status.textContent = ready ? 'انقر أو اسحب داخل الشاشة' : 'جارٍ إقلاع iOS وتحميل الإعداد…';
    if (response.status === 200) {
      frameVersion = response.headers.get('X-Frame-Version') || '';
      const url = URL.createObjectURL(await response.blob());
      display.src = url;
      if (lastUrl) URL.revokeObjectURL(lastUrl);
      lastUrl = url;
    }
  } catch (_) {
    ready = false;
    status.textContent = 'جلسة المحاكي متوقفة';
  }
  setTimeout(refresh, ready ? 8 : 160);
}
function post(path, payload) {
  sending = sending.catch(() => {}).then(() => fetch(path, {
    method:'POST', headers:{'Content-Type':'application/json','X-Guest-Input':'1'}, body:JSON.stringify(payload)
  }));
}
function touch(event, phase) {
  const box = display.getBoundingClientRect();
  const width = Math.min(box.width, box.height * 1220 / 2712), height = width * 2712 / 1220;
  const x = (event.clientX - box.left - (box.width - width)/2) / width;
  const y = (event.clientY - box.top - (box.height - height)/2) / height;
  post('/touch', [phase, Math.max(0, Math.min(1079, Math.floor(x*1125)-22)),
                         Math.max(0, Math.min(2399, Math.floor(y*2436)-18))]);
}
display.addEventListener('pointerdown', event => {
  if (!ready || pointer !== null || event.button !== 0) return;
  pointer = event.pointerId; lastMove = 0;
  display.setPointerCapture(pointer); touch(event, 'down');
});
display.addEventListener('pointermove', event => {
  if (pointer !== event.pointerId || event.timeStamp-lastMove < 32) return;
  lastMove = event.timeStamp; touch(event, 'move');
});
for (const name of ['pointerup','pointercancel','lostpointercapture']) display.addEventListener(name, event => {
  if (pointer !== event.pointerId) return;
  pointer = null; touch(event, 'up');
});
document.getElementById('stop').onclick = () => { ready = false; post('/stop', []); };
refresh();
</script></html>"""


def read_frame(run):
    try:
        with (run / 'live-frame.raw').open('rb') as source:
            return source.read(STRIDE * HEIGHT)
    except FileNotFoundError:
        try:
            with (run / 'guest-ram.bin').open('rb') as source:
                return os.pread(source.fileno(), STRIDE * HEIGHT, FRAMEBUFFER_OFFSET)
        except FileNotFoundError:
            return b''


def consumed_touches(run):
    try:
        with (run / 'quartzcore-events.jsonl').open('rb') as trace:
            size = trace.seek(0, os.SEEK_END)
            tail = os.pread(trace.fileno(), min(size, 65536), max(0, size - 65536))
    except FileNotFoundError:
        return 0
    for line in reversed(tail.splitlines()):
        if b'"gesture": "desktop_' not in line:
            continue
        try:
            return max(0, json.loads(line)['step'] - 12)
        except (KeyError, ValueError):
            continue
    return 0


def make_handler(run, port, native_windows=False):
    lock = threading.Lock()
    frame_lock = threading.Lock()
    journal = run / 'live-touch.jsonl'
    touch_ack = 0
    frame_version = ''
    jpeg = b''
    host = f'127.0.0.1:{port}'
    page = PAGE
    if native_windows:
        page = page.replace('Duchamp QEMU Fast', 'Duchamp QEMU Windows')
        page = page.replace('محاكي Duchamp', 'محاكي Duchamp على ويندوز')

    def version():
        try:
            return str((run / 'live-frame.raw').stat().st_mtime_ns)
        except FileNotFoundError:
            return ''

    def image(after):
        nonlocal frame_version, jpeg
        current = version()
        deadline = time.monotonic() + 0.35
        while current and current == after and time.monotonic() < deadline:
            time.sleep(0.009)
            current = version()
        if current and current == after:
            return 204, b'', current
        with frame_lock:
            if current and current == frame_version:
                return 200, jpeg, current
            raw = read_frame(run)
            if len(raw) != STRIDE * HEIGHT:
                return 204, b'', ''
            frame = Image.frombytes('RGB', (WIDTH, HEIGHT), raw, 'raw', 'BGRX', STRIDE, 1)
            result = io.BytesIO()
            frame.resize((WIDTH // 2, HEIGHT // 2), Image.Resampling.BILINEAR).save(result, 'JPEG', quality=83)
            frame_version, jpeg = current, result.getvalue()
            return 200, jpeg, current

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def send_body(self, status, mime, body=b'', ready=False, version=''):
            self.send_response(status)
            self.send_header('Content-Type', mime)
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Content-Length', str(len(body)))
            self.send_header('X-Guest-Ready', str(int(ready)))
            self.send_header('X-Frame-Version', version)
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if self.headers.get('Host') != host:
                self.send_error(403)
                return
            if self.path == '/':
                self.send_body(200, 'text/html; charset=utf-8', page.encode())
            elif self.path == '/frame' or self.path.startswith('/frame?after='):
                after = self.path.removeprefix('/frame?after=')
                status, data, current = image(after)
                self.send_body(status, 'image/jpeg', data, (run / 'live-ready').is_file(), current)
            else:
                self.send_error(404)

        def do_POST(self):
            nonlocal touch_ack
            if (self.headers.get('Host') != host or self.headers.get('Origin') != 'http://' + host
                    or self.headers.get('X-Guest-Input') != '1'):
                self.send_error(403)
                return
            try:
                size = int(self.headers.get('Content-Length', '0'))
                if not 0 < size < 128:
                    raise ValueError
                payload = json.loads(self.rfile.read(size))
                if self.path == '/stop' and payload == [] and run.is_dir():
                    (run / 'live-stop').touch()
                elif self.path == '/touch' and (run / 'live-ready').is_file():
                    phase, x, y = payload
                    if (phase not in ('down', 'move', 'up') or type(x) is not int or type(y) is not int
                            or not (0 <= x < 1080 and 0 <= y < 2400)):
                        raise ValueError
                    with lock:
                        lines = journal.read_bytes().splitlines() if journal.exists() else []
                        last = json.loads(lines[-1]) if lines else ['up', x, y]
                        pointer_down = last[0] != 'up'
                        if (phase == 'down') == pointer_down:
                            raise ValueError
                        if phase == 'move':
                            touch_ack = max(touch_ack, consumed_touches(run))
                            if len(lines) - touch_ack >= 2:
                                self.send_body(204, 'text/plain')
                                return
                        events = [payload]
                        if phase == 'up' and max(abs(last[1] - x), abs(last[2] - y)) >= 3:
                            events.insert(0, ['move', x, y])
                        with journal.open('ab') as queue:
                            queue.write(''.join(json.dumps(event) + '\n' for event in events).encode())
                else:
                    self.send_error(409)
                    return
            except (TypeError, ValueError):
                self.send_error(400)
                return
            self.send_body(204, 'text/plain')

    return Handler


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', required=True, type=int)
    parser.add_argument('--native-windows', action='store_true')
    parser.add_argument('--attach', action='store_true', help='view an existing QEMU session without restarting it')
    parser.add_argument('run', type=Path)
    parser.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if args.attach:
        if args.command or not (args.run / 'live-ready').is_file() or (args.run / 'result.json').exists():
            parser.error('attach requires a running interactive QEMU session')
        layout = json.loads((args.run / 'layout.json').read_text())
        if not layout['qemu_only'] or layout['physical_storage']:
            parser.error('attach requires the QEMU RAM-only layout')
    elif not args.command or args.run.exists():
        parser.error('a fresh run directory and its QEMU command are required')
    with ThreadingHTTPServer(('127.0.0.1', args.port), make_handler(args.run, args.port, args.native_windows)) as server:
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        try:
            if args.attach:
                while not (args.run / 'result.json').exists() and (args.run / 'guest-ram.bin').is_file():
                    time.sleep(0.4)
                return 0
            return subprocess.run(args.command, check=False).returncode
        finally:
            server.shutdown()
            worker.join()


if __name__ == '__main__':
    raise SystemExit(main())
