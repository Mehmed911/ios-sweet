#!/usr/bin/env python3
"""Verify actual native toolbar/lifecycle effects in a completed normal session."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess


def verify(session, output):
    session, output = Path(session).resolve(), Path(output).resolve()
    output.mkdir(exist_ok=True)
    hfs = Path(__file__).resolve().parents[1] / 'research/libdmg-hfsplus-build/hfsplus'
    commands = []

    def extract(name):
        dest = output / name
        argv = list(map(str, [hfs, session / 'run/var-final.hfs', 'extract', '/tmp/' + name, dest]))
        r = subprocess.run(argv, capture_output=True)
        commands.append(dict(argv=argv, exit_code=r.returncode, stdout=r.stdout.decode(errors='replace'), stderr=r.stderr.decode(errors='replace')))
        if r.returncode or not dest.exists():
            raise RuntimeError(commands[-1])
        return dest.read_text()

    applications = extract('ipc-applications.log')
    shell = extract('ipc-gui-shell.log')
    control = extract('launchctl-control.log')
    witness = dict(line.split('=', 1) for line in extract('duchamp-var-witness').splitlines())
    owners = {}
    traces = []
    for wid, color in [(2, 'red'), (3, 'blue')]:
        owners[str(wid)] = sorted(set((int(pid), int(birth)) for pid, birth in re.findall(r'app=%d status=0 pid=([1-9]\d*) version=(\d+)' % wid, applications)))
        for pid, _ in owners[str(wid)]:
            traces.append(extract('ipc-app-%s-%d.log' % (color, pid)))
    for pid in set(re.findall(r'TOUCH CONNECT pid=(\d+)', shell)):
        traces.append(extract('ipc-virtio-touch-' + pid + '.log'))
    roots = [session / 'guest/root.hfs', session / 'run/ramdisk-final.hfs']
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    checks = dict(normal_eight_jobs_no_observer='GUI APP INTERACTIVE READY jobs=8 no_test_observer=1' in control and 'app-observer' not in control,
                  real_independent_apps=bool(owners['2']) and len(owners['3']) >= 3 and set(owners['2']).isdisjoint(owners['3']),
                  toolbar_background=re.search(r'op=4 app=3 status=0 .*state=1 visible=0', applications) is not None,
                  toolbar_close_and_restart=re.search(r'op=5 app=3 status=0', applications) is not None and re.search(r'op=7 app=3 status=0', applications) is not None,
                  app_children_of_launchd=all('ppid=1 uid=0 parent=/sbin/launchd' in t for t in traces),
                  both_apps_receive_real_contacts=all(any('TOUCH DELIVER id=%d' % wid in t for t in traces) for wid in (2, 3)),
                  real_virtio_report_path=any('origin=virtio-multitouch' in t for t in traces) and 'origin=virtio' in shell,
                  touch_acknowledgements_not_reset_by_launch=len(re.findall('TOUCH CONNECT', shell)) == 1 and 'TOUCH REJECT' not in shell,
                  asynchronous_launch_evidence='LAUNCH QUEUED' in applications and 'READY app=3 status=0' in applications,
                  no_failed_launch_reply=re.search(r'op=(2|7) app=[23] status=4294967295', applications) is None,
                  no_native_failures=all('FAIL' not in t for t in [applications, shell, control, *traces]),
                  root_byte_identical=sha(roots[0]) == sha(roots[1]),
                  writable_var=sha(session / 'guest/var.hfs') != sha(session / 'run/var-final.hfs'),
                  filesystem_witness=witness.get('root_errno') == '30' and witness.get('capacity_errno') == '28' and witness.get('alias') == '/private/var',
                  no_panic_observed=json.loads((session / 'run/result.json').read_text())['status'] == 'no_panic_observed')
    report = dict(passed=all(checks.values()), checks=checks, application_processes=owners, commands=commands,
                  phone_operations=[], physical_status='BLOCKED_BY_MEMORY_EVIDENCE')
    (output / 'verification.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('session', type=Path)
    ap.add_argument('output', type=Path)
    a = ap.parse_args()
    r = verify(a.session, a.output)
    print(json.dumps(r, indent=2))
    raise SystemExit(0 if r['passed'] else 1)
