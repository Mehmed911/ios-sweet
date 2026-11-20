#!/usr/bin/env python3
"""0BSD recursive load-command audit of an intact, locally held dyld cache.

Consumes ipsw `dyld macho --all --json` JSON lines. Cache membership is a
static availability classification, never proof of executable ABI behavior.
"""
import argparse
import json
from pathlib import Path
import uuid
from duchamp_macho_preflight import inspect

IMPORTS = {'LC_LOAD_DYLIB', 'LC_REEXPORT_DYLIB', 'LC_LOAD_UPWARD_DYLIB', 'LC_LOAD_WEAK_DYLIB'}


def version(value):
    parts = tuple(int(x) for x in value.split('.'))
    if not 1 <= len(parts) <= 3 or any(x < 0 for x in parts):
        raise ValueError('invalid OS version')
    return parts + (0,) * (3 - len(parts))


def cache_index(records):
    images = {}
    for record in records:
        names = [x['name'] for x in record['loads'] if x['load_cmd'] in ('LC_ID_DYLIB', 'LC_ID_DYLINKER')]
        if len(names) != 1 or names[0] in images:
            raise ValueError('missing or duplicate cache install name')
        images[names[0]] = record
    return images


def closure(entry, original, images, standalone=None):
    standalone = standalone or {}
    todo = [(entry, original)]
    nodes, edges, seen = {}, [], set()
    while todo:
        path, record = todo.pop()
        if path in seen:
            continue
        seen.add(path)
        if record is None:
            nodes[path] = {'classification': 'UNKNOWN' if path.startswith('@') else 'MISSING'}
            continue
        if 'header' in record:
            h = record['header']
            builds = [x for x in record['loads'] if x['load_cmd'] == 'LC_BUILD_VERSION']
            state = 'PRESENT_IN_SHARED_CACHE'
            if h['cpu'] != 'AARCH64' or h['subcpu'] != 'ARM64':
                state = 'ARCHITECTURE_MISMATCH'
            elif len(builds) != 1 or builds[0].get('platform') != 'iOS' or version(builds[0]['min_os']) > (16, 5, 0):
                state = 'UNKNOWN'
            nodes[path] = dict(classification=state, header=h, build=builds,
                uuid=[x['uuid'] for x in record['loads'] if x['load_cmd'] == 'LC_UUID'],
                abi_execution_proven=False)
            dependencies = [(x['name'], x['load_cmd'] == 'LC_LOAD_WEAK_DYLIB')
                            for x in record['loads'] if x['load_cmd'] in IMPORTS]
        else:
            nodes[path] = dict(classification='AVAILABLE_AND_COMPATIBLE', metadata=record,
                               compatibility_scope='plain ARM64 iOS16.5 metadata only')
            dependencies = [(x['path'], x['weak']) for x in record['dependencies']]
            if record.get('dylinker'):
                dependencies.append((record['dylinker'], False))
        for target, weak in dependencies:
            edges.append(dict(importer=path, target=target, weak=weak))
            if not weak:
                todo.append((target, standalone.get(target, images.get(target))))
    unresolved = {p: v for p, v in nodes.items() if v['classification'] not in
                  ('PRESENT_IN_SHARED_CACHE', 'AVAILABLE_AND_COMPATIBLE')}
    return dict(entry=entry, nodes=nodes, edges=edges, unresolved=unresolved,
                strong_metadata_closure_complete=not unresolved,
                runtime_abi_compatibility_proven=False)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('cache_jsonl', type=Path)
    ap.add_argument('output', type=Path)
    ap.add_argument('--cache-directory', type=Path, required=True)
    a = ap.parse_args()
    images = cache_index(json.loads(line) for line in a.cache_jsonl.read_text().splitlines())
    reports = {}
    for name, source in {
        'backboardd': 'work/ui-daemon-scan-v1/apple-extracted/usr/libexec/backboardd',
        'SpringBoard': 'work/springboard-bundle-v2/apple-extracted/System/Library/CoreServices/SpringBoard.app/SpringBoard'
    }.items():
        guest = '/usr/libexec/backboardd' if name == 'backboardd' else '/System/Library/CoreServices/SpringBoard.app/SpringBoard'
        dyld = inspect('research/dyld-runtime-20F66/runtime-root/usr/lib/dyld')
        reports[name] = closure(guest, inspect(source), images, {'/usr/lib/dyld': dyld})
    # Cross-check every runtime file UUID with the inspection tool's mapping
    # identities. The full byte hashes are checked by the preparation runner.
    components = []
    for p in sorted(a.cache_directory.glob('dyld_shared_cache_arm64*')):
        if p.name.endswith('.symbols'):
            continue
        with p.open('rb') as f:
            header = f.read(104)
        if header[:7] != b'dyld_v1' or len(header) != 104:
            raise ValueError('invalid runtime subcache header: ' + p.name)
        components.append(dict(name=p.name, uuid=str(uuid.UUID(bytes=header[88:104])).upper()))
    report = dict(cache_images=len(images), runtime_components=components, services=reports,
                  classifications_are_not_runtime_success=True)
    a.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: dict(nodes=len(v['nodes']), edges=len(v['edges']),
        unresolved=v['unresolved']) for k, v in reports.items()}, indent=2))


if __name__ == '__main__':
    main()
