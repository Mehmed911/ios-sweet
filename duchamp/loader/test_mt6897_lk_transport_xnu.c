#define _GNU_SOURCE
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>

#include "mt6897_lk_transport.h"
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
	    (length = ftell(file)) <= 0 || fseek(file, 0, SEEK_SET) != 0) {
		return NULL;
	}
	data = malloc((size_t)length);
	if (data == NULL ||
	    fread(data, 1, (size_t)length, file) != (size_t)length) {
		free(data);
		fclose(file);
		return NULL;
	}
	fclose(file);
	*size = (size_t)length;
	return data;
}

static uint32_t
le32(const unsigned char *bytes)
{
	return (uint32_t)bytes[0] | (uint32_t)bytes[1] << 8 |
	    (uint32_t)bytes[2] << 16 | (uint32_t)bytes[3] << 24;
}

static uint64_t
le64(const unsigned char *bytes)
{
	return (uint64_t)le32(bytes) | (uint64_t)le32(bytes + 4) << 32;
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
	static const char message[] = "LK-XNU-RETURN";
	struct test_context *context = context_pointer;
	context->enter_calls++;
	if (target->entry != context->xnu.completed_plan.entry ||
	    target->boot_args != context->xnu.completed_plan.boot_args.destination) {
		return 90;
	}
	return duchamp_resident_complete(context->loader, UINT64_C(0x4c4b584e),
	    message, sizeof(message) - 1);
}

#define CHECK(condition) do { if (!(condition)) { \
	fprintf(stderr, "LK transport XNU check failed at line %d\n", __LINE__); \
	return 1; } checks++; } while (0)

int
main(int argc, char **argv)
{
	const struct duchamp_resident_ops run_ops = {prepare, enter};
	struct duchamp_resident_loader loader;
	struct duchamp_resident_transport transport;
	struct duchamp_resident_transport_status transport_status;
	struct duchamp_resident_result_view view;
	struct duchamp_mt6897_lk_source source;
	struct duchamp_range occupied = {
	    UINT64_C(0x40200000), UINT64_C(0x200000)
	};
	struct test_context context;
	unsigned char *fdt, *capsule, *staging, *scratch, *window;
	unsigned char result_buffer[64];
	size_t fdt_size, capsule_size, payload_size;
	uint64_t generation;
	unsigned checks = 0;

	if (argc != 3) {
		return 2;
	}
	fdt = read_file(argv[1], &fdt_size);
	capsule = read_file(argv[2], &capsule_size);
	if (fdt == NULL || capsule == NULL ||
	    capsule_size <= DUCHAMP_MT6897_LK_CAPSULE_HEADER_SIZE) {
		return 2;
	}
	payload_size = capsule_size - DUCHAMP_MT6897_LK_CAPSULE_HEADER_SIZE;
	generation = le64(capsule + 24);
	staging = malloc(payload_size);
	scratch = malloc(DUCHAMP_MT6897_LK_MAX_READ);
	window = mmap(NULL, WINDOW_SIZE, PROT_READ | PROT_WRITE,
	    MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
	if (staging == NULL || scratch == NULL || window == MAP_FAILED) {
		return 2;
	}
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
	CHECK(duchamp_resident_init(&loader, staging, payload_size,
	    result_buffer, sizeof(result_buffer), generation) == 0);
	CHECK(duchamp_mt6897_lk_source_init(&source, capsule,
	    capsule_size) == 0);
	CHECK(duchamp_resident_transport_init(&transport, &loader, &run_ops,
	    &context, &duchamp_mt6897_lk_source_ops, &source, scratch,
	    DUCHAMP_MT6897_LK_MAX_READ) == 0);
	CHECK(duchamp_resident_transport_run(&transport) == 0);
	CHECK(context.prepare_calls == 1 && context.enter_calls == 1 &&
	    context.xnu.prepare_result == DUCHAMP_GUARD_OK);
	CHECK(source.read_offset == payload_size && source.read_calls != 0);
	CHECK(duchamp_resident_transport_get_status(&transport,
	    &transport_status) == 0 &&
	    transport_status.state == DUCHAMP_TRANSPORT_COMPLETE &&
	    transport_status.bytes_read == payload_size);
	CHECK(duchamp_resident_get_result(&loader, &view) == 0 &&
	    view.code == UINT64_C(0x4c4b584e) && view.size == 13 &&
	    memcmp(view.data, "LK-XNU-RETURN", 13) == 0);
	CHECK(duchamp_resident_transport_run(&transport) ==
	    DUCHAMP_TRANSPORT_RELOAD_REQUIRED && context.enter_calls == 1);

	printf("mt6897-lk-transport-xnu: PASS checks=%u entry=%#llx "
	    "segments=%u bytes=%zu reads=%llu\n", checks,
	    (unsigned long long)context.xnu.completed_plan.entry,
	    context.xnu.completed_plan.segment_count, payload_size,
	    (unsigned long long)source.read_calls);
	munmap(window, WINDOW_SIZE);
	free(scratch);
	free(staging);
	free(capsule);
	free(fdt);
	return 0;
}
