#!/usr/bin/env python3
"""Release the QEMU root-vnode barrier and trace process-1 exec."""

from pathlib import Path
import sys


root = Path(sys.argv[1])


def replace_once(source, old, new, label):
    count = source.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one anchor, found {count}")
    return source.replace(old, new)


early_path = root / "osfmk/arm64/sweet_early.c"
bsd_path = root / "bsd/kern/bsd_init.c"
exec_path = root / "bsd/kern/kern_exec.c"

early = early_path.read_text()
early = replace_once(early, "stage > 173", "stage > 182", "stage ceiling")
early_path.write_text(early)

bsd = bsd_path.read_text()
bsd = replace_once(
    bsd,
    '''#if defined(ARM64_BOARD_CONFIG_SWEET)
\tsweet_early_mark(173, "QEMU ROOTVNODE READY");
\t__asm__ volatile("dsb sy; isb" ::: "memory");
\tfor (;;) {
\t\t__asm__ volatile("wfe" ::: "memory");
\t}
#endif
''',
    '''#if defined(ARM64_BOARD_CONFIG_SWEET)
\tsweet_early_mark(173, "QEMU ROOTVNODE READY");
#endif
''',
    "rootvnode barrier release",
)
bsd = replace_once(
    bsd,
    '''\tbsd_init_kprintf("calling bsd_utaskbootstrap\\n");
\tbsd_utaskbootstrap();
''',
    '''#if defined(ARM64_BOARD_CONFIG_SWEET)
\tsweet_early_mark(174, "PRE INIT PROCESS CREATE");
#endif
\tbsd_init_kprintf("calling bsd_utaskbootstrap\\n");
\tbsd_utaskbootstrap();
#if defined(ARM64_BOARD_CONFIG_SWEET)
\tsweet_early_mark(175, "INIT PROCESS CREATED");
#endif
''',
    "init process markers",
)
bsd = replace_once(
    bsd,
    '''void
bsdinit_task(void)
{
\tproc_t p = current_proc();
''',
    '''void
bsdinit_task(void)
{
\tproc_t p = current_proc();
#if defined(ARM64_BOARD_CONFIG_SWEET)
\tsweet_early_mark(176, "BSD INIT TASK ENTERED");
#endif
''',
    "bsdinit task marker",
)
bsd = replace_once(
    bsd,
    "\tvm_init_before_launchd();\n",
    '''#if defined(ARM64_BOARD_CONFIG_SWEET)
\tsweet_early_mark(177, "PRE VM INIT LAUNCHD");
#endif
\tvm_init_before_launchd();
#if defined(ARM64_BOARD_CONFIG_SWEET)
\tsweet_early_mark(178, "VM INIT LAUNCHD READY");
#endif
''',
    "launchd VM markers",
)
bsd = replace_once(
    bsd,
    "\tload_init_program(p);\n",
    '''#if defined(ARM64_BOARD_CONFIG_SWEET)
\tsweet_early_mark(179, "PRE LOAD INIT PROGRAM");
#endif
\tload_init_program(p);
''',
    "load init marker",
)
bsd_path.write_text(bsd)

kern_exec = exec_path.read_text()
kern_exec = replace_once(
    kern_exec,
    "void\nload_init_program(proc_t p)\n{\n",
    '''#if defined(ARM64_BOARD_CONFIG_SWEET)
extern void sweet_early_mark(unsigned int stage, const char *label);
#endif

void
load_init_program(proc_t p)
{
''',
    "marker declaration",
)
kern_exec = replace_once(
    kern_exec,
    '''\t\tif (is_release_suffix) {
\t\t\tprintf("load_init_program: attempting to load /sbin/launchd\\n");
\t\t\terror = load_init_program_at_path(p, (user_addr_t)scratch_addr, "/sbin/launchd");
\t\t\tif (!error) {
\t\t\t\treturn;
\t\t\t}

\t\t\tpanic("Process 1 exec of launchd.release failed, errno %d", error);
''',
    '''\t\tif (is_release_suffix) {
#if defined(ARM64_BOARD_CONFIG_SWEET)
\t\t\tsweet_early_mark(180, "PRE EXEC SBIN LAUNCHD");
#endif
\t\t\tprintf("load_init_program: attempting to load /sbin/launchd\\n");
\t\t\terror = load_init_program_at_path(p, (user_addr_t)scratch_addr, "/sbin/launchd");
\t\t\tif (!error) {
#if defined(ARM64_BOARD_CONFIG_SWEET)
\t\t\t\tsweet_early_mark(181, "INIT EXEC ACCEPTED");
#endif
\t\t\t\treturn;
\t\t\t}
#if defined(ARM64_BOARD_CONFIG_SWEET)
\t\t\tsweet_early_mark(182, "INIT EXEC FAILED");
#endif
\t\t\tpanic("Process 1 exec of launchd.release failed, errno %d", error);
''',
    "launchd exec markers",
)
exec_path.write_text(kern_exec)
