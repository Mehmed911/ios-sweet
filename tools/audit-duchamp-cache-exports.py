#!/usr/bin/env python3
"""Associate derived framework exports with the matching cache; inspect loader metadata."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
import shutil
import struct
import subprocess
import uuid

REPO = Path(__file__).resolve().parents[1]
NAMES = ('ContainerManagerCommon', 'ContainerManagerSystem', 'ContainerManagerUser', 'CacheDelete')
MACHO = runpy.run_path(str(REPO / 'tools/audit-darwin-runtime.py'))['macho']


def loader_metadata(path):
    data = path.read_bytes()
    count, command_bytes = struct.unpack_from('<II', data, 16)
    cursor = 32
    result = dict(uuid=None, dyld_info=[], chained_fixups=[], segment_ranges=[], cache_pointer_samples=[])
    for _ in range(count):
        cmd, size = struct.unpack_from('<II', data, cursor)
        if size < 8 or cursor + size > 32 + command_bytes:
            raise ValueError('invalid load command')
        if cmd == 0x1b:
            result['uuid'] = str(uuid.UUID(bytes=data[cursor + 8:cursor + 24])).upper()
        elif cmd in (0x22, 0x80000022):
            fields = struct.unpack_from('<10I', data, cursor + 8)
            result['dyld_info'].append(dict(rebase_bytes=fields[1], bind_bytes=fields[3],
                weak_bind_bytes=fields[5], lazy_bind_bytes=fields[7], export_bytes=fields[9]))
        elif cmd == 0x80000034:
            offset, length = struct.unpack_from('<II', data, cursor + 8)
            result['chained_fixups'].append(dict(offset=offset, bytes=length,
                in_file=offset <= len(data) and length <= len(data) - offset))
        elif cmd == 0x19:
            name = data[cursor + 8:cursor + 24].split(b'\0', 1)[0].decode()
            address, virtual_bytes, offset, file_bytes = struct.unpack_from('<4Q', data, cursor + 24)
            if offset > len(data) or file_bytes > len(data) - offset:
                raise ValueError('exported segment outside file')
            result['segment_ranges'].append(dict(name=name, address=address, bytes=virtual_bytes))
            if name.startswith(('__DATA', '__AUTH')):
                for pos in range(offset, offset + file_bytes - 7, 8):
                    target, = struct.unpack_from('<Q', data, pos)
                    if 0x180000000 <= target < 0x240000000 and len(result['cache_pointer_samples']) < 24:
                        result['cache_pointer_samples'].append(dict(file_offset=pos, target=target))
        cursor += size
    result['bind_or_rebase_metadata_present'] = any(item['rebase_bytes'] or item['bind_bytes']
        or item['weak_bind_bytes'] or item['lazy_bind_bytes'] for item in result['dyld_info']) or any(
        item['bytes'] for item in result['chained_fixups'])
    result['sampled_external_cache_pointers'] = [item for item in result['cache_pointer_samples'] if not any(
        segment['address'] <= item['target'] < segment['address'] + segment['bytes']
        for segment in result['segment_ranges'])]
    result['standalone_blockers'] = []
    if result['sampled_external_cache_pointers'] and not result['bind_or_rebase_metadata_present']:
        result['standalone_blockers'].append('external cache addresses without declared bind/rebase metadata')
    result['standalone_payload_allowed'] = False
    result['note'] = 'Pointer samples are observations only; no relocation/binding repair or runtime validation is performed.'
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--cache-info', required=True, type=Path)
    ap.add_argument('--exports', required=True, type=Path)
    ap.add_argument('--output', required=True, type=Path)
    ap.add_argument('--extra', action='append', default=[], help='additional exact cache dependency path')
    args = ap.parse_args()
    if args.output.exists():
        raise SystemExit('preserve existing export audit')
    cache = json.loads(args.cache_info.read_text())
    if cache['uuid'] != 'E5420DB3-30D0-33AA-8B7E-05B5038BB46D' or cache['magic'] != 'dyld_v1   arm64':
        raise SystemExit('cache identity mismatch')
    images = {item['name']: item for item in cache['dylibs']}
    reports = {}
    targets = list(dict.fromkeys(['/System/Library/PrivateFrameworks/' + name + '.framework/' + name
                                 for name in NAMES] + args.extra))
    for guest in targets:
        if not guest.startswith('/') or '..' in guest.split('/') or guest not in images:
            raise SystemExit('unsafe or unavailable cache dependency: ' + guest)
        if len({item['uuid'] for item in cache['dylibs'] if item['name'] == guest}) != 1:
            raise SystemExit('ambiguous cache dependency identity: ' + guest)
        name = Path(guest).name
        source = args.exports / name
        meta = MACHO(source)
        loader = loader_metadata(source)
        if loader['uuid'] != images[guest]['uuid']:
            raise SystemExit('derived export UUID mismatch: ' + name)
        reports[guest] = dict(cache_image=images[guest], macho=meta, loader=loader,
            provenance='Tool-derived cache export with --slide; not unchanged original standalone file',
            standalone_runtime_validated=False)
    args.output.mkdir(parents=True)
    runtime = args.output / 'runtime-root'
    for guest in reports:
        dest = runtime / guest.lstrip('/')
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(args.exports / Path(guest).name, dest)
    (args.output / 'exports.json').write_text(json.dumps(dict(cache_uuid=cache['uuid'],
        cache_image_count=len(cache['dylibs']), unique_image_paths=len(images), exports=reports,
        phone_access=False, partition_write=False), indent=2) + '\n')
    command = ['python3', str(REPO / 'tools/audit-duchamp-ui-runtime.py'), '--root', str(runtime),
        '--root', str(REPO / 'work/lsd-support-audit-v1/apple-extracted'),
        '--root', str(REPO / 'research/cfprefs-runtime-20F66-v2/runtime-root'),
        '--root', str(REPO / 'research/foundation-20F66/apple-extracted'),
        '--output', str(args.output / 'support-closure.json')]
    for guest in ('/usr/libexec/containermanagerd', '/usr/libexec/containermanagerd_system', '/usr/libexec/logd'):
        command += ['--entry', guest, '--require', guest]
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    (args.output / 'closure.log').write_text(result.stdout)
    report = dict(cache_uuid=cache['uuid'], cache_image_count=len(cache['dylibs']), unique_image_paths=len(images), selected_exports=len(reports),
        closure_exit_code=result.returncode, exports_sha256=hashlib.sha256((args.output / 'exports.json').read_bytes()).hexdigest(),
        source_files_available=True, standalone_runtime_validated=False, standalone_payload_allowed=False,
        exports_with_structural_blockers=sum(bool(item['loader']['standalone_blockers']) for item in reports.values()), phone_access=False)
    (args.output / 'summary.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    print(result.stdout)
    return result.returncode


if __name__ == '__main__':
    raise SystemExit(main())
