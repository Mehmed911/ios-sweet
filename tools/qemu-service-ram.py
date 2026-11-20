#!/usr/bin/env python3
"""QEMU-only disk-backed guest RAM for a large, writable diagnostic md0.

The host file is shared QEMU RAM, not a device backend. Only a new copy of
the supplied root is writable. Kernel/ADT inputs are pinned; the phone's
512 MiB layout and existing runner are never modified.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import socket
import struct
import subprocess
import time
import adt
import mkpayload

REPO = Path(__file__).resolve().parents[1]
KERNEL_PIN = 'e465723a540844817a5b9cb36c14984d660f9a8e41f6638240527b469189182b'
ADT_PIN = 'a881410d04a3cec3b7ebd9bee91f510c755683b94f5a26d71c47301fff7417d8'
RAM_BASE = 0x40000000
PHYS_BASE = 0x1c0000000
WINDOW = 4 << 30
PAGE = 0x4000
STUB = 0x40200000
DISPLAY_TIMER_SITES = (0xfffffe0007a4d878, 0xfffffe0007a4dae4)


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as source:
        for chunk in iter(lambda: source.read(4 << 20), b''):
            digest.update(chunk)
    return digest.hexdigest()


def child(node, name):
    matches = [c for c in node.children if c.name == name]
    require(len(matches) == 1, 'ambiguous ADT node: ' + name)
    return matches[0]


def virtual_tree(raw):
    require(hashlib.sha256(raw).hexdigest() == ADT_PIN, 'only the pinned QEMU base ADT is accepted')
    tree, end = adt.parse(raw)
    require(end == len(raw), 'trailing ADT data')
    require(not any(c.name in ('sweet-ufs', 'duchamp-qemu-ufs') for c in tree.children), 'storage node forbidden')
    chosen = child(tree, 'chosen')
    require(child(chosen, 'memory-map').prop('RAMDisk') is None, 'preexisting RAMDisk forbidden')
    require(chosen.prop('dram-base') == struct.pack('<Q', PHYS_BASE), 'RAM base differs')
    chosen.props = [(n, f, struct.pack('<Q', WINDOW) if n == 'dram-size' else
        b'duchamp-qemu-large-ram-only-v1\0' if n == 'firmware-version' else v) for n, f, v in chosen.props]
    return adt.serialize(tree)


def layout(payload, root_bytes, root_growth=0):
    require(0 < root_bytes <= 3 << 30 and root_bytes % PAGE == 0, 'root size must be aligned and at most 3 GiB')
    require(0 <= root_growth <= 128 << 20 and root_growth % PAGE == 0, 'invalid HFS growth allowance')
    root_bytes += root_growth
    require(len(payload) >= 0x2a8, 'truncated payload')
    magic, version, count = struct.unpack_from('<8sII', payload)
    require(magic == b'SWEETXNU' and version == 1 and 0 < count <= 32, 'invalid payload')
    require(0x2a8 + count * 32 <= len(payload), 'segment table outside payload')
    vb, entry, adt_off, adt_size, kernel_end, pb, mem = struct.unpack_from('<7Q', payload, 0x10)
    require(pb == PHYS_BASE and mem == WINDOW, 'not a QEMU large RAM window')
    require(adt_size > 0 and adt_off <= len(payload) and adt_size <= len(payload) - adt_off, 'ADT outside payload')
    raw = payload[adt_off:adt_off + adt_size]
    tree, end = adt.parse(raw)
    require(end == len(raw), 'bad packed ADT')
    chosen = child(tree, 'chosen')
    require(chosen.prop('firmware-version') == b'duchamp-qemu-large-ram-only-v1\0', 'missing QEMU firmware gate')
    require(child(chosen, 'memory-map').prop('RAMDisk') is None, 'RAMDisk already present')
    delta = pb - vb
    segments = []
    highest = pb
    for i in range(count):
        va, size, offset, file_size = struct.unpack_from('<4Q', payload, 0x2a8 + 32 * i)
        pa = va + delta
        require(size >= file_size and offset <= len(payload) and file_size <= len(payload) - offset, 'invalid segment file range')
        require(pb <= pa and size <= pb + mem - pa, 'segment outside RAM window')
        require(all(pa + size <= a or a + b <= pa for a, b, _, _ in segments), 'overlapping kernel segments')
        highest = max(highest, pa + size)
        segments.append((pa, size, offset, file_size))
    root_pa = (kernel_end + delta + PAGE - 1) & -PAGE
    require(root_pa >= highest, 'RAMDisk overlaps kernel')
    updated_adt = mkpayload.add_ramdisk_to_adt(raw, root_pa, root_bytes)
    adt_pa = root_pa + root_bytes
    boot_pa = (adt_pa + len(updated_adt) + PAGE - 1) & -PAGE
    top = boot_pa + PAGE
    require(top <= pb + mem and pb + mem - top >= 256 << 20, 'insufficient free guest memory')
    ram_bytes = ((pb + mem - RAM_BASE + (1 << 30) - 1) >> 30) << 30
    return dict(virt_base=vb, phys_base=pb, mem_size=mem, ram_base=RAM_BASE, ram_bytes=ram_bytes,
        root_pa=root_pa, root_bytes=root_bytes, adt_pa=adt_pa, boot_pa=boot_pa, top=top,
        entry_pa=entry + delta, adt=updated_adt, segments=segments,
        cmdline=payload[0x48:0x48 + 608])


def configure_display_timer(payload, plan, refresh_hz):
    require(refresh_hz in (60, 120), 'supported guest display rates are 60 and 120 Hz')
    if refresh_hz == 60:
        return payload
    # AppleCLCD::start and vsyncFired in KERNEL_PIN both load w1 before the
    # same setTimeoutUS virtual call. The rearm site covers both power paths.
    old = struct.pack('<2I', 0x52882361, 0xd63f0100)  # mov w1, #16667; blr x8
    period_us = round(1_000_000 / refresh_hz)
    replacement = struct.pack('<I', 0x52800001 | (period_us << 5))
    delta = plan['phys_base'] - plan['virt_base']
    updated = bytearray(payload)
    for va in DISPLAY_TIMER_SITES:
        pa = va + delta
        matches = [offset + pa - start for start, _, offset, size in plan['segments']
                   if start <= pa and pa + len(old) <= start + size]
        require(len(matches) == 1 and payload[matches[0]:matches[0] + len(old)] == old,
                'pinned guest display timer instruction differs at ' + hex(va))
        offset = matches[0]
        updated[offset:offset + len(replacement)] = replacement
    return bytes(updated)


def pack_boot_args(plan, fb):
    ba = struct.pack('<HH4x4Q6QI4xQI', 2, 2, plan['virt_base'], PHYS_BASE, WINDOW, plan['top'],
        fb['base'], 1, fb['stride'], fb['width'], fb['height'], 32, 0,
        plan['adt_pa'] - (PHYS_BASE - plan['virt_base']), len(plan['adt']))
    ba += plan['cmdline'] + bytes(4) + struct.pack('<QQ', 0, WINDOW)
    require(len(ba) == 736, 'boot args layout differs')
    return ba


def copy_range(source, destination, count):
    while count:
        data = source.read(min(count, 4 << 20))
        require(bool(data), 'short source while copying RAM')
        destination.write(data)
        count -= len(data)


def monitor(endpoint, execute, arguments=None):
    with socket.socket(socket.AF_UNIX) as sock:
        sock.settimeout(15)
        sock.connect(str(endpoint))
        with sock.makefile('rw') as stream:
            require(bool(stream.readline()), 'no QMP greeting')
            def call(command, args):
                stream.write(json.dumps(dict(execute=command, arguments=args or {})) + '\n')
                stream.flush()
                while True:
                    line = stream.readline()
                    require(bool(line), 'QMP disconnected')
                    result = json.loads(line)
                    require('error' not in result, 'QMP error: ' + str(result.get('error')))
                    if 'return' in result:
                        return result['return']
            call('qmp_capabilities', {})
            return call(execute, arguments)


def run_vm(kernel, base_adt, root, out, seconds, stop_markers, cmdline=None, debugger_script=None,
           save_guest_root=True, display_hz=60, kernel_manifest=None, passive_trace_config=None):
    kernel, base_adt, root, out = (Path(p).resolve() for p in (kernel, base_adt, root, out))
    require(os.name == 'posix' and not str(out).startswith('/mnt/'), 'guest RAM output must use the native Linux disk')
    require(not out.exists(), 'preserve existing run directory')
    require(10 <= seconds <= 900, 'bounded VM runtime required')
    if kernel_manifest is None:
        require(sha(kernel) == KERNEL_PIN, 'kernel pin changed')
        kernel_pin = KERNEL_PIN
    else:
        # Source-linked experiments use their complete link receipt. Never
        # silently substitute the historical CI kernel or patch its instructions.
        from duchamp_source_kernel import select
        kernel_pin = select(kernel, Path(kernel_manifest).resolve())
        require(display_hz == 60 and debugger_script is None,
                'source-linked profile forbids instruction/debugger patches')
    if passive_trace_config is not None:
        require(kernel_manifest is not None and debugger_script is None,
                'passive tracing requires an explicit source receipt and no legacy debugger')
        passive_trace_config = Path(passive_trace_config).resolve()
        passive_config = json.loads(passive_trace_config.read_text())
        require(passive_config.get('passive_only') is True and
                passive_config.get('kernel_sha256') == kernel_pin and
                passive_config.get('source_trace_sha256') == sha(REPO / 'tools/duchamp-render-passive.gdb'),
                'passive trace source/configuration mismatch')
    source_root_pin = sha(root)
    with root.open('rb') as source:
        source.seek(1024)
        require(source.read(2) == b'H+', 'root is not HFS+')
    raw_adt = virtual_tree(base_adt.read_bytes())
    out.mkdir(parents=True)
    virtual_adt = out / 'qemu-large.adt'
    virtual_adt.write_bytes(raw_adt)
    cmdline = cmdline or ('debug=0xc serial=3 cpus=1 keepsyms=1 -enable_kprintf_spam -noprogress '
        'rd=md0 rootrw=1 sweet_console_fb=1 duchamp_timer_irq_ack=1 unentitled_ios_sim_launch=1 '
        'launchdsuffix=sweet launchd_log_serial=1')
    require('rd=md0' in cmdline.split() and not any(x.startswith('sweet-qemu-ufs=') for x in cmdline.split()), 'RAM root only')
    payload, _ = mkpayload.build(kernel, virtual_adt, cmdline)
    plan = layout(payload, root.stat().st_size)
    payload = configure_display_timer(payload, plan, display_hz)
    (out / 'kernel-only-payload.bin').write_bytes(payload)
    fb = dict(base=0xfcc2f000, width=1220, height=2712, stride=4992)
    ba = pack_boot_args(plan, fb)
    ram_path = out / 'guest-ram.bin'
    with ram_path.open('xb') as ram:
        ram.truncate(plan['ram_bytes'])
        for pa, _, offset, file_size in plan['segments']:
            ram.seek(pa - RAM_BASE)
            ram.write(payload[offset:offset + file_size])
        ram.seek(plan['root_pa'] - RAM_BASE)
        with root.open('rb') as source:
            copy_range(source, ram, plan['root_bytes'])
        ram.seek(plan['adt_pa'] - RAM_BASE); ram.write(plan['adt'])
        ram.seek(plan['boot_pa'] - RAM_BASE); ram.write(ba)
        ram.seek(STUB - RAM_BASE)
        ram.write(struct.pack('<4I2Q', 0x58000080, 0x580000a1, 0xd61f0020, 0xd503201f, plan['boot_pa'], plan['entry_pa']))
    serializable = {k: v for k, v in plan.items() if k not in ('adt', 'cmdline')}
    serializable.update(root_sha256=source_root_pin, source_adt_sha256=ADT_PIN, kernel_sha256=kernel_pin,
        cmdline=cmdline, qemu_only=True, physical_storage=False, large_ram_not_phone_layout=True,
        display_hz=display_hz)
    if kernel_manifest is not None:
        serializable['source_link_receipt_sha256'] = sha(kernel_manifest)
    if passive_trace_config is not None:
        serializable['passive_trace_config_sha256'] = sha(passive_trace_config)
    (out / 'layout.json').write_text(json.dumps(serializable, indent=2) + '\n')
    spec = importlib.util.spec_from_file_location('service_ram_screen', REPO / 'tools/qemu-sweet.py')
    screen_tool = importlib.util.module_from_spec(spec); spec.loader.exec_module(screen_tool)
    symbols = subprocess.check_output(['llvm-nm', '--defined-only', str(kernel)], text=True)
    fonts = [int(row.split()[0], 16) for row in symbols.splitlines() if row.split()[-1:] == ['_iso_font']]
    require(len(fonts) == 1, 'font symbol not unique')
    font = screen_tool.payload_data(payload, fonts[0], 4096)
    endpoint = Path('/tmp') / ('duchamp-service-ram-%d.sock' % os.getpid())
    require(not endpoint.exists(), 'QMP endpoint already exists')
    command = ['qemu-system-aarch64', '-M', 'virt,gic-version=3,memory-backend=duchamp_ram',
        '-cpu', 'cortex-a76', '-smp', '1', '-m', str(plan['ram_bytes'] >> 20) + 'M',
        '-object', 'memory-backend-file,id=duchamp_ram,size=%d,mem-path=%s,share=on,prealloc=off' % (plan['ram_bytes'], ram_path),
        '-nodefaults', '-nographic', '-serial', 'file:' + str(out / 'serial.txt'),
        '-qmp', 'unix:%s,server=on,wait=off' % endpoint, '-no-reboot',
        '-d', 'int,guest_errors,unimp', '-D', str(out / 'qemu.log'),
        '-device', 'loader,addr=%#x,cpu-num=0' % STUB]
    debug_endpoint = Path('/tmp') / ('duchamp-service-gdb-%d.sock' % os.getpid())
    if debugger_script is not None or passive_trace_config is not None:
        require(not debug_endpoint.exists() and
                (passive_trace_config is not None or Path(debugger_script).is_file()), 'invalid debugger input/endpoint')
        command += ['-S', '-gdb', 'unix:%s,server=on,wait=off' % debug_endpoint]
    (out / 'command.json').write_text(json.dumps(command, indent=2) + '\n')
    process = None; result = dict(stop_marker=None, snapshots=0)
    began = time.monotonic()
    try:
        with (out / 'qemu-stderr.txt').open('w') as errors:
            process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=errors, stderr=errors)
        if debugger_script is not None or passive_trace_config is not None:
            deadline = time.monotonic() + 15
            while not debug_endpoint.exists() and process.poll() is None and time.monotonic() < deadline:
                time.sleep(0.1)
            require(debug_endpoint.exists(), 'QEMU debugger endpoint did not start')
            script = out / 'debugger.gdb'
            trace_source = REPO / 'tools/duchamp-render-passive.gdb' if passive_trace_config is not None else Path(debugger_script)
            script.write_text('set pagination off\nset confirm off\nset architecture aarch64\n'
                'target remote %s\n' % debug_endpoint + trace_source.read_text())
            environment = os.environ.copy()
            if passive_trace_config is not None:
                environment['DUCHAMP_PASSIVE_TRACE_CONFIG'] = str(passive_trace_config)
            with (out / 'debugger.log').open('w') as debug_log:
                try:
                    debugger = subprocess.run(['gdb-multiarch', '-q', '-nx', '-batch', '-x', str(script)],
                        cwd=out, stdout=debug_log, stderr=subprocess.STDOUT, timeout=seconds - 5, env=environment)
                    result['debugger_exit_code'] = debugger.returncode
                except subprocess.TimeoutExpired:
                    result['debugger_timed_out'] = True
            monitor(endpoint, 'cont')
        frames = out / 'frames'; frames.mkdir()
        next_snapshot = began + 4
        while process.poll() is None and time.monotonic() - began < seconds:
            if time.monotonic() >= next_snapshot:
                monitor(endpoint, 'stop')
                raw = out / 'fb.raw'
                monitor(endpoint, 'pmemsave', dict(val=fb['base'], size=fb['stride'] * fb['height'], filename=str(raw)))
                screen, unknown = screen_tool.decode_screen(raw.read_bytes(), font, fb)
                (frames / ('%04d.txt' % result['snapshots'])).write_text(screen)
                result['snapshots'] += 1
                marker = next((x for x in stop_markers if x in screen), None)
                if marker:
                    result['stop_marker'] = marker
                    break
                monitor(endpoint, 'cont')
                next_snapshot = time.monotonic() + 4
            time.sleep(0.2)
        if process.poll() is None:
            monitor(endpoint, 'stop')
            registers = monitor(endpoint, 'human-monitor-command', {'command-line': 'info registers'})
            (out / 'regs.txt').write_text(registers)
            raw = out / 'fb.raw'
            monitor(endpoint, 'pmemsave', dict(val=fb['base'], size=fb['stride'] * fb['height'], filename=str(raw)))
            screen, unknown = screen_tool.decode_screen(raw.read_bytes(), font, fb)
            (out / 'fb.txt').write_text(screen)
            screen_tool.write_png(out / 'fb.png', raw.read_bytes(), fb)
            result.update(screen_tool.screen_result(screen, unknown))
            result['saved_framebuffer'] = True
            # The stopped, shared memory backend exposes the guest-written md0
            # bytes coherently. Save that range only, not the 10 GiB RAM file.
            if save_guest_root:
                with ram_path.open('rb') as source, (out / 'ramdisk-final.hfs').open('xb') as dest:
                    source.seek(plan['root_pa'] - RAM_BASE)
                    copy_range(source, dest, plan['root_bytes'])
            result['saved_guest_root'] = save_guest_root
        else:
            result.update(status='qemu_exited', qemu_returncode=process.returncode)
    except Exception as error:
        result['error'] = repr(error)
        raise
    finally:
        if process is not None and process.poll() is None:
            process.kill(); process.wait(timeout=15)
        result.update(elapsed_host_seconds=round(time.monotonic() - began, 3),
            source_root_unchanged=sha(root) == source_root_pin, hardware_timing_claimed=False)
        (out / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('kernel', 'adt', 'root', 'output'):
        parser.add_argument('--' + name, required=True, type=Path)
    parser.add_argument('--seconds', type=int, default=180)
    parser.add_argument('--stop-on-text', action='append', default=[])
    parser.add_argument('--debugger-script', type=Path, help='bounded QEMU-only GDB diagnostic script')
    parser.add_argument('--no-save-guest-root', action='store_true', help='save framebuffer and shared RAM only')
    args = parser.parse_args()
    result = run_vm(args.kernel, args.adt, args.root, args.output, args.seconds,
        args.stop_on_text + ['SWEET EARLY PANIC:', 'Library not loaded:', 'Symbol not found:'],
        debugger_script=args.debugger_script, save_guest_root=not args.no_save_guest_root)
    print(json.dumps(result, indent=2))
    return 0 if result.get('stop_marker') in args.stop_on_text and 'error' not in result else 1


if __name__ == '__main__':
    raise SystemExit(main())
