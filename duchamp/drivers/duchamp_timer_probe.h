#ifndef DUCHAMP_TIMER_PROBE_H
#define DUCHAMP_TIMER_PROBE_H

#include <stdint.h>

#define DTPROBE_CTL_ENABLE UINT64_C(1)
#define DTPROBE_CTL_IMASK  UINT64_C(2)
#define DTPROBE_CTL_ISTATUS UINT64_C(4)

enum dtprobe_result {
	DTPROBE_OK = 0,
	DTPROBE_ARGUMENT = -1,
	DTPROBE_FREQUENCY_MISMATCH = -2,
	DTPROBE_ALREADY_ENABLED = -3,
	DTPROBE_TIMEOUT = -4,
	DTPROBE_EARLY_STATUS = -5,
	DTPROBE_CONTROL_STATE = -6,
};

/* Pure validation helper. The caller performs the architected sysreg I/O. */
static inline int
dtprobe_expiry_check(uint32_t expected_hz, uint64_t observed_hz,
    uint64_t initial_ctl, uint64_t ticks, uint64_t start, uint64_t end,
    uint64_t expiry_ctl, unsigned int polls, unsigned int max_polls)
{
	if (!expected_hz || !observed_hz || observed_hz > UINT32_MAX ||
	    !ticks || !max_polls || polls > max_polls) {
		return DTPROBE_ARGUMENT;
	}
	if (observed_hz != expected_hz) {
		return DTPROBE_FREQUENCY_MISMATCH;
	}
	if (initial_ctl & DTPROBE_CTL_ENABLE) {
		return DTPROBE_ALREADY_ENABLED;
	}
	if ((expiry_ctl & DTPROBE_CTL_ISTATUS) == 0) {
		return DTPROBE_TIMEOUT;
	}
	if ((expiry_ctl & (DTPROBE_CTL_ENABLE | DTPROBE_CTL_IMASK)) !=
	    (DTPROBE_CTL_ENABLE | DTPROBE_CTL_IMASK)) {
		return DTPROBE_CONTROL_STATE;
	}
	if (end < start || end - start < ticks) {
		return DTPROBE_EARLY_STATUS;
	}
	return DTPROBE_OK;
}

#endif
