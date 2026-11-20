#include "return_slot.h"

#define RETURN_SLOT_BYTES 32u

static int
range_inside(uint64_t address, uint64_t size, uint64_t base, size_t window_size)
{
	uint64_t offset;

	if (address < base) return 0;
	offset = address - base;
	return offset <= window_size && size <= window_size - offset;
}

static int
magic_at(const unsigned char *p)
{
	static const unsigned char magic[8] = {
		'X', 'N', 'U', 'L', 'D', 'R', 'S', 'T'
	};
	unsigned i;

	for (i = 0; i < sizeof(magic); i++) {
		if (p[i] != magic[i]) return 0;
	}
	return 1;
}

static void
write_le64(unsigned char *p, uint64_t value)
{
	unsigned i;

	for (i = 0; i < 8; i++) {
		p[i] = (unsigned char)(value >> (i * 8));
	}
}

unsigned
duchamp_loader_patch_return_slot(void *window_pointer, size_t window_size,
	const struct duchamp_dry_run_plan *plan, uint64_t return_stub_pa,
	uint64_t checkpoint, struct duchamp_return_slot_report *report)
{
	unsigned char *window = window_pointer;
	uint64_t base, found_pa = 0;
	unsigned matches = 0, index;

	if (report == NULL) return DUCHAMP_RETURN_SLOT_ARGUMENT;
	report->result = DUCHAMP_RETURN_SLOT_ARGUMENT;
	report->matches = 0;
	report->slot_pa = 0;
	report->return_stub_pa = return_stub_pa;
	report->checkpoint = checkpoint;
	report->phys_minus_virt = 0;
	if (window == NULL || plan == NULL || plan->segment_count == 0 ||
	    plan->segment_count > DUCHAMP_MAX_SEGMENTS || return_stub_pa == 0) {
		return report->result;
	}
	if ((return_stub_pa & 3) != 0) {
		report->result = DUCHAMP_RETURN_SLOT_ALIGNMENT;
		return report->result;
	}
	base = plan->boot_args.phys_base;
	for (index = 0; index < plan->segment_count; index++) {
		const struct duchamp_copy_plan *segment = &plan->segments[index];
		uint64_t offset, at;

		if (!range_inside(segment->destination, segment->copy_size, base,
		    window_size)) {
			report->result = DUCHAMP_RETURN_SLOT_RANGE;
			return report->result;
		}
		if (segment->copy_size < RETURN_SLOT_BYTES) continue;
		offset = segment->destination - base;
		for (at = 0; at <= segment->copy_size - RETURN_SLOT_BYTES; at += 8) {
			if (magic_at(window + offset + at)) {
				matches++;
				found_pa = segment->destination + at;
			}
		}
	}
	report->matches = matches;
	if (matches == 0) {
		report->result = DUCHAMP_RETURN_SLOT_NOT_FOUND;
		return report->result;
	}
	if (matches != 1) {
		report->result = DUCHAMP_RETURN_SLOT_MULTIPLE;
		return report->result;
	}
	if ((found_pa & 7) != 0 ||
	    !range_inside(found_pa, RETURN_SLOT_BYTES, base, window_size)) {
		report->result = DUCHAMP_RETURN_SLOT_ALIGNMENT;
		return report->result;
	}
	unsigned char *slot = window + (found_pa - base);
	write_le64(slot + 8, return_stub_pa);
	write_le64(slot + 16, checkpoint);
	write_le64(slot + 24,
	    plan->boot_args.phys_base - plan->boot_args.virt_base);
	report->slot_pa = found_pa;
	report->phys_minus_virt =
	    plan->boot_args.phys_base - plan->boot_args.virt_base;
	report->result = DUCHAMP_RETURN_SLOT_OK;
	return report->result;
}
