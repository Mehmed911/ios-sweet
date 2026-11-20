#!/usr/bin/env python3
"""0BSD: source-compile the IOSurface error fix and relink the exact XNU inputs.

No existing source, object, kernel or receipt is overwritten. No GPU service
is published by this change. The baseline receipt remains independently valid.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
from duchamp_source_kernel import select


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('output', type=Path)
    ap.add_argument('--baseline-manifest', type=Path, required=True)
    ap.add_argument('--compile-recipe', type=Path, required=True)
    ap.add_argument('--baseline-commands', type=Path, required=True)
    a = ap.parse_args()
    out = a.output.resolve()
    out.mkdir()
    receipt = a.baseline_manifest.resolve()
    baseline = json.loads(receipt.read_text())
    select(Path(baseline['kernel']), receipt)
    recipe = json.loads(a.compile_recipe.read_text())
    row = next(r for r in recipe if r['source'].endswith('/SweetSurface.cpp'))
    original = Path(row['source'])
    source = out / 'SweetSurface.cpp'
    source.write_bytes(original.read_bytes())
    patch = Path('xnu/patches/0218-duchamp-iosurface-unsupported.patch').resolve()
    commands = []

    def run(argv, cwd=None):
        argv = list(map(str, argv))
        log = out / ('command-%03d.log' % len(commands))
        with log.open('wb') as f:
            r = subprocess.run(argv, cwd=cwd, stdout=f, stderr=subprocess.STDOUT, timeout=240)
        commands.append(dict(argv=argv, cwd=str(cwd or Path.cwd()), exit_code=r.returncode,
                             log=str(log), sha256=sha(log)))
        (out / 'commands.json').write_text(json.dumps(commands, indent=2) + '\n')
        if r.returncode:
            raise RuntimeError(log.read_text(errors='replace')[-6000:])

    run(['patch', '--batch', '--forward', str(source), str(patch)])
    assert 'accept and ignore' not in source.read_text()
    obj = out / 'SweetSurface.cpo'
    argv = row['argv'].copy()
    argv[argv.index('-c') + 1] = str(source)
    argv[argv.index('-o') + 1] = str(obj)
    argv += ['-I' + str(original.parent)]
    run(argv, row['cwd'])
    linked = [dict(object=str(obj), new_object_sha256=sha(obj), source=str(source),
                   source_sha256=sha(source)) if Path(x['object']).name == obj.name else x
              for x in baseline['input_objects']]
    assert len(linked) == 1127 and sum(x['object'] == str(obj) for x in linked) == 1
    filelist = out / 'link.filelist'
    filelist.write_text(''.join(x['object'] + '\n' for x in linked))
    base_commands = json.loads(a.baseline_commands.read_text())
    argv = next(x['argv'].copy() for x in base_commands if '-filelist' in x['argv'])
    argv[argv.index('-filelist') + 1] = str(filelist)
    kernel = out / 'kernel.development.sweet'
    argv[argv.index('-o') + 1] = str(kernel)
    run(argv)
    run(['python3', '-B', 'tools/duchamp_xnu_link.py', kernel])
    result = dict(baseline, kernel=str(kernel), sha256=sha(kernel), bytes=kernel.stat().st_size,
                  input_objects=linked, parent_manifest=str(receipt), parent_manifest_sha256=sha(receipt),
                  patch=str(patch), patch_sha256=sha(patch), original_source_sha256=sha(original))
    (out / 'build-manifest.json').write_text(json.dumps(result, indent=2) + '\n')
    select(kernel, out / 'build-manifest.json')
    select(Path(baseline['kernel']), receipt)
    print(json.dumps(dict(kernel=str(kernel), sha256=sha(kernel), source_objects=len(linked))))


if __name__ == '__main__':
    main()
