#!/usr/bin/env python3
"""Compile QEMU-only VirtIO input and fully relink verified source-built XNU.

Preserves the baseline kernel/objects. Requires their source-build receipts;
never patches an existing kernel binary or pulls in archived CI objects.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('output', type=Path)
    ap.add_argument('--baseline-build', type=Path, required=True)
    a = ap.parse_args()
    out = a.output.resolve()
    out.mkdir()
    base = a.baseline_build.resolve()
    recipe = json.loads((base / 'source-build-compile-commands.json').read_text())
    baseline = json.loads((base / 'new-kernel-link.json').read_text())
    assert baseline['exit_code'] == 0
    assert sha(baseline['kernel']) == baseline['sha256'] == 'e7b51ecb16fe9ad21a78455714b2bf26c1dee1fbc3a6a7f0cb3971a9cd569457'
    commands = []

    def run(argv, cwd=None):
        argv = list(map(str, argv))
        log = out / ('command-%03d.log' % len(commands))
        with log.open('wb') as f:
            r = subprocess.run(argv, cwd=cwd, stdout=f, stderr=subprocess.STDOUT, timeout=240)
        commands.append(dict(argv=argv, cwd=str(cwd or Path.cwd()), exit_code=r.returncode, log=str(log), sha256=sha(log)))
        (out / 'commands.json').write_text(json.dumps(commands, indent=2) + '\n')
        if r.returncode:
            raise RuntimeError(log.read_text(errors='replace'))

    # Verify the complete source-built object set before selecting any inputs.
    resolved = baseline['input_objects']
    for row in resolved:
        assert sha(row['object']) == row['new_object_sha256'], row['object']
    assert len(recipe) == len(resolved) == 1126
    tools = Path(__file__).resolve().parent
    cpp = next(row for row in recipe if row['source'].endswith('/IOKitBSDInit.cpp'))
    c = next(row for row in recipe if row['source'].endswith('/qemu_spi2_touch.c'))
    original = Path(cpp['source'])
    source = original.read_text()
    declaration = 'extern "C" int duchamp_dual_ramdisk_init(const char *root_name);'
    call = 'dual_registered = duchamp_dual_ramdisk_init(rdBootVar);'
    assert source.count(declaration) == source.count(call) == 1
    source = source.replace(declaration, declaration + '\nextern "C" int duchamp_qemu_pointer_register(void);')
    source = source.replace(call, call + '\n\t\tif (duchamp_qemu_pointer_register()) printf("DUCHAMP QEMU POINTER PROFILE REJECTED\\n");')
    modified = out / 'IOKitBSDInit.cpp'
    modified.write_text(source)
    import difflib
    (out / 'IOKitBSDInit.patch').write_text(''.join(difflib.unified_diff(original.read_text().splitlines(True),
        source.splitlines(True), fromfile='a/iokit/bsddev/IOKitBSDInit.cpp', tofile='b/iokit/bsddev/IOKitBSDInit.cpp')))
    objects = []
    for row, src, name in ((cpp, modified, 'IOKitBSDInit.cpo'), (c, tools / 'duchamp-qemu-pointer-kernel.c', 'duchamp-qemu-pointer.o')):
        argv = row['argv'].copy()
        obj = out / name
        argv[argv.index('-c') + 1] = str(src)
        argv[argv.index('-o') + 1] = str(obj)
        argv += ['-I' + str(tools), '-I' + str(original.parent)]
        run(argv, row['cwd'])
        objects.append(dict(object=str(obj), new_object_sha256=sha(obj), source=str(src), source_sha256=sha(src)))
    linked = [objects[0] if Path(row['object']).name == 'IOKitBSDInit.cpo' else row for row in resolved] + [objects[1]]
    assert len(linked) == 1127 and len({row['object'] for row in linked}) == 1127
    filelist = out / 'link.filelist'
    filelist.write_text(''.join(row['object'] + '\n' for row in linked))
    argv = baseline['argv'].copy()
    argv[argv.index('-filelist') + 1] = str(filelist)
    kernel = out / 'kernel.development.sweet'
    argv[argv.index('-o') + 1] = str(kernel)
    run(argv)
    run(['python3', '-B', str(tools / 'duchamp_xnu_link.py'), kernel])
    assert sha(baseline['kernel']) == baseline['sha256']
    manifest = dict(baseline_kernel=baseline['kernel'], baseline_sha256=baseline['sha256'],
                    kernel=str(kernel), sha256=sha(kernel), bytes=kernel.stat().st_size,
                    baseline_receipt=str(base / 'new-kernel-link.json'), input_objects=linked,
                    source_header_sha256=sha(tools / 'duchamp-virtio-pointer.h'),
                    touch_header_sha256=sha(tools / 'duchamp-virtio-touch.h'),
                    phone_operations=[], physical_status='BLOCKED_BY_MEMORY_EVIDENCE')
    (out / 'build-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps({k: v for k, v in manifest.items() if k != 'input_objects'}, indent=2))


if __name__ == '__main__':
    main()
