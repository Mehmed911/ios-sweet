#ifndef DUCHAMP_COUNTER_PROBE_H
#define DUCHAMP_COUNTER_PROBE_H

#include <stdint.h>

enum dcounter_result {
	DCOUNTER_OK = 0,
	DCOUNTER_ARGUMENT = -1,
	DCOUNTER_FREQUENCY_MISMATCH = -2,
	DCOUNTER_NOT_ADVANCING = -3,
};

/* Pure validation helper. The caller performs the architected register reads. */
static inline int
dcounter_progress_check(uint32_t expected_hz, uint64_t observed_hz,
			uint64_t start, uint64_t end)
{
	if (!expected_hz || !observed_hz || observed_hz > UINT32_MAX)
		return DCOUNTER_ARGUMENT;
	if (observed_hz != expected_hz)
		return DCOUNTER_FREQUENCY_MISMATCH;
	if (end <= start)
		return DCOUNTER_NOT_ADVANCING;
	return DCOUNTER_OK;
}

#endif
