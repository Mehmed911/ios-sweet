#!/usr/bin/env python3
"""Prepare the isolated 20F66 QEMU scene trial from the pinned V6 RAM root."""
import argparse
import hashlib
import json
from pathlib import Path
import plistlib
import shutil
import subprocess

REPO = Path(__file__).resolve().parents[1]
BASE_PIN = '8029fb33aa7805e773e10848f05af0f85349a1e1c9fe1e3dcea35890f3f9c171'
HFS_PIN = 'be041fa07ae8cbe040a2ec3811241af993eea597e8d46917f6c32359b2cd8b1b'
RESOURCES_PIN = '9ce1d6f3dcfdca12fe7258e3a7dd65f2d74b578c27e92950d01372704925373c'
NLP_PIN = '657d77ee3088b3a42c75f00606f7aee8900c395d334e3f1492e662c27d44638a'
ARTWORK_PIN = '94536a8c82130f7cc51d51231dbcee13c1184b17eeb70f0a74ab1e5e9ec5369d'
ADDRESS_BOOK_PIN = '3604a54ea85ffaa6006f53816f6fccc13e1ca37f1e55f936a104fceeb1296356'
FRAMEWORK = Path('System/Library/PrivateFrameworks/UIKitCore.framework')
CORE_NLP = Path('System/Library/PrivateFrameworks/CoreNLP.framework')
ARTWORK = FRAMEWORK / 'Artwork.bundle'
COVER_SHEET = FRAMEWORK.with_name('CoverSheet.framework')
ADDRESS_BOOK = FRAMEWORK.with_name('AddressBookLegacy.framework')
JOB = '/System/Library/LaunchDaemons/com.apple.backboardd.plist'
ATTENTION_SERVICE = 'com.apple.AttentionAwareness'


def sha(path):
    with path.open('rb') as file:
        return hashlib.file_digest(file, 'sha256').hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def pin_files(root, paths, expected):
    files = {'/' + path.relative_to(root).as_posix(): path for path in paths}
    receipt = {guest: dict(bytes=path.stat().st_size, sha256=sha(path)) for guest, path in files.items()}
    canonical = json.dumps(receipt, sort_keys=True, separators=(',', ':')).encode()
    require(hashlib.sha256(canonical).hexdigest() == expected, '20F66 resource pins mismatch')
    return files, receipt


def prepare(base, resources, out, language_resources=None, artwork_resources=None, address_book_resources=None):
    helper = REPO / 'work/ui-surface-qemu-v3/evidence/hfsplus'
    require(sha(base) == BASE_PIN, 'expected the pinned V6 QEMU RAM root')
    require(sha(helper) == HFS_PIN, 'HFS helper pin mismatch')
    framework = resources / FRAMEWORK
    collations = sorted(framework.glob('*.lproj/UITableViewLocalizedSectionIndex.plist'))
    require(len(collations) == 41, 'expected 41 original collation dictionaries')
    files, receipt = pin_files(resources, [framework / 'Info.plist', *collations], RESOURCES_PIN)
    if language_resources:
        models = sorted(path for path in (language_resources / CORE_NLP).iterdir() if path.is_file())
        paths = [*models, language_resources / 'usr/share/langid/langid.inv']
        language_files, language_receipt = pin_files(language_resources, paths, NLP_PIN)
        files.update(language_files)
        receipt.update(language_receipt)
    if artwork_resources:
        artwork = artwork_resources / ARTWORK
        cover_sheet = artwork_resources / COVER_SHEET
        paths = sorted(path for path in artwork.rglob('*') if path.is_file())
        paths.extend([cover_sheet / 'Assets.car', cover_sheet / 'Info.plist'])
        artwork_files, artwork_receipt = pin_files(artwork_resources, paths, ARTWORK_PIN)
        files.update(artwork_files)
        receipt.update(artwork_receipt)
    if address_book_resources:
        paths = sorted(path for path in (address_book_resources / ADDRESS_BOOK).rglob('*')
                       if path.is_file() and '_CodeSignature' not in path.parts)
        address_book_files, address_book_receipt = pin_files(address_book_resources, paths, ADDRESS_BOOK_PIN)
        files.update(address_book_files)
        receipt.update(address_book_receipt)
    out.mkdir(parents=True, exist_ok=False)
    root = out / 'root.hfs'
    subprocess.run(['cp', '--sparse=always', str(base), str(root)], check=True)
    require(sha(root) == BASE_PIN, 'RAM root copy mismatch')
    local_helper = Path(shutil.copyfile(helper, out / 'hfsplus'))
    local_helper.chmod(0o755)

    def volume(*args):
        command = [str(x) for x in (local_helper, root, *args)]
        return subprocess.check_output(command, stderr=subprocess.STDOUT, text=True)

    before, after = out / 'job-before.plist', out / 'job-after.plist'
    volume('extract', JOB, before)
    job = plistlib.loads(before.read_bytes())
    require(job['Label'] == 'com.apple.backboardd' and job['MachServices'].pop(ATTENTION_SERVICE) is True,
            'unexpected BackBoard job')
    after.write_bytes(plistlib.dumps(job))
    files[JOB] = after
    known = set()
    for guest, source in files.items():
        for parent in reversed(Path(guest).parents):
            if parent in known:
                continue
            if 'No such file or directory' in volume('ls', parent):
                volume('mkdir', parent)
                volume('chmod', '755', parent)
            known.add(parent)
        volume('add', source, guest)
        volume('chmod', '755' if guest == '/' + (ARTWORK / 'Artwork').as_posix() else '644', guest)
        roundtrip = out / 'roundtrip'
        volume('extract', guest, roundtrip)
        require(roundtrip.read_bytes() == source.read_bytes(), 'installation mismatch: ' + guest)
        roundtrip.unlink()
    require(sha(base) == BASE_PIN, 'source RAM root changed')
    report = dict(qemu_only=True, base_sha256=BASE_PIN, root_sha256=sha(root),
        omitted_backboard_service=ATTENTION_SERVICE, job_before_sha256=sha(before),
        job_after_sha256=sha(after), resources=receipt)
    (out / 'receipt.json').write_text(json.dumps(report, indent=2) + '\n')
    print(root)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-root', required=True, type=Path)
    parser.add_argument('--resources', required=True, type=Path, help='local tree of pinned UIKitCore resources')
    parser.add_argument('--language-resources', type=Path, help='local tree of pinned CoreNLP and langid resources')
    parser.add_argument('--artwork-resources', type=Path, help='local tree of pinned UIKitCore artwork and CoverSheet resources')
    parser.add_argument('--address-book-resources', type=Path, help='local tree of pinned AddressBookLegacy resources')
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    prepare(args.base_root.resolve(), args.resources.resolve(), args.output.resolve(),
        args.language_resources, args.artwork_resources, args.address_book_resources)


if __name__ == '__main__':
    main()
