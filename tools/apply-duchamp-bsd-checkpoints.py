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

early = early_path.read_text()
early = replace_once(early, "stage > 154", "stage > 160", "stage ceiling")
early_path.write_text(early)

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
        "\tsweet_early_mark(160, \"DUCHAMP PRE ROOT SETCONF\");\n"
        "\t__asm__ volatile(\"dsb sy; isb\" ::: \"memory\");\n\tfor (;;) {\n"
        "\t\t__asm__ volatile(\"wfe\" ::: \"memory\");\n\t}\n#endif\n\n"
        "\t/* Mount the root file system. */",
        "pre-root barrier",
    ),
]

for old, new, label in edits:
    bsd = replace_once(bsd, old, new, label)

bsd_path.write_text(bsd)
