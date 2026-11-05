#include "mt6897_lk_transport.h"

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

static int
magic_ok(const unsigned char *bytes)
{
	static const unsigned char magic[8] = {
	    'D', 'U', 'C', 'H', 'L', 'K', 'R', '1'
	};
	unsigned index;
	for (index = 0; index < sizeof(magic); index++) {
		if (bytes[index] != magic[index]) {
			return 0;
		}
	}
	return 1;
}

unsigned
duchamp_mt6897_lk_source_init(struct duchamp_mt6897_lk_source *source,
	const void *capsule, size_t capsule_size)
{
	if (source == NULL) {
		return DUCHAMP_TRANSPORT_ARGUMENT;
	}
	source->capsule = capsule;
	source->capsule_size = capsule_size;
	source->payload = NULL;
	source->payload_size = 0;
	source->generation = 0;
	source->payload_receipt = 0;
	source->described = 0;
	source->read_offset = 0;
	source->read_calls = 0;
	if (capsule == NULL || capsule_size <
	    DUCHAMP_MT6897_LK_CAPSULE_HEADER_SIZE) {
		return DUCHAMP_TRANSPORT_ARGUMENT;
	}
	return DUCHAMP_TRANSPORT_OK;
}

unsigned
duchamp_mt6897_lk_source_describe(
	struct duchamp_mt6897_lk_source *source,
	struct duchamp_resident_source_description *description)
{
	const unsigned char *header;
	uint64_t total_size, generation, payload_offset, payload_size;
	uint64_t payload_receipt, flags;

	if (source == NULL || description == NULL || source->capsule == NULL ||
	    source->capsule_size < DUCHAMP_MT6897_LK_CAPSULE_HEADER_SIZE ||
	    source->read_offset != 0 || source->read_calls != 0) {
		return DUCHAMP_TRANSPORT_ARGUMENT;
	}
	header = source->capsule;
	total_size = le64(header + 16);
	generation = le64(header + 24);
	payload_offset = le64(header + 32);
	payload_size = le64(header + 40);
	payload_receipt = le64(header + 48);
	flags = le64(header + 56);
	if (!magic_ok(header) ||
	    le32(header + 8) != DUCHAMP_MT6897_LK_CAPSULE_VERSION ||
	    le32(header + 12) != DUCHAMP_MT6897_LK_CAPSULE_HEADER_SIZE ||
	    total_size != source->capsule_size || generation == 0 ||
	    payload_offset != DUCHAMP_MT6897_LK_CAPSULE_HEADER_SIZE ||
	    payload_size == 0 || payload_size > SIZE_MAX ||
	    payload_size != total_size - payload_offset ||
	    flags != DUCHAMP_MT6897_LK_CAPSULE_FLAG_IMMUTABLE) {
		return DUCHAMP_TRANSPORT_RANGE;
	}
	if (duchamp_resident_receipt(header + payload_offset,
	    (size_t)payload_size) != payload_receipt || payload_receipt == 0) {
		return DUCHAMP_TRANSPORT_RECEIPT;
	}
	source->payload = header + payload_offset;
	source->payload_size = (size_t)payload_size;
	source->generation = generation;
	source->payload_receipt = payload_receipt;
	source->described = 1;
	description->version = DUCHAMP_RESIDENT_SOURCE_VERSION;
	description->flags = DUCHAMP_RESIDENT_SOURCE_IMMUTABLE |
	    DUCHAMP_RESIDENT_SOURCE_LK_PRELOADED;
	description->generation = generation;
	description->payload_size = payload_size;
	description->payload_receipt = payload_receipt;
	description->maximum_read = DUCHAMP_MT6897_LK_MAX_READ;
	description->backing = source->capsule;
	description->backing_size = source->capsule_size;
	return DUCHAMP_TRANSPORT_OK;
}

static unsigned
describe(void *context_pointer,
	struct duchamp_resident_source_description *description)
{
	return duchamp_mt6897_lk_source_describe(context_pointer, description);
}

static unsigned
read_payload(void *context_pointer, uint64_t offset, void *buffer,
	size_t requested, size_t *actual)
{
	struct duchamp_mt6897_lk_source *source = context_pointer;
	unsigned char *destination = buffer;
	size_t index;

	if (actual != NULL) {
		*actual = 0;
	}
	if (source == NULL || buffer == NULL || actual == NULL ||
	    source->described != 1 || requested == 0 ||
	    offset != source->read_offset || offset > source->payload_size ||
	    requested > source->payload_size - (size_t)offset) {
		return DUCHAMP_TRANSPORT_RANGE;
	}
	for (index = 0; index < requested; index++) {
		destination[index] = source->payload[(size_t)offset + index];
	}
	source->read_offset += requested;
	source->read_calls++;
	*actual = requested;
	return DUCHAMP_TRANSPORT_OK;
}

const struct duchamp_resident_source_ops duchamp_mt6897_lk_source_ops = {
	describe,
	read_payload,
};
