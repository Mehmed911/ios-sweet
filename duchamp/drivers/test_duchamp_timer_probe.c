#include "duchamp_timer_probe.h"

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

#ifdef DUCHAMP_TIMER_EXPIRY_ARCH_WRITES
static uint64_t
read_cntvct(void)
{
	return __builtin_arm_rsr64("CNTVCT_EL0");
}

static uint64_t
read_cntfrq(void)
{
	return __builtin_arm_rsr64("CNTFRQ_EL0");
}

static uint64_t
read_cntv_ctl(void)
{
	return __builtin_arm_rsr64("CNTV_CTL_EL0");
}

static void
write_cntv_cval(uint64_t value)
{
	__builtin_arm_wsr64("CNTV_CVAL_EL0", value);
}

static void
write_cntv_ctl(uint64_t value)
{
	__builtin_arm_wsr64("CNTV_CTL_EL0", value);
	__asm__ volatile("isb" ::: "memory");
}
#endif

int
main(void)
{
	CHECK(dtprobe_expiry_check(0, 13000000, 0, 1, 1, 2, 7, 0, 1) ==
	    DTPROBE_ARGUMENT);
	CHECK(dtprobe_expiry_check(13000000, 62500000, 0, 1, 1, 2, 7, 0,
	    1) == DTPROBE_FREQUENCY_MISMATCH);
	CHECK(dtprobe_expiry_check(13000000, 13000000, 1, 1, 1, 2, 7, 0,
	    1) == DTPROBE_ALREADY_ENABLED);
	CHECK(dtprobe_expiry_check(13000000, 13000000, 0, 1, 1, 2, 0, 0,
	    1) == DTPROBE_TIMEOUT);
	CHECK(dtprobe_expiry_check(13000000, 13000000, 0, 1, 1, 2, 5, 0,
	    1) == DTPROBE_CONTROL_STATE);
	CHECK(dtprobe_expiry_check(13000000, 13000000, 0, 2, 4, 5, 7, 0,
	    1) == DTPROBE_EARLY_STATUS);
	CHECK(dtprobe_expiry_check(13000000, 13000000, 0, 2, 4, 6, 7, 0,
	    1) == DTPROBE_OK);
	CHECK(dtprobe_expiry_check(UINT32_MAX, UINT32_MAX, 0, 1, 0,
	    UINT64_MAX, 7, 1, 1) == DTPROBE_OK);
	CHECK(dtprobe_expiry_check(13000000, 13000000, 0, 1, 1, 2, 7, 2,
	    1) == DTPROBE_ARGUMENT);

#ifdef DUCHAMP_TIMER_EXPIRY_ARCH_WRITES
	uint64_t const frequency = read_cntfrq();
	uint64_t const initial_ctl = read_cntv_ctl();
	uint64_t const ticks = frequency / 1000;
	uint64_t const max_elapsed = frequency / 10;
	uint64_t const start = read_cntvct();
	uint64_t end = start;
	uint64_t expiry_ctl = initial_ctl;
	unsigned int polls;

	CHECK(frequency == UINT64_C(62500000));
	CHECK((initial_ctl & DTPROBE_CTL_ENABLE) == 0);
	CHECK(ticks == UINT64_C(62500));
	write_cntv_cval(start + ticks);
	write_cntv_ctl(DTPROBE_CTL_ENABLE | DTPROBE_CTL_IMASK);
	for (polls = 0; polls < 10000000; polls++) {
		expiry_ctl = read_cntv_ctl();
		end = read_cntvct();
		if (expiry_ctl & DTPROBE_CTL_ISTATUS) {
			break;
		}
		if (end - start > max_elapsed) {
			break;
		}
		__asm__ volatile("isb" ::: "memory");
	}
	write_cntv_ctl(0);
	CHECK(expiry_ctl & DTPROBE_CTL_ISTATUS);
	CHECK(end - start >= ticks);
	CHECK(dtprobe_expiry_check(62500000, frequency, initial_ctl, ticks,
	    start, end, expiry_ctl, polls, 10000000) == DTPROBE_OK);
	printf("timer expiry qemu freq=%u ticks=%u elapsed=%u polls=%u ctl=%u\n",
	    (unsigned int)frequency, (unsigned int)ticks,
	    (unsigned int)(end - start), polls, (unsigned int)expiry_ctl);
#endif

	printf("%u timer expiry probe checks passed\n", checks);
	return 0;
}
