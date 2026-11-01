#include "duchamp_counter_probe.h"

#ifdef MT6897_MODEL_FREESTANDING
void model_assert_fail(const char *, unsigned) __attribute__((noreturn));
int printf(const char *, ...);
#define assert(x) ((x) ? (void)0 : model_assert_fail(#x, __LINE__))
#else
#include <assert.h>
#include <stdio.h>
#endif

static unsigned int checks;
#define CHECK(x) do { checks++; assert(x); } while (0)

#ifdef DUCHAMP_COUNTER_ARCH_READS
static uint64_t
read_cntfrq(void)
{
	uint64_t value;

	__asm__ volatile("mrs %0, cntfrq_el0" : "=r"(value));
	return value;
}

static uint64_t
read_cntvct(void)
{
	uint64_t value;

	__asm__ volatile("isb; mrs %0, cntvct_el0" : "=r"(value) :: "memory");
	return value;
}
#endif

int
main(void)
{
	CHECK(dcounter_progress_check(0, 13000000, 1, 2) ==
	    DCOUNTER_ARGUMENT);
	CHECK(dcounter_progress_check(13000000, 0, 1, 2) ==
	    DCOUNTER_ARGUMENT);
	CHECK(dcounter_progress_check(1, UINT64_C(0x100000000), 1, 2) ==
	    DCOUNTER_ARGUMENT);
	CHECK(dcounter_progress_check(13000000, 62500000, 1, 2) ==
	    DCOUNTER_FREQUENCY_MISMATCH);
	CHECK(dcounter_progress_check(13000000, 13000000, 2, 2) ==
	    DCOUNTER_NOT_ADVANCING);
	CHECK(dcounter_progress_check(13000000, 13000000, 3, 2) ==
	    DCOUNTER_NOT_ADVANCING);
	CHECK(dcounter_progress_check(13000000, 13000000, 1, 2) ==
	    DCOUNTER_OK);
	CHECK(dcounter_progress_check(UINT32_MAX, UINT32_MAX, 1, UINT64_MAX) ==
	    DCOUNTER_OK);

#ifdef DUCHAMP_COUNTER_ARCH_READS
	uint64_t frequency = read_cntfrq();
	uint64_t start = read_cntvct();
	uint64_t end = start;
	unsigned int polls;

	for (polls = 0; polls < 1000000 && end <= start; polls++)
		end = read_cntvct();
	CHECK(frequency == UINT64_C(62500000));
	CHECK(end > start);
	CHECK(dcounter_progress_check(62500000, frequency, start, end) ==
	    DCOUNTER_OK);
#endif

	printf("%u counter probe checks passed\n", checks);
	return 0;
}
