#ifndef DUCHAMP_TIMER_BOOT_H
#define DUCHAMP_TIMER_BOOT_H
#include <stdint.h>

/* Validate the architected counter contract before XNU uses its ADT-derived
 * timebase frequency.  This helper performs no register, MMIO or firmware I/O. */
enum dtimer_result {
    DTIMER_OK=0,
    DTIMER_ARGUMENT=-1,
    DTIMER_FREQUENCY_MISMATCH=-2
};

static inline int
dtimer_frequency_check(uint32_t expected_hz,uint64_t observed_hz) {
    if(!expected_hz || !observed_hz || observed_hz>UINT32_MAX)
        return DTIMER_ARGUMENT;
    return observed_hz==expected_hz ? DTIMER_OK : DTIMER_FREQUENCY_MISMATCH;
}
#endif
