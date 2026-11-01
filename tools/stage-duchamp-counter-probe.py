#!/usr/bin/env python3
"""Stage an opt-in, pre-GIC architected-counter probe into patched XNU."""

import argparse
import hashlib
import json
from pathlib import Path


MARKER = "DUCHAMP PRE-GIC COUNTER PROBE V1"
INCLUDE_ANCHOR = (
    '#include <arm/duchamp_timer_boot.h>\n'
    '#endif\n'
)
BODY_ANCHOR = (
    "\tcpu_machine_idle_init(TRUE);\n\n"
    "\tPE_init_platform(TRUE, &BootCpuData);"
)


def once(text, old, new):
    if text.count(old) != 1:
        raise ValueError("unexpected or changed counter-probe source anchor")
    return text.replace(old, new, 1)


def transform(text):
    text = once(
        text,
        INCLUDE_ANCHOR,
        INCLUDE_ANCHOR
        + '#if defined(DUCHAMP)\n'
        + '#include <arm/duchamp_counter_probe.h>\n'
        + '#endif\n',
    )
    body = '''\tcpu_machine_idle_init(TRUE);

#if defined(DUCHAMP)
\t/* DUCHAMP PRE-GIC COUNTER PROBE V1: sysreg reads only. */
\tint duchamp_counter_probe = 0;
\tif (PE_parse_boot_argn("duchamp_counter_probe", &duchamp_counter_probe,
\t    sizeof(duchamp_counter_probe)) && duchamp_counter_probe == 1) {
\t\tuint64_t const frequency = __builtin_arm_rsr64("CNTFRQ_EL0");
\t\tuint64_t const start = __builtin_arm_rsr64("CNTVCT_EL0");
\t\tuint64_t end = start;
\t\tunsigned int polls;

\t\tfor (polls = 0; polls < 1000000 && end <= start; polls++) {
\t\t\t__asm__ volatile("isb" ::: "memory");
\t\t\tend = __builtin_arm_rsr64("CNTVCT_EL0");
\t\t}
\t\tint const status = dcounter_progress_check(
\t\t    gPEClockFrequencyInfo.timebase_frequency_hz, frequency,
\t\t    start, end);
\t\tif (status == DCOUNTER_OK) {
\t\t\tkprintf("DUCHAMP COUNTER PROBE PASS freq=%llu delta=%llu polls=%u\\n",
\t\t\t    (unsigned long long)frequency,
\t\t\t    (unsigned long long)(end - start), polls);
\t\t\tsweet_early_mark(23, "DUCHAMP COUNTER PROBE PASS");
\t\t} else {
\t\t\tkprintf("DUCHAMP COUNTER PROBE FAIL status=%d freq=%llu polls=%u\\n",
\t\t\t    status, (unsigned long long)frequency, polls);
\t\t\tsweet_early_mark(23, "DUCHAMP COUNTER PROBE FAIL");
\t\t}
\t\t__asm__ volatile("dsb sy; isb" ::: "memory");
\t\tfor (;;) {
\t\t\t__asm__ volatile("wfe" ::: "memory");
\t\t}
\t}
#endif

\tPE_init_platform(TRUE, &BootCpuData);'''
    return once(text, BODY_ANCHOR, body)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stage(root):
    repo = Path(__file__).resolve().parent.parent
    source = repo / "duchamp" / "drivers" / "duchamp_counter_probe.h"
    target = root / "osfmk" / "arm" / "duchamp_counter_probe.h"
    receipt = root / "osfmk" / "arm" / "duchamp_counter_probe.json"
    arm_init = root / "osfmk" / "arm" / "arm_init.c"
    old = arm_init.read_text(encoding="utf-8")
    header_hash = digest(source)
    if MARKER in old:
        if (
            old.count(MARKER) != 1
            or not target.is_file()
            or target.read_bytes() != source.read_bytes()
            or not receipt.is_file()
        ):
            raise ValueError("partial or changed counter-probe staging")
        expected = {
            "source_sha256": digest(arm_init),
            "header_sha256": header_hash,
        }
        if json.loads(receipt.read_text(encoding="utf-8")) != expected:
            raise ValueError("changed staged counter-probe source")
        return {"already_staged": True, "header_sha256": header_hash}
    if target.exists() or receipt.exists():
        raise ValueError("preserve existing counter-probe header/receipt")
    new = transform(old)
    target.write_bytes(source.read_bytes())
    arm_init.write_text(new, encoding="utf-8")
    metadata = {
        "source_sha256": digest(arm_init),
        "header_sha256": header_hash,
    }
    receipt.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    return {"already_staged": False, "header_sha256": header_hash}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("xnu", type=Path)
    args = parser.parse_args()
    print(json.dumps(stage(args.xnu.resolve()), indent=2))


if __name__ == "__main__":
    main()
