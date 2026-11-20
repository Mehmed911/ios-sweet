"""Local mouse viewer -> QMP -> real VirtIO device. Framebuffer mapping is read-only."""
import base64
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import mmap
import re
from pathlib import Path
import secrets
import socket
import struct
import threading
import time
import zlib


def qmp(path, command, arguments=None):
    with socket.socket(socket.AF_UNIX) as s:
        s.settimeout(5)
        s.connect(str(path))
        f = s.makefile('rwb', buffering=0)
        json.loads(f.readline())
        for cmd, args in [('qmp_capabilities', {}), (command, arguments or {})]:
            f.write(json.dumps(dict(execute=cmd, arguments=args)).encode() + b'\n')
            while True:
                line = f.readline()
                if not line:
                    raise RuntimeError('QMP disconnected')
                response = json.loads(line)
                if 'error' in response:
                    raise RuntimeError(response['error'])
                if 'return' in response:
                    break
        return response['return']


def png(raw, w=160, h=96):
    def chunk(kind, data):
        return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data))
    rgb = bytearray()
    for y in range(h):
        rgb.append(0)
        for x in range(w):
            b, g, r, _ = raw[(y * w + x) * 4:(y * w + x) * 4 + 4]
            rgb += bytes((r, g, b))
    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>2I5B', w, h, 8, 2, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(rgb)) + chunk(b'IEND', b'')


HTML = '''<!doctype html><html><meta charset="utf-8"><title>Darwin QEMU mouse</title>
<style>body{background:#111923;color:#e8edf0;font:18px system-ui;margin:32px}canvas{width:800px;height:480px;image-rendering:pixelated;touch-action:none;border:1px solid #7a8a98;cursor:none}button{padding:10px 20px;margin:12px}small{display:block;color:#a8bbca}</style>
<h2>Darwin · QEMU</h2><canvas id="screen" width="160" height="96"></canvas><div id="state">Connecting…</div>
<button id="reconnect">Reconnect mouse</button><small>Drag a window by its top strip; resize at its lower-right corner. Orange and blue buttons launch apps.</small>
<script>
const c=document.getElementById('screen'),ctx=c.getContext('2d'),state=document.getElementById('state'),token=location.hash.slice(1);
let sid=null,seq=0,down=false,sending=false,queue=[],trusted=0;
async function post(path,body){const r=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json','X-Input-Token':token},body:JSON.stringify(body)});if(!r.ok)throw Error(await r.text());return r.json()}
async function connect(){queue=[];down=false;try{const r=await post('/connect',{});sid=r.id;seq=0;state.textContent='Mouse connected · real VirtIO tablet';}catch(e){state.textContent='Waiting for XNU input…';setTimeout(connect,500)}}
async function pump(){if(sending||!sid)return;sending=true;try{while(queue.length){const {edge,...p}=queue.shift();await post('/event',{id:sid,seq:++seq,...p});}}catch(e){state.textContent='Input disconnected: '+e;await release();setTimeout(connect,500);}finally{sending=false;}}
function input(e,left){if(!sid)return;const r=c.getBoundingClientRect(),x=Math.max(0,Math.min(159,Math.floor((e.clientX-r.left)*160/r.width))),y=Math.max(0,Math.min(95,Math.floor((e.clientY-r.top)*96/r.height)));const p={x,y,left,origin:e.isTrusted?'browser-pointer':'untrusted-dom',edge:e.type!=='pointermove'};if(e.isTrusted)trusted++;if(!p.edge&&queue.length&&!queue[queue.length-1].edge&&queue[queue.length-1].left===left)queue[queue.length-1]=p;else queue.push(p);if(queue.length>64){release();return;}pump();}
c.onpointerdown=e=>{if(e.button!==0)return;e.preventDefault();down=true;c.setPointerCapture(e.pointerId);input(e,true)};
c.onpointermove=e=>{e.preventDefault();input(e,down)};
c.onpointerup=e=>{if(e.button!==0)return;down=false;input(e,false);if(c.hasPointerCapture(e.pointerId))c.releasePointerCapture(e.pointerId)};
async function release(){if(sid){const old=sid;sid=null;queue=[];down=false;try{await post('/disconnect',{id:old})}catch(e){}state.textContent='Mouse disconnected; button released';}}
window.onblur=release;document.onvisibilitychange=()=>{if(document.hidden)release()};window.onpagehide=release;
c.onpointercancel=release;c.oncontextmenu=e=>e.preventDefault();
document.getElementById('reconnect').onclick=async()=>{await release();await connect()};
setInterval(()=>{if(sid)post('/heartbeat',{id:sid}).catch(release)},1000);
async function frame(){try{const r=await fetch('/frame',{cache:'no-store'});if(r.ok){const b=await createImageBitmap(await r.blob());ctx.drawImage(b,0,0);b.close()}}catch(e){}setTimeout(frame,60)}frame();connect();
</script></html>'''


class Viewer:
    max_body = 512
    def __init__(self, runtime, output, port=0):
        self.runtime = runtime
        self.output = Path(output)
        self.output.mkdir(exist_ok=True)
        self.token = secrets.token_urlsafe(32)
        self.lock = threading.RLock()
        self.id = None
        self.seq = 0
        self.left = False
        self.x = self.y = 0
        self.last = 0
        self.events = []
        self.memory_file = open(runtime['memory'], 'rb')
        self.memory = mmap.mmap(self.memory_file.fileno(), runtime['ram_bytes'], access=mmap.ACCESS_READ)
        self.closed = threading.Event()
        self.http = ThreadingHTTPServer(('127.0.0.1', port), self.handler())
        self.url = 'http://127.0.0.1:%d/#%s' % (self.http.server_port, self.token)
        (self.output / 'viewer.json').write_text(json.dumps(dict(url=self.url, scope='local QEMU only; no phone'), indent=2) + '\n')
        self.thread = threading.Thread(target=self.http.serve_forever, daemon=True)
        self.thread.start()
        self.monitor = threading.Thread(target=self.watchdog, daemon=True)
        self.monitor.start()

    def journal(self, record):
        record = dict(host_monotonic=time.monotonic(), **record)
        self.events.append(record)
        with (self.output / 'input-events.jsonl').open('a') as f:
            f.write(json.dumps(record) + '\n')

    def read(self):
        r = self.runtime
        fb, canvas = r['framebuffer'], r['canvas']
        start = fb['base'] - r['ram_base'] + canvas['y'] * fb['stride'] + canvas['x'] * 4
        size = canvas['width'] * 4
        if start < 0 or start + (canvas['height'] - 1) * fb['stride'] + size > len(self.memory):
            raise ValueError('framebuffer outside mapped QEMU RAM')
        return b''.join(self.memory[start + y * fb['stride']:start + y * fb['stride'] + size] for y in range(canvas['height']))

    def device(self, x, y, left, origin):
        events = [{'type': 'abs', 'data': {'axis': 'x', 'value': round(x * 32767 / 159)}},
                  {'type': 'abs', 'data': {'axis': 'y', 'value': round(y * 32767 / 95)}},
                  {'type': 'btn', 'data': {'button': 'left', 'down': left}}]
        response = qmp(self.runtime['qmp'], 'input-send-event', {'events': events})
        self.x, self.y, self.left = x, y, left
        self.journal(dict(kind='device_event', origin=origin, x=x, y=y, left=left, qmp_events=events, response=response))

    def ready(self):
        status = qmp(self.runtime['qmp'], 'human-monitor-command', {'command-line': 'xp /1wx 0xa003e70'})
        match = re.search(r':\s*0x([0-9a-fA-F]+)', status)
        return match is not None and int(match[1], 16) == 15

    def disconnect(self, reason):
        if self.id:
            self.device(self.x, self.y, False, reason)
            self.journal(dict(kind='disconnect', reason=reason))
            self.id = None

    def watchdog(self):
        while not self.closed.wait(.25):
            with self.lock:
                if self.id and time.monotonic() - self.last > 3:
                    try:
                        self.disconnect('source-timeout')
                    except (OSError, RuntimeError):
                        self.id = None

    def action(self, path, body):
        with self.lock:
            if not isinstance(body, dict):
                raise ValueError('object required')
            if path == '/connect':
                if body:
                    raise ValueError('unexpected connect fields')
                if not self.ready():
                    raise ValueError('XNU input device not ready')
                self.disconnect('source-replaced')
                self.id = secrets.token_hex(16)
                self.seq = 0
                self.last = time.monotonic()
                self.journal(dict(kind='connect'))
                return dict(id=self.id)
            if not self.id or body.get('id') != self.id:
                raise ValueError('stale input source')
            self.last = time.monotonic()
            if path == '/heartbeat' and set(body) == {'id'}:
                return dict(alive=True)
            if path == '/disconnect' and set(body) == {'id'}:
                self.disconnect('source-disconnect')
                return dict(released=True)
            if path != '/event' or set(body) != {'id', 'seq', 'x', 'y', 'left', 'origin'}:
                raise ValueError('invalid event fields')
            x, y, seq, left = (body[k] for k in ('x', 'y', 'seq', 'left'))
            if type(seq) is not int or seq != self.seq + 1 or type(x) is not int or type(y) is not int or type(left) is not bool or not 0 <= x < 160 or not 0 <= y < 96:
                raise ValueError('invalid sequence, bounds or button')
            if body['origin'] not in ('browser-pointer', 'untrusted-dom', 'qmp-device-test'):
                raise ValueError('unknown origin')
            if not self.ready():
                raise ValueError('XNU input device disconnected')
            self.device(x, y, left, body['origin'])
            self.seq = seq
            return dict(sequence=seq)

    def handler(self):
        viewer = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_):
                pass

            def reply(self, status, content, mime):
                self.send_response(status)
                self.send_header('Content-Type', mime)
                self.send_header('Cache-Control', 'no-store')
                self.send_header('Content-Length', str(len(content)))
                self.end_headers()
                self.wfile.write(content)

            def do_GET(self):
                if self.path == '/':
                    self.reply(200, HTML.encode(), 'text/html; charset=utf-8')
                elif self.path == '/frame':
                    self.reply(200, png(viewer.read()), 'image/png')
                else:
                    self.reply(404, b'not found', 'text/plain')

            def do_POST(self):
                expected_origin = 'http://127.0.0.1:%d' % viewer.http.server_port
                if self.headers.get('X-Input-Token') != viewer.token or self.headers.get('Origin', expected_origin) != expected_origin:
                    self.reply(403, b'local input token/origin required', 'text/plain')
                    return
                try:
                    size = int(self.headers.get('Content-Length', '-1'))
                    if not 0 <= size <= viewer.max_body:
                        raise ValueError('body too large')
                    body = json.loads(self.rfile.read(size))
                    result = viewer.action(self.path, body)
                except (ValueError, OSError, RuntimeError) as e:
                    viewer.journal(dict(kind='rejected', error=str(e)))
                    self.reply(400, str(e).encode(), 'text/plain')
                else:
                    self.reply(200, json.dumps(result).encode(), 'application/json')
        return Handler

    def close(self):
        self.closed.set()
        self.http.shutdown()
        self.http.server_close()
        self.thread.join()
        self.monitor.join()
        self.memory.close()
        self.memory_file.close()
