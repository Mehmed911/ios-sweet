#ifndef DUCHAMP_RESIDENT_PROTOCOL_H
#define DUCHAMP_RESIDENT_PROTOCOL_H

#include <stddef.h>
#include <stdint.h>

#define DUCHAMP_RESIDENT_PROTOCOL_VERSION 1u

enum duchamp_resident_state {
	DUCHAMP_RESIDENT_EMPTY = 0,
	DUCHAMP_RESIDENT_RECEIVING = 1,
	DUCHAMP_RESIDENT_READY = 2,
	DUCHAMP_RESIDENT_RUNNING = 3,
	DUCHAMP_RESIDENT_RETURNED = 4,
	DUCHAMP_RESIDENT_FAILED = 5,
};

enum duchamp_resident_result {
	DUCHAMP_RESIDENT_OK = 0,
	DUCHAMP_RESIDENT_ARGUMENT = 1,
	DUCHAMP_RESIDENT_STATE = 2,
	DUCHAMP_RESIDENT_CAPACITY = 3,
	DUCHAMP_RESIDENT_ORDER = 4,
	DUCHAMP_RESIDENT_INCOMPLETE = 5,
	DUCHAMP_RESIDENT_RECEIPT = 6,
	DUCHAMP_RESIDENT_PREPARE = 7,
	DUCHAMP_RESIDENT_UNEXPECTED_RETURN = 8,
	DUCHAMP_RESIDENT_RESULT_RANGE = 9,
	DUCHAMP_RESIDENT_RELOAD_REQUIRED = 10,
};

struct duchamp_resident_target {
	uint64_t entry;
	uint64_t boot_args;
};

struct duchamp_resident_loader;

struct duchamp_resident_ops {
	unsigned (*prepare)(void *context, const void *payload,
	    size_t payload_size, struct duchamp_resident_target *target);
	unsigned (*enter)(void *context,
	    const struct duchamp_resident_target *target);
};

struct duchamp_resident_loader {
	uint32_t version;
	uint32_t state;
	uint32_t last_error;
	uint32_t detail;
	uint64_t generation;
	uint64_t payload_receipt;
	uint64_t result_receipt;
	uint64_t result_code;
	uint64_t run_count;
	unsigned char *staging;
	size_t staging_capacity;
	size_t expected_size;
	size_t received_size;
	unsigned char *result;
	size_t result_capacity;
	size_t result_size;
};

struct duchamp_resident_status {
	uint32_t version;
	uint32_t state;
	uint32_t last_error;
	uint32_t detail;
	uint64_t generation;
	uint64_t payload_receipt;
	uint64_t result_receipt;
	uint64_t result_code;
	uint64_t run_count;
	size_t staging_capacity;
	size_t expected_size;
	size_t received_size;
	size_t result_size;
};

struct duchamp_resident_result_view {
	uint64_t code;
	uint64_t receipt;
	const void *data;
	size_t size;
};

/* Mutation receipt used by the staging protocol; it is not authentication. */
uint64_t duchamp_resident_receipt(const void *data, size_t size);

unsigned duchamp_resident_init(struct duchamp_resident_loader *loader,
	void *staging, size_t staging_capacity,
	void *result, size_t result_capacity, uint64_t generation);
unsigned duchamp_resident_begin(struct duchamp_resident_loader *loader,
	size_t payload_size);
unsigned duchamp_resident_receive(struct duchamp_resident_loader *loader,
	size_t offset, const void *data, size_t size);
unsigned duchamp_resident_run(struct duchamp_resident_loader *loader,
	const struct duchamp_resident_ops *ops, void *context);
unsigned duchamp_resident_complete(struct duchamp_resident_loader *loader,
	uint64_t code, const void *result, size_t result_size);
unsigned duchamp_resident_get_status(const struct duchamp_resident_loader *loader,
	struct duchamp_resident_status *status);
unsigned duchamp_resident_get_result(const struct duchamp_resident_loader *loader,
	struct duchamp_resident_result_view *result);

#endif
