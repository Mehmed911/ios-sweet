#include "resident_transport.h"

static int
add_ok(uintptr_t start, size_t size, uintptr_t *end)
{
	*end = start + size;
	return *end >= start;
}

static int
overlap(const void *first_pointer, size_t first_size,
	const void *second_pointer, size_t second_size)
{
	uintptr_t first = (uintptr_t)first_pointer;
	uintptr_t second = (uintptr_t)second_pointer;
	uintptr_t first_end, second_end;
	if (first_size == 0 || second_size == 0) {
		return 0;
	}
	if (!add_ok(first, first_size, &first_end) ||
	    !add_ok(second, second_size, &second_end)) {
		return 1;
	}
	return first < second_end && second < first_end;
}

static int
valid(const struct duchamp_resident_transport *transport)
{
	return transport != NULL &&
	    transport->version == DUCHAMP_RESIDENT_TRANSPORT_VERSION &&
	    transport->state <= DUCHAMP_TRANSPORT_FAILED &&
	    transport->generation != 0 && transport->loader != NULL &&
	    transport->run_ops != NULL &&
	    transport->run_ops->prepare != NULL &&
	    transport->run_ops->enter != NULL &&
	    transport->run_context != NULL &&
	    transport->source_ops != NULL &&
	    transport->source_ops->describe != NULL &&
	    transport->source_ops->read != NULL &&
	    transport->source_context != NULL && transport->scratch != NULL &&
	    transport->scratch_capacity != 0 &&
	    !overlap(transport->scratch, transport->scratch_capacity,
	    transport->loader->staging, transport->loader->staging_capacity) &&
	    !overlap(transport->scratch, transport->scratch_capacity,
	    transport->loader->result, transport->loader->result_capacity);
}

static unsigned
fail(struct duchamp_resident_transport *transport, unsigned error,
	unsigned detail)
{
	if (transport != NULL) {
		transport->state = DUCHAMP_TRANSPORT_FAILED;
		transport->last_error = error;
		transport->detail = detail;
	}
	return error;
}

unsigned
duchamp_resident_transport_init(
	struct duchamp_resident_transport *transport,
	struct duchamp_resident_loader *loader,
	const struct duchamp_resident_ops *run_ops, void *run_context,
	const struct duchamp_resident_source_ops *source_ops,
	void *source_context, void *scratch, size_t scratch_capacity)
{
	struct duchamp_resident_status status;

	if (transport == NULL) {
		return DUCHAMP_TRANSPORT_ARGUMENT;
	}
	transport->version = 0;
	transport->state = DUCHAMP_TRANSPORT_FAILED;
	transport->last_error = DUCHAMP_TRANSPORT_ARGUMENT;
	transport->detail = 0;
	transport->generation = 0;
	transport->bytes_read = 0;
	transport->loader = loader;
	transport->run_ops = run_ops;
	transport->run_context = run_context;
	transport->source_ops = source_ops;
	transport->source_context = source_context;
	transport->scratch = scratch;
	transport->scratch_capacity = scratch_capacity;
	if (loader == NULL || run_ops == NULL || run_ops->prepare == NULL ||
	    run_ops->enter == NULL || run_context == NULL || source_ops == NULL ||
	    source_ops->describe == NULL || source_ops->read == NULL ||
	    source_context == NULL || scratch == NULL || scratch_capacity == 0 ||
	    duchamp_resident_get_status(loader, &status) != DUCHAMP_RESIDENT_OK ||
	    status.state != DUCHAMP_RESIDENT_EMPTY ||
	    overlap(scratch, scratch_capacity, loader->staging,
	    loader->staging_capacity) ||
	    overlap(scratch, scratch_capacity, loader->result,
	    loader->result_capacity)) {
		return DUCHAMP_TRANSPORT_ARGUMENT;
	}
	transport->version = DUCHAMP_RESIDENT_TRANSPORT_VERSION;
	transport->state = DUCHAMP_TRANSPORT_NEW;
	transport->last_error = DUCHAMP_TRANSPORT_OK;
	transport->generation = status.generation;
	return DUCHAMP_TRANSPORT_OK;
}

unsigned
duchamp_resident_transport_run(struct duchamp_resident_transport *transport)
{
	struct duchamp_resident_source_description description;
	struct duchamp_resident_status status;
	uint64_t offset = 0;
	unsigned result;

	if (!valid(transport)) {
		return DUCHAMP_TRANSPORT_ARGUMENT;
	}
	if (transport->state == DUCHAMP_TRANSPORT_COMPLETE ||
	    transport->state == DUCHAMP_TRANSPORT_FAILED) {
		return DUCHAMP_TRANSPORT_RELOAD_REQUIRED;
	}
	if (transport->state != DUCHAMP_TRANSPORT_NEW) {
		return fail(transport, DUCHAMP_TRANSPORT_ARGUMENT, 0);
	}
	description.version = 0;
	description.flags = 0;
	description.generation = 0;
	description.payload_size = 0;
	description.payload_receipt = 0;
	description.maximum_read = 0;
	description.backing = NULL;
	description.backing_size = 0;
	result = transport->source_ops->describe(transport->source_context,
	    &description);
	if (result != 0) {
		return fail(transport, DUCHAMP_TRANSPORT_SOURCE, result);
	}
	if (description.version != DUCHAMP_RESIDENT_SOURCE_VERSION) {
		return fail(transport, DUCHAMP_TRANSPORT_VERSION,
		    description.version);
	}
	if (description.flags != (DUCHAMP_RESIDENT_SOURCE_IMMUTABLE |
	    DUCHAMP_RESIDENT_SOURCE_LK_PRELOADED)) {
		return fail(transport, DUCHAMP_TRANSPORT_CAPABILITY,
		    description.flags);
	}
	if (description.generation != transport->generation) {
		return fail(transport, DUCHAMP_TRANSPORT_GENERATION, 0);
	}
	if (description.payload_size == 0 ||
	    description.payload_size > SIZE_MAX ||
	    description.maximum_read == 0 ||
	    description.payload_receipt == 0 || description.backing == NULL ||
	    description.backing_size < description.payload_size ||
	    overlap(description.backing, description.backing_size,
	    transport->scratch, transport->scratch_capacity) ||
	    overlap(description.backing, description.backing_size,
	    transport->loader->staging,
	    transport->loader->staging_capacity) ||
	    overlap(description.backing, description.backing_size,
	    transport->loader->result, transport->loader->result_capacity)) {
		return fail(transport, DUCHAMP_TRANSPORT_RANGE, 0);
	}
	result = duchamp_resident_get_status(transport->loader, &status);
	if (result != DUCHAMP_RESIDENT_OK ||
	    description.payload_size > status.staging_capacity) {
		return fail(transport, DUCHAMP_TRANSPORT_RANGE, result);
	}
	result = duchamp_resident_begin(transport->loader,
	    (size_t)description.payload_size);
	if (result != DUCHAMP_RESIDENT_OK) {
		return fail(transport, DUCHAMP_TRANSPORT_PROTOCOL, result);
	}
	transport->state = DUCHAMP_TRANSPORT_TRANSFERRING;
	while (offset < description.payload_size) {
		uint64_t remaining = description.payload_size - offset;
		size_t requested = transport->scratch_capacity;
		size_t actual = 0;
		if (requested > description.maximum_read) {
			requested = description.maximum_read;
		}
		if ((uint64_t)requested > remaining) {
			requested = (size_t)remaining;
		}
		result = transport->source_ops->read(transport->source_context,
		    offset, transport->scratch, requested, &actual);
		if (result != 0) {
			return fail(transport, DUCHAMP_TRANSPORT_SOURCE, result);
		}
		if (actual != requested) {
			return fail(transport, DUCHAMP_TRANSPORT_SHORT_READ,
			    (unsigned)actual);
		}
		result = duchamp_resident_receive(transport->loader,
		    (size_t)offset, transport->scratch, actual);
		if (result != DUCHAMP_RESIDENT_OK) {
			return fail(transport, DUCHAMP_TRANSPORT_PROTOCOL, result);
		}
		offset += actual;
		transport->bytes_read = offset;
	}
	result = duchamp_resident_get_status(transport->loader, &status);
	if (result != DUCHAMP_RESIDENT_OK ||
	    status.state != DUCHAMP_RESIDENT_READY ||
	    status.payload_receipt != description.payload_receipt) {
		return fail(transport, DUCHAMP_TRANSPORT_RECEIPT, result);
	}
	result = duchamp_resident_run(transport->loader, transport->run_ops,
	    transport->run_context);
	if (result != DUCHAMP_RESIDENT_OK) {
		return fail(transport, DUCHAMP_TRANSPORT_PROTOCOL, result);
	}
	transport->state = DUCHAMP_TRANSPORT_COMPLETE;
	transport->last_error = DUCHAMP_TRANSPORT_OK;
	transport->detail = 0;
	return DUCHAMP_TRANSPORT_OK;
}

unsigned
duchamp_resident_transport_get_status(
	const struct duchamp_resident_transport *transport,
	struct duchamp_resident_transport_status *status)
{
	if (!valid(transport) || status == NULL) {
		return DUCHAMP_TRANSPORT_ARGUMENT;
	}
	status->version = transport->version;
	status->state = transport->state;
	status->last_error = transport->last_error;
	status->detail = transport->detail;
	status->generation = transport->generation;
	status->bytes_read = transport->bytes_read;
	return DUCHAMP_TRANSPORT_OK;
}
