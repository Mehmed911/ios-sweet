#define _GNU_SOURCE
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>

#include "resident_xnu.h"

#define WINDOW_SIZE UINT64_C(0x20000000)

struct test_context {
	struct duchamp_resident_loader *loader;
	struct duchamp_resident_xnu_context xnu;
	unsigned prepare_calls;
	unsigned enter_calls;
};

static unsigned char *
read_file(const char *path, size_t *size)
{
	FILE *file = fopen(path, "rb");
	unsigned char *data;
	long length;
	if (file == NULL || fseek(file, 0, SEEK_END) != 0 ||
	    (length = ftell(file)) <= 0 || fseek(file, 0, SEEK_SET) != 0) return NULL;
	data = malloc((size_t)length);
	if (data == NULL || fread(data, 1, (size_t)length, file) != (size_t)length) return NULL;
	fclose(file);
	*size = (size_t)length;
	return data;
}

static unsigned
prepare(void *context_pointer, const void *payload, size_t payload_size,
	struct duchamp_resident_target *target)
{
	struct test_context *context = context_pointer;
	context->prepare_calls++;
	return duchamp_resident_xnu_prepare(&context->xnu, payload,
	    payload_size, target);
}

static unsigned
enter(void *context_pointer, const struct duchamp_resident_target *target)
{
	static const char message[] = "XNU-RETURN";
	struct test_context *context = context_pointer;
	context->enter_calls++;
	if (target->entry != context->xnu.completed_plan.entry ||
	    target->boot_args != context->xnu.completed_plan.boot_args.destination) {
		return 90;
	}
	return duchamp_resident_complete(context->loader, 0x44554348,
	    message, sizeof(message) - 1);
}

static int
all_value(const unsigned char *bytes, size_t size, unsigned char value)
{
	size_t index;
	for (index = 0; index < size; index++) if (bytes[index] != value) return 0;
	return 1;
}

static void
write_be32(unsigned char *bytes, uint32_t value)
{
	bytes[0] = (unsigned char)(value >> 24);
	bytes[1] = (unsigned char)(value >> 16);
	bytes[2] = (unsigned char)(value >> 8);
	bytes[3] = (unsigned char)value;
}

#define CHECK(condition) do { if (!(condition)) { \
	fprintf(stderr, "resident XNU check failed at line %d\n", __LINE__); \
	return 1; } checks++; } while (0)

int
main(int argc, char **argv)
{
	const struct duchamp_resident_ops ops = {prepare, enter};
	struct duchamp_resident_loader loader;
	struct duchamp_resident_result_view view;
	struct duchamp_range occupied = {UINT64_C(0x40200000), UINT64_C(0x200000)};
	struct test_context context;
	unsigned char *fdt, *bad_fdt, *source, *staging, *window;
	unsigned char result_buffer[64];
	size_t fdt_size, payload_size, offset;
	uint64_t completed_entry;
	unsigned completed_segments;
	unsigned checks = 0;

	if (argc != 3) return 2;
	fdt = read_file(argv[1], &fdt_size);
	source = read_file(argv[2], &payload_size);
	staging = malloc(payload_size);
	bad_fdt = malloc(fdt_size);
	window = mmap(NULL, WINDOW_SIZE, PROT_READ | PROT_WRITE,
	    MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
	if (fdt == NULL || bad_fdt == NULL || source == NULL || staging == NULL ||
	    window == MAP_FAILED) return 2;
	memcpy(bad_fdt, fdt, fdt_size);
	write_be32(bad_fdt + 36, 0);
	CHECK(duchamp_fdt_window_check(bad_fdt, fdt_size, UINT64_C(0x1c0000000),
	    WINDOW_SIZE, NULL, 0) == DUCHAMP_GUARD_FDT_HEADER);
	memcpy(bad_fdt, fdt, fdt_size);
	write_be32(bad_fdt + 8, UINT32_C(0xfffffff0));
	write_be32(bad_fdt + 36, UINT32_C(0x20));
	CHECK(duchamp_fdt_window_check(bad_fdt, fdt_size, UINT64_C(0x1c0000000),
	    WINDOW_SIZE, NULL, 0) == DUCHAMP_GUARD_FDT_HEADER);
	memcpy(bad_fdt, fdt, fdt_size);
	write_be32(bad_fdt + 12, UINT32_C(0xfffffff0));
	write_be32(bad_fdt + 32, UINT32_C(0x20));
	CHECK(duchamp_fdt_window_check(bad_fdt, fdt_size, UINT64_C(0x1c0000000),
	    WINDOW_SIZE, NULL, 0) == DUCHAMP_GUARD_FDT_HEADER);
	memcpy(bad_fdt, fdt, fdt_size);
	write_be32(bad_fdt + 16, UINT32_C(0xfffffff8));
	CHECK(duchamp_fdt_window_check(bad_fdt, fdt_size, UINT64_C(0x1c0000000),
	    WINDOW_SIZE, NULL, 0) == DUCHAMP_GUARD_FDT_HEADER);
	memset(window, 0xa5, WINDOW_SIZE);
	memset(&context, 0, sizeof(context));
	context.loader = &loader;
	context.xnu.fdt = fdt;
	context.xnu.fdt_size = fdt_size;
	context.xnu.fdt_physical = UINT64_C(0x40000000);
	context.xnu.staging = staging;
	context.xnu.staging_capacity = payload_size;
	context.xnu.staging_physical = UINT64_C(0x90000000);
	context.xnu.occupied = &occupied;
	context.xnu.occupied_count = 1;
	context.xnu.framebuffer.base = UINT64_C(0xfcc2f000);
	context.xnu.framebuffer.stride = 4992;
	context.xnu.framebuffer.width = 1220;
	context.xnu.framebuffer.height = 2712;
	context.xnu.framebuffer.depth = 32;
	context.xnu.window = window;
	context.xnu.window_size = WINDOW_SIZE;
	CHECK(duchamp_resident_init(&loader, staging, payload_size, result_buffer,
	    sizeof(result_buffer), 0x20261105) == 0);
	CHECK(duchamp_resident_begin(&loader, payload_size) == 0);
	for (offset = 0; offset < payload_size;) {
		size_t chunk = payload_size - offset;
		if (chunk > 65537) chunk = 65537;
		CHECK(duchamp_resident_receive(&loader, offset, source + offset, chunk) == 0);
		offset += chunk;
	}
	CHECK(loader.state == DUCHAMP_RESIDENT_READY);
	CHECK(duchamp_resident_run(&loader, &ops, &context) == 0);
	CHECK(context.prepare_calls == 1 && context.enter_calls == 1 &&
	    context.xnu.prepare_result == DUCHAMP_GUARD_OK);
	CHECK(loader.state == DUCHAMP_RESIDENT_RETURNED && loader.run_count == 1);
	CHECK(duchamp_resident_get_result(&loader, &view) == 0 &&
	    view.code == UINT64_C(0x44554348) && view.size == 10 &&
	    memcmp(view.data, "XNU-RETURN", 10) == 0);
	completed_entry = context.xnu.completed_plan.entry;
	completed_segments = context.xnu.completed_plan.segment_count;
	for (unsigned index = 0; index < context.xnu.completed_plan.segment_count; index++) {
		const struct duchamp_copy_plan *segment =
		    &context.xnu.completed_plan.segments[index];
		uint64_t target_offset = segment->destination -
		    context.xnu.completed_plan.boot_args.phys_base;
		CHECK(memcmp(window + target_offset,
		    staging + segment->source_offset, segment->copy_size) == 0);
		CHECK(all_value(window + target_offset + segment->copy_size,
		    segment->zero_size, 0));
	}
	CHECK(duchamp_resident_run(&loader, &ops, &context) ==
	    DUCHAMP_RESIDENT_RELOAD_REQUIRED);

	memset(window, 0x5a, 0x10000);
	memset(&context, 0, sizeof(context));
	context.loader = &loader;
	context.xnu.fdt = fdt;
	context.xnu.fdt_size = fdt_size;
	context.xnu.fdt_physical = UINT64_C(0x40000000);
	context.xnu.staging = staging;
	context.xnu.staging_capacity = payload_size;
	context.xnu.staging_physical = UINT64_C(0x1c0200000);
	context.xnu.framebuffer.base = UINT64_C(0xfcc2f000);
	context.xnu.framebuffer.stride = 4992;
	context.xnu.framebuffer.width = 1220;
	context.xnu.framebuffer.height = 2712;
	context.xnu.framebuffer.depth = 32;
	context.xnu.window = window;
	context.xnu.window_size = WINDOW_SIZE;
	CHECK(duchamp_resident_init(&loader, staging, payload_size, result_buffer,
	    sizeof(result_buffer), 0x20261106) == 0 &&
	    duchamp_resident_begin(&loader, payload_size) == 0 &&
	    duchamp_resident_receive(&loader, 0, source, payload_size) == 0);
	CHECK(duchamp_resident_run(&loader, &ops, &context) ==
	    DUCHAMP_RESIDENT_PREPARE && context.enter_calls == 0 &&
	    context.xnu.prepare_result == DUCHAMP_GUARD_OCCUPIED);
	CHECK(all_value(window, 0x10000, 0x5a));

	printf("resident-xnu-tests: PASS checks=%u entry=%#llx segments=%u\n",
	    checks, (unsigned long long)completed_entry, completed_segments);
	munmap(window, WINDOW_SIZE);
	free(staging);
	free(source);
	free(bad_fdt);
	free(fdt);
	return 0;
}
