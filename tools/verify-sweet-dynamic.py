#!/usr/bin/env python3
"""Validate actual C/libSystem execution, file I/O, fork, and clean exit in QEMU."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('run', type=Path)
    for key in ('kernel', 'init', 'program', 'root', 'payload', 'audit'):
        ap.add_argument('--' + key, type=Path, required=True)
    args = ap.parse_args()
    spec = importlib.util.spec_from_file_location('runtime_audit', Path(__file__).with_name('audit-darwin-runtime.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    binary = module.macho(args.program)
    screen = (args.run / 'fb.txt').read_text()
    result = json.loads((args.run / 'result.json').read_text())
    audit = json.loads(args.audit.read_text())
    entry = re.search(r'SWEET C: entered main pid=(\d+) images=(\d+)', screen)
    checks = {
        'runtime_dependency_audit': audit['passed'],
        'uses_real_dyld': binary['dylinker'] == '/usr/lib/dyld',
        'uses_libSystem': any(d['path'] == '/usr/lib/libSystem.B.dylib' for d in binary['dependencies']),
        'has_main_and_signature': binary['main_entry'] is not None and binary['code_signature'],
        'no_visible_panic': result['status'] == 'no_panic_observed',
        'screen_decoded': result['unknown_glyphs'] == 0,
        'entered_c_main': bool(entry) and int(entry[1]) > 1 and int(entry[2]) >= 2,
        'loaded_libSystem': 'SWEET C: real libSystem loaded by dyld' in screen,
        'libc_file_roundtrip': 'SWEET C: libc file bytes and EOF verified' in screen,
        'libc_fork_child': 'SWEET C: libc fork child running pid=' in screen,
        'libc_waitpid_status': 'SWEET C: libc fork and waitpid status 42 verified' in screen,
        'c_program_passed': 'SWEET C: DYNAMIC RUNTIME PASS' in screen,
        'c_program_clean_exit': 'SWEET dynamic init: C child exit 0 verified' in screen,
        'init_still_running': screen.count('SWEET dynamic init: still alive') >= 2,
        'no_failure': 'TEST FAILED' not in screen and 'SWEET C: FAIL' not in screen,
    }
    report = dict(passed=all(checks.values()), checks=checks,
                  sha256={key: hashlib.sha256(getattr(args, key).read_bytes()).hexdigest()
                          for key in ('kernel', 'init', 'program', 'root', 'payload')},
                  runtime_sha256={path: info['sha256'] for path, info in audit['files'].items()},
                  framebuffer_snapshot_only=True)
    (args.run / 'verification.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(dict(passed=report['passed'], checks=checks, sha256=report['sha256']), indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
