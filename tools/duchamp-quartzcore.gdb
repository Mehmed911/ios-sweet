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
SOFTWARE_WIDTH = 1125
SOFTWARE_HEIGHT = 2436
SOFTWARE_STRIDE = 4608
TOUCH_TIMER = 0xfffffe0007a51038
TOUCH_TIMER_RESUME = 0xfffffe0007a510b0
TOUCH_TIMER_DELAY = 0xfffffe0007a510f4
TOUCH_SEND = 0xfffffe0007a5191c
# Finger starts within the digitizer's bottom-edge region.
SWIPE_Y = (2380, 2350, 2290, 2180, 2020, 1810, 1580, 1350, 1180, 1180)
# Center of the first visible language row in the pinned Setup display.
ENGLISH_TAP_Y = 530
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
setup_trace = os.environ.get('SWEET_QEMU_SETUP_TRACE') == '1'
setup_session = os.environ.get('SWEET_QEMU_SETUP_SESSION') == '1'
setup_without_proximity = os.environ.get('SWEET_QEMU_SETUP_WITHOUT_PROXIMITY') == '1'
setup_software_scanout = os.environ.get('SWEET_QEMU_SETUP_SOFTWARE_SCANOUT') == '1'
setup_swipe = os.environ.get('SWEET_QEMU_SETUP_SWIPE') == '1'
setup_region = os.environ.get('SWEET_QEMU_SETUP_REGION') == '1'
setup_live = os.environ.get('SWEET_QEMU_SETUP_INTERACTIVE') == '1'
setup_submissions = {}
ui_processes = ('backboardd', 'SpringBoard', 'Setup') if setup_trace else ('backboardd', 'SpringBoard')
setup_capture_delays = (0, 60, 120, 180, 240, 300)
swipe_capture_delays = (45, 120, 240, 480, 720)
region_capture_delays = (60, 180, 360, 540)
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

def user_ivar(object_address, offset_address):
    offset = uint(offset_address + state['slide'], 4)
    if not object_address or not 8 <= offset < 0x1000 or offset % 8:
        return 0
    return uint(object_address + offset)


def string_hint(address, match):
    if not address:
        return None
    try:
        header = read(address, 64)
    except gdb.MemoryError:
        return None
    data = [header[16:]]
    for offset in (16, 24, 32):
        pointer = int.from_bytes(header[offset:offset + 8], 'little')
        if pointer:
            try:
                data.append(read(pointer, 64))
            except gdb.MemoryError:
                pass
    for chunk in data:
        value = chunk.split(b'\0', 1)[0].decode('ascii', 'replace')
        if value.isascii() and match(value):
            return value
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

def task_image_base(pid):
    proc = uint(0xfffffe0007c04550)
    for _ in range(512):
        if not proc:
            break
        if uint(proc + 0x60, 4) == pid:
            task = proc + uint(0xfffffe0007b807d0)
            base = uint(task + 0x600)
            if 0x100000000 <= base < 0x160000000 and base % 0x4000 == 0:
                return base
            break
        proc = uint(proc)
    raise ValueError('cannot locate Mach-O base for PID ' + str(pid))


def cstring(address, size):
    if not address:
        return b''
    data = bytearray()
    for _ in range(size):
        byte = read(address + len(data), 1)
        if byte == b'\0':
            return bytes(data)
        data.extend(byte)
    return b''


def mobile_domain(base):
    # Pinned launchd domain registry: 11 buckets and a next pointer at 0x18.
    descriptor = base + 0x6d3f8
    matches = []
    seen = set()
    for i in range(11):
        domain = uint(descriptor + i * 8)
        while domain:
            if domain in seen or len(seen) >= 64 or uint(domain + 0x68) != descriptor:
                raise ValueError('unexpected launchd user domain registry')
            seen.add(domain)
            if uint(domain + 0x70) == 501:
                if cstring(uint(domain + 0x3a8), 16) != b'iOSUser':
                    raise ValueError('unexpected session name for user/501')
                matches.append(domain)
            domain = uint(domain + 0x18)
    if len(matches) != 1:
        raise ValueError('expected one existing user/501 bootstrap domain')
    return matches[0]


def trace_setup_session(kind, pid, name):
    if pid != 1 or name != 'launchd' or not state.get('setup_activation_seen'):
        return False
    base = state['launchd_base']
    tid = uint(reg(registers['TPIDR_EL1']) + 0x550)
    if kind == 'setup_submit':
        label = cstring(reg('x22'), 85)
        prefix, suffix = b'UIKitApplication:com.apple.purplebuddy[', b'][rb-legacy]'
        if not label.startswith(prefix) or not label.endswith(suffix):
            return False
        instance = label[len(prefix):-len(suffix)]
        if not 1 <= len(instance) <= 16 or any(c not in b'0123456789abcdefABCDEF' for c in instance):
            return False
        # Pinned LC_UUID from the original 20F66 PID 1 image.
        uuid = bytes.fromhex('babc0c9dbf6e35138ba8c8e876f3119a')
        if (read(base, 4) != bytes.fromhex('cffaedfe') or uuid not in read(base, 4096)
                or opcode_at(reg('pc')) != 'f7010094'):
            raise ValueError('unexpected 20F66 launchd submit image')
        domain = reg('x1')
        if (domain != reg('x23') or uint(domain + 0x68) != base + 0x6d370
                or uint(domain + 0x70) != 0 or cstring(uint(domain + 0x3a8), 16) != b'System'):
            raise ValueError('Setup submission is not targeting the system domain')
        selected = mobile_domain(base)
        setup_submissions[tid] = (reg('x0'), selected, label.decode('ascii'))
        state['setup_selected_domain'] = selected
        emit(kind, pid, name, tid=tid, label=label.decode('ascii'), job=hex(reg('x0')),
             original_domain=hex(domain), domain=hex(selected), target='user/501')
        return True
    if tid not in setup_submissions:
        return False
    job, domain, label = setup_submissions[tid]
    if kind == 'setup_submit_done':
        del setup_submissions[tid]
        emit(kind, pid, name, tid=tid, label=label,
             error=uint(reg('sp') + 0x20, 4), service=hex(reg('x0')))
        return False
    if kind == 'setup_normalized':
        if reg('x19') == job and reg('x22') == domain and reg('x0'):
            if opcode_at(reg('pc')) != '40fdffb4':
                raise ValueError('unexpected 20F66 launchd normalization return')
            setup_submissions[tid] = (reg('x0'), domain, label)
            emit(kind, pid, name, tid=tid, label=label, job=hex(reg('x0')))
        return False
    if kind == 'setup_session_checked':
        if reg('x19') == job and reg('x22') == domain:
            emit(kind, pid, name, tid=tid, label=label, accepted=bool(reg('x0') & 1))
        return False
    if reg('x19') != job or reg('x0') != domain:
        return False
    if (opcode_at(reg('pc')) != '219a0094' or uint(domain + 0x68) != base + 0x6d3f8
            or uint(domain + 0x70) != 501 or reg('x1') != 0
            or cstring(uint(domain + 0x3a8), 16) != b'iOSUser'):
        raise ValueError('Setup request does not match the missing iOSUser session case')
    # Supply the selected domain's existing session name to the native matcher for
    # this submission only. The native validator still makes the decision.
    state['setup_session_arg'] = uint(domain + 0x3a8)
    emit(kind, pid, name, tid=tid, label=label, requested=None, selected='iOSUser')
    return True


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


def publish_live_scanout():
    with open('live-frame.tmp', 'wb') as frame:
        frame.write(framebuffer())
    os.replace('live-frame.tmp', 'live-frame.raw')


def next_live_touch():
    if 'touch_input' not in state:
        try:
            state['touch_input'] = open('live-touch.jsonl', 'rb')
        except FileNotFoundError:
            return None
    line = state['touch_input'].readline(256)
    if not line:
        return None
    phase, x, y = json.loads(line)
    if phase not in ('down', 'move', 'up') or type(x) is not int or type(y) is not int:
        raise ValueError('invalid desktop touch event')
    if not (0 <= x < 1080 and 0 <= y < 2400):
        raise ValueError('desktop touch outside digitizer')
    return phase != 'up', x, y, 'desktop_' + phase


def setup_pixels_ready(source):
    # Sample the central welcome content and its background.
    samples = [source[y * SOFTWARE_STRIDE + x * 4]
               for y in range(800, 1500, 8) for x in range(230, 900, 8)]
    return sum(pixel >= 220 for pixel in samples) > len(samples) // 2 and sum(
        pixel < 200 for pixel in samples) >= 20


def language_table_visible(source):
    # Native table labels sit near the left edge, on a flat row background.
    # Sample several rows so a transition or the Hello artwork cannot arm a tap.
    row_counts = []
    for center in (540, 661, 782, 903, 1024):
        contrast = 0
        for y in range(center - 22, center + 23, 2):
            row = y * SOFTWARE_STRIDE
            background = source[row + 400 * 4]
            if background > 64:
                contrast += sum(source[row + x * 4] < background - 36 for x in range(14, 150, 2))
        row_counts.append(contrast)
    return row_counts[0] >= 24 and sum(count >= 24 for count in row_counts) >= 3


def region_capture_phase(vsync):
    if not state.get('swipe_captures'):
        return 'hello'
    if state.get('swipe_step', 0) == len(SWIPE_Y):
        if (not state.get('language_frame') and state.get('language_cells')
                and language_table_visible(state['last_software_frame'])):
            return 'language'
    if state.get('swipe_step', 0) == len(SWIPE_Y) + 2 and state.get('region_cells'):
        count = state.get('region_captures', 0)
        if count < len(region_capture_delays) and vsync >= state.get('next_region_capture', 0):
            return 'region'
    return None


def scale_software_frame(source, width, height, stride):
    columns = [(x * SOFTWARE_WIDTH // width) * 4 for x in range(width)]
    runs = []
    start = end = columns[0]
    for x in columns[1:]:
        if x != end + 4:
            runs.append((start, end + 4))
            start = x
        end = x
    runs.append((start, end + 4))
    padding = bytes(stride - width * 4)
    rows = []
    for y in range(SOFTWARE_HEIGHT):
        row = source[y * SOFTWARE_STRIDE:(y + 1) * SOFTWARE_STRIDE]
        rows.append(b''.join(row[first:last] for first, last in runs) + padding)
    return b''.join(rows[y * SOFTWARE_HEIGHT // height] for y in range(height))


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
            if kind == 'touch_timer':
                if opcode_at(TOUCH_TIMER) != 'de030094' or reg('x1') != 12 or reg('x2') != 0x40:
                    raise ValueError('unexpected QEMU HID timer call')
                state['advance_touch'] = True
                return True
            if kind == 'touch_delay':
                if opcode_at(TOUCH_TIMER_DELAY) != '680240f9':
                    raise ValueError('unexpected QEMU HID timer delay site')
                if state.get('setup_blit'):
                    state['short_touch_delay'] = True
                    return True
                return False
            if kind == 'touch_dispatch':
                if opcode_at(reg('pc')) != '00013fd6' or not reg('x1'):
                    raise ValueError('unexpected digitizer dispatch')
                clients = uint(reg('x0') + 0xa0)
                emit(kind, 0, 'kernel', step=state.get('live_touch_step', state['swipe_step']), event_va=hex(reg('x1')),
                     clients=uint(clients + 0x14, 4) if clients else 0)
                return False
            if kind == 'touch_enqueue':
                if state.get('swipe_step'):
                    emit(kind, 0, 'kernel', step=state.get('live_touch_step', state['swipe_step']), event_va=hex(reg('x1')))
                return False
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
            if kind.startswith(('setup_language_', 'setup_region_')):
                if name == 'Setup' and pid == state.get('setup_pid') and hits[kind, name] < 8:
                    hits[kind, name] += 1
                    step = state.get('swipe_step', 0)
                    fields = dict(pc=hex(reg('pc')), after_swipe=step >= len(SWIPE_Y), touch_step=step)
                    if kind == 'setup_language_cell':
                        state['language_cells'] = True
                    elif kind == 'setup_language_selected_row':
                        fields['row'] = reg('x0')
                    elif kind == 'setup_language_choice':
                        fields['code'] = string_hint(reg('x2'), lambda s: 2 <= len(s) <= 10
                                                     and all(c.isalpha() or c in '_-' for c in s))
                    elif kind == 'setup_region_cell':
                        state['region_cells'] = True
                    emit(kind, pid, name, **fields)
                return False
            if kind in ('hid_service_candidate', 'hid_service_result', 'hid_service_open'):
                if name == 'backboardd' and (kind != 'hid_service_open' or reg('x2') == 0x65737563):
                    emit(kind, pid, name, x0=hex(reg('x0')), x1=hex(reg('x1')), x2=hex(reg('x2')))
                return False
            if kind in ('setup_submit', 'setup_normalized', 'setup_session_select', 'setup_session_checked',
                        'setup_submit_done'):
                return trace_setup_session(kind, pid, name)
            if kind == 'shared_cache':
                identity = (name, pid) if name == 'Setup' else name
                if name not in ui_processes or identity in state.get('cache_users', ()):
                    return False
                # _shared_region_check_np has just obtained the start address,
                # at SP+0x38, from vm_shared_region_start_address.
                base = uint(reg('sp') + 0x38)
                slide = base - CACHE_BASE
                if slide < 0 or slide > 0x56110000 or slide % 0x4000:
                    raise ValueError('unexpected cache base ' + hex(base))
                emit(kind, pid, name, base=hex(base), slide=hex(slide))
                state.setdefault('cache_users', set()).add(identity)
                if name == 'backboardd':
                    state['slide'] = slide
                    return True
                if state.get('slide', slide) != slide:
                    raise ValueError('SpringBoard has a different cache slide')
                if setup_without_proximity and name == 'Setup':
                    base = task_image_base(pid)
                    state.setdefault('setup_images', {})[pid] = base
                    state['install_setup_proximity'] = base + 0xabc08
                    return True
                return False
            if kind.startswith('rbs_setup_'):
                if name != 'runningboardd' or not state.get('setup_activation_seen'):
                    return False
            elif name not in ui_processes and kind not in ('present', 'present_done', 'copy_rows'):
                return False
            if kind in ('springboard_ipc', 'setup_transition', 'setup_activate') and name != 'SpringBoard':
                return False
            if kind == 'setup_proximity_resume':
                base = state.get('setup_images', {}).get(pid)
                if name != 'Setup' or not base or reg('pc') != base + 0xabc08:
                    return False
                if read(reg('pc'), 20) != bytes.fromhex('ff8301d1f65703a9f44f04a9fd7b05a9fd430191'):
                    raise ValueError('unexpected ProximitySetupController entry')
                try:
                    port = uint(0x1e1f689b0 + state['slide'], 4)
                except gdb.MemoryError:
                    port = None
                state['return_setup_no_peer'] = reg('x30')
                emit(kind, pid, name, needs_to_resume=False, cached_display_port=port)
                return True
            if kind in ('setup_backboard_port', 'setup_backboard_reply'):
                if name != 'Setup':
                    return False
                if kind == 'setup_backboard_port':
                    port = reg('x0') & 0xffffffff
                    state.setdefault('setup_display_ports', {})[pid] = port
                    emit(kind, pid, name, mach_port=port, service='com.apple.backboard.display.services')
                else:
                    port = state.get('setup_display_ports', {}).get(pid, 0)
                    status = reg('x0') & 0xffffffff
                    values = struct.unpack('<4f', read(reg('sp') + 0x10, 16))
                    emit(kind, pid, name, mach_port=port, status=status,
                         screen_values=list(values), connected=bool(port and status == 0))
                return False
            if kind in ('setup_sw_destination', 'setup_sw_draw_complete'):
                if (name != 'backboardd' or not state.get('software_attempted')
                        or (not setup_swipe and state.get('setup_blit'))):
                    return False
                if kind == 'setup_sw_destination':
                    if (opcode_at(reg('pc')) == 'e9234029' and reg('x1') and reg('x1') == reg('x4')
                            and reg('x2') == SOFTWARE_STRIDE and reg('x3') == 32):
                        state['setup_software_target'] = (reg('x0'), reg('x1'))
                elif (reg('x1') == 0 and state.get('setup_software_target', (None, None))[0] == reg('x0')
                      and 'setup_software_pixels' not in state):
                    address = state['setup_software_target'][1]
                    pixels = read(address, SOFTWARE_STRIDE * SOFTWARE_HEIGHT)
                    if state.get('setup_blit') or setup_pixels_ready(pixels):
                        if not setup_swipe:
                            with open('setup-software-source.raw', 'xb') as capture:
                                capture.write(pixels)
                        state['setup_software_pixels'] = pixels
                        if not setup_swipe or not state.get('setup_blit'):
                            emit('setup_sw_pixels', pid, name, address=hex(address), width=SOFTWARE_WIDTH,
                                 height=SOFTWARE_HEIGHT, stride=SOFTWARE_STRIDE, sha256=hashlib.sha256(pixels).hexdigest())
                return False
            if kind == 'context_commit' and name == 'Setup':
                state['setup_pid'] = pid
                if state.pop('display_trace_parked', False):
                    state['arm_setup_scanout'] = True
            if kind == 'setup_activate':
                state['setup_activation_seen'] = True
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
                eligible = any(surface and mask & (1 << i) for i, surface in enumerate(surfaces))
                capture_due = (not setup_trace or
                    (state.get('setup_pid') is None and not state.get('baseline_captured')) or
                    (state.get('setup_pid') is not None and fields['vsync'] >= state.get('next_setup_capture', 0)))
                if (kind == 'present' and eligible and (setup_swipe or capture_due)
                        and (not setup_software_scanout or 'setup_software_pixels' in state)):
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
                if setup_software_scanout:
                    present = state['nonempty_present']
                    destination = reg('x1')
                    if (layer != 0 or width != 1220 * 4 or height != FRAMEBUFFER_HEIGHT
                            or start != 0 or stride != 5120 or any(present['surfaces'][1:])
                            or destination < 0xfffffe0000000000):
                        raise ValueError('Setup scanout does not match the pinned full-screen IOSurface')
                    software = state.pop('setup_software_pixels')
                    if setup_swipe and software == state.get('last_software_frame'):
                        state['disable_site'] = self
                        return True
                    output = scale_software_frame(software, width // 4, height, stride)
                    read(destination + len(output) - 1, 1)
                    gdb.selected_inferior().write_memory(destination, output)
                    state['setup_blit'] = True
                    blit = dict(swap_id=present['swap_id'], surface_id=surface,
                                source_sha256=hashlib.sha256(software).hexdigest(),
                                scanout_source_sha256=hashlib.sha256(output).hexdigest())
                    if setup_swipe:
                        state['last_software_frame'] = software
                        state['current_blit'] = blit
                    else:
                        emit('setup_sw_blit', pid, name, **blit)
                rows = sorted({height * fraction // 4 for fraction in range(4)} | {height - 1})
                state['sample'] = (layer, surface, width, [
                    (row, start + row * FRAMEBUFFER_STRIDE, read(reg('x1') + row * stride, width))
                    for row in rows])
                state['disable_site'] = self
                return True
            elif kind == 'present_done':
                present = state.pop('nonempty_present', None)
                if present is None:
                    return False
                before = state.pop('frame_before')
                sample = state.pop('sample', None)
                if setup_swipe:
                    blit = state.pop('current_blit', None)
                    if not blit or not sample:
                        return False
                    emit('setup_refresh', pid, name, **blit, vsync=present['vsync'])
                    if setup_live:
                        publish_live_scanout()
                    count = state.get('swipe_captures', 0)
                    if setup_region:
                        phase = region_capture_phase(present['vsync'])
                        if not phase:
                            return False
                        present['setup_phase'] = phase
                        if phase == 'language':
                            state['language_frame'] = present['swap_id']
                        elif phase == 'region':
                            region_count = state.get('region_captures', 0)
                            state['region_captures'] = region_count + 1
                            state['next_region_capture'] = present['vsync'] + region_capture_delays[region_count]
                    elif (count >= len(swipe_capture_delays) or count and
                            (state.get('swipe_step') != len(SWIPE_Y)
                             or present['vsync'] < state.get('next_setup_capture', 0))):
                        return False
                    source_name = 'setup-software-source-%08x.raw' % present['swap_id']
                    with open(source_name, 'xb') as source:
                        source.write(state['last_software_frame'])
                    emit('setup_sw_blit', pid, name, **blit, source_capture=source_name)
                    state['swipe_captures'] = count + 1
                    if not setup_region:
                        state['next_setup_capture'] = present['vsync'] + swipe_capture_delays[count]
                    present['swipe_step'] = state.get('swipe_step', 0)
                pixels = framebuffer()
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
                         swap_id=present['swap_id'])
                capture = 'native-frame.raw'
                if setup_trace:
                    capture = 'native-frame-%08x.raw' % present['swap_id']
                    present['setup_pid'] = state.get('setup_pid')
                with open(capture, 'xb') as frame:
                    frame.write(pixels)
                emit(kind, pid, name, capture=capture, sha256=hashlib.sha256(pixels).hexdigest(),
                     before_sha256=hashlib.sha256(before).hexdigest(), **present)
                if setup_live and present.get('setup_phase') == 'region' and not state.get('live_ready'):
                    state['live_ready'] = True
                    with open('live-ready', 'x') as ready:
                        ready.write(str(present['swap_id']) + '\n')
                if not setup_trace:
                    return True
                if setup_swipe:
                    return False
                if setup_software_scanout and state.get('setup_blit'):
                    return True
                if present['setup_pid'] is None:
                    state['baseline_captured'] = True
                    return False
                count = state.get('setup_captures', 0) + 1
                state['setup_captures'] = count
                if count == len(setup_capture_delays):
                    return True
                state['next_setup_capture'] = present['vsync'] + setup_capture_delays[count]
                return False
            elif kind == 'springboard_ipc':
                fields = user_stack()
            elif kind == 'software_fallback':
                if name != 'backboardd' or reg('x0') or state.get('software_attempted'):
                    return False
                if setup_software_scanout and not state.get('setup_pid'):
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
                if kind == 'rbs_setup_finish':
                    fields['error'] = hex(reg('x5'))
                if kind == 'rbs_setup_request':
                    # 20F66 RBSLaunchRequest._context and RBSLaunchContext._bundleIdentifier.
                    try:
                        context = user_ivar(reg('x2'), 0x1dd3b6b08)
                        identifier = user_ivar(context, 0x1dd3b69fc)
                        fields['bundle'] = string_hint(identifier, lambda value: value.startswith('com.apple.'))
                    except gdb.MemoryError:
                        fields['bundle'] = None
                if kind == 'rbs_setup_result':
                    error = uint(reg('sp') + 8)
                    fields.update(result=hex(reg('x0')), error=hex(error))
                    if error:
                        try:
                            fields['error_code'] = user_ivar(error, 0x1dce8886c)
                            domain = user_ivar(error, 0x1dce88870)
                            fields['error_domain'] = string_hint(domain, lambda value: value.endswith('ErrorDomain'))
                        except gdb.MemoryError:
                            pass
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
                    or state.get('arm_setup_scanout', False) or sample_once and hits[kind, name] >= 4)
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
    if (setup_session or setup_without_proximity) and not setup_trace:
        raise RuntimeError('Setup experiments require the Setup trace')
    if setup_software_scanout and not (setup_session and setup_without_proximity and software_test):
        raise RuntimeError('Setup software scanout requires the manual Setup and software renderer experiments')
    if setup_swipe and (not setup_software_scanout or 'sweethidtest=15' not in layout['cmdline'].split()):
        raise RuntimeError('Setup swipe requires software scanout and its bounded QEMU HID timer')
    if setup_region and (not setup_swipe or not layout.get('setup_fonts') or not layout.get('hid_plugin')):
        raise RuntimeError('Setup region replay requires the QEMU swipe, fonts and HID plugin')
    if setup_live and not setup_region:
        raise RuntimeError('Interactive Setup requires the QEMU region replay')
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
    if setup_swipe:
        points.extend(Trace(va, kind) for va, kind in (
            (TOUCH_TIMER, 'touch_timer'), (TOUCH_TIMER_DELAY, 'touch_delay'),
            (0xfffffe0007a51800, 'touch_dispatch'), (0xfffffe0007a5be24, 'touch_enqueue')))
        points.extend(Trace(va + state['slide'], kind) for va, kind in (
            (0x18e5896b8, 'hid_service_candidate'), (0x18e5897d0, 'hid_service_result'),
            (0x18e54c55c, 'hid_service_open')))
    if software_test:
        points.append(Trace(0x1882e25b0 + state['slide'], 'software_fallback'))
    if setup_software_scanout:
        points.extend(Trace(va + state['slide'], name) for name, va in {
            'setup_sw_destination': 0x18843cbfc, 'setup_sw_draw_complete': 0x18843c698,
        }.items())
    if setup_trace:
        points.extend(Trace(va + state['slide'], name) for name, va in {
            'setup_transition': 0x1c50ad8c0, 'setup_activate': 0x1c50adc60,
            'rbs_setup_request': 0x1f52e4f68, 'rbs_setup_execute': 0x1f52bfef0,
            'rbs_setup_finish': 0x1f52e498c, 'rbs_setup_result': 0x1f529f504,
            'setup_backboard_port': 0x18dcb6574, 'setup_backboard_reply': 0x18dcb6590,
        }.items())
    if setup_session:
        state['launchd_base'] = task_image_base(1)
        points.extend(Trace(state['launchd_base'] + offset, kind) for offset, kind in {
            0x37ec4: 'setup_submit', 0x346c: 'setup_normalized', 0x361c: 'setup_session_select',
            0x3620: 'setup_session_checked', 0x37ec8: 'setup_submit_done',
        }.items())
    if setup_without_proximity:
        # Leave the hot display sites idle until Setup submits its first context.
        scanout_kinds = (set(USER_SITES) | {'power', 'swap', 'present', 'present_done'}) - {'context_commit'}
        state['display_trace_parked'] = True
        for point in points:
            if point.kind in scanout_kinds:
                point.enabled = False
    while True:
        gdb.execute('continue')
        if 'error' in state:
            raise RuntimeError(state['error'])
        if state.pop('arm_setup_scanout', False):
            for point in points:
                if point.kind in scanout_kinds:
                    point.enabled = True
        elif 'install_setup_proximity' in state:
            address = state.pop('install_setup_proximity')
            if not any(point.kind == 'setup_proximity_resume' and point.location == '*' + hex(address)
                       for point in points):
                points.append(Trace(address, 'setup_proximity_resume'))
                if setup_swipe:
                    base = address - 0xabc08
                    points.extend(Trace(base + offset, kind) for offset, kind in {
                        0x37b28: 'setup_language_init', 0x37d3c: 'setup_language_did_load',
                        0x37e58: 'setup_language_will_appear', 0x383f0: 'setup_language_number_of_rows',
                    }.items())
                    if setup_region:
                        points.extend(Trace(base + offset, kind) for offset, kind in {
                            0x38424: 'setup_language_cell', 0x386a8: 'setup_language_selected_row',
                            0x38118: 'setup_language_choice', 0x390ac: 'setup_region_will_appear',
                            0x39a50: 'setup_region_number_of_rows', 0x39aec: 'setup_region_cell',
                        }.items())
        elif 'return_setup_no_peer' in state:
            gdb.execute('set $x0 = 0', to_string=True)
            gdb.execute('set $pc = ' + hex(state.pop('return_setup_no_peer')), to_string=True)
        elif 'setup_selected_domain' in state:
            selected = hex(state.pop('setup_selected_domain'))
            gdb.execute('set $x1 = ' + selected, to_string=True)
            gdb.execute('set $x23 = ' + selected, to_string=True)
        elif 'setup_session_arg' in state:
            gdb.execute('set $x1 = ' + hex(state.pop('setup_session_arg')), to_string=True)
        elif state.pop('rewrite_usage', False):
            gdb.execute('set $x2 = 0x30', to_string=True)
            emit('qemu_power_key', 0, 'kernel', down=state['wake_pressed'])
        elif state.pop('advance_touch', False):
            step = state.get('swipe_step', 0)
            live = setup_live and step == len(SWIPE_Y) + 2
            # Skip the timer's ordinary Home event even when there is no
            # gesture pending or the observation window has ended.
            gdb.execute('set $pc = ' + hex(TOUCH_TIMER_RESUME), to_string=True)
            if setup_live and os.path.exists('live-stop'):
                emit('setup_desktop_stopped', 0, 'kernel')
                break
            if live:
                # The original test callback stops after 60 samples. Keep its
                # diagnostic timer available only inside this pinned QEMU run.
                if opcode_at(TOUCH_TIMER_RESUME) != '88b640b9':
                    raise RuntimeError('unexpected QEMU HID timer counter')
                counter = reg('x20') + 0xb4
                if uint(counter, 4) >= 50:
                    gdb.selected_inferior().write_memory(counter, bytes(4))
                touch = next_live_touch() if state.get('live_ready') else None
                if not touch:
                    continue
                down, x, y, gesture = touch
            elif step == len(SWIPE_Y) + (2 if setup_region else 0):
                emit('setup_swipe_window_complete', 0, 'kernel', captures=state['swipe_captures'],
                     region_captures=state.get('region_captures', 0))
                break
            elif not state.get('swipe_captures'):
                continue
            elif step < len(SWIPE_Y):
                down, x, y, gesture = step < len(SWIPE_Y) - 1, 540, SWIPE_Y[step], 'swipe'
            elif state.get('language_frame'):
                down, x, y, gesture = step == len(SWIPE_Y), 540, ENGLISH_TAP_Y, 'english_tap'
            else:
                state['language_waits'] = state.get('language_waits', 0) + 1
                if state['language_waits'] == 13:
                    emit('setup_language_frame_timeout', 0, 'kernel')
                    break
                continue
            if opcode_at(TOUCH_SEND) != 'e80300aa' or not uint(0xfffffe00081029f0):
                raise RuntimeError('pinned QEMU digitizer is unavailable')
            for register, value in zip(('x0', 'x1', 'x2', 'x3', 'x30'), (0, int(down), x, y, TOUCH_TIMER_RESUME)):
                gdb.execute('set $%s = %#x' % (register, value), to_string=True)
            gdb.execute('set $pc = ' + hex(TOUCH_SEND), to_string=True)
            if live:
                step = state.get('live_touch_step', step) + 1
                state['live_touch_step'] = step
                state['live_touch_down'] = down
            else:
                step += 1
                state['swipe_step'] = step
            emit('qemu_touch', 0, 'kernel', step=step, down=down, x=x, y=y, gesture=gesture)
        elif state.pop('short_touch_delay', False):
            step = state.get('swipe_step', 0)
            delay = 25
            if setup_region:
                if step == len(SWIPE_Y):
                    delay = 2500
                elif step == len(SWIPE_Y) + 1:
                    delay = 80
                elif step == len(SWIPE_Y) + 2:
                    delay = (25 if state.get('live_touch_down') else 60) if setup_live else 35000
            elif step == len(SWIPE_Y):
                delay = 35000
            gdb.execute('set $x1 = ' + str(delay), to_string=True)
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
            if 'copy_site' in state:
                state['copy_site'].enabled = True
            else:
                state['copy_site'] = Trace(0xfffffe0007a4df10, 'copy_rows')
                points.append(state['copy_site'])
        elif 'disable_site' in state:
            state.pop('disable_site').enabled = False
        else:
            break
finally:
    for point in points:
        point.delete()
    gdb.execute('detach')
end
