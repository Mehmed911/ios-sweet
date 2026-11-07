# QEMU guest only. Kernel e465723a; iOS 20F66 arm64 cache E5420DB3-30D0-33AA-8B7E-05B5038BB46D.
# Trace mode is read-only. The opt-in experiments alter a live QEMU register.
python
import gdb
import hashlib
import json
import os
import struct
from collections import Counter

CACHE_BASE = 0x180000000
KERNEL_SHA256 = 'e465723a540844817a5b9cb36c14984d660f9a8e41f6638240527b469189182b'
FRAMEBUFFER_OFFSET = 0xfcc2f000 - 0x40000000
FRAMEBUFFER_STRIDE = 4992
FRAMEBUFFER_HEIGHT = 2712
USER_SITES = {
    'render_display': 0x1882d90dc,
    'transaction_commit': 0x1882d5148,
    'context_commit': 0x1882a7e3c,
    'display_set_enabled': 0x1883911e4,
    'display_set_power_state': 0x18838dbc0,
    'display_disable_updates': 0x1884deae8,
    'display_create_surface': 0x188372634,
    'display_present_surface': 0x1885244ec,
    'display_clear_layers': 0x18852bc30,
    'display_swap_layer': 0x188531698,
    'sw_new_context': 0x188437dd4,
    'metal_new_context': 0x188437f9c,
    'null_new_context': 0x188437e28,
    'display_metal_result': 0x1885330c4,
    'metal_device_result': 0x18837b758,
    'vsync_callback': 0x1882b1800,
    'timer_callback': 0x1883480a4,
    'iosurface_create': 0x1a392fed4,
    'swap_set_layer': 0x1af1c0848,
    'kern_swap_set_layer': 0x1af1c08a4,
    'layer_surface_id': 0x1af1c09a0,
}
points = []
hits = Counter()
state = {}
wake_test = os.environ.get('SWEET_QEMU_POWER_EVENT') == '1'
software_test = os.environ.get('SWEET_QEMU_SOFTWARE_RENDERER') == '1'
registers = {r.name.upper(): r.name for r in gdb.newest_frame().architecture().registers()}

def reg(name):
    return int(gdb.parse_and_eval('$' + name)) & ((1 << 64) - 1)

def read(address, size):
    return bytes(gdb.selected_inferior().read_memory(address, size))

def uint(address, size=8):
    return int.from_bytes(read(address, size), 'little')

def opcode_at(address):
    try:
        return read(address, 4).hex()
    except gdb.MemoryError:
        # The breakpoint can precede the first demand-paged instruction fetch.
        return None

def process():
    thread = reg(registers['TPIDR_EL1'])
    thread_ro = uint(thread + 0x488)
    if uint(thread_ro) != thread:
        raise ValueError('thread_ro back pointer mismatch')
    proc = uint(thread_ro + 0x10)
    if not proc:
        return 0, 'kernel'
    name = read(proc + 0x5d1, 33).split(b'\0', 1)[0]
    if not name:
        name = read(proc + 0x5c0, 17).split(b'\0', 1)[0]
    return uint(proc + 0x60, 4), name.decode('ascii', 'replace')

def emit(kind, pid, name, **fields):
    event = dict(event=kind, pid=pid, process=name, **fields)
    with open('quartzcore-events.jsonl', 'a') as log:
        log.write(json.dumps(event) + '\n')
    gdb.write('QUARTZCORE ' + json.dumps(event) + '\n')

def framebuffer():
    with open('guest-ram.bin', 'rb') as ram:
        ram.seek(FRAMEBUFFER_OFFSET)
        pixels = ram.read(FRAMEBUFFER_STRIDE * FRAMEBUFFER_HEIGHT)
    if len(pixels) != FRAMEBUFFER_STRIDE * FRAMEBUFFER_HEIGHT:
        raise ValueError('short physical framebuffer')
    return pixels


def user_stack():
    thread = reg(registers['TPIDR_EL1'])
    saved = uint(thread + 0x110)
    if uint(saved, 4) != 0x15:
        raise ValueError('unexpected ARM64 saved state')
    fp, lr, sp, pc = struct.unpack('<4Q', read(saved + 0xf0, 32))
    frames = []
    while fp and fp % 8 == 0 and len(frames) < 12:
        try:
            next_fp, return_pc = struct.unpack('<2Q', read(fp, 16))
        except gdb.MemoryError:
            break
        frames.append(hex(return_pc))
        if next_fp <= fp or next_fp - fp > 1 << 20:
            break
        fp = next_fp
    return dict(tid=uint(thread + 0x550), user_pc=hex(pc), user_lr=hex(lr), user_sp=hex(sp), frames=frames)

class Trace(gdb.Breakpoint):
    def __init__(self, address, kind):
        super().__init__('*' + hex(address), type=gdb.BP_HARDWARE_BREAKPOINT, internal=True)
        self.kind = kind

    def stop(self):
        kind = self.kind
        try:
            if kind == 'timer_key':
                down = reg('x3') & 0xff
                press = state.get('power_off', False) and 'wake_pressed' not in state and down
                release = state.get('wake_pressed', False) and not down
                if press or release:
                    if read(reg('pc'), 4) != bytes.fromhex('de030094') or reg('x1') != 12 or reg('x2') != 0x40:
                        raise ValueError('unexpected HID event construction')
                    # This one-shot experiment uses the guest's existing HID
                    # timer to deliver a power press/release after display off.
                    # Change only the usage argument, never firmware or code.
                    state['wake_pressed'] = bool(down)
                    state['rewrite_usage'] = True
                    return True
                return False
            pid, name = process()
            if kind == 'shared_cache':
                if name not in ('backboardd', 'SpringBoard') or name in state.get('cache_users', ()):
                    return False
                # _shared_region_check_np has just obtained the start address,
                # at SP+0x38, from vm_shared_region_start_address.
                base = uint(reg('sp') + 0x38)
                slide = base - CACHE_BASE
                if slide < 0 or slide > 0x56110000 or slide % 0x4000:
                    raise ValueError('unexpected cache base ' + hex(base))
                emit(kind, pid, name, base=hex(base), slide=hex(slide))
                state.setdefault('cache_users', set()).add(name)
                if name == 'backboardd':
                    state['slide'] = slide
                    return True
                if state.get('slide', slide) != slide:
                    raise ValueError('SpringBoard has a different cache slide')
                return False
            if name not in ('backboardd', 'SpringBoard') and kind not in ('present', 'present_done', 'copy_rows'):
                return False
            if kind == 'springboard_ipc' and name != 'SpringBoard':
                return False
            hits[kind, name] += 1
            fields = {}
            if kind == 'power':
                fb = uint(reg('x0') + 0xd8)
                fields = dict(value=uint(uint(reg('x20') + 0x20)), vsync=uint(fb + 0x98), object_va=hex(fb))
                state['power_off'] = fields['value'] == 0
                if fields['value'] == 0 and 'ipc_site' not in state:
                    state['install_ipc_site'] = True
            elif kind in ('swap', 'present'):
                record = read(reg('x1'), 0x46c)
                surfaces = struct.unpack_from('<4I', record, 0x54)
                mask, = struct.unpack_from('<I', record, 0x104)
                fields = dict(swap_id=struct.unpack_from('<I', record, 0x50)[0],
                              surfaces=surfaces, mask=hex(mask), vsync=uint(reg('x0') + 0x98))
                if kind == 'present' and any(surface and mask & (1 << i) for i, surface in enumerate(surfaces)):
                    state['nonempty_present'] = fields.copy()
                    state['frame_before'] = framebuffer()
                    state['install_copy_site'] = True
            elif kind == 'copy_rows':
                # At the pinned AppleCLCD memmove call, x25 is the layer
                # and x20 is the row. The first hit describes the clipped copy.
                if opcode_at(reg('pc')) != 'e8ba0394' or reg('x20') != 0:
                    raise ValueError('unexpected AppleCLCD row copy site')
                layer, width, height = reg('x25'), reg('x2'), reg('x21')
                surface = state['nonempty_present']['surfaces'][layer]
                fb = uint(reg('x29') - 0x70)
                start = reg('x0') - uint(fb + 0xc8)
                stride = reg('x9') & 0xffffffff
                if (not surface or not 0 < height <= FRAMEBUFFER_HEIGHT or not 0 < width <= stride
                        or start < 0 or start % FRAMEBUFFER_STRIDE + width > FRAMEBUFFER_STRIDE
                        or start + (height - 1) * FRAMEBUFFER_STRIDE + width > len(state['frame_before'])):
                    raise ValueError('unexpected AppleCLCD layer bounds')
                rows = sorted({height * fraction // 4 for fraction in range(4)} | {height - 1})
                state['sample'] = (layer, surface, width, [
                    (row, start + row * FRAMEBUFFER_STRIDE, read(reg('x1') + row * stride, width))
                    for row in rows])
                state['disable_site'] = self
                return True
            elif kind == 'present_done':
                if 'nonempty_present' not in state:
                    return False
                pixels, before = framebuffer(), state['frame_before']
                sample = state.get('sample')
                if sample:
                    layer, surface, width, expected_rows = sample
                    rows = []
                    for row, offset, expected in expected_rows:
                        before_row = before[offset:offset + width]
                        actual = pixels[offset:offset + width]
                        rows.append(dict(row=row, offset=offset, bytes=width,
                            source_sha256=hashlib.sha256(expected).hexdigest(),
                            physical_sha256=hashlib.sha256(actual).hexdigest(),
                            matches=actual == expected, changed=actual != before_row))
                    emit('layer_pixels', pid, name, layer=layer, surface_id=surface, rows=rows,
                         swap_id=state['nonempty_present']['swap_id'])
                with open('native-frame.raw', 'xb') as frame:
                    frame.write(pixels)
                emit(kind, pid, name, sha256=hashlib.sha256(pixels).hexdigest(),
                     before_sha256=hashlib.sha256(before).hexdigest(), **state['nonempty_present'])
                return True
            elif kind == 'springboard_ipc':
                fields = user_stack()
            elif kind == 'software_fallback':
                if name != 'backboardd' or reg('x0') or state.get('software_attempted'):
                    return False
                if opcode_at(reg('pc')) != '400900b4':
                    raise ValueError('renderer fallback branch does not match')
                state['software_attempted'] = True
                state['redirect_renderer'] = True
                return True
            else:
                pc, lr = reg('pc'), reg('x30')
                fields = dict(pc=hex(pc), lr=hex(lr), opcode=opcode_at(pc),
                              args=[hex(reg('x' + str(i))) for i in range(5)])
                if kind == 'layer_surface_id':
                    fields.update(layer=reg('x24'), surface_id=reg('x0') & 0xffffffff,
                                  surface=hex(reg('x21')), connection=hex(reg('x20')))
            # Layer clears can exhaust the sample cap before the first real frame.
            has_surface = ((kind in ('swap_set_layer', 'kern_swap_set_layer') and reg('x2'))
                           or (kind == 'layer_surface_id' and reg('x0'))
                           or (kind in ('swap', 'present') and any(fields['surfaces'])))
            if hits[kind, name] <= 12 or has_surface:
                emit(kind, pid, name, **fields)
            sample_once = kind in ('vsync_callback', 'timer_callback', 'springboard_ipc')
            if sample_once and hits[kind, name] >= 4:
                state['disable_site'] = self
            return (state.get('install_ipc_site', False) or state.get('install_copy_site', False)
                    or sample_once and hits[kind, name] >= 4)
        except Exception as error:
            state['error'] = str(error)
            gdb.write('QUARTZCORE_TRACE_ERROR ' + str(error) + '\n')
            return True

try:
    with open('layout.json') as source:
        layout = json.load(source)
    if (not layout['qemu_only'] or layout['physical_storage'] or layout['kernel_sha256'] != KERNEL_SHA256
            or layout['ram_base'] != 0x40000000):
        raise RuntimeError('this script requires the pinned QEMU-only RAM layout')
    if wake_test and software_test:
        raise RuntimeError('select one experiment per run')
    cache = Trace(0xfffffe0007885ee0, 'shared_cache')
    points.append(cache)
    gdb.execute('continue')
    if 'slide' not in state:
        raise RuntimeError('no backboardd cache slide')
    points.extend(Trace(va + state['slide'], name) for name, va in USER_SITES.items())
    points.extend(Trace(va, name) for name, va in {
        'power': 0xfffffe0007a4e3d8, 'swap': 0xfffffe0007a4dfec,
        'present': 0xfffffe0007a4dc24, 'present_done': 0xfffffe0007a4db58}.items())
    if wake_test:
        points.append(Trace(0xfffffe0007a51038, 'timer_key'))
    if software_test:
        points.append(Trace(0x1882e25b0 + state['slide'], 'software_fallback'))
    while True:
        gdb.execute('continue')
        if state.pop('rewrite_usage', False):
            gdb.execute('set $x2 = 0x30', to_string=True)
            emit('qemu_power_key', 0, 'kernel', down=state['wake_pressed'])
        elif state.pop('redirect_renderer', False):
            # EAGLServer::renderer expects an OGL::Context at its common
            # assignment. Route one observed nil Metal result through
            # QuartzCore's own SWContext constructor.
            slide = state['slide']
            gdb.execute('set $x30 = ' + hex(0x1882e25d4 + slide), to_string=True)
            gdb.execute('set $pc = ' + hex(USER_SITES['sw_new_context'] + slide), to_string=True)
            emit('qemu_software_fallback', *process(), return_to=hex(0x1882e25d4 + slide))
        elif state.pop('install_ipc_site', False):
            state['ipc_site'] = Trace(0xfffffe0007314af8, 'springboard_ipc')
            points.append(state['ipc_site'])
        elif state.pop('install_copy_site', False):
            points.append(Trace(0xfffffe0007a4df10, 'copy_rows'))
        elif 'disable_site' in state:
            state.pop('disable_site').enabled = False
        else:
            break
finally:
    for point in points:
        point.delete()
    gdb.execute('detach')
end
