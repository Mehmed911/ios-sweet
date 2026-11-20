#!/usr/bin/env python3
"""Build the macOS 13.5 dispatch kernel firehose archive on Linux."""

import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess


DISPATCH = 'cdb61e93e803d0093635f356753a9a30c09836db'
TARGET_CONDITIONALS = '2dbd9a6885bd6ece5195c2f67c75e29c63bd7519cbbe8b6bcc6ebd279de118b2'
EXPECTED = {
    '___firehose_buffer_create',
    '___firehose_buffer_tracepoint_flush',
    '___firehose_buffer_tracepoint_reserve',
    '___firehose_kernel_configuration_valid',
    '___firehose_merge_updates',
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('libdispatch', 'buildtree', 'target_conditionals', 'output'):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    dispatch, tree, conditionals, out = (getattr(args, name).resolve() for name in
                                        ('libdispatch', 'buildtree', 'target_conditionals', 'output'))
    revision = subprocess.check_output(['git', '-C', dispatch, 'rev-parse', 'HEAD'], text=True).strip()
    if revision != DISPATCH or subprocess.check_output(
            ['git', '-C', dispatch, 'status', '--porcelain'], text=True).strip():
        parser.error('expected unmodified libdispatch-1415.140.2 at the pinned commit')
    if conditionals.name != 'TargetConditionals.h' or sha(conditionals) != TARGET_CONDITIONALS:
        parser.error('expected the pinned UniXNU Linux TargetConditionals.h')
    fakeroot = tree / 'fakeroot/usr/local/include'
    obj = tree / 'build/xnu.obj'
    sweet = obj / 'DEVELOPMENT_ARM64_SWEET'
    if 'xnu-8796.141.3' not in (sweet / 'version.c').read_text():
        parser.error('expected exported headers from xnu-8796.141.3 DEVELOPMENT ARM64 SWEET')

    out.mkdir()
    commands = []

    def run(name, *argv):
        command = list(map(str, argv))
        log = out / f'{name}.log'
        with log.open('wb') as stream:
            result = subprocess.run(command, stdout=stream, stderr=subprocess.STDOUT)
        commands.append(dict(argv=command, exit_code=result.returncode, log=log.name))
        (out / 'commands.json').write_text(json.dumps(commands, indent=2) + '\n')
        if result.returncode:
            raise SystemExit(f'{name} exited {result.returncode}. See {log}')
        return log.read_text()

    compiler = run('clang-version', 'clang', '--version')
    resource = Path(run('resource-directory', 'clang', '-print-resource-dir').strip())
    debug = obj / 'EXPORT_HDRS/osfmk/kern/debug.h'
    source = dispatch / 'src/firehose/firehose_buffer.c'
    object_path = out / 'firehose_buffer.o'
    archive = out / 'libfirehose_kernel.a'
    # Use the kernel declaration of panic, while keeping the installed user
    # header view for machine/cpu_capabilities.h used by the tracepoint headers.
    roots = (conditionals.parent, dispatch, fakeroot / 'kernel', fakeroot / 'os',
             fakeroot / 'firehose', fakeroot, obj / 'EXPORT_HDRS/osfmk', obj / 'EXPORT_HDRS/bsd',
             sweet / 'bsd', tree / 'xnu/EXTERNAL_HEADERS', tree / 'xnu/libkern')
    run('compile', 'clang', '-target', 'arm64-apple-macos15.5', '-std=gnu11', '-Os', '-g', '-mkernel',
        '-nostdinc', '-Wno-packed', '-DKERNEL=1', '-DDISPATCH_USE_DTRACE=0',
        '-DOS_ATOMIC_CONFIG_MEMORY_ORDER_DEPENDENCY=1', '-DOS_ATOMIC_CONFIG_STARVATION_FREE_ONLY=0',
        '-fdebug-compilation-dir=/duchamp-firehose',
        *(f'-ffile-prefix-map={root}=/inputs/{label}' for root, label in
          ((dispatch, 'libdispatch'), (tree, 'xnu-tree'), (conditionals.parent, 'conditions'))),
        '-isystem', resource / 'include', '-include', debug,
        *(f'-I{path}' for path in roots), '-MD', '-MF', out / 'firehose.d',
        '-c', source, '-o', object_path)
    if struct.unpack_from('<4I', object_path.read_bytes()) != (0xFEEDFACF, 0x100000C, 0, 1):
        raise SystemExit('Expected one plain ARM64 Mach-O object')
    run('archive', 'llvm-ar', '--format=darwin', 'rcsD', archive, object_path)
    if run('members', 'llvm-ar', 't', archive).splitlines() != ['firehose_buffer.o']:
        raise SystemExit('Unexpected archive members')
    run('macho', 'llvm-objdump', '--macho', '--private-headers', object_path)
    symbols = run('defined-symbols', 'llvm-nm', '-g', '--defined-only', '--just-symbol-name', archive)
    missing = EXPECTED.difference(symbols.splitlines())
    if missing:
        raise SystemExit(f'Missing kernel Firehose exports {sorted(missing)}')
    run('undefined-symbols', 'llvm-nm', '-u', archive)
    report = dict(libdispatch=revision, xnu='xnu-8796.141.3', target='arm64-apple-macos15.5',
                  compiler=compiler.splitlines()[0], archive_sha256=sha(archive), archive_bytes=archive.stat().st_size,
                  object_sha256=sha(object_path), validated_exports=sorted(EXPECTED),
                  source_sha256=sha(source), debug_header_sha256=sha(debug),
                  target_conditionals_sha256=sha(conditionals))
    (out / 'verification.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
