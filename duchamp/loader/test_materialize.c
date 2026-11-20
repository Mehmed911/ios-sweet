#define _GNU_SOURCE
#include <errno.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>

#include "materialize.h"

#define WINDOW_SIZE UINT64_C(0x20000000)
#define BOOT_ARGS_PAGE UINT64_C(0x4000)

struct boot_video_test {
	uint64_t base, display, row_bytes, width, height, depth;
};

struct boot_args_test {
	uint16_t revision, version;
	uint64_t virt_base, phys_base, memory_size, top_of_kernel_data;
	struct boot_video_test video;
	uint32_t machine_type;
	uint64_t device_tree;
	uint32_t device_tree_length;
	char command_line[608];
	uint64_t boot_flags, memory_size_actual;
};

static uint32_t
read_le32(const unsigned char *p)
{
	return (uint32_t)p[0] | (uint32_t)p[1] << 8 |
	    (uint32_t)p[2] << 16 | (uint32_t)p[3] << 24;
}

static unsigned char *
read_file(const char *path, size_t *size)
{
	FILE *file = fopen(path, "rb");
	unsigned char *data;
	long length;
	if (!file || fseek(file, 0, SEEK_END) || (length = ftell(file)) <= 0 ||
	    fseek(file, 0, SEEK_SET)) return NULL;
	data = malloc((size_t)length);
	if (!data || fread(data, 1, (size_t)length, file) != (size_t)length) return NULL;
	fclose(file);
	*size = (size_t)length;
	return data;
}

static int
all_value(const unsigned char *data, uint64_t size, unsigned char value)
{
	for (uint64_t i = 0; i < size; i++) if (data[i] != value) return 0;
	return 1;
}

int
main(int argc, char **argv)
{
	unsigned char *fdt, *payload, *window;
	size_t fdt_size, payload_size;
	struct duchamp_dry_run_plan plan;
	struct duchamp_framebuffer framebuffer = {
		.base = UINT64_C(0xfcc2f000), .stride = 4992,
		.width = 1220, .height = 2712, .depth = 32
	};
	uint64_t completed_entry, completed_top;
	unsigned expected_segment_count, result;
	if (argc != 3) return 2;
	fdt = read_file(argv[1], &fdt_size);
	payload = read_file(argv[2], &payload_size);
	window = mmap(NULL, WINDOW_SIZE, PROT_READ | PROT_WRITE,
	    MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
	if (!fdt || !payload || window == MAP_FAILED) return 2;
	memset(window, 0xa5, WINDOW_SIZE);
	expected_segment_count = read_le32(payload + 12);
	result = duchamp_loader_materialize(fdt, fdt_size, payload, payload_size,
	    NULL, 0, &framebuffer, window, WINDOW_SIZE, &plan);
	if (result != DUCHAMP_GUARD_OK ||
	    plan.segment_count != expected_segment_count) {
		fprintf(stderr, "materialize failed: result=%u segments=%u\n",
		    result, plan.segment_count);
		return 1;
	}
	for (unsigned i = 0; i < plan.segment_count; i++) {
		const struct duchamp_copy_plan *segment = &plan.segments[i];
		uint64_t offset = segment->destination - plan.boot_args.phys_base;
		if (memcmp(window + offset, payload + segment->source_offset,
		    segment->copy_size) != 0 ||
		    !all_value(window + offset + segment->copy_size,
		    segment->zero_size, 0)) {
			fprintf(stderr, "segment %u mismatch\n", i);
			return 1;
		}
	}
	{
		uint64_t offset = plan.adt.destination - plan.boot_args.phys_base;
		if (memcmp(window + offset, payload + plan.adt.source_offset,
		    plan.adt.copy_size) != 0) return 1;
	}
	{
		uint64_t offset = plan.boot_args.destination - plan.boot_args.phys_base;
		struct boot_args_test *args = (struct boot_args_test *)(window + offset);
		if (args->revision != 2 || args->version != 2 ||
		    args->virt_base != plan.boot_args.virt_base ||
		    args->phys_base != plan.boot_args.phys_base ||
		    args->memory_size != WINDOW_SIZE ||
		    args->top_of_kernel_data != plan.boot_args.top_of_kernel_data ||
		    args->video.base != framebuffer.base || args->video.display != 1 ||
		    args->video.row_bytes != framebuffer.stride ||
		    args->device_tree != plan.boot_args.device_tree_virtual ||
		    args->device_tree_length != plan.boot_args.device_tree_size ||
		    memcmp(args->command_line, payload + 0x48, 608) != 0 ||
		    args->memory_size_actual != WINDOW_SIZE ||
		    !all_value(window + offset + sizeof(*args),
		    BOOT_ARGS_PAGE - sizeof(*args), 0)) return 1;
	}
	if (!all_value(window + WINDOW_SIZE - 0x4000, 0x4000, 0xa5)) {
		fprintf(stderr, "write escaped planned top\n");
		return 1;
	}
	completed_entry = plan.entry;
	completed_top = plan.boot_args.top_of_kernel_data;

	memset(window, 0x5a, 0x10000);
	payload[0] ^= 0xff;
	result = duchamp_loader_materialize(fdt, fdt_size, payload, payload_size,
	    NULL, 0, &framebuffer, window, WINDOW_SIZE, &plan);
	if (result != DUCHAMP_GUARD_PAYLOAD_HEADER ||
	    !all_value(window, 0x10000, 0x5a)) {
		fprintf(stderr, "failure path modified destination\n");
		return 1;
	}

	printf("materialize-tests: PASS entry=%#llx segments=%u top=%#llx\n",
	    (unsigned long long)completed_entry, expected_segment_count,
	    (unsigned long long)completed_top);
	munmap(window, WINDOW_SIZE);
	free(payload);
	free(fdt);
	return 0;
}
