#include "materialize.h"

#define BOOT_ARGS_PAGE 0x4000u
#define COMMAND_LINE_LENGTH 608u

struct boot_video {
	uint64_t base;
	uint64_t display;
	uint64_t row_bytes;
	uint64_t width;
	uint64_t height;
	uint64_t depth;
};

struct boot_args_v2 {
	uint16_t revision;
	uint16_t version;
	uint64_t virt_base;
	uint64_t phys_base;
	uint64_t memory_size;
	uint64_t top_of_kernel_data;
	struct boot_video video;
	uint32_t machine_type;
	uint64_t device_tree;
	uint32_t device_tree_length;
	char command_line[COMMAND_LINE_LENGTH];
	uint64_t boot_flags;
	uint64_t memory_size_actual;
};

_Static_assert(__builtin_offsetof(struct boot_args_v2, video) == 40, "boot_args video offset");
_Static_assert(__builtin_offsetof(struct boot_args_v2, command_line) == 108, "boot_args command line offset");
_Static_assert(sizeof(struct boot_args_v2) == 736, "boot_args size");

static void
copy_bytes(void *destination_pointer, const void *source_pointer, uint64_t size)
{
	unsigned char *destination = destination_pointer;
	const unsigned char *source = source_pointer;
	uint64_t index;
	for (index = 0; index < size; index++) {
		destination[index] = source[index];
	}
}

static void
zero_bytes(void *destination_pointer, uint64_t size)
{
	unsigned char *destination = destination_pointer;
	uint64_t index;
	for (index = 0; index < size; index++) {
		destination[index] = 0;
	}
}

static int
range_inside_window(uint64_t address, uint64_t size, uint64_t base, size_t window_size)
{
	uint64_t offset;
	if (address < base) {
		return 0;
	}
	offset = address - base;
	return offset <= window_size && size <= window_size - offset;
}

unsigned
duchamp_loader_materialize(const void *fdt, size_t fdt_size,
    const void *payload_pointer, size_t payload_size,
    const struct duchamp_range *occupied, unsigned occupied_count,
    const struct duchamp_framebuffer *framebuffer,
    void *window_pointer, size_t window_size,
    struct duchamp_dry_run_plan *completed_plan)
{
	const unsigned char *payload = payload_pointer;
	unsigned char *window = window_pointer;
	struct duchamp_dry_run_plan plan;
	struct boot_args_v2 *boot_args;
	uint64_t base, offset;
	unsigned result, index;

	if (window == NULL || completed_plan == NULL) {
		return DUCHAMP_GUARD_ARGUMENT;
	}
	result = duchamp_loader_dry_run(fdt, fdt_size, payload, payload_size,
	    occupied, occupied_count, framebuffer, &plan);
	if (result != DUCHAMP_GUARD_OK) {
		zero_bytes(completed_plan, sizeof(*completed_plan));
		return result;
	}
	base = plan.boot_args.phys_base;
	if (plan.boot_args.top_of_kernel_data < base ||
	    plan.boot_args.top_of_kernel_data - base > window_size ||
	    !range_inside_window(plan.adt.destination, plan.adt.copy_size, base, window_size) ||
	    !range_inside_window(plan.boot_args.destination, BOOT_ARGS_PAGE, base, window_size)) {
		zero_bytes(completed_plan, sizeof(*completed_plan));
		return DUCHAMP_GUARD_PLATFORM;
	}
	for (index = 0; index < plan.segment_count; index++) {
		const struct duchamp_copy_plan *segment = &plan.segments[index];
		if (!range_inside_window(segment->destination,
		    segment->copy_size + segment->zero_size, base, window_size)) {
			zero_bytes(completed_plan, sizeof(*completed_plan));
			return DUCHAMP_GUARD_PLATFORM;
		}
	}
	for (index = 0; index < plan.segment_count; index++) {
		const struct duchamp_copy_plan *segment = &plan.segments[index];
		offset = segment->destination - base;
		copy_bytes(window + offset, payload + segment->source_offset, segment->copy_size);
		zero_bytes(window + offset + segment->copy_size, segment->zero_size);
	}
	offset = plan.adt.destination - base;
	copy_bytes(window + offset, payload + plan.adt.source_offset, plan.adt.copy_size);
	offset = plan.boot_args.destination - base;
	zero_bytes(window + offset, BOOT_ARGS_PAGE);
	boot_args = (struct boot_args_v2 *)(window + offset);
	boot_args->revision = 2;
	boot_args->version = 2;
	boot_args->virt_base = plan.boot_args.virt_base;
	boot_args->phys_base = base;
	boot_args->memory_size = plan.boot_args.memory_size;
	boot_args->top_of_kernel_data = plan.boot_args.top_of_kernel_data;
	boot_args->video.base = framebuffer->base;
	boot_args->video.display = 1;
	boot_args->video.row_bytes = framebuffer->stride;
	boot_args->video.width = framebuffer->width;
	boot_args->video.height = framebuffer->height;
	boot_args->video.depth = framebuffer->depth;
	boot_args->device_tree = plan.boot_args.device_tree_virtual;
	boot_args->device_tree_length = (uint32_t)plan.boot_args.device_tree_size;
	copy_bytes(boot_args->command_line, payload + 0x48, COMMAND_LINE_LENGTH);
	boot_args->memory_size_actual = plan.boot_args.memory_size;
	copy_bytes(completed_plan, &plan, sizeof(plan));
	return DUCHAMP_GUARD_OK;
}
