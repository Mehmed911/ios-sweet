#!/bin/bash
set -euo pipefail

python3 - "$PWD" <<'PY'
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
sleh = root / "osfmk/arm64/sleh.c"
init = root / "osfmk/arm/arm_init.c"

text = sleh.read_text()
needle = "\t\tsleh_interrupt_handler_prologue(state, DBG_INTR_TYPE_TIMER);\n"
replacement = needle + "#if defined(DUCHAMP)\n\t\tsweet_early_mark(16, \"DUCHAMP TIMER IRQ\");\n#endif\n"
if "DUCHAMP TIMER IRQ" not in text:
    if text.count(needle) != 1:
        raise SystemExit("timer IRQ insertion point not found uniquely")
    sleh.write_text(text.replace(needle, replacement, 1))

text = init.read_text()
old = '''\t/* First MT6897 experiment: stop before serial/IRQ/IOKit/BSD startup. */
\tsweet_early_mark(15, "DUCHAMP XNU MEMORY READY");
\t__asm__ volatile("dsb sy; isb" ::: "memory");
\tfor (;;) {
\t\t__asm__ volatile("wfe" ::: "memory");
\t}'''
new = '''\t/* Timer-only experiment: arm one virtual-timer IRQ, then stop in WFE. */
\tsweet_early_mark(15, "DUCHAMP TIMER TEST ARMED");
\t__builtin_arm_wsr64("CNTV_TVAL_EL0", 1000000);
\t__builtin_arm_wsr64("CNTV_CTL_EL0", 1);
\t__asm__ volatile("msr daifclr, #2; isb" ::: "memory");
\t__asm__ volatile("dsb sy; isb" ::: "memory");
\tfor (;;) {
\t\t__asm__ volatile("wfe" ::: "memory");
\t}'''
if "DUCHAMP TIMER TEST ARMED" not in text:
    if text.count(old) != 1:
        raise SystemExit("timer arm insertion point not found uniquely")
    init.write_text(text.replace(old, new, 1))
PY
