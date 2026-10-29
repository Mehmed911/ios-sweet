#!/usr/bin/env python3
"""Trace PID 1's first syscall and its /dev/console open result."""

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
vfs_path = root / "bsd/vfs/vfs_syscalls.c"

early = early_path.read_text()
early = replace_once(early, "stage > 182", "stage > 186", "stage ceiling")

syscalls = syscalls_path.read_text()
syscalls = replace_once(
    syscalls,
    "extern void\nunix_syscall(struct arm_saved_state * regs, thread_t thread_act, struct proc * proc);\n",
    """extern void
unix_syscall(struct arm_saved_state * regs, thread_t thread_act, struct proc * proc);

#if defined(ARM64_BOARD_CONFIG_SWEET)
extern void sweet_early_mark(unsigned int stage, const char *label);
static boolean_t sweet_pid1_first_syscall_seen;
#endif
""",
    "syscall marker declaration",
)
syscalls = replace_once(
    syscalls,
    "\tpid = proc_pid(proc);\n",
    """\tpid = proc_pid(proc);
#if defined(ARM64_BOARD_CONFIG_SWEET)
\tif (pid == 1 && !sweet_pid1_first_syscall_seen) {
\t\tsweet_pid1_first_syscall_seen = TRUE;
\t\tsweet_early_mark(183, "PID1 FIRST SYSCALL");
\t}
#endif
""",
    "PID 1 first syscall marker",
)
vfs = vfs_path.read_text()
vfs = replace_once(
    vfs,
    "int\nopen_nocancel(__unused proc_t p, struct open_nocancel_args *uap,\n    int32_t *retval)\n{\n\treturn openat_internal(vfs_context_current(), uap->path, uap->flags,\n\t           uap->mode, AT_FDCWD, UIO_USERSPACE, retval);\n}\n",
    """#if defined(ARM64_BOARD_CONFIG_SWEET)
extern void sweet_early_mark(unsigned int stage, const char *label);
#endif

int
open_nocancel(proc_t p, struct open_nocancel_args *uap,
    int32_t *retval)
{
#if defined(ARM64_BOARD_CONFIG_SWEET)
\tchar sweet_path[MAXPATHLEN];
\tsize_t sweet_path_len = 0;
\tboolean_t sweet_console_open = FALSE;
\tif (proc_pid(p) == 1 &&
\t    copyinstr(uap->path, sweet_path, sizeof(sweet_path), &sweet_path_len) == 0 &&
\t    strcmp(sweet_path, "/dev/console") == 0) {
\t\tsweet_console_open = TRUE;
\t\tsweet_early_mark(184, "PID1 OPEN CONSOLE");
\t}
#endif
\tint error = openat_internal(vfs_context_current(), uap->path, uap->flags,
\t    uap->mode, AT_FDCWD, UIO_USERSPACE, retval);
#if defined(ARM64_BOARD_CONFIG_SWEET)
\tif (sweet_console_open) {
\t\tsweet_early_mark(error == 0 ? 185 : 186,
\t\t    error == 0 ? "PID1 CONSOLE OPEN OK" : "PID1 CONSOLE OPEN FAILED");
\t}
#endif
\treturn error;
}
""",
    "console open result markers",
)
early_path.write_text(early)
syscalls_path.write_text(syscalls)
vfs_path.write_text(vfs)
