#!/usr/bin/env python3
"""Run the pinned Duchamp Setup guest on native Windows QEMU."""
import argparse
import json
import os
from pathlib import Path
import secrets
import socket
import struct
import subprocess
import sys
import tempfile
import threading
import time
from contextlib import ExitStack

RAM_BASE = 0x40000000
STUB = 0x40200000
PHYS_BASE = 0x1c0000000
WINDOW = 4 << 30
FB_BANK = 0xfcc00000
CONSOLE_BANK = 0x9c000000
CONSOLE_BYTES = 24 << 20
FB = dict(base=0xfcc2f000, width=1220, height=2712, stride=4992)
FRAME_BYTES = FB['stride'] * FB['height']
SLICE = 4 << 20


def check(ok, message):
    if not ok:
        raise RuntimeError(message)


def qmp_channel(sock):
    sock.settimeout(10)
    stream = sock.makefile('rwb')
    check('QMP' in json.loads(stream.readline()), 'invalid native QMP greeting')

    def call(command, **arguments):
        stream.write(json.dumps(dict(execute=command, arguments=arguments)).encode() + b'\n')
        stream.flush()
        while line := stream.readline():
            reply = json.loads(line)
            check('error' not in reply, str(reply.get('error')))
            if 'return' in reply:
                return reply['return']
        raise EOFError('native QMP disconnected')

    call('qmp_capabilities')
    return call


def native_worker(control_port, gdb_host, gdb_port, token, log):
    import ctypes
    from ctypes import wintypes

    with socket.create_connection(('127.0.0.1', control_port), timeout=12) as control, \
            socket.create_server(('127.0.0.1', 0)) as listener, \
            socket.create_server(('127.0.0.1', 0)) as debug_listener, \
            tempfile.TemporaryDirectory(prefix='duchamp-firmware-', dir=log.parent) as firmware_dir, \
            log.open('w', encoding='utf-8') as errors:
        control.settimeout(60)
        control.sendall(token)
        listener.settimeout(15)
        debug_listener.settimeout(15)
        qemu = Path(os.environ['ProgramFiles']) / 'qemu' / 'qemu-system-aarch64.exe'
        # A ROM enables virt's ACPI DIMM map. Use an inert branch-to-self
        # rather than loading a full UEFI image. The loader sets the first PC
        # to the pinned XNU stub, and GDB verifies it before continuing.
        firmware = Path(firmware_dir) / 'acpi-enable.bin'
        firmware.write_bytes(struct.pack('<I', 0x14000000))
        command = [str(qemu), '-M', 'virt-10.2,gic-version=3,acpi=on',
            '-cpu', 'cortex-a76', '-smp', '1', '-m', '32M,slots=3,maxmem=10G',
            '-bios', str(firmware),
            '-object', 'memory-backend-ram,id=xnu,size=4G',
            '-object', 'memory-backend-ram,id=fb,size=16M',
            '-object', 'memory-backend-ram,id=console,size=24M',
            '-device', 'pc-dimm,id=xnu-dimm,memdev=xnu,addr=0x1c0000000',
            '-device', 'pc-dimm,id=fb-dimm,memdev=fb,addr=0xfcc00000',
            '-device', 'pc-dimm,id=console-dimm,memdev=console,addr=0x9c000000',
            '-nodefaults', '-S', '-display', 'none', '-monitor', 'none', '-no-reboot',
            '-serial', 'file:' + str(log.with_suffix('.serial.txt')),
            '-device', f'loader,addr={STUB:#x},cpu-num=0',
            '-chardev', f'socket,id=duchamp_gdb,host=127.0.0.1,port={debug_listener.getsockname()[1]},server=off,nodelay=on',
            '-gdb', 'chardev:duchamp_gdb',
            '-qmp', f'tcp:127.0.0.1:{listener.getsockname()[1]},server=off']
        with subprocess.Popen(command, stderr=errors, creationflags=subprocess.CREATE_NO_WINDOW) as vm:
            try:
                qmp_sock, _ = listener.accept()
                gdb_target, _ = debug_listener.accept()
                with qmp_sock, gdb_target, connect_wsl(gdb_host, gdb_port) as gdb_bridge, control.makefile('rb') as incoming:
                    threading.Thread(target=duplex, args=(gdb_target, gdb_bridge), daemon=True).start()
                    qmp = qmp_channel(qmp_sock)
                    check(qmp('query-status')['status'] == 'prelaunch', 'native VM is not paused')
                    banks = {d['data']['id']: (d['data']['addr'], d['data']['size'])
                             for d in qmp('query-memory-devices')}
                    check(banks == {'xnu-dimm': (PHYS_BASE, WINDOW), 'fb-dimm': (FB_BANK, 16 << 20),
                                    'console-dimm': (CONSOLE_BANK, CONSOLE_BYTES)},
                          'unexpected native RAM map')
                    blocks = qmp('human-monitor-command', **{'command-line': 'info ramblock'})
                    # Read host pointers from this exact paused QEMU child.
                    host = {}
                    for line in blocks.splitlines():
                        columns = line.split()
                        if len(columns) == 8 and columns[0] in ('xnu', 'fb', 'mach-virt.ram') and columns[-1] == 'rw':
                            host[columns[0]] = (int(columns[-2], 16), int(columns[-3], 16))
                    check({key: size for key, (_, size) in host.items()} ==
                          {'xnu': WINDOW, 'fb': 16 << 20, 'mach-virt.ram': 32 << 20},
                          'missing native RAM block addresses')
                    kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
                    kernel32.OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
                    kernel32.OpenProcess.restype = wintypes.HANDLE
                    kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)
                    for name in ('WriteProcessMemory', 'ReadProcessMemory'):
                        getattr(kernel32, name).argtypes = (
                            wintypes.HANDLE, ctypes.c_void_p, ctypes.c_void_p,
                            ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t))
                    handle = kernel32.OpenProcess(0x38, False, vm.pid)
                    if not handle:
                        raise ctypes.WinError(ctypes.get_last_error())

                    def transfer(operation, address, data, length):
                        done = ctypes.c_size_t()
                        if not operation(handle, address, data, length, ctypes.byref(done)):
                            raise ctypes.WinError(ctypes.get_last_error())
                        check(done.value == length, 'short transfer to/from native guest RAM')

                    try:
                        control.sendall(struct.pack('<I', vm.pid))
                        while True:
                            address, count = struct.unpack('<QQ', incoming.read(16))
                            if count == 0:
                                break
                            if address == STUB and count == 32:
                                target = host['mach-virt.ram'][0] + STUB - RAM_BASE
                            else:
                                check(PHYS_BASE <= address < PHYS_BASE + WINDOW and
                                      count <= PHYS_BASE + WINDOW - address, 'native RAM write out of bounds')
                                target = host['xnu'][0] + address - PHYS_BASE
                            while count:
                                data = incoming.read(min(SLICE, count))
                                check(data, 'short native RAM input')
                                transfer(kernel32.WriteProcessMemory, target, data, len(data))
                                target += len(data)
                                count -= len(data)
                        control.sendall(b'R')
                        pixels = ctypes.create_string_buffer(FRAME_BYTES)
                        address = host['fb'][0] + FB['base'] - FB_BANK
                        control.settimeout(None)
                        while incoming.read(1) == b'F':
                            transfer(kernel32.ReadProcessMemory, address, pixels, FRAME_BYTES)
                            control.sendall(pixels)
                    finally:
                        kernel32.CloseHandle(handle)
                    qmp('quit')
            finally:
                try:
                    vm.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    vm.terminate()
                    vm.wait(timeout=10)


def connect_wsl(host, port):
    for attempt in range(20):
        try:
            peer = socket.create_connection((host, port), timeout=1)
            peer.settimeout(None)
            return peer
        except OSError:
            if attempt == 19:
                raise
            time.sleep(0.25)


def relay(source, destination):
    try:
        while data := source.recv(65536):
            destination.sendall(data)
    except OSError:
        pass
    finally:
        try:
            destination.shutdown(socket.SHUT_WR)
        except OSError:
            pass


def duplex(target, client):
    for peer in (target, client):
        peer.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    up = threading.Thread(target=relay, args=(client, target), daemon=True)
    up.start()
    relay(target, client)
    up.join(timeout=3)


def serve_gdb(native, debugger, expected_peer):
    target, address = native.accept()
    with target:
        check(address[0] == expected_peer, 'unexpected native GDB peer')
        with debugger.accept()[0] as client:
            duplex(target, client)


def wsl_gdb_address():
    if subprocess.check_output(['wslinfo', '--networking-mode'], text=True).strip() != 'nat':
        return '127.0.0.1', '127.0.0.1'
    # WSL localhost forwarding batches the small RSP acknowledgement and
    # reply packets. Connect over the private host-only WSL NAT link instead.
    routes = json.loads(subprocess.check_output(['ip', '-j', '-4', 'route', 'show', 'default'], text=True))
    check(len(routes) == 1 and 'gateway' in routes[0], 'cannot identify the private WSL gateway')
    gateway = routes[0]['gateway']
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
        probe.connect((gateway, 9))
        return probe.getsockname()[0], gateway


def serve_frames(listener, control):
    with control.makefile('rb') as frames:
        while True:
            with listener.accept()[0] as viewer:
                try:
                    control.sendall(b'F')
                    data = frames.read(FRAME_BYTES)
                    check(len(data) == FRAME_BYTES, 'short native framebuffer')
                    viewer.sendall(data)
                except (BrokenPipeError, ConnectionResetError):
                    return


def prepare_boot(runner, root, previous, out):
    import mkpayload
    from duchamp_setup_assets import add_setup_assets

    kernel = Path('work/ci-41543710742-kernel/artifact/kernel.development.sweet')
    adt = Path('research/mt6897-boot/bsd-service-split-ci41543710742-qemu-authorized.adt')
    check(runner.sha(kernel) == runner.KERNEL_PIN, 'native kernel pin changed')
    cmdline = json.loads((previous / 'layout.json').read_text())['cmdline']
    check('rd=md0' in cmdline.split() and not any(arg.startswith(('sweet-qemu-ufs=', 'sweethidtest='))
          for arg in cmdline.split()), 'expected a clean RAM-only root profile')
    cmdline += ' sweethidtest=15'
    virtual_adt = out / 'qemu-large.adt'
    virtual_adt.write_bytes(runner.virtual_tree(adt.read_bytes()))
    payload, _ = mkpayload.build(kernel, virtual_adt, cmdline)
    plan = runner.layout(payload, root.stat().st_size, 128 << 20)
    display_hz = 120
    payload = runner.configure_display_timer(payload, plan, display_hz)
    state = {k: v for k, v in plan.items() if k not in ('adt', 'cmdline')}
    state.update(cmdline=cmdline, qemu_only=True, physical_storage=False,
                 kernel_sha256=runner.KERNEL_PIN, native_windows_qemu=True, display_hz=display_hz)
    return payload, plan, state, runner.pack_boot_args(plan, FB), add_setup_assets


def stop_process(process):
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


def finish_worker(process):
    try:
        process.wait(timeout=12)
    except subprocess.TimeoutExpired:
        stop_process(process)


def linux_runner(base, out, windows_python, native_log):
    import importlib.util
    runner = Path(__file__).with_name('qemu-service-ram.py')
    spec = importlib.util.spec_from_file_location('qemu_service_ram', runner)
    ram_runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ram_runner)

    check(not out.exists(), 'refusing to overwrite a native Setup run')
    check(subprocess.check_output(['findmnt', '-n', '-o', 'FSTYPE', '-T', out.parent],
          text=True).strip() == 'tmpfs', 'native overlay must be on the existing tmpfs')
    out.mkdir()
    root = base / 'setup-root-watchdog-v1' / 'root.hfs'
    payload, plan, layout, boot_args, install_assets = prepare_boot(ram_runner, root, base / 'setup-run-v6', out)
    cow = out / 'root-overlay.qcow2'
    fused = out / 'root-overlay.hfs'
    subprocess.run(['qemu-img', 'create', '-q', '-f', 'qcow2', '-F', 'raw', '-b',
                    root, cow, str(plan['root_bytes'])], check=True)
    fused.touch(exist_ok=False)
    with ExitStack() as stack:
        stack.callback(cow.unlink, missing_ok=True)
        stack.callback(fused.unlink, missing_ok=True)
        storage = subprocess.Popen(['qemu-storage-daemon',
            '--blockdev', f'driver=file,node-name=container,filename={cow}',
            '--blockdev', 'driver=qcow2,node-name=root,file=container',
            '--export', f'type=fuse,id=root-export,node-name=root,mountpoint={fused},writable=on,allow-other=off'])
        stack.callback(stop_process, storage)
        deadline = time.monotonic() + 10
        while fused.stat().st_size == 0 and storage.poll() is None and time.monotonic() < deadline:
            time.sleep(0.1)
        check(fused.stat().st_size == plan['root_bytes'], 'native HFS overlay did not mount')
        layout.update(install_assets(fused, plan, out, 0))
        check('setup_fonts' in layout and 'hid_plugin' in layout, 'native Setup assets are incomplete')
        (out / 'layout.json').write_text(json.dumps(layout, indent=2) + '\n')
        gdb_host, gdb_peer = wsl_gdb_address()
        control_listener = stack.enter_context(socket.create_server(('127.0.0.1', 0)))
        native_gdb = stack.enter_context(socket.create_server((gdb_host, 0)))
        local_gdb = stack.enter_context(socket.create_server(('127.0.0.1', 0)))
        control_listener.settimeout(20)
        native_gdb.settimeout(60)
        local_gdb.settimeout(90)
        token = secrets.token_bytes(32)
        windows_path = lambda path: subprocess.check_output(['wslpath', '-w', path], text=True).strip()
        worker = subprocess.Popen([windows_python, windows_path(Path(__file__).resolve()), '--worker',
            str(control_listener.getsockname()[1]), gdb_host, str(native_gdb.getsockname()[1]),
            token.hex(), windows_path(native_log.resolve())])
        stack.callback(finish_worker, worker)
        control = stack.enter_context(control_listener.accept()[0])
        control.settimeout(60)
        with control.makefile('rb') as incoming:
            check(incoming.read(len(token)) == token, 'unknown native QEMU worker')
            raw_pid = incoming.read(4)
            check(len(raw_pid) == 4, 'native QEMU did not finish initialization. See its Windows log.')
            pid = struct.unpack('<I', raw_pid)[0]
            (out / 'windows-qemu.pid').write_text(str(pid) + '\n')

            def write(address, data):
                control.sendall(struct.pack('<QQ', address, len(data)))
                control.sendall(data)

            for address, _, offset, length in plan['segments']:
                if length:
                    write(address, payload[offset:offset + length])
            with fused.open('rb') as image:
                address = plan['root_pa']
                while data := image.read(SLICE):
                    if data.count(0) != len(data):
                        write(address, data)
                    address += len(data)
                check(address == plan['adt_pa'], 'short native HFS image')
            write(plan['adt_pa'], plan['adt'])
            write(plan['boot_pa'], boot_args)
            write(STUB, struct.pack('<4I2Q', 0x58000080, 0x580000a1, 0xd61f0020, 0xd503201f,
                                   plan['boot_pa'], plan['entry_pa']))
            control.sendall(bytes(16))
            check(incoming.read(1) == b'R', 'native RAM staging failed')
        stop_process(storage)
        fused.unlink()
        cow.unlink()
        control.settimeout(20)
        threading.Thread(target=serve_gdb, args=(native_gdb, local_gdb, gdb_peer), daemon=True).start()
        frame_dir = stack.enter_context(tempfile.TemporaryDirectory(prefix='duchamp-native-'))
        endpoint = str(Path(frame_dir) / 'fb.sock')
        frame_listener = stack.enter_context(socket.socket(socket.AF_UNIX))
        frame_listener.bind(endpoint)
        frame_listener.listen()
        threading.Thread(target=serve_frames, args=(frame_listener, control), daemon=True).start()
        env = dict(os.environ, SWEET_QEMU_WINDOWS_FRAME_SOCKET=endpoint)
        script = out / 'debugger.gdb'
        script.write_text('set pagination off\nset confirm off\nset architecture aarch64\n'
            f'target remote 127.0.0.1:{local_gdb.getsockname()[1]}\n'
            'python import gdb; assert int(gdb.parse_and_eval("$pc")) == 0x40200000\n' +
            Path('tools/duchamp-quartzcore.gdb').read_text())
        with (out / 'debugger.log').open('w') as debug_log:
            debugger = subprocess.run(['gdb-multiarch', '-q', '-nx', '-batch', '-x', str(script)],
                cwd=out, env=env, stdout=debug_log, stderr=subprocess.STDOUT, timeout=3600)
        control.shutdown(socket.SHUT_WR)
        worker.wait(timeout=15)
        (out / 'result.json').write_text(json.dumps({'native_qemu_pid': pid, 'gdb_exit': debugger.returncode}) + '\n')
        return debugger.returncode


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--worker', nargs=5, metavar=('CONTROL', 'GDB_HOST', 'GDB_PORT', 'TOKEN', 'LOG'))
    parser.add_argument('--linux', nargs=4, metavar=('FIXTURES', 'RUN', 'WINDOWS_PYTHON', 'LOG'))
    args = parser.parse_args()
    if args.worker and os.name == 'nt':
        control, host, gdb, token, log = args.worker
        return native_worker(int(control), host, int(gdb), bytes.fromhex(token), Path(log))
    if args.linux and os.name == 'posix':
        base, out, python, log = map(Path, args.linux)
        return linux_runner(base, out, python, log)
    parser.error('choose the native Windows worker or WSL launcher')


if __name__ == '__main__':
    sys.exit(main())
