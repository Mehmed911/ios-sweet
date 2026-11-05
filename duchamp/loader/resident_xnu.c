#include "resident_xnu.h"

static uint64_t
read_le64(const unsigned char *bytes)
{
	uint64_t value = 0;
	unsigned index;
	for (index = 0; index < 8; index++) {
		value |= (uint64_t)bytes[index] << (index * 8);
	}
	return value;
}

static int
add_ok(uint64_t first, uint64_t second, uint64_t *sum)
{
	*sum = first + second;
	return *sum >= first;
}

static int
overlaps(uint64_t first_start, uint64_t first_size,
	uint64_t second_start, uint64_t second_size)
{
	uint64_t first_end, second_end;
	return first_size != 0 && second_size != 0 &&
	    add_ok(first_start, first_size, &first_end) &&
	    add_ok(second_start, second_size, &second_end) &&
	    first_start < second_end && second_start < first_end;
}

static void
clear_bytes(void *pointer, size_t size)
{
	unsigned char *bytes = pointer;
	size_t index;
	for (index = 0; index < size; index++) {
		bytes[index] = 0;
	}
}

unsigned
duchamp_resident_xnu_prepare(void *context_pointer, const void *payload,
	size_t payload_size, struct duchamp_resident_target *target)
{
	struct duchamp_resident_xnu_context *context = context_pointer;
	struct duchamp_range occupied[DUCHAMP_RESIDENT_MAX_OCCUPIED];
	uint64_t end;
	unsigned index, result;

	if (context != NULL) {
		clear_bytes(&context->completed_plan, sizeof(context->completed_plan));
		context->prepare_result = DUCHAMP_GUARD_ARGUMENT;
	}
	if (target != NULL) {
		target->entry = 0;
		target->boot_args = 0;
	}
	if (context == NULL || target == NULL || context->fdt == NULL ||
	    context->fdt_size == 0 || context->fdt_physical == 0 ||
	    context->staging == NULL || payload != context->staging ||
	    payload_size == 0 || payload_size > context->staging_capacity ||
	    context->staging_physical == 0 ||
	    (context->staging_physical & UINT64_C(0x3fff)) != 0 ||
	    context->window == NULL || context->window_physical == 0 ||
	    context->window_size == 0 ||
	    context->occupied_count > DUCHAMP_RESIDENT_MAX_OCCUPIED - 2 ||
	    (context->occupied_count != 0 && context->occupied == NULL) ||
	    !add_ok(context->fdt_physical, context->fdt_size, &end) ||
	    !add_ok(context->staging_physical, payload_size, &end) ||
	    overlaps(context->fdt_physical, context->fdt_size,
	    context->staging_physical, payload_size)) {
		return DUCHAMP_GUARD_ARGUMENT;
	}
	if (payload_size < 0x48 ||
	    read_le64((const unsigned char *)payload + 0x38) !=
	    context->window_physical ||
	    read_le64((const unsigned char *)payload + 0x40) !=
	    context->window_size) {
		context->prepare_result = DUCHAMP_GUARD_PLATFORM;
		return DUCHAMP_GUARD_PLATFORM;
	}
	for (index = 0; index < context->occupied_count; index++) {
		uint64_t occupied_end;
		if (context->occupied[index].size == 0 ||
		    !add_ok(context->occupied[index].start,
		    context->occupied[index].size, &occupied_end) ||
		    overlaps(context->occupied[index].start,
		    context->occupied[index].size, context->fdt_physical,
		    context->fdt_size) ||
		    overlaps(context->occupied[index].start,
		    context->occupied[index].size, context->staging_physical,
		    payload_size)) {
			return DUCHAMP_GUARD_OCCUPIED;
		}
		occupied[index] = context->occupied[index];
	}
	occupied[index].start = context->fdt_physical;
	occupied[index].size = context->fdt_size;
	index++;
	occupied[index].start = context->staging_physical;
	occupied[index].size = payload_size;
	index++;
	result = duchamp_loader_materialize(context->fdt, context->fdt_size,
	    payload, payload_size, occupied, index, &context->framebuffer,
	    context->window, context->window_size, &context->completed_plan);
	context->prepare_result = result;
	if (result != DUCHAMP_GUARD_OK) {
		clear_bytes(&context->completed_plan, sizeof(context->completed_plan));
		return result;
	}
	target->entry = context->completed_plan.entry;
	target->boot_args = context->completed_plan.boot_args.destination;
	return DUCHAMP_GUARD_OK;
}
