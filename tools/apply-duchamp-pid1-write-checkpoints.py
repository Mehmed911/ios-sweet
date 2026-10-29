#!/usr/bin/env python3
"""Trace the first write syscall made by PID 1 after opening its console."""

from pathlib import Path
import sys


root = Path(sys.argv[1])


def replace_once(source, old, new, label):
    count = source.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one anchor, found {count}")
    return source.replace(old, new)


early_path = root / "osfmk/arm64/sweet_early.c"
syscalls_path = root / "bsd/dev/arm/systemcalls.c"

early = early_path.read_text()
early = replace_once(early, "stage > 191", "stage > 194", "stage ceiling")

syscalls = syscalls_path.read_text()
syscalls = replace_once(
    syscalls,
    "static boolean_t sweet_pid1_first_syscall_seen;\n",
    """static boolean_t sweet_pid1_first_syscall_seen;
static boolean_t sweet_pid1_first_write_seen;
static boolean_t sweet_pid1_first_write_pending;
""",
    "PID 1 write state",
)
syscalls = replace_once(
    syscalls,
    '''\tif (pid == 1 && !sweet_pid1_first_syscall_seen) {
\t\tsweet_pid1_first_syscall_seen = TRUE;
\t\tsweet_early_mark(183, "PID1 FIRST SYSCALL");
\t}
''',
    '''\tif (pid == 1 && !sweet_pid1_first_syscall_seen) {
\t\tsweet_pid1_first_syscall_seen = TRUE;
\t\tsweet_early_mark(183, "PID1 FIRST SYSCALL");
\t}
\tif (pid == 1 && code == 4 && !sweet_pid1_first_write_seen) {
\t\tsweet_pid1_first_write_seen = TRUE;
\t\tsweet_pid1_first_write_pending = TRUE;
\t\tsweet_early_mark(192, "PID1 FIRST CONSOLE WRITE");
\t}
''',
    "PID 1 first write entry",
)
syscalls = replace_once(
    syscalls,
    '''\terror = (*(callp->sy_call))(proc, &uthread->uu_arg[0], &(uthread->uu_rval[0]));
\tAUDIT_SYSCALL_EXIT(code, proc, uthread, error);
''',
    '''\terror = (*(callp->sy_call))(proc, &uthread->uu_arg[0], &(uthread->uu_rval[0]));
\tAUDIT_SYSCALL_EXIT(code, proc, uthread, error);
#if defined(ARM64_BOARD_CONFIG_SWEET)
\tif (sweet_pid1_first_write_pending) {
\t\tsweet_pid1_first_write_pending = FALSE;
\t\tsweet_early_mark(error == 0 ? 193 : 194,
\t\t    error == 0 ? "SWEET USERSPACE PID1 RUNNING" : "PID1 CONSOLE WRITE FAILED");
\t}
#endif
''',
    "PID 1 first write result",
)

early_path.write_text(early)
syscalls_path.write_text(syscalls)
