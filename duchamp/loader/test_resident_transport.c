#include <stdint.h>
#include <stdio.h>
#include <string.h>

#include "mt6897_lk_transport.h"

struct callbacks {
	struct duchamp_resident_loader *loader;
	unsigned prepare_calls;
	unsigned enter_calls;
};

struct artificial_source {
	const unsigned char *payload;
	size_t size;
	uint64_t generation;
	unsigned flags;
	unsigned mode;
	unsigned describe_calls;
	unsigned read_calls;
};

static unsigned
prepare(void *context_pointer, const void *payload, size_t payload_size,
	struct duchamp_resident_target *target)
{
	struct callbacks *context = context_pointer;
	const unsigned char *bytes = payload;
	context->prepare_calls++;
	if (payload_size != 8 || bytes[0] != 'S' || bytes[7] != 'U') {
		return 1;
	}
	target->entry = UINT64_C(0x1c1480488);
	target->boot_args = UINT64_C(0x1c256c000);
	return 0;
}

static unsigned
enter(void *context_pointer, const struct duchamp_resident_target *target)
{
	static const unsigned char result[4] = {'P', 'A', 'S', 'S'};
	struct callbacks *context = context_pointer;
	context->enter_calls++;
	if (target->entry != UINT64_C(0x1c1480488) ||
	    target->boot_args != UINT64_C(0x1c256c000)) {
		return 1;
	}
	return duchamp_resident_complete(context->loader, 42, result,
	    sizeof(result));
}

static void
put_le32(unsigned char *bytes, uint32_t value)
{
	unsigned index;
	for (index = 0; index < 4; index++) {
		bytes[index] = (unsigned char)(value >> (index * 8));
	}
}

static void
put_le64(unsigned char *bytes, uint64_t value)
{
	unsigned index;
	for (index = 0; index < 8; index++) {
		bytes[index] = (unsigned char)(value >> (index * 8));
	}
}

static void
make_capsule(unsigned char *capsule, const unsigned char *payload,
	size_t payload_size, uint64_t generation)
{
	memset(capsule, 0, DUCHAMP_MT6897_LK_CAPSULE_HEADER_SIZE + payload_size);
	memcpy(capsule, "DUCHLKR1", 8);
	put_le32(capsule + 8, DUCHAMP_MT6897_LK_CAPSULE_VERSION);
	put_le32(capsule + 12, DUCHAMP_MT6897_LK_CAPSULE_HEADER_SIZE);
	put_le64(capsule + 16,
	    DUCHAMP_MT6897_LK_CAPSULE_HEADER_SIZE + payload_size);
	put_le64(capsule + 24, generation);
	put_le64(capsule + 32, DUCHAMP_MT6897_LK_CAPSULE_HEADER_SIZE);
	put_le64(capsule + 40, payload_size);
	put_le64(capsule + 48,
	    duchamp_resident_receipt(payload, payload_size));
	put_le64(capsule + 56, DUCHAMP_MT6897_LK_CAPSULE_FLAG_IMMUTABLE);
	memcpy(capsule + DUCHAMP_MT6897_LK_CAPSULE_HEADER_SIZE, payload,
	    payload_size);
}

static unsigned
artificial_describe(void *context_pointer,
	struct duchamp_resident_source_description *description)
{
	struct artificial_source *source = context_pointer;
	source->describe_calls++;
	description->version = DUCHAMP_RESIDENT_SOURCE_VERSION;
	description->flags = source->flags;
	description->generation = source->generation;
	description->payload_size = source->size;
	description->payload_receipt = duchamp_resident_receipt(source->payload,
	    source->size);
	description->maximum_read = 4;
	description->backing = source->payload;
	description->backing_size = source->size;
	return 0;
}

static unsigned
artificial_read(void *context_pointer, uint64_t offset, void *buffer,
	size_t requested, size_t *actual)
{
	struct artificial_source *source = context_pointer;
	size_t index, returned = requested;
	source->read_calls++;
	if (source->mode == 1 && requested != 0) {
		returned--;
	}
	for (index = 0; index < returned; index++) {
		((unsigned char *)buffer)[index] = source->payload[offset + index];
	}
	if (source->mode == 2 && returned != 0) {
		((unsigned char *)buffer)[0] ^= 0xff;
	}
	*actual = returned;
	return 0;
}

static const struct duchamp_resident_source_ops artificial_ops = {
	artificial_describe,
	artificial_read,
};

#define CHECK(condition) do { if (!(condition)) { \
	fprintf(stderr, "resident transport check failed at line %d\n", __LINE__); \
	return 1; } checks++; } while (0)

int
main(void)
{
	static const unsigned char payload[8] = {
	    'S', 'W', 'E', 'E', 'T', 'X', 'N', 'U'
	};
	const struct duchamp_resident_ops run_ops = {prepare, enter};
	struct duchamp_resident_loader loader;
	struct duchamp_resident_transport transport;
	struct duchamp_resident_transport_status transport_status;
	struct duchamp_resident_status loader_status;
	struct duchamp_resident_result_view result_view;
	struct duchamp_mt6897_lk_source source;
	struct callbacks callbacks;
	struct artificial_source artificial;
	unsigned char capsule[DUCHAMP_MT6897_LK_CAPSULE_HEADER_SIZE +
	    sizeof(payload)];
	unsigned char staging[32], result[32], scratch[3];
	unsigned char alias[128];
	unsigned checks = 0;

	make_capsule(capsule, payload, sizeof(payload), 7);
	memset(&callbacks, 0, sizeof(callbacks));
	CHECK(duchamp_resident_init(&loader, staging, sizeof(staging), result,
	    sizeof(result), 7) == DUCHAMP_RESIDENT_OK);
	callbacks.loader = &loader;
	CHECK(duchamp_mt6897_lk_source_init(&source, capsule,
	    sizeof(capsule)) == DUCHAMP_TRANSPORT_OK);
	CHECK(duchamp_resident_transport_init(&transport, &loader, &run_ops,
	    &callbacks, &duchamp_mt6897_lk_source_ops, &source, scratch,
	    sizeof(scratch)) == DUCHAMP_TRANSPORT_OK);
	CHECK(duchamp_resident_transport_run(&transport) ==
	    DUCHAMP_TRANSPORT_OK);
	CHECK(source.described == 1 && source.read_calls == 3 &&
	    source.read_offset == sizeof(payload));
	CHECK(callbacks.prepare_calls == 1 && callbacks.enter_calls == 1);
	CHECK(duchamp_resident_transport_get_status(&transport,
	    &transport_status) == DUCHAMP_TRANSPORT_OK &&
	    transport_status.state == DUCHAMP_TRANSPORT_COMPLETE &&
	    transport_status.bytes_read == sizeof(payload));
	CHECK(duchamp_resident_get_status(&loader, &loader_status) == 0 &&
	    loader_status.state == DUCHAMP_RESIDENT_RETURNED &&
	    loader_status.result_code == 42);
	CHECK(duchamp_resident_get_result(&loader, &result_view) == 0 &&
	    result_view.size == 4 &&
	    memcmp(result_view.data, "PASS", 4) == 0);
	CHECK(duchamp_resident_transport_run(&transport) ==
	    DUCHAMP_TRANSPORT_RELOAD_REQUIRED && source.read_calls == 3 &&
	    callbacks.enter_calls == 1);

	/* A stale generation fails before begin or any source read. */
	make_capsule(capsule, payload, sizeof(payload), 8);
	memset(&callbacks, 0, sizeof(callbacks));
	CHECK(duchamp_resident_init(&loader, staging, sizeof(staging), result,
	    sizeof(result), 7) == 0);
	callbacks.loader = &loader;
	CHECK(duchamp_mt6897_lk_source_init(&source, capsule,
	    sizeof(capsule)) == 0);
	CHECK(duchamp_resident_transport_init(&transport, &loader, &run_ops,
	    &callbacks, &duchamp_mt6897_lk_source_ops, &source, scratch,
	    sizeof(scratch)) == 0);
	CHECK(duchamp_resident_transport_run(&transport) ==
	    DUCHAMP_TRANSPORT_GENERATION && source.read_calls == 0 &&
	    loader.state == DUCHAMP_RESIDENT_EMPTY);
	CHECK(duchamp_resident_transport_run(&transport) ==
	    DUCHAMP_TRANSPORT_RELOAD_REQUIRED);

	/* A corrupt receipt is rejected by the LK source before staging. */
	make_capsule(capsule, payload, sizeof(payload), 7);
	capsule[48] ^= 1;
	CHECK(duchamp_resident_init(&loader, staging, sizeof(staging), result,
	    sizeof(result), 7) == 0);
	CHECK(duchamp_mt6897_lk_source_init(&source, capsule,
	    sizeof(capsule)) == 0);
	CHECK(duchamp_resident_transport_init(&transport, &loader, &run_ops,
	    &callbacks, &duchamp_mt6897_lk_source_ops, &source, scratch,
	    sizeof(scratch)) == 0);
	CHECK(duchamp_resident_transport_run(&transport) ==
	    DUCHAMP_TRANSPORT_SOURCE &&
	    transport.detail == DUCHAMP_TRANSPORT_RECEIPT &&
	    loader.state == DUCHAMP_RESIDENT_EMPTY);

	/* A capsule cannot claim bytes that LK did not preload. */
	make_capsule(capsule, payload, sizeof(payload), 7);
	CHECK(duchamp_resident_init(&loader, staging, sizeof(staging), result,
	    sizeof(result), 7) == 0);
	CHECK(duchamp_mt6897_lk_source_init(&source, capsule,
	    sizeof(capsule) - 1) == 0);
	CHECK(duchamp_resident_transport_init(&transport, &loader, &run_ops,
	    &callbacks, &duchamp_mt6897_lk_source_ops, &source, scratch,
	    sizeof(scratch)) == 0);
	CHECK(duchamp_resident_transport_run(&transport) ==
	    DUCHAMP_TRANSPORT_SOURCE && loader.state == DUCHAMP_RESIDENT_EMPTY);

	/* The transfer scratch area may not alias staging or result memory. */
	CHECK(duchamp_resident_init(&loader, staging, sizeof(staging), result,
	    sizeof(result), 7) == 0);
	CHECK(duchamp_mt6897_lk_source_init(&source, capsule,
	    sizeof(capsule)) == 0);
	CHECK(duchamp_resident_transport_init(&transport, &loader, &run_ops,
	    &callbacks, &duchamp_mt6897_lk_source_ops, &source, staging + 1,
	    3) == DUCHAMP_TRANSPORT_ARGUMENT);

	/* LK-preloaded capsule bytes must be disjoint from all mutable buffers. */
	make_capsule(alias, payload, sizeof(payload), 7);
	CHECK(duchamp_resident_init(&loader, alias, sizeof(alias), result,
	    sizeof(result), 7) == 0);
	CHECK(duchamp_mt6897_lk_source_init(&source, alias,
	    DUCHAMP_MT6897_LK_CAPSULE_HEADER_SIZE + sizeof(payload)) == 0);
	CHECK(duchamp_resident_transport_init(&transport, &loader, &run_ops,
	    &callbacks, &duchamp_mt6897_lk_source_ops, &source, scratch,
	    sizeof(scratch)) == 0);
	CHECK(duchamp_resident_transport_run(&transport) ==
	    DUCHAMP_TRANSPORT_RANGE && loader.state == DUCHAMP_RESIDENT_EMPTY &&
	    source.read_calls == 0);

	/* A short provider read terminally closes this transport instance. */
	memset(&artificial, 0, sizeof(artificial));
	artificial.payload = payload;
	artificial.size = sizeof(payload);
	artificial.generation = 7;
	artificial.flags = DUCHAMP_RESIDENT_SOURCE_IMMUTABLE |
	    DUCHAMP_RESIDENT_SOURCE_LK_PRELOADED;
	artificial.mode = 1;
	CHECK(duchamp_resident_init(&loader, staging, sizeof(staging), result,
	    sizeof(result), 7) == 0);
	CHECK(duchamp_resident_transport_init(&transport, &loader, &run_ops,
	    &callbacks, &artificial_ops, &artificial, scratch,
	    sizeof(scratch)) == 0);
	CHECK(duchamp_resident_transport_run(&transport) ==
	    DUCHAMP_TRANSPORT_SHORT_READ && loader.state ==
	    DUCHAMP_RESIDENT_RECEIVING && callbacks.enter_calls == 0);
	CHECK(duchamp_resident_transport_run(&transport) ==
	    DUCHAMP_TRANSPORT_RELOAD_REQUIRED && artificial.read_calls == 1);

	/* Changed bytes are caught again after the complete transfer. */
	memset(&artificial, 0, sizeof(artificial));
	artificial.payload = payload;
	artificial.size = sizeof(payload);
	artificial.generation = 7;
	artificial.flags = DUCHAMP_RESIDENT_SOURCE_IMMUTABLE |
	    DUCHAMP_RESIDENT_SOURCE_LK_PRELOADED;
	artificial.mode = 2;
	CHECK(duchamp_resident_init(&loader, staging, sizeof(staging), result,
	    sizeof(result), 7) == 0);
	CHECK(duchamp_resident_transport_init(&transport, &loader, &run_ops,
	    &callbacks, &artificial_ops, &artificial, scratch,
	    sizeof(scratch)) == 0);
	CHECK(duchamp_resident_transport_run(&transport) ==
	    DUCHAMP_TRANSPORT_RECEIPT && callbacks.enter_calls == 0);

	/* Unknown source capabilities are never silently accepted. */
	memset(&artificial, 0, sizeof(artificial));
	artificial.payload = payload;
	artificial.size = sizeof(payload);
	artificial.generation = 7;
	artificial.flags = DUCHAMP_RESIDENT_SOURCE_IMMUTABLE | (1u << 7);
	CHECK(duchamp_resident_init(&loader, staging, sizeof(staging), result,
	    sizeof(result), 7) == 0);
	CHECK(duchamp_resident_transport_init(&transport, &loader, &run_ops,
	    &callbacks, &artificial_ops, &artificial, scratch,
	    sizeof(scratch)) == 0);
	CHECK(duchamp_resident_transport_run(&transport) ==
	    DUCHAMP_TRANSPORT_CAPABILITY && artificial.read_calls == 0 &&
	    loader.state == DUCHAMP_RESIDENT_EMPTY);

	printf("resident-transport-tests: PASS checks=%u\n", checks);
	return 0;
}
