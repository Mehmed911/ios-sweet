#include <stdint.h>

#include "phone_capture.h"
#include "../loader/mt6897_entry.h"

#define FDT_LOW_BASE UINT64_C(0x40000000)
#define FDT_LOW_SIZE UINT64_C(0x40000000)
#define FB_BASE UINT64_C(0xfcc2f000)
#define FB_STRIDE 4992U
#define FB_WIDTH 1220U
#define FB_HEIGHT 2712U

struct duchamp_mt6897_entry_state duchamp_bootshim_entry_state;
uint64_t duchamp_bootshim_runtime_head;
struct duchamp_phone_capture_record duchamp_bootshim_phone_capture_record;

struct duchamp_phone_capture_exception {
	uint64_t kind;
	uint64_t esr;
	uint64_t elr;
	uint64_t far;
	uint64_t sp;
};

volatile struct duchamp_phone_capture_exception
    duchamp_bootshim_phone_capture_exception;

void
duchamp_bootshim_exception(uint64_t kind, uint64_t esr, uint64_t elr,
	uint64_t far, uint64_t sp)
{
	duchamp_bootshim_phone_capture_exception.kind = kind;
	duchamp_bootshim_phone_capture_exception.esr = esr;
	duchamp_bootshim_phone_capture_exception.elr = elr;
	duchamp_bootshim_phone_capture_exception.far = far;
	duchamp_bootshim_phone_capture_exception.sp = sp;
}

void
duchamp_bootshim_main(void)
{
	unsigned entry_result = duchamp_mt6897_entry_check(
	    &duchamp_bootshim_entry_state, FDT_LOW_BASE, FDT_LOW_SIZE);

	(void)duchamp_phone_capture_run((volatile void *)(uintptr_t)FB_BASE,
	    FB_STRIDE, FB_WIDTH, FB_HEIGHT, duchamp_bootshim_runtime_head,
	    duchamp_bootshim_entry_state.entry_x0,
	    duchamp_bootshim_entry_state.current_el,
	    duchamp_bootshim_entry_state.sctlr_el1, entry_result,
	    &duchamp_bootshim_phone_capture_record);
}
