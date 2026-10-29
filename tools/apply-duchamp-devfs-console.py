#!/usr/bin/env python3
"""Create the QEMU RAM-root /dev mountpoint and trace devfs mounting."""

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
vfs_path = root / "bsd/vfs/vfs_syscalls.c"

early = early_path.read_text()
early = replace_once(early, "stage > 186", "stage > 191", "stage ceiling")

vfs = vfs_path.read_text()
vfs = replace_once(
    vfs,
    "\treturn error;\n}\n\n/*\n * mkdir_extended: Create a directory; with extended security (ACL).\n",
    '''\treturn error;
}

#if defined(ARM64_BOARD_CONFIG_SWEET)
int
sweet_mkdir_kernel(const char *path, mode_t mode)
{
\tstruct vnode_attr va;
\tVATTR_INIT(&va);
\tVATTR_SET(&va, va_mode, mode & ACCESSPERMS);
\treturn mkdir1at(vfs_context_kernel(), (user_addr_t)(uintptr_t)path, &va,
\t    AT_FDCWD, UIO_SYSSPACE);
}
#endif

/*
 * mkdir_extended: Create a directory; with extended security (ACL).
''',
    "kernel mkdir helper",
)

bsd = bsd_path.read_text()
bsd = replace_once(
    bsd,
    "#include <miscfs/devfs/devfsdefs.h>     /* for devfs_kernel_mount() */\n",
    '''#include <miscfs/devfs/devfsdefs.h>     /* for devfs_kernel_mount() */
#if defined(ARM64_BOARD_CONFIG_SWEET)
extern int sweet_mkdir_kernel(const char *path, mode_t mode);
#endif
''',
    "kernel mkdir declaration",
)
bsd = replace_once(
    bsd,
    '''#if DEVFS
\t{
\t\tchar mounthere[] = "/dev"; /* !const because of internal casting */

\t\tbsd_init_kprintf("calling devfs_kernel_mount\\n");
\t\tdevfs_kernel_mount(mounthere);
\t}
#endif /* DEVFS */
''',
    '''#if DEVFS
\t{
\t\tchar mounthere[] = "/dev"; /* !const because of internal casting */
#if defined(ARM64_BOARD_CONFIG_SWEET)
\t\tsweet_early_mark(187, "PREPARE DEVFS MOUNT");
\t\tint mkdir_error = sweet_mkdir_kernel(mounthere, 0755);
\t\tsweet_early_mark((mkdir_error == 0 || mkdir_error == EEXIST) ? 188 : 189,
\t\t    (mkdir_error == 0 || mkdir_error == EEXIST) ?
\t\t    "DEV DIRECTORY READY" : "DEV DIRECTORY FAILED");
#endif
\t\tbsd_init_kprintf("calling devfs_kernel_mount\\n");
\t\tint devfs_error = devfs_kernel_mount(mounthere);
#if defined(ARM64_BOARD_CONFIG_SWEET)
\t\tsweet_early_mark(devfs_error == 0 ? 190 : 191,
\t\t    devfs_error == 0 ? "DEVFS CONSOLE READY" : "DEVFS MOUNT FAILED");
#endif
\t}
#endif /* DEVFS */
''',
    "devfs mount diagnostics",
)

early_path.write_text(early)
vfs_path.write_text(vfs)
bsd_path.write_text(bsd)
