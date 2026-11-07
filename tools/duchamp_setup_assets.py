"""Install and verify the pinned Setup assets in a disposable HFS+ root."""
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess


def digest(path):
    with path.open('rb') as source:
        return hashlib.file_digest(source, 'sha256').hexdigest()


def add_setup_assets(ram, plan, run, root_offset):
    fonts = os.environ.get('SWEET_QEMU_SETUP_FONTS')
    plugin_base = '/System/Library/HIDPlugins/ServicePlugins/IOHIDEventServicePlugin.plugin'
    plugin_files = {
        'Info.plist': ('Info.plist', '644', 'a09e0f38ae3c99784343d787e8c8c9e3e7dc95c2b79683de0f3e9f939881cb17'),
        'IOHIDEventServicePlugin': ('IOHIDEventServicePlugin', '755', '77de693a5a23c4f8b45bb03974968fb1ee2ce21964834d6e662f69948c142a9c'),
        'CodeResources': ('_CodeSignature/CodeResources', '644', '3c727b0f043e463c0227db49cef54c5567715986d08a46c98923c9bb73585e5a'),
    }
    env = dict(os.environ, LD_PRELOAD=os.environ['SWEET_QEMU_SETUP_HFS_SLICE'],
               QZ_GUEST_RAM=str(ram), QZ_GUEST_ROOT_OFFSET=str(root_offset),
               QZ_GUEST_ROOT_SIZE=str(plan['root_bytes']), QZ_GUEST_ROOT_WRITABLE='1')

    def hfs(*args):
        return subprocess.check_output([os.environ['SWEET_QEMU_SETUP_HFSPLUS'], ram, *args],
                                       env=env, text=True, stderr=subprocess.STDOUT)

    def install(assets, base, files):
        directories = set()
        for filename, (relative, mode, sha) in files.items():
            path = base + '/' + relative
            source = assets / filename
            assert digest(source) == sha
            for directory in reversed(Path(path).parents):
                if directory == Path('/') or directory in directories:
                    continue
                if 'No such file or directory' in hfs('ls', directory):
                    hfs('mkdir', directory)
                    hfs('chmod', '755', directory)
                directories.add(directory)
            hfs('add', source, path)
            hfs('chmod', mode, path)
            roundtrip = run / 'setup-asset-roundtrip'
            hfs('extract', path, roundtrip)
            assert digest(roundtrip) == sha
            roundtrip.unlink()
        return {base + '/' + relative: sha for relative, _, sha in files.values()}

    result = {}
    if fonts:
        assert 'grew volume: ' + str(plan['root_bytes']) in hfs('grow', str(plan['root_bytes']))
        with ram.open('rb') as source:
            for offset in (1024, plan['root_bytes'] - 1024):
                source.seek(root_offset + offset)
                header = source.read(48)
                block_size, blocks = struct.unpack_from('>II', header, 40)
                assert header[:2] == b'H+' and block_size * blocks == plan['root_bytes']
        assets = Path(fonts)
        manifest = assets / 'manifest.json'
        assert digest(manifest) == 'cc4979a574aad865c70407cc2a8a30cfdc3ae35c47ecd9f6768e446f69336d46'
        files = {path: (path, '644', entry['sha256']) for path, entry in json.loads(manifest.read_text()).items()}
        result['setup_fonts'] = install(assets, '/System/Library/Fonts', files)
    plugin = os.environ.get('SWEET_QEMU_SETUP_HID_PLUGIN')
    if plugin:
        result['hid_plugin'] = install(Path(plugin), plugin_base, plugin_files)
    return result
