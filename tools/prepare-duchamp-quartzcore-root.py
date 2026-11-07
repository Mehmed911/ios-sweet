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
CORE_EMOJI_PIN = 'bcbc16a716e1f85d37d78ccb65023f04188280aeacbe10cd6506880b0cc28d81'
SETUP_PIN = 'b28f03bea0430f53ecffdd989192297691b8fa4a83db3eacc3a450eb0cbb78e7'
SETUP_POLICY_PIN = 'cf8aa452e22d31c82c3b50aca14cfc17b92b151334feb92a5c4e546aa9e7fb09'
FRAMEWORK = Path('System/Library/PrivateFrameworks/UIKitCore.framework')
CORE_NLP = Path('System/Library/PrivateFrameworks/CoreNLP.framework')
ARTWORK = FRAMEWORK / 'Artwork.bundle'
COVER_SHEET = FRAMEWORK.with_name('CoverSheet.framework')
ADDRESS_BOOK = FRAMEWORK.with_name('AddressBookLegacy.framework')
CORE_EMOJI = FRAMEWORK.with_name('CoreEmoji.framework')
SETUP_APP = Path('Applications/Setup.app')
SETUP_FRAMEWORKS = tuple(FRAMEWORK.with_name(name + '.framework') for name in (
    'SetupAssistant', 'SetupAssistantUI', 'SetupAssistantSupport'))
SETUP_POLICY_FILES = (
    'FeatureFlags/Domain/RunningBoard.plist',
    'PrivateFrameworks/RunningBoard.framework/Info.plist',
    'PrivateFrameworks/RunningBoardServices.framework/Info.plist',
    'PrivateFrameworks/FrontBoard.framework/com.apple.frontboard.applibrary.plist',
    'PrivateFrameworks/FrontBoard.framework/Info.plist',
    'PrivateFrameworks/FrontBoardServices.framework/Info.plist',
)
CONTROLLER = '/sbin/sweet-platform-services'
EXECUTABLES = {'/' + (ARTWORK / 'Artwork').as_posix(), '/' + (SETUP_APP / 'Setup').as_posix(), CONTROLLER}
JOB = '/System/Library/LaunchDaemons/com.apple.backboardd.plist'
LSD_JOB = '/System/Library/LaunchDaemons/com.apple.lsd.plist'
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


def build_setup_controller(out):
    runtime = REPO / 'research/cfprefs-runtime-20F66-v2/runtime-root'
    obj, binary = out / 'controller.o', out / 'controller'
    subprocess.run(['clang', '-target', 'arm64-apple-ios16.5', '-O1', '-Wall', '-Wextra', '-Werror',
        '-fno-stack-protector', '-fno-builtin', '-DSWEET_UI_PROBES=1', '-DSWEET_UI_READINESS=1',
        '-DSWEET_SPRINGBOARD_PROBE=1', '-DSWEET_LSD_QUERY_SECONDS=45',
        '-c', str(REPO / 'tools/sweet-platform-services.c'), '-o', str(obj)], check=True)
    subprocess.run(['ld64.lld', '-arch', 'arm64', '-platform_version', 'ios', '16.5', '16.5',
        '-adhoc_codesign', '-syslibroot', str(runtime), '-L' + str(runtime / 'usr/lib'),
        '-lSystem.B', '-e', '_main', '-o', str(binary), str(obj)], check=True)
    return binary


def prepare(base, resources, out, language_resources=None, artwork_resources=None, address_book_resources=None,
            emoji_resources=None, setup_resources=None, setup_lsd_system=False):
    require(not setup_lsd_system or setup_resources, 'system lsd is only for the Setup fixture')
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
    if emoji_resources:
        paths = sorted(path for path in (emoji_resources / CORE_EMOJI).rglob('*')
                       if path.is_file() and '_CodeSignature' not in path.parts)
        emoji_files, emoji_receipt = pin_files(emoji_resources, paths, CORE_EMOJI_PIN)
        files.update(emoji_files)
        receipt.update(emoji_receipt)
    if setup_resources:
        paths = sorted(path for component in (SETUP_APP, *SETUP_FRAMEWORKS)
                       for path in (setup_resources / component).rglob('*') if path.is_file())
        setup_files, setup_receipt = pin_files(setup_resources, paths, SETUP_PIN)
        files.update(setup_files)
        receipt.update(setup_receipt)
        library = setup_resources / 'System/Library'
        paths = sorted(path for name in ('LifecyclePolicy', 'RunningBoard')
                       for path in (library / name).rglob('*') if path.is_file())
        paths.extend(library / name for name in SETUP_POLICY_FILES)
        policy_files, policy_receipt = pin_files(setup_resources, paths, SETUP_POLICY_PIN)
        files.update(policy_files)
        receipt.update(policy_receipt)
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
    if setup_resources:
        files[CONTROLLER] = build_setup_controller(out)
    if setup_lsd_system:
        lsd_before, lsd_after = out / 'lsd-before.plist', out / 'lsd-system.plist'
        volume('extract', LSD_JOB, lsd_before)
        lsd = plistlib.loads(lsd_before.read_bytes())
        require(lsd['Label'] == 'com.apple.lsd' and lsd['UserName'] == 'mobile'
                and lsd['MachServices']['com.apple.lsd.mapdb'] is True
                and 'LimitLoadToSessionType' not in lsd, 'unexpected LaunchServices job')
        lsd['LimitLoadToSessionType'] = 'System'
        lsd_after.write_bytes(plistlib.dumps(lsd))
        files[LSD_JOB] = lsd_after
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
        volume('chmod', '755' if guest in EXECUTABLES else '644', guest)
        roundtrip = out / 'roundtrip'
        volume('extract', guest, roundtrip)
        require(roundtrip.read_bytes() == source.read_bytes(), 'installation mismatch: ' + guest)
        roundtrip.unlink()
    require(sha(base) == BASE_PIN, 'source RAM root changed')
    report = dict(qemu_only=True, base_sha256=BASE_PIN, root_sha256=sha(root),
        omitted_backboard_service=ATTENTION_SERVICE, job_before_sha256=sha(before),
        job_after_sha256=sha(after), resources=receipt)
    if setup_resources:
        report.update(controller_sha256=sha(files[CONTROLLER]), native_query_seconds=45)
    if setup_lsd_system:
        report.update(lsd_system_job=dict(original_sha256=sha(lsd_before), qemu_sha256=sha(lsd_after)))
    (out / 'receipt.json').write_text(json.dumps(report, indent=2) + '\n')
    print(root)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-root', required=True, type=Path)
    parser.add_argument('--resources', required=True, type=Path, help='local tree of pinned UIKitCore resources')
    parser.add_argument('--language-resources', type=Path, help='local tree of pinned CoreNLP and langid resources')
    parser.add_argument('--artwork-resources', type=Path, help='local tree of pinned UIKitCore artwork and CoverSheet resources')
    parser.add_argument('--address-book-resources', type=Path, help='local tree of pinned AddressBookLegacy resources')
    parser.add_argument('--emoji-resources', type=Path, help='local tree of pinned CoreEmoji resources')
    parser.add_argument('--setup-resources', type=Path, help='local tree of pinned Setup app and framework resources')
    parser.add_argument('--setup-lsd-system', action='store_true', help='keep native lsd in the system bootstrap domain')
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    prepare(args.base_root.resolve(), args.resources.resolve(), args.output.resolve(),
        args.language_resources, args.artwork_resources, args.address_book_resources,
        args.emoji_resources, args.setup_resources, args.setup_lsd_system)


if __name__ == '__main__':
    main()
