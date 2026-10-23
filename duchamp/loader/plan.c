#include "plan.h"

static uint32_t
read_le32(const unsigned char *pointer)
{
	return (uint32_t)pointer[0] | (uint32_t)pointer[1] << 8 |
	       (uint32_t)pointer[2] << 16 | (uint32_t)pointer[3] << 24;
}

static uint64_t
read_le64(const unsigned char *pointer)
{
	return (uint64_t)read_le32(pointer) | (uint64_t)read_le32(pointer + 4) << 32;
}

static int
multiply_ok(uint64_t first, uint64_t second, uint64_t *product)
{
	if (first != 0 && second > UINT64_MAX / first) {
		return 0;
	}
	*product = first * second;
	return 1;
}

static int
add_ok(uint64_t first, uint64_t second, uint64_t *sum)
{
	*sum = first + second;
	return *sum >= first;
}

static void
clear_plan(struct duchamp_dry_run_plan *plan)
{
	unsigned char *bytes = (unsigned char *)plan;
	size_t index;
	for (index = 0; index < sizeof(*plan); index++) {
		bytes[index] = 0;
	}
}

unsigned
duchamp_loader_dry_run(const void *fdt, size_t fdt_size,
    const void *payload_pointer, size_t payload_size,
    const struct duchamp_range *occupied, unsigned occupied_count,
    const struct duchamp_framebuffer *framebuffer,
    struct duchamp_dry_run_plan *dry_run)
{
	const unsigned char *payload = payload_pointer;
	struct duchamp_payload_plan placement;
	uint64_t virt_base, phys_base, memory_size, adt_offset, adt_size;
	uint64_t framebuffer_size, framebuffer_end, minimum_stride;
	unsigned result, index, segment_count;

	if (dry_run == NULL) {
		return DUCHAMP_GUARD_ARGUMENT;
	}
	clear_plan(dry_run);
	if (framebuffer == NULL || payload == NULL || framebuffer->base == 0 ||
	    framebuffer->width == 0 || framebuffer->height == 0 ||
	    framebuffer->depth != 32 ||
	    !multiply_ok(framebuffer->width, 4, &minimum_stride) ||
	    framebuffer->stride < minimum_stride || (framebuffer->stride & 3) != 0 ||
	    !multiply_ok(framebuffer->stride, framebuffer->height, &framebuffer_size) ||
	    !add_ok(framebuffer->base, framebuffer_size, &framebuffer_end)) {
		return DUCHAMP_GUARD_PLATFORM;
	}
	result = duchamp_loader_plan_check(fdt, fdt_size, payload, payload_size,
	    occupied, occupied_count, &placement);
	if (result != DUCHAMP_GUARD_OK) {
		return result;
	}
	(void)framebuffer_end;
	segment_count = read_le32(payload + 12);
	virt_base = read_le64(payload + 0x10);
	adt_offset = read_le64(payload + 0x20);
	adt_size = read_le64(payload + 0x28);
	phys_base = read_le64(payload + 0x38);
	memory_size = read_le64(payload + 0x40);
	dry_run->entry = placement.entry;
	dry_run->segment_count = segment_count;
	for (index = 0; index < segment_count; index++) {
		const unsigned char *segment = payload + 0x2a8 + index * 32;
		uint64_t virtual_address = read_le64(segment);
		uint64_t virtual_size = read_le64(segment + 8);
		uint64_t file_size = read_le64(segment + 24);
		dry_run->segments[index].source_offset = read_le64(segment + 16);
		dry_run->segments[index].destination = phys_base + virtual_address - virt_base;
		dry_run->segments[index].copy_size = file_size;
		dry_run->segments[index].zero_size = virtual_size - file_size;
	}
	dry_run->adt.source_offset = adt_offset;
	dry_run->adt.destination = placement.adt;
	dry_run->adt.copy_size = adt_size;
	dry_run->boot_args.destination = placement.boot_args;
	dry_run->boot_args.virt_base = virt_base;
	dry_run->boot_args.phys_base = phys_base;
	dry_run->boot_args.memory_size = memory_size;
	dry_run->boot_args.top_of_kernel_data = placement.top;
	dry_run->boot_args.device_tree_virtual = virt_base + placement.adt - phys_base;
	dry_run->boot_args.device_tree_size = adt_size;
	dry_run->boot_args.video = *framebuffer;
	return DUCHAMP_GUARD_OK;
}
