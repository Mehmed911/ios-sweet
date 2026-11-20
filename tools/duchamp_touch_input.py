"""Bounded local host contacts -> actual QEMU VirtIO multitouch, no guest RPC injection."""
import re
import struct
import secrets
import time
from duchamp_live_input import Viewer, qmp

HTML = '''<!doctype html><html><meta charset="utf-8"><title>Darwin apps · multitouch</title>
<style>body{background:#111923;color:#e8edf0;font:18px system-ui;margin:32px}canvas{width:800px;height:480px;image-rendering:pixelated;touch-action:none;border:1px solid #7a8a98}button{padding:10px;margin:12px}small{display:block;color:#a8bbca}</style>
<h2>Darwin applications · QEMU</h2><canvas id="screen" width="160" height="96"></canvas><div id="state">Connecting…</div>
<button id="reconnect">Reconnect contacts</button><small>Orange / blue: launch or foreground. Green: background. Red: close. Purple: restart.<br>Drag title strips; resize lower-right corners. Multiple contacts capture independently.</small>
<script>
const c=document.getElementById('screen'),ctx=c.getContext('2d'),state=document.getElementById('state'),token=location.hash.slice(1);
let sid=null,seq=0,sending=false,queue=[],pointers=new Map();
async function post(path,body){const r=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json','X-Input-Token':token},body:JSON.stringify(body)});if(!r.ok)throw Error(await r.text());return r.json()}
async function connect(){queue=[];pointers.clear();try{const r=await post('/connect',{});sid=r.id;seq=0;state.textContent='Multitouch connected · real VirtIO';}catch(e){state.textContent='Waiting for XNU…';setTimeout(connect,500)}}
async function release(){if(!sid)return;const old=sid;sid=null;queue=[];pointers.clear();try{const r=await post('/disconnect',{id:old});state.textContent=r.released?'Contacts cancelled':'Disconnected · restart input session';}catch(e){state.textContent='Disconnected · delivery unconfirmed';}}
async function pump(){if(sending||!sid)return;sending=true;try{while(queue.length){const p=queue.shift();await post('/touch',{id:sid,seq:++seq,contacts:[p.contact],origin:p.origin})}}catch(e){state.textContent='Disconnected: '+e;await release();}finally{sending=false}}
function event(e,phase){e.preventDefault();if(!sid)return;let slot=pointers.get(e.pointerId);if(phase==='begin'){if(e.pointerType==='mouse'&&e.button!==0)return;if(slot!==undefined)return;slot=Array.from({length:11},(_,i)=>i).find(i=>!Array.from(pointers.values()).includes(i));if(slot===undefined){release();return}pointers.set(e.pointerId,slot);c.setPointerCapture(e.pointerId)}else if(slot===undefined)return;
 const r=c.getBoundingClientRect(),x=Math.max(0,Math.min(159,Math.floor((e.clientX-r.left)*160/r.width))),y=Math.max(0,Math.min(95,Math.floor((e.clientY-r.top)*96/r.height)));const p={contact:{slot,id:slot,phase,x,y},origin:e.isTrusted?'browser-multitouch':'untrusted-dom'};
 if(phase==='move'&&queue.length&&queue[queue.length-1].contact.phase==='move'&&queue[queue.length-1].contact.slot===slot)queue[queue.length-1]=p;else queue.push(p);
 if(phase==='end'||phase==='cancel'){pointers.delete(e.pointerId);if(c.hasPointerCapture(e.pointerId))c.releasePointerCapture(e.pointerId)}if(queue.length>64){release();return}pump()}
c.onpointerdown=e=>event(e,'begin');c.onpointermove=e=>event(e,'move');c.onpointerup=e=>event(e,'end');c.onpointercancel=e=>event(e,'cancel');c.oncontextmenu=e=>e.preventDefault();
window.onblur=release;window.onpagehide=release;document.onvisibilitychange=()=>{if(document.hidden)release()};document.getElementById('reconnect').onclick=async()=>{await release();await connect()};
setInterval(()=>{if(sid)post('/heartbeat',{id:sid}).catch(release)},1000);
async function frame(){try{const r=await fetch('/frame',{cache:'no-store'});if(r.ok){const b=await createImageBitmap(await r.blob());ctx.drawImage(b,0,0);b.close()}}catch(e){}setTimeout(frame,60)}frame();connect();
</script></html>'''


class TouchViewer(Viewer):
    max_body = 2048

    def __init__(self, *args, **kwargs):
        self.contacts = {}
        self.resync_required = False
        super().__init__(*args, **kwargs)

    def ready(self):
        status = qmp(self.runtime['qmp'], 'human-monitor-command', {'command-line': 'xp /1wx 0xa003c70'})
        match = re.search(r':\s*0x([0-9a-fA-F]+)', status)
        return match is not None and int(match[1], 16) == 15

    def batch(self, contacts, origin):
        if not isinstance(contacts, list) or not 1 <= len(contacts) <= 11:
            raise ValueError('one to eleven contacts required')
        pending = dict(self.contacts)
        events, seen = [], set()
        for c in contacts:
            if not isinstance(c, dict) or set(c) != {'slot', 'id', 'x', 'y', 'phase'}:
                raise ValueError('invalid contact fields')
            slot, cid, x, y, phase = (c[k] for k in ('slot', 'id', 'x', 'y', 'phase'))
            if any(type(v) is not int for v in (slot, cid, x, y)) or not 0 <= slot <= 10 or not 0 <= cid <= 10 or not 0 <= x < 160 or not 0 <= y < 96 or slot in seen or phase not in ('begin', 'move', 'end', 'cancel'):
                raise ValueError('invalid contact bounds/phase')
            seen.add(slot)
            old = pending.get(slot)
            if phase == 'begin':
                if old or any(p['id'] == cid for p in pending.values()):
                    raise ValueError('active slot or duplicate tracking ID')
            elif not old or old['id'] != cid:
                raise ValueError('stale contact')
            # QEMU's end/cancel carries no coordinate data; retain the last
            # accepted position and never imply that up moved the contact.
            kind = dict(begin='begin', move='update', end='end', cancel='cancel')[phase]
            events.append({'type': 'mtt', 'data': {'type': kind, 'slot': slot, 'tracking-id': -1 if phase in ('end', 'cancel') else cid, 'axis': 'x', 'value': 0}})
            if phase in ('begin', 'move'):
                for axis, value, span in [('x', x, 159), ('y', y, 95)]:
                    events.append({'type': 'mtt', 'data': {'type': 'data', 'slot': slot, 'tracking-id': cid, 'axis': axis, 'value': round(value * 32767 / span)}})
                pending[slot] = dict(c)
            else:
                del pending[slot]
        # QEMU10.2 drops a complete report if there are too few descriptors;
        # it does not synthesize SYN_DROPPED. Reserve enough actual queue space
        # before submitting the complete event set plus its implicit SYN.
        needed = 1 + sum(1 if e['data']['type'] == 'data' else 2 for e in events)
        space = self.wait_queue(needed)
        response = qmp(self.runtime['qmp'], 'input-send-event', {'events': events})
        self.contacts = pending
        self.journal(dict(kind='touch_device', origin=origin, contacts=contacts, qmp_events=events, queue_available=space, queue_required=needed, response=response))

    def queue_space(self):
        # Queue address registers are write-only in modern VirtIO MMIO. Use
        # QEMU's supported debug query, verified against the installed 10.2.1;
        # never infer an address from an unsuccessful register read.
        state = qmp(self.runtime['qmp'], 'x-query-virtio-queue-status',
                    {'path': '/machine/peripheral/duchamp-touch', 'queue': 0})
        if (state.get('name') != 'virtio-input' or state.get('queue-index') != 0 or
                state.get('vring-num') != 64 or state.get('inuse') != 0):
            raise ValueError('unsupported virtual input queue state')
        driver, consumed = state.get('vring-avail'), state.get('last-avail-idx')
        if (type(driver) is not int or driver % 2 or
                not self.runtime['ram_base'] <= driver <= self.runtime['ram_base'] + self.runtime['ram_bytes'] - 4 or
                type(consumed) is not int or not 0 <= consumed <= 65535):
            raise ValueError('invalid virtual queue address/index')
        available = struct.unpack_from('<H', self.memory, driver - self.runtime['ram_base'] + 2)[0]
        return (available - consumed) & 0xffff

    def wait_queue(self, needed):
        deadline = time.monotonic() + 2
        while time.monotonic() < deadline:
            space = self.queue_space()
            if needed <= space <= 64:
                return space
            if not self.ready():
                break
            time.sleep(.01)
        raise ValueError('virtual input queue backpressure timeout; no report submitted')

    def disconnect(self, reason):
        delivered = True
        if self.id:
            try:
                if self.contacts:
                    self.batch([dict(p, phase='cancel') for p in self.contacts.values()], reason)
            except (OSError, RuntimeError, ValueError) as e:
                delivered = False
                self.resync_required = True
                self.journal(dict(kind='cancel_not_delivered', error=str(e)))
            finally:
                self.contacts.clear()
                self.journal(dict(kind='disconnect', reason=reason))
                self.id = None
        return delivered

    def action(self, path, body):
        if path == '/event':
            raise ValueError('this profile accepts contact transactions, not tablet events')
        if path == '/connect':
            with self.lock:
                if body != {} or self.resync_required or not self.ready():
                    raise ValueError('touch source requires ready device and a clean input session')
                if not self.disconnect('source-replaced'):
                    raise ValueError('cancel delivery unverified; new guest input session required')
                self.id = secrets.token_hex(16)
                self.seq = 0
                self.last = time.monotonic()
                self.journal(dict(kind='connect'))
                return dict(id=self.id)
        if path == '/disconnect':
            with self.lock:
                if not isinstance(body, dict) or set(body) != {'id'} or not self.id or body['id'] != self.id:
                    raise ValueError('stale touch source')
                delivered = self.disconnect('source-disconnect')
                return dict(released=delivered, new_session_required=self.resync_required)
        if path != '/touch':
            return super().action(path, body)
        with self.lock:
            if not isinstance(body, dict) or set(body) != {'id', 'seq', 'contacts', 'origin'} or body['id'] != self.id or not self.id:
                raise ValueError('stale touch source/fields')
            if type(body['seq']) is not int or body['seq'] != self.seq + 1 or body['origin'] not in ('qmp-multitouch-test', 'browser-multitouch', 'untrusted-dom'):
                raise ValueError('invalid touch sequence/origin')
            if not self.ready():
                raise ValueError('touch driver disconnected')
            self.batch(body['contacts'], body['origin'])
            self.seq = body['seq']
            self.last = time.monotonic()
            return dict(sequence=self.seq)

    def handler(self):
        parent = super().handler()

        class Handler(parent):
            def do_GET(self):
                if self.path == '/':
                    self.reply(200, HTML.encode(), 'text/html; charset=utf-8')
                else:
                    super().do_GET()
        return Handler
