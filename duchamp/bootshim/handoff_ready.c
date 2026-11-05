#include "handoff_ready.h"

#define SCTLR_MCI (UINT64_C(1) | (UINT64_C(1) << 2) | (UINT64_C(1) << 12))

unsigned
duchamp_handoff_ready_check(uint64_t current_el, uint64_t sctlr,
	uint64_t window_base, uint64_t window_size, uint64_t entry,
	uint64_t boot_args, struct duchamp_handoff_ready *report)
{
	uint64_t end;
	unsigned result = DUCHAMP_READY_OK;
	if (report == 0) return DUCHAMP_READY_ARGUMENT;
	report->current_el = current_el;
	report->sctlr = sctlr;
	report->entry = entry;
	report->boot_args = boot_args;
	if (window_size == 0 || window_base > UINT64_MAX - window_size) {
		result = DUCHAMP_READY_ARGUMENT;
	} else if (current_el != 4) {
		result = DUCHAMP_READY_EXCEPTION_LEVEL;
	} else if ((sctlr & SCTLR_MCI) != 0) {
		result = DUCHAMP_READY_TRANSLATION_STATE;
	} else {
		end = window_base + window_size;
		if (entry < window_base || entry >= end || boot_args < window_base ||
		    boot_args > end || end - boot_args < 0x4000) {
			result = DUCHAMP_READY_RANGE;
		} else if ((entry & 3) != 0 || (boot_args & 0x3fff) != 0) {
			result = DUCHAMP_READY_ALIGNMENT;
		}
	}
	report->result = result;
	report->reserved = 0;
	return result;
}

void
duchamp_handoff_barrier(void)
{
#if defined(__aarch64__) && !defined(DUCHAMP_TEST_NO_ARCH_BARRIER)
	__asm__ volatile("dsb sy; ic iallu; dsb sy; isb" ::: "memory");
#endif
}
