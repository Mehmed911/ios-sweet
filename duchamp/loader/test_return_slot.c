#include <stdio.h>
#include <string.h>

#include "return_slot.h"

static uint64_t
read_le64(const unsigned char *p)
{
	uint64_t value = 0;
	unsigned i;

	for (i = 0; i < 8; i++) value |= (uint64_t)p[i] << (i * 8);
	return value;
}

int
main(void)
{
	unsigned char window[512];
	struct duchamp_dry_run_plan plan;
	struct duchamp_return_slot_report report;
	const uint64_t base = UINT64_C(0x1c0000000);
	const uint64_t virt = UINT64_C(0xfffffff004000000);
	const uint64_t stub = UINT64_C(0x40081234);
	static const unsigned char magic[8] = {
		'X', 'N', 'U', 'L', 'D', 'R', 'S', 'T'
	};

	memset(window, 0, sizeof(window));
	memset(&plan, 0, sizeof(plan));
	plan.segment_count = 1;
	plan.segments[0].destination = base;
	plan.segments[0].copy_size = sizeof(window);
	plan.boot_args.phys_base = base;
	plan.boot_args.virt_base = virt;
	memcpy(window + 128, magic, sizeof(magic));
	if (duchamp_loader_patch_return_slot(window, sizeof(window), &plan,
	    stub, 27, &report) != DUCHAMP_RETURN_SLOT_OK) return 1;
	if (report.matches != 1 || report.slot_pa != base + 128 ||
	    read_le64(window + 136) != stub || read_le64(window + 144) != 27 ||
	    read_le64(window + 152) != base - virt) return 2;
	memset(window + 128, 0, 32);
	if (duchamp_loader_patch_return_slot(window, sizeof(window), &plan,
	    stub, 0, &report) != DUCHAMP_RETURN_SLOT_NOT_FOUND) return 3;
	memcpy(window + 64, magic, 8);
	memcpy(window + 128, magic, 8);
	if (duchamp_loader_patch_return_slot(window, sizeof(window), &plan,
	    stub, 0, &report) != DUCHAMP_RETURN_SLOT_MULTIPLE) return 4;
	if (duchamp_loader_patch_return_slot(window, sizeof(window), &plan,
	    stub + 1, 0, &report) != DUCHAMP_RETURN_SLOT_ALIGNMENT) return 5;
	plan.segments[0].destination = base - 8;
	if (duchamp_loader_patch_return_slot(window, sizeof(window), &plan,
	    stub, 0, &report) != DUCHAMP_RETURN_SLOT_RANGE) return 6;
	puts("return-slot-tests: PASS");
	return 0;
}
