#include <stdio.h>
#include "handoff_ready.h"

int
main(void)
{
	struct duchamp_handoff_ready report;
	const uint64_t base = UINT64_C(0x1c0000000);
	const uint64_t size = UINT64_C(0x20000000);
	if (duchamp_handoff_ready_check(4, 0, base, size,
	    UINT64_C(0x1c1480488), UINT64_C(0x1c24dc000), &report) != 0)
		return 1;
	if (duchamp_handoff_ready_check(8, 0, base, size,
	    UINT64_C(0x1c1480488), UINT64_C(0x1c24dc000), &report) !=
	    DUCHAMP_READY_EXCEPTION_LEVEL) return 1;
	if (duchamp_handoff_ready_check(4, 1, base, size,
	    UINT64_C(0x1c1480488), UINT64_C(0x1c24dc000), &report) !=
	    DUCHAMP_READY_TRANSLATION_STATE) return 1;
	if (duchamp_handoff_ready_check(4, 0, base, size,
	    base - 4, UINT64_C(0x1c24dc000), &report) !=
	    DUCHAMP_READY_RANGE) return 1;
	if (duchamp_handoff_ready_check(4, 0, base, size,
	    UINT64_C(0x1c1480489), UINT64_C(0x1c24dc000), &report) !=
	    DUCHAMP_READY_ALIGNMENT) return 1;
	duchamp_handoff_barrier();
	puts("handoff-ready-tests: PASS");
	return 0;
}
