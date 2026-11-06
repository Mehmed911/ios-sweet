#!/usr/bin/env python3
"""Extract and inventory the acquired matching SystemOS dyld cache locally."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

REPO = Path(__file__).resolve().parents[1]
IMAGE_PIN = '2279bf443856fcb6a3f00b1fa06a32ba02a66fdf6ab6b12019462c7498aafdd3'


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(8 << 20), b''):
            digest.update(chunk)
    return digest.hexdigest()


def expected_components(source):
    prefix = 'System/Library/Caches/com.apple.dyld/'
    expected = {}
    for block in (source / 'file-list.txt').read_text().split('\n\n'):
        fields = dict(line.split(' = ', 1) for line in block.splitlines() if ' = ' in line)
        path = fields.get('Path', '')
        if path.startswith(prefix) and fields.get('Size', '').isdigit():
            name = path[len(prefix):]
            if '/' not in name and ':' not in name and name.startswith('dyld_shared_cache_arm64'):
                expected[name] = int(fields['Size'])
    if len(expected) != 44:
        raise SystemExit('incomplete or changed cache file inventory')
    return expected


def verify_reused_component(path, name, size, manifest):
    info = manifest['files'].get(name)
    if not info or info['bytes'] != size or path.stat().st_size != size or sha(path) != info['sha256']:
        raise SystemExit('reused cache component provenance mismatch: ' + name)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source', required=True, type=Path)
    ap.add_argument('--output', required=True, type=Path)
    ap.add_argument('--cache-input', type=Path, help='preserved partial cache extraction for strict recovery')
    ap.add_argument('--recovered-linkedit', type=Path, help='strict apfs-fuse ZBM decoder output')
    ap.add_argument('--recovered-dir', type=Path, help='complete strict three-component ZBM recovery')
    ap.add_argument('--cache-manifest', type=Path, help='source-bound receipt for reused ordinary components')
    ap.add_argument('--regular-only', action='store_true', help='freshly extract/hash the 41 ordinary components')
    args = ap.parse_args()
    source, out = args.source.resolve(), args.output.resolve()
    if out.exists():
        raise SystemExit('preserve existing output')
    decoded_options = int(bool(args.recovered_linkedit)) + int(bool(args.recovered_dir))
    if bool(args.cache_input) != bool(decoded_options) or decoded_options > 1:
        raise SystemExit('recovery requires cache input and exactly one decoded-file or decoded-directory option')
    if args.cache_input and not args.cache_manifest:
        raise SystemExit('reused cache input requires its source-bound component manifest')
    if args.regular_only and args.cache_input:
        raise SystemExit('ordinary extraction and reuse are separate modes')
    receipt = json.loads((source / 'acquisition.json').read_text())
    image = source / '096-04666-078.dmg'
    if not (receipt['complete'] and receipt['zip_crc_verified'] and receipt['sha256'] == IMAGE_PIN
            and image.stat().st_size == 2726297600 and sha(image) == IMAGE_PIN):
        raise SystemExit('SystemOS acquisition identity mismatch')
    out.mkdir(parents=True)
    target = out / 'apple-extracted'
    cache_dir = target / 'System/Library/Caches/com.apple.dyld'
    recovery = None
    expected = expected_components(source)
    if args.regular_only:
        compressed = {'dyld_shared_cache_arm64.42.dyldlinkedit', 'dyld_shared_cache_arm64.28.dyldlinkedit', 'dyld_shared_cache_arm64.symbols'}
        regular = {name: size for name, size in expected.items() if name not in compressed}
        with (out / 'extract.log').open('w') as log:
            subprocess.run(['7z', 'x', '-y', '-bd', '-bb0', '-spd', '-o' + str(target), str(image),
                *['System/Library/Caches/com.apple.dyld/' + name for name in regular]],
                check=True, stdout=log, stderr=subprocess.STDOUT)
        verified = {}
        for name, size in regular.items():
            path = cache_dir / name
            if not path.is_file() or path.stat().st_size != size:
                raise SystemExit('ordinary source extraction failed: ' + name)
            verified[name] = dict(bytes=size, sha256=sha(path))
        (out / 'component-manifest.json').write_text(json.dumps(dict(source_image_sha256=IMAGE_PIN,
            source_extraction_completed=True, ordinary_count=len(regular), files=verified), indent=2) + '\n')
        print('Source-bound ordinary cache extraction: PASS components=' + str(len(regular)), flush=True)
        return
    if args.cache_input:
        manifest = json.loads(args.cache_manifest.read_text())
        if manifest.get('source_image_sha256') != IMAGE_PIN or manifest.get('source_extraction_completed') is not True:
            raise SystemExit('cache component manifest is not tied to the verified image')
        recovered = {}
        if args.recovered_dir:
            decoded_receipt = json.loads((args.recovered_dir / 'receipt.json').read_text())
            if not (decoded_receipt['passed'] and decoded_receipt['image_sha256'] == IMAGE_PIN
                    and decoded_receipt['unknown_component_rejected']):
                raise SystemExit('invalid recovery receipt')
            for name, info in decoded_receipt['files'].items():
                if '/' in name or not name.startswith('dyld_shared_cache_arm64'):
                    raise SystemExit('unsafe recovered component name')
                decoded = args.recovered_dir.resolve() / name
                if decoded.stat().st_size != info['bytes'] or sha(decoded) != info['sha256']:
                    raise SystemExit('recovered component changed')
                recovered[name] = decoded
        else:
            decoded = args.recovered_linkedit.resolve()
            decoded_pin = '05256dce35f488828f2316e5651a24cfbcb48a751597be0303657cede2f9128f'
            if decoded.stat().st_size != 333955072 or sha(decoded) != decoded_pin:
                raise SystemExit('decoded linkedit pin mismatch')
            recovered['dyld_shared_cache_arm64.42.dyldlinkedit'] = decoded
        cache_dir.mkdir(parents=True)
        for name, size in expected.items():
            original = args.cache_input.resolve() / name
            if name in recovered:
                original = recovered[name]
            else:
                verify_reused_component(original, name, size, manifest)
            if not original.is_file() or original.stat().st_size != size:
                raise SystemExit('missing/incorrect cache component: ' + name)
            shutil.copyfile(original, cache_dir / name)
        recovery = dict(input=str(args.cache_input.resolve()), decoded_files={name: sha(path) for name, path in recovered.items()},
                        source_component_manifest_sha256=sha(args.cache_manifest),
                        expected_components=len(expected), strict_size_checks=True)
    else:
        with (out / 'extract.log').open('w') as log:
            result = subprocess.run(['7z', 'x', '-y', '-bd', '-bb0', '-spd', '-o' + str(target), str(image),
                'System/Library/Caches/com.apple.dyld'], stdout=log, stderr=subprocess.STDOUT)
        if result.returncode:
            (out / 'extraction-failure.json').write_text(json.dumps(dict(source_image_sha256=IMAGE_PIN,
                extraction_exit_code=result.returncode, complete=False, input_preserved=True), indent=2) + '\n')
            raise SystemExit('7z extraction incomplete; preserve output and inspect log')
    files = {path.name: dict(bytes=path.stat().st_size, sha256=sha(path))
             for path in sorted(cache_dir.iterdir()) if path.is_file()}
    cache = cache_dir / 'dyld_shared_cache_arm64'
    ipsw = REPO / 'research/host-ipsw-3.1.739/ipsw'
    with (out / 'cache-info.json').open('w') as log, (out / 'cache-info.stderr.txt').open('w') as error:
        result = subprocess.run([str(ipsw), 'dyld', 'info', '--json', '--dylibs', str(cache)], stdout=log, stderr=error)
    report = dict(source_image_sha256=IMAGE_PIN, source_build='20F66', cache=str(cache), files=files,
        total_bytes=sum(item['bytes'] for item in files.values()), cache_info_exit_code=result.returncode,
        zbm_recovery=recovery,
        ipsw_sha256=sha(ipsw), scope=dict(phone_access=False, partition_write=False,
            cache_executed=False, standalone_framework_execution_compatible=False))
    (out / 'receipt.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({key: value for key, value in report.items() if key != 'files'}, indent=2), flush=True)
    if result.returncode:
        raise SystemExit('cache inventory failed; preserved extraction/logs')


if __name__ == '__main__':
    main()
