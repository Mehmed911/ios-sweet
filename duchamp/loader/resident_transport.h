#ifndef DUCHAMP_RESIDENT_TRANSPORT_H
#define DUCHAMP_RESIDENT_TRANSPORT_H

#include "resident_protocol.h"

#define DUCHAMP_RESIDENT_TRANSPORT_VERSION 1u
#define DUCHAMP_RESIDENT_SOURCE_VERSION 1u

enum duchamp_resident_source_flag {
	DUCHAMP_RESIDENT_SOURCE_IMMUTABLE = 1u << 0,
	DUCHAMP_RESIDENT_SOURCE_LK_PRELOADED = 1u << 1,
};

enum duchamp_resident_transport_state {
	DUCHAMP_TRANSPORT_NEW = 0,
	DUCHAMP_TRANSPORT_TRANSFERRING = 1,
	DUCHAMP_TRANSPORT_COMPLETE = 2,
	DUCHAMP_TRANSPORT_FAILED = 3,
};

enum duchamp_resident_transport_result {
	DUCHAMP_TRANSPORT_OK = 0,
	DUCHAMP_TRANSPORT_ARGUMENT = 1,
	DUCHAMP_TRANSPORT_VERSION = 2,
	DUCHAMP_TRANSPORT_CAPABILITY = 3,
	DUCHAMP_TRANSPORT_GENERATION = 4,
	DUCHAMP_TRANSPORT_RANGE = 5,
	DUCHAMP_TRANSPORT_SOURCE = 6,
	DUCHAMP_TRANSPORT_SHORT_READ = 7,
	DUCHAMP_TRANSPORT_RECEIPT = 8,
	DUCHAMP_TRANSPORT_PROTOCOL = 9,
	DUCHAMP_TRANSPORT_RELOAD_REQUIRED = 10,
};

struct duchamp_resident_source_description {
	uint32_t version;
	uint32_t flags;
	uint64_t generation;
	uint64_t payload_size;
	uint64_t payload_receipt;
	size_t maximum_read;
	const void *backing;
	size_t backing_size;
};

struct duchamp_resident_source_ops {
	unsigned (*describe)(void *context,
	    struct duchamp_resident_source_description *description);
	unsigned (*read)(void *context, uint64_t offset, void *buffer,
	    size_t requested, size_t *actual);
};

struct duchamp_resident_transport {
	uint32_t version;
	uint32_t state;
	uint32_t last_error;
	uint32_t detail;
	uint64_t generation;
	uint64_t bytes_read;
	struct duchamp_resident_loader *loader;
	const struct duchamp_resident_ops *run_ops;
	void *run_context;
	const struct duchamp_resident_source_ops *source_ops;
	void *source_context;
	unsigned char *scratch;
	size_t scratch_capacity;
};

struct duchamp_resident_transport_status {
	uint32_t version;
	uint32_t state;
	uint32_t last_error;
	uint32_t detail;
	uint64_t generation;
	uint64_t bytes_read;
};

unsigned duchamp_resident_transport_init(
	struct duchamp_resident_transport *transport,
	struct duchamp_resident_loader *loader,
	const struct duchamp_resident_ops *run_ops, void *run_context,
	const struct duchamp_resident_source_ops *source_ops,
	void *source_context, void *scratch, size_t scratch_capacity);
unsigned duchamp_resident_transport_run(
	struct duchamp_resident_transport *transport);
unsigned duchamp_resident_transport_get_status(
	const struct duchamp_resident_transport *transport,
	struct duchamp_resident_transport_status *status);

#endif
