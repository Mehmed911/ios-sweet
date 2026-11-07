# QEMU only. Addresses and object layouts are for kernel SHA-256 e465723a540844817a5b9cb36c14984d660f9a8e41f6638240527b469189182b.
# Run with qemu-service-ram.py --debugger-script. Hardware breakpoints do not patch guest memory.
python
import json
import struct
import gdb

registers = {r.name.upper(): r.name for r in gdb.newest_frame().architecture().registers()}
events = []

def reg(name):
    return int(gdb.parse_and_eval('$' + name)) & ((1 << 64) - 1)

def read(address, size):
    return bytes(gdb.selected_inferior().read_memory(address, size))

def uint(address, size=8):
    return int.from_bytes(read(address, size), 'little')

def process():
    thread = reg(registers['TPIDR_EL1'])
    # Layout verified against current_thread_ro, current_proc, proc_selfpid and proc_best_name.
    thread_ro = uint(thread + 0x488)
    if uint(thread_ro) != thread:
        raise ValueError('thread_ro back pointer mismatch')
    proc = uint(thread_ro + 0x10)
    if not proc:
        return dict(pid=0, name='kernel')
    comm = read(proc + 0x5c0, 17).split(b'\0', 1)[0]
    name = read(proc + 0x5d1, 33).split(b'\0', 1)[0]
    return dict(pid=uint(proc + 0x60, 4), name=(name or comm).decode('ascii', 'replace'))

def record(address):
    data = read(address, 0x46c)
    return dict(swap_id=struct.unpack_from('<I', data, 0x50)[0],
                mask=struct.unpack_from('<I', data, 0x104)[0],
                surfaces=struct.unpack_from('<4I', data, 0x54),
                source=struct.unpack_from('<4i', data, 0x64),
                destination=struct.unpack_from('<4i', data, 0xc4))

class Trace(gdb.Breakpoint):
    def __init__(self, address, kind):
        super().__init__('*' + hex(address), type=gdb.BP_HARDWARE_BREAKPOINT, internal=True)
        self.kind = kind

    def stop(self):
        try:
            if self.kind == 'power':
                fb = uint(reg('x0') + 0xd8)
                event = dict(value=uint(uint(reg('x20') + 0x20)),
                             power_off=uint(fb + 0x568, 1), vsync=uint(fb + 0x98), **process())
            else:
                event = record(reg('x1'))
                event['power_off'] = uint(reg('x0') + 0x568, 1)
                event['vsync'] = uint(reg('x0') + 0x98)
                if self.kind == 'swap':
                    event.update(process())
            event['event'] = self.kind
            events.append(event)
            gdb.write('COMPOSITOR ' + json.dumps(event) + '\n')
            with open('compositor-events.jsonl', 'a') as log:
                log.write(json.dumps(event) + '\n')
            # Capture the power-off and first swap before letting the VM finish.
            saw_off = any(entry['event'] == 'power' and entry['value'] == 0 for entry in events)
            saw_swap = any(entry['event'] == 'swap' for entry in events)
            return len(events) >= 32 or (saw_off and saw_swap)
        except Exception as error:
            gdb.write('COMPOSITOR_TRACE_ERROR ' + str(error) + '\n')
            return True

try:
    if 'TPIDR_EL1' not in registers:
        raise RuntimeError('TPIDR_EL1 is unavailable')
    points = [Trace(0xfffffe0007a4e3d8, 'power'), Trace(0xfffffe0007a4dfec, 'swap'),
              Trace(0xfffffe0007a4dc24, 'present')]
    gdb.execute('continue')
finally:
    for point in locals().get('points', []):
        point.delete()
    gdb.execute('detach')
end
