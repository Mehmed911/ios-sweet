#!/usr/bin/env python3
"""Acquire the matching original SystemOS ZIP member into a new private directory."""
import argparse
import hashlib
import json
from pathlib import Path
import plistlib
import runpy
import subprocess
import remotezip

REPO = Path(__file__).resolve().parents[1]
ENTRY = ('096-04666-078.dmg', 8, 1094826706, 2726297600, 4822870835, 501033685)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    out = args.output.resolve()
    if out.exists():
        raise SystemExit('preserve existing acquisition directory')
    manifest_path = REPO / 'research/launchctl-20F66/BuildManifest.plist'
    manifest = plistlib.loads(manifest_path.read_bytes())
    paths = {item.get('Manifest', {}).get('Cryptex1,SystemOS', {}).get('Info', {}).get('Path')
             for item in manifest['BuildIdentities']}
    if manifest['ProductBuildVersion'] != '20F66' or ENTRY[0] not in paths:
        raise SystemExit('saved build manifest does not identify matching SystemOS')
    url = runpy.run_path(str(REPO / 'tools/prepare-darwin-runtime.py'))['URL']
    entry = next(item for item in remotezip.central_dir(url) if item[0] == ENTRY[0])
    if tuple(entry) != ENTRY:
        raise SystemExit('live ZIP metadata differs from pinned local index')
    out.mkdir(parents=True)
    receipt = dict(source_url=url, build='20F66', zip_entry=list(entry),
        manifest_sha256=hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
        zip_metadata_matched=True, complete=False,
        scope=dict(phone_access=False, partition_write=False, signature_authenticated=False))
    (out / 'acquisition.json').write_text(json.dumps(receipt, indent=2) + '\n')
    remotezip.extract(url, entry, str(out))
    member = out / ENTRY[0]
    digest = hashlib.sha256()
    with member.open('rb') as stream:
        for chunk in iter(lambda: stream.read(8 << 20), b''):
            digest.update(chunk)
    receipt.update(complete=True, bytes=member.stat().st_size, sha256=digest.hexdigest(), zip_crc_verified=True)
    (out / 'acquisition.json').write_text(json.dumps(receipt, indent=2) + '\n')
    with (out / 'file-list.txt').open('w') as log:
        listing = subprocess.run(['7z', 'l', '-slt', str(member)], stdout=log, stderr=subprocess.STDOUT)
    receipt['listing_exit_code'] = listing.returncode
    (out / 'acquisition.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt, indent=2), flush=True)


if __name__ == '__main__':
    main()
