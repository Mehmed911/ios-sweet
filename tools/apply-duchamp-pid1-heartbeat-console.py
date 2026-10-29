#!/usr/bin/env python3
"""Trace PID 1 getpid/heartbeat and optionally mirror its console to the early FB."""

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
km_path = root / "bsd/dev/arm/km.c"

early = early_path.read_text()
early = replace_once(early, "stage > 194", "stage > 199", "stage ceiling")

syscalls = syscalls_path.read_text()
syscalls = replace_once(
    syscalls,
    '''static boolean_t sweet_pid1_first_write_seen;
static boolean_t sweet_pid1_first_write_pending;
''',
    '''static boolean_t sweet_pid1_first_write_seen;
static boolean_t sweet_pid1_first_write_pending;
static boolean_t sweet_pid1_getpid_pending;
static boolean_t sweet_pid1_heartbeat_pending;
''',
    "PID 1 heartbeat state",
)
syscalls = replace_once(
    syscalls,
    '''\tif (pid == 1 && code == 4 && !sweet_pid1_first_write_seen) {
\t\tsweet_pid1_first_write_seen = TRUE;
\t\tsweet_pid1_first_write_pending = TRUE;
\t\tsweet_early_mark(192, "PID1 FIRST CONSOLE WRITE");
\t}
''',
    '''\tif (pid == 1 && !sweet_pid1_first_write_seen && code == 4) {
\t\tsweet_pid1_first_write_seen = TRUE;
\t\tsweet_pid1_first_write_pending = TRUE;
\t\tsweet_early_mark(192, "PID1 FIRST CONSOLE WRITE");
\t}
\tif (pid == 1 && code == 20 && !sweet_pid1_getpid_pending) {
\t\tsweet_pid1_getpid_pending = TRUE;
\t\tsweet_early_mark(195, "PID1 GETPID ENTERED");
\t}
\tif (pid == 1 && code == 93 && !sweet_pid1_heartbeat_pending) {
\t\tsweet_pid1_heartbeat_pending = TRUE;
\t\tsweet_early_mark(197, "PID1 HEARTBEAT ENTERED");
\t}
''',
    "PID 1 getpid and heartbeat entry",
)
syscalls = replace_once(
    syscalls,
    '''\tif (sweet_pid1_first_write_pending) {
\t\tsweet_pid1_first_write_pending = FALSE;
\t\tsweet_early_mark(error == 0 ? 193 : 194,
\t\t    error == 0 ? "SWEET USERSPACE PID1 RUNNING" : "PID1 CONSOLE WRITE FAILED");
\t}
''',
    '''\tif (sweet_pid1_first_write_pending) {
\t\tsweet_pid1_first_write_pending = FALSE;
\t\tsweet_early_mark(error == 0 ? 193 : 194,
\t\t    error == 0 ? "SWEET USERSPACE PID1 RUNNING" : "PID1 CONSOLE WRITE FAILED");
\t}
\tif (sweet_pid1_getpid_pending) {
\t\tsweet_pid1_getpid_pending = FALSE;
\t\tsweet_early_mark(196,
\t\t    error == 0 && uthread->uu_rval[0] == 1 ? "PID1 GETPID OK" : "PID1 GETPID FAILED");
\t}
\tif (sweet_pid1_heartbeat_pending) {
\t\tsweet_pid1_heartbeat_pending = FALSE;
\t\tsweet_early_mark(198,
\t\t    error == 0 ? "PID1 HEARTBEAT RETURNED" : "PID1 HEARTBEAT FAILED");
\t}
''',
    "PID 1 getpid and heartbeat results",
)

km = km_path.read_text()
km = replace_once(
    km,
    "#include <console/serial_protos.h>\n",
    '''#include <console/serial_protos.h>
#if defined(ARM64_BOARD_CONFIG_SWEET)
#include <arm64/sweet_early.h>
#endif
''',
    "early framebuffer include",
)
km = replace_once(
    km,
    "int             initialized = 0;\n",
    '''int             initialized = 0;
#if defined(ARM64_BOARD_CONFIG_SWEET)
static int sweet_console_fb;
#endif
''',
    "console mirror state",
)
km = replace_once(
    km,
    '''void
kminit(void)
{
\tkm_tty[0] = ttymalloc();
''',
    '''void
kminit(void)
{
#if defined(ARM64_BOARD_CONFIG_SWEET)
\tPE_parse_boot_argn("sweet_console_fb", &sweet_console_fb, sizeof(sweet_console_fb));
#endif
\tkm_tty[0] = ttymalloc();
''',
    "console mirror boot argument",
)
km = replace_once(
    km,
    '''\tif (!disableConsoleOutput && initialized) {
\t\t/* OCRNL */
''',
    '''\tif (!disableConsoleOutput && initialized) {
#if defined(ARM64_BOARD_CONFIG_SWEET)
\t\tif (sweet_console_fb) {
\t\t\tsweet_early_putc(c);
\t\t}
#endif
\t\t/* OCRNL */
''',
    "single-character console mirror",
)
km = replace_once(
    km,
    '''\t\tfor (cp = buf; cp < &buf[cc]; cp++) {
\t\t\t/* output the buffer one charatcer at a time */
\t\t\t*cp = *cp & 0x7f;
\t\t}
\t\tif (cc > 1) {
''',
    '''\t\tfor (cp = buf; cp < &buf[cc]; cp++) {
\t\t\t/* output the buffer one charatcer at a time */
\t\t\t*cp = *cp & 0x7f;
\t\t}
#if defined(ARM64_BOARD_CONFIG_SWEET)
\t\tif (sweet_console_fb && cc > 1) {
\t\t\tfor (cp = buf; cp < &buf[cc]; cp++) {
\t\t\t\tsweet_early_putc((char)*cp);
\t\t\t}
\t\t}
#endif
\t\tif (cc > 1) {
''',
    "buffered console mirror",
)

early_path.write_text(early)
syscalls_path.write_text(syscalls)
km_path.write_text(km)
