#!/usr/bin/env python3
"""Require exec/file/IPC, exit/restart, and verified stop/continue/terminate.

A non-panic framebuffer is not a userspace success condition. This validator
checks the complete diagnostic scenario and records hashes of its inputs.
The framebuffer is a circular snapshot, not a complete serial log.
"""
import argparse
import hashlib
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run', type=Path)
    for name in ('kernel', 'init', 'worker', 'root', 'payload'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    result = json.loads((args.run / 'result.json').read_text())
    screen = (args.run / 'fb.txt').read_text()
    # Rotate the circular rows to the PID 1 startup message for sequence checks.
    marker = '*** SWEET userspace: init running as PID 1 ***'
    start = screen.find(marker)
    ordered = screen[start:] + screen[:start] if start >= 0 else screen
    started = 'SWEET worker: exec successful, child PID verified'
    restart = 'SWEET init: restarting worker in stay mode'
    heartbeat = 'SWEET worker: still alive'
    file_ok = 'SWEET worker: RAM file bytes and EOF verified'
    ipc_ok = 'SWEET init: IPC READYv1 and EOF verified'
    ipc_sent = 'SWEET worker: IPC READYv1 sent and closed'
    tail = ordered.split(restart, 1)[-1] if restart in ordered else ''
    stop = 'SWEET init: SIGSTOP wait4 verified'
    cont = 'SWEET init: SIGCONT wait4 verified'
    term = 'SWEET init: SIGTERM wait4 verified'
    final_restart = 'SWEET init: restarting after SIGTERM'
    signal_events = [
        'SWEET init: SIGSTOP sending', stop,
        'SWEET init: stopped hold complete',
        'SWEET init: SIGCONT sending', cont,
        'SWEET init: resumed heartbeat window complete',
        'SWEET init: SIGTERM sending', term,
        'SWEET init: terminated worker ESRCH verified', final_restart,
    ]
    cursor = 0
    signal_order = True
    for event in signal_events:
        pos = ordered.find(event, cursor)
        if pos < 0:
            signal_order = False
            break
        cursor = pos + len(event)

    def between(first, last):
        begin = ordered.find(first)
        end = ordered.find(last, begin + len(first)) if begin >= 0 else -1
        return ordered[begin:end] if begin >= 0 and end > begin else ''

    stopped = between(stop, 'SWEET init: SIGCONT sending')
    resumed = between(cont, 'SWEET init: SIGTERM sending')
    final_tail = ordered.split(final_restart, 1)[-1] if final_restart in ordered else ''
    checks = {
        'snapshot_decoded': result.get('unknown_glyphs') == 0,
        'no_visible_panic': result.get('status') == 'no_panic_observed',
        'pid1_started': start >= 0,
        'worker_installed': 'SWEET init: worker file installed' in screen,
        'three_exec_entries': screen.count(started) == 3,
        'three_ram_file_roundtrips': screen.count(file_ok) == 3,
        'three_worker_pipe_messages': screen.count(ipc_sent) == 3,
        'three_parent_pipe_verifications': screen.count(ipc_ok) == 3,
        'intentional_exit': 'SWEET worker: intentional exit 42' in screen,
        'wait4_reaped': 'SWEET init: wait4 reaped worker, status hex:' in screen,
        'correct_wait_status': '00002a00' in screen,
        'worker_restarted': restart in screen,
        'restarted_worker_entered': started in tail,
        'restarted_worker_file_and_ipc': all(mark in tail for mark in (file_ok, ipc_ok, ipc_sent)),
        'restarted_worker_heartbeats': tail.count(heartbeat) >= 2,
        'signal_events_ordered': signal_order,
        'sigstop_status': stop + '\n0000117f' in ordered,
        'no_heartbeat_while_stopped': bool(stopped) and heartbeat not in stopped,
        'sigcont_status': cont + '\n0000137f' in ordered,
        'heartbeat_after_continue': heartbeat in resumed,
        'sigterm_status': term + '\n0000000f' in ordered,
        'terminated_pid_absent': signal_events[-2] in ordered,
        'final_worker_started': started in final_tail,
        'final_worker_file_and_ipc': all(mark in final_tail for mark in (file_ok, ipc_ok, ipc_sent)),
        'final_worker_heartbeats': final_tail.count(heartbeat) >= 2,
        'parent_heartbeats': screen.count('SWEET init: still alive') >= 3,
        'no_test_failure': 'TEST FAILED' not in screen and 'execve failed' not in screen,
    }
    hashes = {name: hashlib.sha256(getattr(args, name).read_bytes()).hexdigest()
              for name in ('kernel', 'init', 'worker', 'root', 'payload')}
    report = {'passed': all(checks.values()), 'checks': checks,
              'sha256': hashes, 'framebuffer_snapshot_only': True}
    (args.run / 'verification.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
