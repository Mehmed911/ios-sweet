#!/usr/bin/env python3
"""Package a locally proved services RAM root for a separate Duchamp trial."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys

REPO = Path(__file__).resolve().parents[1]
CMDLINE = ('debug=0xc serial=3 cpus=1 keepsyms=1 -enable_kprintf_spam '
           '-noprogress rd=md0 rootrw=1 sweet_console_fb=1 '
           'duchamp_timer_irq_ack=1 unentitled_ios_sim_launch=1 '
           'launchdsuffix=sweet launchd_log_serial=1')
PINS = {
    'kernel': 'e465723a540844817a5b9cb36c14984d660f9a8e41f6638240527b469189182b',
    'root.hfs': '3e800f071990192fefd69684477618532c85ab85accbd74f750a51c2f70e6baf',
    'phone.adt': '6ae3d3c054676a78d33c02ff89c6d19b6e851df63c74e973e599dd04aaa541c0',
    'qemu.adt': 'a881410d04a3cec3b7ebd9bee91f510c755683b94f5a26d71c47301fff7417d8',
}
STOCK_PIN = '1b972f4f1c98428f2fca1e7c1c8cf463e0122a70a290e482be3230c7838e3e12'
FDT_PIN = '9c49589f70044127be8941a9ea5537977f440ccd5ac15cfd24e120c8a1181d29'
AVB_PIN = '1f1fddd2764eba76dc659415406062251edcf2eb6b4e83b0f01d0224cd631281'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def symbols(elf):
    text = subprocess.check_output(['llvm-nm', '-n', str(elf)], text=True)
    return {line.split()[-1]: int(line.split()[0], 16)
            for line in text.splitlines() if len(line.split()) >= 3}


def inspect_payload(blob):
    require(len(blob) >= 0x2a8, 'truncated payload')
    require(struct.unpack_from('<8sII', blob) == (b'SWEETXNU', 1, 11),
            'unexpected payload header')
    virt, entry, adt_offset, adt_size, end, physical, memory = struct.unpack_from('<7Q', blob, 0x10)
    require((physical, memory) == (0x1c0000000, 0x20000000), 'unexpected payload window')
    require(blob[0x48:0x2a8].split(b'\0', 1)[0].decode() == CMDLINE, 'unexpected command line')
    slots = []
    for index in range(11):
        va, _size, offset, count = struct.unpack_from('<4Q', blob, 0x2a8 + index * 32)
        require(offset <= len(blob) and count <= len(blob) - offset, 'invalid segment file range')
        at = blob.find(b'XNULDRST', offset, offset + count)
        while at != -1:
            slots.append(physical + va - virt + at - offset)
            at = blob.find(b'XNULDRST', at + 1, offset + count)
    require(len(slots) == 1 and slots[0] % 8 == 0, 'missing or ambiguous return slot')
    ramdisk = struct.unpack_from('<4Q', blob, 0x2a8 + 10 * 32)
    require(ramdisk[1] == ramdisk[3] == 32 * 1024 * 1024, 'RAM root size changed')
    return {'entry': physical + entry - virt,
            'adt': physical + end - virt, 'adt_bytes': adt_size,
            'adt_offset': adt_offset, 'return_slot': slots[0],
            'delta': (physical - virt) & ((1 << 64) - 1)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--proof-dir', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    proof, out = args.proof_dir.resolve(), args.output.resolve()
    require(not out.exists(), 'preserve existing output')
    for name, expected in PINS.items():
        require(sha256(proof / name) == expected, 'proof input pin mismatch: ' + name)
    guest = json.loads((proof / 'run/verification.json').read_text())
    require(guest.get('passed') is True and len(guest.get('checks', {})) == 74
            and all(value is True for value in guest['checks'].values()),
            'full 74-check service proof is required')
    require(guest['sha256']['root.hfs'] == PINS['root.hfs'] and
            guest['sha256']['payload.bin'] == sha256(proof / 'payload.bin'),
            'guest proof input mismatch')
    stock = REPO.parent / 'phone-boot/boot_a.img'
    fdt = REPO.parent / 'phone-fdt.bin'
    avb = REPO / 'work/tooling/avb-android-platform-14.0.0_r28/avbtool.py'
    require(sha256(stock) == STOCK_PIN and sha256(fdt) == FDT_PIN and
            sha256(avb) == AVB_PIN, 'stock/FDT/AVB tool pin mismatch')

    sys.path.insert(0, str(REPO / 'tools'))
    spec = importlib.util.spec_from_file_location('duchamp_services_mkpayload', REPO / 'tools/mkpayload.py')
    mkpayload = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mkpayload)
    blobs = {}
    for profile in ('phone', 'qemu'):
        blobs[profile], _info = mkpayload.build(str(proof / 'kernel'),
            str(proof / (profile + '.adt')), CMDLINE, str(proof / 'root.hfs'))
    require(blobs['qemu'] == (proof / 'payload.bin').read_bytes(),
            'tested QEMU payload reconstruction mismatch')
    plans = {name: inspect_payload(blob) for name, blob in blobs.items()}
    out.mkdir(parents=True)
    logs = out / 'logs'
    logs.mkdir()
    checks = {'pinned_inputs': True, 'full_guest_batch_74_checks': True,
              'qemu_payload_reconstruction': True, 'ram_root_32_mib': True}

    def run(name, command, env=None):
        result = subprocess.run([str(item) for item in command], cwd=REPO,
            env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        (logs / (name + '.log')).write_text(result.stdout)
        require(result.returncode == 0, name + ' failed: ' + result.stdout[-6000:])
        return result.stdout

    for profile, blob in blobs.items():
        payload = out / ('payload-' + profile + '.bin')
        payload.write_bytes(blob)
        env = os.environ.copy()
        for flag in ('PHONE_LAYOUT', 'QEMU_ONLY', 'LK_RAM_TRANSPORT', 'PHONE_CAPTURE',
                     'PHONE_CONTRACT', 'TEST_XNU_RETURN', 'RETURN_CHECKPOINT', 'EXTRA_CFLAGS'):
            env.pop(flag, None)
        env.update(PAYLOAD=str(payload), MATERIALIZE='1', READY='1', JUMP='1',
                   RETURN='1', SHIM_OUT=str(out / (profile + '-shim')))
        if profile == 'qemu':
            env['EXTRA_CFLAGS'] = '-DDUCHAMP_TEST_NO_WATCHDOG=1'
        run(profile + '-build', ['sh', 'duchamp/bootshim/build.sh'], env)
        elf = out / (profile + '-shim/duchamp-diagnostic.elf')
        image = (out / (profile + '-shim/Image')).read_bytes()
        sym = symbols(elf)
        require(sym['_head'] == 0 and sym['_end'] == len(image), 'unexpected Image layout')
        require(image[sym['duchamp_embedded_payload_start']:sym['duchamp_embedded_payload_end']] == blob,
                profile + ' embedded payload mismatch')
        require(len(image) < (0x47c80000 - 0x40000000), 'Image exceeds measured FDT placement')
        reloc = run(profile + '-relocations', ['llvm-readelf', '-r', elf])
        unresolved = run(profile + '-undefined', ['llvm-nm', '-u', elf]).strip()
        disassembly = run(profile + '-disassembly', ['llvm-objdump', '-d', elf])
        require('There are no relocations' in reloc and not unresolved,
                profile + ' ELF is not freestanding')
        require(len(re.findall(r'\bbr\s+x\d+\b', disassembly)) == 1,
                profile + ' must have exactly one final indirect branch')
        checks[profile + '_elf_and_embedded_payload'] = True

    env = os.environ.copy()
    env['SHIM_TEST_OUT'] = str(out / 'host-tests')
    run('host-tests', ['sh', 'duchamp/bootshim/test.sh', fdt, out / 'payload-phone.bin'], env)
    checks['host_entry_preflight_handoff_return'] = True
    run('materialize-build', ['clang', '-std=c11', '-O2', '-Wall', '-Wextra', '-Werror',
        'duchamp/loader/test_materialize.c', 'duchamp/loader/guard.c',
        'duchamp/loader/plan.c', 'duchamp/loader/materialize.c',
        '-o', out / 'host-tests/test_materialize'])
    run('materialize', [out / 'host-tests/test_materialize', fdt, out / 'payload-phone.bin'])
    checks['full_materialization_byte_comparison'] = True
    sym = symbols(out / 'qemu-shim/duchamp-diagnostic.elf')
    run('bootshim-qemu-entry', ['python3', 'duchamp/bootshim/test_qemu.py',
        '--image', out / 'qemu-shim/Image', '--pattern', 'xnu', '--memory', '8G',
        '--wait', '2', '--dtb', fdt, '--slot-pa', hex(plans['qemu']['return_slot']),
        '--expect-slot-stub', hex(0x40200000 + sym['duchamp_xnu_return_stub']),
        '--expect-slot-checkpoint', '0', '--expect-slot-delta', hex(plans['qemu']['delta']),
        '--return-record-pa', hex(0x40200000 + sym['duchamp_bootshim_xnu_return_record']),
        '--expect-no-return'])
    checks['real_bootshim_qemu_xnu_entry'] = True

    raw_path = out / 'boot-raw.img'
    run('pack', ['python3', 'duchamp/bootshim/pack_boot.py', '--stock-boot', stock,
        '--kernel', out / 'phone-shim/Image', '--out', raw_path, '--lz4-legacy'])
    raw, original = raw_path.read_bytes(), stock.read_bytes()
    footer = struct.unpack('>4sIIQQQ28s', original[-64:])
    require(footer[:3] == (b'AVBf', 1, 0) and footer[3] == footer[4] == 16318464,
            'unexpected stock AVB container')
    require(len(raw) <= footer[3] and
            raw[:8] + raw[12:1584] == original[:8] + original[12:1584],
            'payload exceeds stock region or changes stock metadata')
    final = out / 'duchamp-services-batch-avb-none-lz4.img'
    with final.open('xb') as stream:
        stream.write(raw)
        stream.write(bytes(footer[3] - len(raw)))
    run('avb-add', ['python3', avb, 'add_hash_footer', '--image', final,
        '--partition_name', 'boot', '--partition_size', '67108864', '--algorithm', 'NONE',
        '--salt', 'dc377119eeeb00c358acad59da11fc706f6274025cc6ca1273d1b2ff7245f936'])
    verification = out / 'verification'
    verification.mkdir()
    shutil.copyfile(final, verification / 'boot.img')
    run('avb-verify', ['python3', avb, 'verify_image', '--image', verification / 'boot.img'])
    info = run('avb-info', ['python3', avb, 'info_image', '--image', final])
    require('Algorithm:                NONE' in info and 'Partition Name:        boot' in info,
            'unexpected AVB algorithm or partition')
    require(final.stat().st_size == 67108864 and final.read_bytes()[:len(raw)] == raw,
            'final boot image layout mismatch')
    checks['boot_v4_metadata_and_stock_region'] = True
    checks['avb_none_footer_hash_and_size'] = True
    kernel_size = struct.unpack_from('<I', raw, 8)[0]
    compressed = verification / 'kernel.lz4'
    compressed.write_bytes(raw[4096:4096 + kernel_size])
    require(compressed.read_bytes()[:4] == bytes.fromhex('02214c18'), 'not legacy LZ4')
    run('lz4-roundtrip', ['lz4', '-d', str(compressed), str(verification / 'Image')])
    require((verification / 'Image').read_bytes() == (out / 'phone-shim/Image').read_bytes(),
            'LZ4 roundtrip mismatch')
    checks['lz4_roundtrip_byte_identical'] = True
    source_files = ['duchamp/bootshim/start.S', 'duchamp/bootshim/shim.c',
        'duchamp/bootshim/shim.ld',
        'duchamp/bootshim/build.sh', 'duchamp/loader/guard.c', 'duchamp/loader/plan.c',
        'duchamp/loader/materialize.c', 'duchamp/loader/return_slot.c']
    report = {'passed': all(checks.values()), 'checks': checks,
        'kernel_sha256': PINS['kernel'], 'root_sha256': PINS['root.hfs'],
        'guest_checks': 74, 'guest_elapsed_host_seconds': guest['elapsed_host_seconds'],
        'guest_verification_sha256': sha256(proof / 'run/verification.json'),
        'boot_image': str(final), 'boot_image_bytes': final.stat().st_size,
        'boot_image_sha256': sha256(final), 'compressed_kernel_bytes': kernel_size,
        'phone_payload_sha256': sha256(out / 'payload-phone.bin'),
        'qemu_payload_sha256': sha256(out / 'payload-qemu.bin'),
        'source_sha256': {path: sha256(REPO / path) for path in source_files},
        'scope': {'phone_access': False, 'partition_write': False,
                  'physical_ufs_enabled': False, 'phone_service_batch_proven': False}}
    (out / 'verification.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        raise SystemExit('services candidate failed: ' + str(error))
