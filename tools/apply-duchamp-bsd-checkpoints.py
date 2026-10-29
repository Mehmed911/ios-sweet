#!/usr/bin/env python3
"""Apply the Duchamp BSD pre-root checkpoints using strict semantic anchors."""

from pathlib import Path
import sys


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one anchor, found {count}")
    return text.replace(old, new, 1)


if len(sys.argv) != 2:
    raise SystemExit("usage: apply-duchamp-bsd-checkpoints.py XNU_ROOT")

root = Path(sys.argv[1])
early_path = root / "osfmk/arm64/sweet_early.c"
bsd_path = root / "bsd/kern/bsd_init.c"
iokit_path = root / "iokit/bsddev/IOKitBSDInit.cpp"

early = early_path.read_text()
early = replace_once(early, "stage > 154", "stage > 172", "stage ceiling")
early_path.write_text(early)

startup_path = root / "osfmk/kern/startup.c"
startup = startup_path.read_text()
stage154_barrier = '''#if defined(DUCHAMP)
	sweet_early_mark(154, "DUCHAMP PRE BSD INIT");
	__asm__ volatile("dsb sy; isb" ::: "memory");
	for (;;) {
		__asm__ volatile("wfe" ::: "memory");
	}
#endif
'''
stage154_released = '''#if defined(DUCHAMP)
	sweet_early_mark(154, "DUCHAMP PRE BSD INIT");
#endif
'''
if stage154_barrier in startup:
    startup = replace_once(startup, stage154_barrier, stage154_released, "stage 154 release")
elif stage154_released not in startup:
    raise SystemExit("stage 154 release: neither barrier nor released anchor found")
startup_path.write_text(startup)

bsd = bsd_path.read_text()
edits = [
    (
        "#include <sys/conf.h>\n#include <sys/buf_internal.h>",
        "#include <sys/conf.h>\n\n#if defined(ARM64_BOARD_CONFIG_SWEET)\n"
        "#include <arm64/sweet_early.h>\n#endif\n#include <sys/buf_internal.h>",
        "sweet early include",
    ),
    (
        "\tplatform_stall_panic_or_spin(PLATFORM_STALL_XNU_LOCATION_BSD_INIT);\n#endif\n\n#define DEBUG_BSDINIT 0",
        "\tplatform_stall_panic_or_spin(PLATFORM_STALL_XNU_LOCATION_BSD_INIT);\n#endif\n"
        "#if defined(ARM64_BOARD_CONFIG_SWEET)\n\tsweet_early_mark(155, \"BSD init entered\");\n#endif\n\n"
        "#define DEBUG_BSDINIT 0",
        "BSD entry",
    ),
    (
        "\tfdt_init(kernproc);\n\tkernproc->p_fd.fd_cmask",
        "\tfdt_init(kernproc);\n#if defined(ARM64_BOARD_CONFIG_SWEET)\n"
        "\tsweet_early_mark(156, \"kernproc core ready\");\n#endif\n\tkernproc->p_fd.fd_cmask",
        "kernproc",
    ),
    (
        "\tbsd_init_kprintf(\"calling bsd_bufferinit\\n\");",
        "#if defined(ARM64_BOARD_CONFIG_SWEET)\n\tsweet_early_mark(157, \"BSD services entering\");\n#endif\n"
        "\tbsd_init_kprintf(\"calling bsd_bufferinit\\n\");",
        "BSD services",
    ),
    (
        "\tvfsinit();\n\n#if defined(ARM64_BOARD_CONFIG_SWEET)",
        "\tvfsinit();\n#if defined(ARM64_BOARD_CONFIG_SWEET)\n"
        "\tsweet_early_mark(158, \"VFS core ready\");\n#endif\n\n#if defined(ARM64_BOARD_CONFIG_SWEET)",
        "VFS",
    ),
    (
        "\tbsd_init_kprintf(\"calling bsd_autoconf\\n\");",
        "#if defined(ARM64_BOARD_CONFIG_SWEET)\n\tsweet_early_mark(159, \"BSD autoconf entering\");\n#endif\n"
        "\tbsd_init_kprintf(\"calling bsd_autoconf\\n\");",
        "autoconf",
    ),
    (
        "\tinittodr(0);\n\n\t/* Mount the root file system. */",
        "\tinittodr(0);\n#if defined(ARM64_BOARD_CONFIG_SWEET)\n"
        "\tsweet_early_mark(160, \"DUCHAMP PRE ROOT SETCONF\");\n#endif\n\n"
        "\t/* Mount the root file system. */",
        "pre-root barrier",
    ),
    (
        "\terr = IOFindBSDRoot(rootdevice, sizeof(rootdevice), &rootdev, &flags);",
        "#if defined(ARM64_BOARD_CONFIG_SWEET)\n"
        "\tsweet_early_mark(161, \"setconf entered\");\n"
        "\tsweet_early_mark(162, \"PRE IOFindBSDRoot\");\n"
        "#endif\n\n"
        "\terr = IOFindBSDRoot(rootdevice, sizeof(rootdevice), &rootdev, &flags);",
        "setconf pre-root lookup barrier",
    ),
]

for old, new, label in edits:
    bsd = replace_once(bsd, old, new, label)

bsd_path.write_text(bsd)

iokit = iokit_path.read_text()
iokit = replace_once(
    iokit,
    "#include <sys/mount.h>\n#include <corecrypto/ccsha2.h>",
    "#include <sys/mount.h>\n#if defined(ARM64_BOARD_CONFIG_SWEET)\n"
    "extern \"C\" void sweet_early_mark(unsigned int stage, const char *label);\n"
    "#endif\n#include <corecrypto/ccsha2.h>",
    "IOKit early marker declaration",
)
iokit = replace_once(
    iokit,
    "\tstatic int          mountAttempts = 0;\n\n\tint xchar, dchar;",
    "\tstatic int          mountAttempts = 0;\n\n#if defined(ARM64_BOARD_CONFIG_SWEET)\n"
    "\tsweet_early_mark(163, \"IOFindBSDRoot entered\");\n#endif\n\n\tint xchar, dchar;",
    "IOFindBSDRoot entry",
)
iokit = replace_once(
    iokit,
    "\tmatching->release();\n\tmatching = NULL;\n\n\tif (mountAttempts++)",
    "\tmatching->release();\n\tmatching = NULL;\n#if defined(ARM64_BOARD_CONFIG_SWEET)\n"
    "\tsweet_early_mark(164, \"IOBSD resource ready\");\n#endif\n\n\tif (mountAttempts++)",
    "IOBSD resource ready",
)
iokit = replace_once(
    iokit,
    "\t\trdBootVar[0] = 0;\n\t}\n\n\tif ((regEntry",
    "\t\trdBootVar[0] = 0;\n\t}\n#if defined(ARM64_BOARD_CONFIG_SWEET)\n"
    "\tsweet_early_mark(165, \"root boot arg parsed\");\n#endif\n\n\tif ((regEntry",
    "root boot argument",
)
iokit = replace_once(
    iokit,
    "\tif (strcmp(rdBootVar, \"ufsroot0\") == 0) {\n"
    "\t\textern int sweet_ufs_rootdev(dev_t *dev);\n"
    "\t\tOSSafeReleaseNULL(matching);\n"
    "\t\tint ufs_error = sweet_ufs_rootdev(root);\n"
    "\t\tif (ufs_error) {\n"
    "\t\t\tpanic(\"IOFindBSDRoot: SWEET UFS root %s unavailable: %d\", rdBootVar, ufs_error);\n"
    "\t\t}\n"
    "\t\tstrlcpy(rootName, rdBootVar, rootNameSize);\n"
    "\t\tIOLog(\"BSD root: %s, major %d, minor %d\\n\", rootName, major(*root), minor(*root));\n"
    "\t\t*oflags = 0;\n"
    "\t\tgoto iofrootx;\n"
    "\t}",
    "\tsweet_early_mark(166, \"root selection ready\");\n"
    "\tif (strcmp(rdBootVar, \"ufsroot0\") == 0) {\n"
    "\t\tchar backend[16] = \"mt6897\";\n"
    "\t\tPE_parse_boot_argn(\"sweet-root-backend\", backend, sizeof(backend));\n"
    "\t\tsweet_early_mark(167, \"root backend selected\");\n"
    "\t\tOSSafeReleaseNULL(matching);\n"
    "\t\tif (strcmp(backend, \"qemu-ram\") == 0) {\n"
    "\t\t\t*root = mdevlookup(0);\n"
    "\t\t\tstrlcpy(rootName, \"md0\", rootNameSize);\n"
    "\t\t\t*oflags = 0;\n"
    "\t\t\tsweet_early_mark(168, \"QEMU RAM BLOCK READY\");\n"
    "\t\t\tgoto iofrootx;\n"
    "\t\t}\n"
    "\t\tsweet_early_mark(169, \"MT6897 BACKEND STUB\");\n"
    "\t\treturn kIOReturnUnsupported;\n"
    "\t}",
    "safe root backend selector",
)
iokit_path.write_text(iokit)

bsd = bsd_path.read_text()
bsd = replace_once(
    bsd,
    '''\t\tbsd_init_kprintf("vfs_mountroot\\n");
\t\tif (0 == (err = vfs_mountroot())) {
\t\t\tbreak;
\t\t}
''',
    '''\t\tbsd_init_kprintf("vfs_mountroot\\n");
#if defined(ARM64_BOARD_CONFIG_SWEET)
\t\tsweet_early_mark(170, "DUCHAMP PRE MOUNTROOT");
#endif
\t\terr = vfs_mountroot();
#if defined(ARM64_BOARD_CONFIG_SWEET)
\t\tif (err == 0) {
\t\t\tsweet_early_mark(171, "QEMU RAM ROOT MOUNTED");
\t\t} else {
\t\t\tsweet_early_mark(172, "QEMU RAM ROOT MOUNT FAILED");
\t\t}
\t\t__asm__ volatile("dsb sy; isb" ::: "memory");
\t\tfor (;;) {
\t\t\t__asm__ volatile("wfe" ::: "memory");
\t\t}
#endif
\t\tif (err == 0) {
\t\t\tbreak;
\t\t}
''',
    "RAM root mount result barrier",
)
bsd_path.write_text(bsd)
