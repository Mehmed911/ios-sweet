#!/usr/bin/env python3
"""Stage an opt-in, pre-GIC virtual-timer expiry probe into patched XNU."""

import argparse
import hashlib
import json
from pathlib import Path


MARKER = "DUCHAMP PRE-GIC TIMER EXPIRY PROBE V1"
COUNTER_MARKER = "DUCHAMP PRE-GIC COUNTER PROBE V1"
INCLUDE_ANCHOR = (
    '#if defined(DUCHAMP)\n'
    '#include <arm/duchamp_counter_probe.h>\n'
    '#endif\n'
)
BODY_ANCHOR = "#endif\n\n\tPE_init_platform(TRUE, &BootCpuData);"


def once(text, old, new):
    if text.count(old) != 1:
        raise ValueError("unexpected or changed timer-probe source anchor")
    return text.replace(old, new, 1)


def transform(text):
    if text.count(COUNTER_MARKER) != 1:
        raise ValueError("counter probe must be staged exactly once first")
    text = once(
        text,
        INCLUDE_ANCHOR,
        INCLUDE_ANCHOR
        + '#if defined(DUCHAMP)\n'
        + '#include <arm/duchamp_timer_probe.h>\n'
        + '#endif\n',
    )
    body = '''#endif

#if defined(DUCHAMP)
	/* DUCHAMP PRE-GIC TIMER EXPIRY PROBE V1: masked sysregs only. */
	int duchamp_timer_probe = 0;
	if (PE_parse_boot_argn("duchamp_timer_probe", &duchamp_timer_probe,
	    sizeof(duchamp_timer_probe)) && duchamp_timer_probe == 1) {
		uint32_t const expected_frequency =
		    gPEClockFrequencyInfo.timebase_frequency_hz;
		uint64_t const frequency = __builtin_arm_rsr64("CNTFRQ_EL0");
		uint64_t const initial_ctl = __builtin_arm_rsr64("CNTV_CTL_EL0");
		uint64_t const ticks = frequency / 1000;
		uint64_t start = 0;
		uint64_t end = 0;
		uint64_t expiry_ctl = initial_ctl;
		unsigned int polls = 0;
		int status;

		if (!expected_frequency || frequency != expected_frequency) {
			status = DTPROBE_FREQUENCY_MISMATCH;
		} else if (initial_ctl & DTPROBE_CTL_ENABLE) {
			status = DTPROBE_ALREADY_ENABLED;
		} else if (!ticks) {
			status = DTPROBE_ARGUMENT;
		} else {
			uint64_t const max_elapsed = frequency / 10;

			start = __builtin_arm_rsr64("CNTVCT_EL0");
			end = start;
			__builtin_arm_wsr64("CNTV_CVAL_EL0", start + ticks);
			__builtin_arm_wsr64("CNTV_CTL_EL0",
			    DTPROBE_CTL_ENABLE | DTPROBE_CTL_IMASK);
			__asm__ volatile("isb" ::: "memory");
			for (polls = 0; polls < 10000000; polls++) {
				expiry_ctl = __builtin_arm_rsr64("CNTV_CTL_EL0");
				end = __builtin_arm_rsr64("CNTVCT_EL0");
				if (expiry_ctl & DTPROBE_CTL_ISTATUS) {
					break;
				}
				if (end - start > max_elapsed) {
					break;
				}
				__asm__ volatile("isb" ::: "memory");
			}
			__builtin_arm_wsr64("CNTV_CTL_EL0", 0);
			__asm__ volatile("isb" ::: "memory");
			status = dtprobe_expiry_check(expected_frequency, frequency,
			    initial_ctl, ticks, start, end, expiry_ctl, polls,
			    10000000);
		}
		if (status == DTPROBE_OK) {
			kprintf("DUCHAMP TIMER EXPIRY PROBE PASS freq=%llu ticks=%llu "
			    "elapsed=%llu polls=%u ctl=0x%llx\\n",
			    (unsigned long long)frequency, (unsigned long long)ticks,
			    (unsigned long long)(end - start), polls,
			    (unsigned long long)expiry_ctl);
			sweet_early_mark(24, "DUCHAMP TIMER EXPIRY PROBE PASS");
		} else {
			kprintf("DUCHAMP TIMER EXPIRY PROBE FAIL status=%d freq=%llu "
			    "initial_ctl=0x%llx polls=%u\\n", status,
			    (unsigned long long)frequency,
			    (unsigned long long)initial_ctl, polls);
			sweet_early_mark(24, "DUCHAMP TIMER EXPIRY PROBE FAIL");
		}
		__asm__ volatile("dsb sy; isb" ::: "memory");
		for (;;) {
			__asm__ volatile("wfe" ::: "memory");
		}
	}
#endif

	PE_init_platform(TRUE, &BootCpuData);'''
    return once(text, BODY_ANCHOR, body)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stage(root):
    repo = Path(__file__).resolve().parent.parent
    source = repo / "duchamp" / "drivers" / "duchamp_timer_probe.h"
    target = root / "osfmk" / "arm" / "duchamp_timer_probe.h"
    receipt = root / "osfmk" / "arm" / "duchamp_timer_probe.json"
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
            raise ValueError("partial or changed timer-probe staging")
        expected = {
            "source_sha256": digest(arm_init),
            "header_sha256": header_hash,
        }
        if json.loads(receipt.read_text(encoding="utf-8")) != expected:
            raise ValueError("changed staged timer-probe source")
        return {"already_staged": True, "header_sha256": header_hash}
    if target.exists() or receipt.exists():
        raise ValueError("preserve existing timer-probe header/receipt")
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
