#!/usr/bin/env python3
"""Serve one pinned Duchamp QEMU display and digitizer over Windows loopback."""

import argparse
import io
import json
import os
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from PIL import Image

WIDTH, HEIGHT, STRIDE = 1220, 2712, 4992
FRAMEBUFFER_OFFSET = 0xFCC2F000 - 0x40000000

PAGE = """<!doctype html>
<html lang="ar" dir="rtl"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Duchamp QEMU</title>
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
let ready = false, pointer = null, lastMove = 0, lastUrl, sending = Promise.resolve();
async function refresh() {
  try {
    const response = await fetch('/frame', {cache:'no-store'});
    ready = response.headers.get('X-Guest-Ready') === '1';
    display.classList.toggle('ready', ready);
    status.textContent = ready ? 'انقر أو اسحب داخل الشاشة' : 'جارٍ إقلاع iOS وتحميل الإعداد…';
    if (response.status === 200) {
      const url = URL.createObjectURL(await response.blob());
      display.src = url;
      if (lastUrl) URL.revokeObjectURL(lastUrl);
      lastUrl = url;
    }
  } catch (_) {
    ready = false;
    status.textContent = 'جلسة المحاكي متوقفة';
  }
  setTimeout(refresh, 180);
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
  if (pointer !== event.pointerId || event.timeStamp-lastMove < 34) return;
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


def make_handler(run, port):
    lock = threading.Lock()
    pointer_down = False
    host = f'127.0.0.1:{port}'

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def send_body(self, status, mime, body=b'', ready=False):
            self.send_response(status)
            self.send_header('Content-Type', mime)
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Content-Length', str(len(body)))
            self.send_header('X-Guest-Ready', str(int(ready)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if self.headers.get('Host') != host:
                self.send_error(403)
                return
            if self.path == '/':
                self.send_body(200, 'text/html; charset=utf-8', PAGE.encode())
            elif self.path == '/frame':
                raw = read_frame(run)
                if len(raw) != STRIDE * HEIGHT:
                    self.send_body(204, 'image/jpeg')
                    return
                frame = Image.frombytes('RGB', (WIDTH, HEIGHT), raw, 'raw', 'BGRX', STRIDE, 1)
                result = io.BytesIO()
                frame.resize((WIDTH // 2, HEIGHT // 2)).save(result, 'JPEG', quality=83)
                self.send_body(200, 'image/jpeg', result.getvalue(), (run / 'live-ready').is_file())
            else:
                self.send_error(404)

        def do_POST(self):
            nonlocal pointer_down
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
                        if (phase == 'down') == pointer_down:
                            raise ValueError
                        with (run / 'live-touch.jsonl').open('ab') as queue:
                            queue.write((json.dumps(payload) + '\n').encode())
                        pointer_down = phase != 'up'
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
    parser.add_argument('run', type=Path)
    parser.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if not args.command or args.run.exists():
        parser.error('a fresh run directory and its QEMU command are required')
    with ThreadingHTTPServer(('127.0.0.1', args.port), make_handler(args.run, args.port)) as server:
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        try:
            return subprocess.run(args.command, check=False).returncode
        finally:
            server.shutdown()
            worker.join()


if __name__ == '__main__':
    raise SystemExit(main())
