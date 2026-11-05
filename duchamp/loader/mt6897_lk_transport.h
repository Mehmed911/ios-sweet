#ifndef DUCHAMP_MT6897_LK_TRANSPORT_H
#define DUCHAMP_MT6897_LK_TRANSPORT_H

#include "resident_transport.h"

#define DUCHAMP_MT6897_LK_CAPSULE_VERSION 1u
#define DUCHAMP_MT6897_LK_CAPSULE_HEADER_SIZE 64u
#define DUCHAMP_MT6897_LK_CAPSULE_FLAG_IMMUTABLE UINT64_C(1)
#define DUCHAMP_MT6897_LK_MAX_READ (64u * 1024u)

struct duchamp_mt6897_lk_source {
	const unsigned char *capsule;
	size_t capsule_size;
	const unsigned char *payload;
	size_t payload_size;
	uint64_t generation;
	uint64_t payload_receipt;
	unsigned described;
	uint64_t read_offset;
	uint64_t read_calls;
};

unsigned duchamp_mt6897_lk_source_init(
	struct duchamp_mt6897_lk_source *source,
	const void *capsule, size_t capsule_size);
unsigned duchamp_mt6897_lk_source_describe(
	struct duchamp_mt6897_lk_source *source,
	struct duchamp_resident_source_description *description);

extern const struct duchamp_resident_source_ops
    duchamp_mt6897_lk_source_ops;

#endif
