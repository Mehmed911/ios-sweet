#!/usr/bin/env python3
"""Run actual launchd-managed compositor/clients on the preserved XNU in QEMU."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import duchamp_compositor_expectations as oracle
import qemu_ramroot_var as layout


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    parser.add_argument('--kernel', type=Path, required=True)
    parser.add_argument('--mkfs', type=Path, required=True)
    parser.add_argument('--kernel-manifest', type=Path, help='explicit source-link receipt passed through to graphics runner')
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir()
    execution = out / 'execution'
    command = [sys.executable, '-B', 'tools/test-duchamp-darwin-graphics.py', str(execution),
               '--kernel', str(args.kernel.resolve()), '--mkfs', str(args.mkfs.resolve()), '--compositor']
    if args.kernel_manifest:
        command += ['--kernel-manifest', str(args.kernel_manifest.resolve())]
    log = out / 'execution.log'
    with log.open('wb') as stream:
        result = subprocess.run(command, cwd=layout.REPO, stdout=stream, stderr=subprocess.STDOUT, timeout=600)
    commands = [dict(argv=command, cwd=str(layout.REPO), exit_code=result.returncode,
                     log=str(log), sha256=hashlib.sha256(log.read_bytes()).hexdigest())]
    hfs = layout.REPO / 'research/libdmg-hfsplus-build/hfsplus'
    var = execution / 'guest/run/var-final.hfs'
    for name in ('compositor', 'comp-red', 'comp-overlay', 'compositor-service', 'comp-early-red', 'comp-early-overlay'):
        argv = [str(hfs), str(var), 'extract', '/tmp/ipc-' + name + '.log', str(out / (name + '.log'))]
        r = subprocess.run(argv, capture_output=True)
        commands.append(dict(argv=argv, exit_code=r.returncode))
    (out / 'commands.json').write_text(json.dumps(commands, indent=2) + '\n')
    if result.returncode:
        print(log.read_text(errors='replace')[-4500:])
        for name in ('compositor', 'comp-red', 'comp-overlay'):
            p = out / (name + '.log')
            if p.exists(): print(name + ':\n' + p.read_text(errors='replace')[-4000:])
        (out / 'verification.json').write_text(json.dumps(dict(passed=False, reason='guest baseline or execution failed',
                                                              exit_code=result.returncode), indent=2) + '\n')
        return 1
    trace = (out / 'compositor.log').read_text()
    red = (out / 'comp-red.log').read_text()
    overlay = (out / 'comp-overlay.log').read_text()
    normal = (out / 'compositor-service.log').read_text()
    early = [(out / ('comp-early-' + name + '.log')).read_text() for name in ('red', 'overlay')]
    baseline = json.loads((execution / 'verification.json').read_text())
    filesystems = json.loads((execution / 'guest/verification.json').read_text())
    services = json.loads((execution / 'guest/service-verification.json').read_text())
    frames = json.loads((execution / 'guest/run/frame-sequence.json').read_text())
    control = (execution / 'guest/guest/launchctl-control.log').read_text()
    expected = oracle.frames()
    phases = re.findall(r'^PHASE (\d+) front=(\d+) epoch=(\d+) output_surface=(\d+) swap=(\d+)$', trace, re.M)
    registrations = re.findall(r'^REGISTER role=(\d+) pid=(\d+) birth=(\d+) surface=(\d+) bytes=(\d+) stride=(\d+)$', trace, re.M)
    cleanup = re.findall(r'^DEAD role=(\d+) pid=(\d+) kernel_notification=1 closed=1 lookup=0xe00002f0 events=2 acked=2$', trace, re.M)
    identities = [re.search(r'^IDENTITY pid=(\d+) ppid=1 uid=0 parent=/sbin/launchd$', s, re.M) for s in (trace, red, overlay)]
    byte_matches = {name: (execution / ('guest/run/sequence-' + name + '.raw')).is_file() and
                    (execution / ('guest/run/sequence-' + name + '.raw')).read_bytes() == pixels
                    for name, pixels in expected.items()}
    checks = {
        'all_real_processes_under_launchd': all(identities) and len({m[1] for m in identities}) == 3,
        'launchd_mach_service_checkin': 'service=org.duchamp.qemu.compositor' in trace,
        'two_surface_capabilities_imported': len(registrations) == 2 and {m[0] for m in registrations} == {'1', '2'},
        'audit_pid_binds_owners': all(m[1] == identities[int(m[0])][1] for m in registrations),
        'shared_bounds_rejection': 'SHARED BOUNDS rejection=1' in overlay,
        'ownership_rect_replay_rejections': 'DIRTY 8x8 committed foreign=denied bounds=denied replay=denied' in overlay and
            re.search(r'PASS cleanup=2 owner_denials=[1-9]\d* rect_denials=[1-9]\d* replay_denials=[1-9]\d*', trace) is not None,
        'all_frames_captured_in_order': [f['name'] for f in frames] == list(expected) and
            all(a['sample'] < b['sample'] for a, b in zip(frames, frames[1:])),
        'all_framebuffer_bytes_exact': all(byte_matches.values()),
        'alpha_and_visible_surfaces': byte_matches['blend'],
        'dirty_region_isolated': byte_matches['dirty'],
        'z_order_and_restore': byte_matches['zorder'] and byte_matches['restored'],
        'front_back_buffers_alternate': len(phases) == 6 and {p[1] for p in phases} == {'0', '1'} and
            len({p[3] for p in phases}) == 2 and all(int(a[2]) < int(b[2]) for a, b in zip(phases, phases[1:])),
        'focused_press_release_overlay': re.findall(r'EVENT role=2 .* seq=\d+ down=(\d)', overlay) == ['1', '0'],
        'focused_press_release_red': re.findall(r'EVENT role=1 .* seq=\d+ down=(\d)', red) == ['1', '0'],
        'capture_survives_focus_change': 'FOCUS changed_to_red_while_pressed=1' in trace,
        'focus_rpc_checks_owner': 'FOCUS RPC owner_verified=1' in overlay,
        'abrupt_overlay_termination': re.search(r'TERMINATE overlay pid=\d+ signal=9 after_release_ack=1', trace) is not None,
        'kernel_death_notifications_and_unmaps': [x[0] for x in cleanup] == ['2', '1'],
        'display_recovers_after_client_exit': byte_matches['cleanup_overlay'] and byte_matches['cleanup_all'],
        'launchd_service_lifecycle': re.search(r'COMPOSITOR LIFECYCLE PASS pid=\d+ bootout=0 gone=1', control) is not None,
        'normal_mode_survives_early_client_exit': re.search(r'COMPOSITOR NORMAL PASS pid=\d+ early_cleanup=2 survived=1 gone=1', control) is not None and
            all('EARLY EXIT' in text for text in early),
        'normal_mode_reclaims_before_any_input': sorted(re.findall(r'DEAD role=(\d) .*kernel_notification=1 closed=1 lookup=0xe00002f0 events=0 acked=0', normal)) == ['1', '2'] and
            'TERMINATE overlay' not in normal and 'FAIL' not in normal,
        'graphics_baseline_10': baseline['passed'] and len(baseline['checks']) == 10,
        'dual_ramdisk_baseline_11': filesystems['passed'] and len(filesystems['checks']) == 11,
        'service_baseline_74': services['passed'] and len(services['checks']) == 74,
    }
    report = dict(passed=all(checks.values()), checks=checks, frames=frames, phases=phases,
                  registrations=registrations, cleanup=cleanup, kernel_sha256=baseline['kernel_sha256'],
                  phone_operations=[], native_status='BLOCKED_BY_MEMORY_EVIDENCE', physical_ufs_enabled=False,
                  scope='QEMU userspace software compositor; no Apple graphics service or physical GPU claim')
    (out / 'verification.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
