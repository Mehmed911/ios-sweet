#include "resident_protocol.h"

static void
zero_bytes(void *pointer, size_t size)
{
	unsigned char *bytes = pointer;
	size_t index;
	for (index = 0; index < size; index++) {
		bytes[index] = 0;
	}
}

static void
copy_bytes(void *destination_pointer, const void *source_pointer, size_t size)
{
	unsigned char *destination = destination_pointer;
	const unsigned char *source = source_pointer;
	size_t index;
	if (destination == source || size == 0) {
		return;
	}
	if ((uintptr_t)destination > (uintptr_t)source &&
	    (uintptr_t)destination - (uintptr_t)source < size) {
		for (index = size; index != 0; index--) {
			destination[index - 1] = source[index - 1];
		}
		return;
	}
	for (index = 0; index < size; index++) {
		destination[index] = source[index];
	}
}

uint64_t
duchamp_resident_receipt(const void *pointer, size_t size)
{
	const unsigned char *bytes = pointer;
	uint64_t value = UINT64_C(1469598103934665603);
	size_t index;
	if (pointer == NULL && size != 0) {
		return 0;
	}
	for (index = 0; index < size; index++) {
		value ^= bytes[index];
		value *= UINT64_C(1099511628211);
	}
	value ^= (uint64_t)size;
	value *= UINT64_C(1099511628211);
	return value;
}

static int
pointer_ranges_overlap(const void *first_pointer, size_t first_size,
	const void *second_pointer, size_t second_size)
{
	uintptr_t first = (uintptr_t)first_pointer;
	uintptr_t second = (uintptr_t)second_pointer;
	uintptr_t first_end, second_end;
	if (first_size > UINTPTR_MAX - first ||
	    second_size > UINTPTR_MAX - second) {
		return 1;
	}
	first_end = first + first_size;
	second_end = second + second_size;
	return first_size != 0 && second_size != 0 &&
	    first < second_end && second < first_end;
}

static int
valid(const struct duchamp_resident_loader *loader)
{
	return loader != NULL &&
	    loader->version == DUCHAMP_RESIDENT_PROTOCOL_VERSION &&
	    loader->generation != 0 && loader->staging != NULL &&
	    loader->staging_capacity != 0 && loader->result != NULL &&
	    loader->result_capacity != 0 &&
	    loader->state <= DUCHAMP_RESIDENT_FAILED &&
	    loader->expected_size <= loader->staging_capacity &&
	    loader->received_size <= loader->expected_size &&
	    loader->result_size <= loader->result_capacity &&
	    loader->run_count <= 1 &&
	    !pointer_ranges_overlap(loader->staging, loader->staging_capacity,
	    loader->result, loader->result_capacity);
}

static int
terminal(const struct duchamp_resident_loader *loader)
{
	return loader->state == DUCHAMP_RESIDENT_RETURNED ||
	    loader->state == DUCHAMP_RESIDENT_FAILED;
}

static unsigned
fail(struct duchamp_resident_loader *loader, unsigned error)
{
	if (loader != NULL) {
		loader->last_error = error;
		loader->state = DUCHAMP_RESIDENT_FAILED;
	}
	return error;
}

unsigned
duchamp_resident_init(struct duchamp_resident_loader *loader,
	void *staging, size_t staging_capacity,
	void *result_buffer, size_t result_capacity, uint64_t generation)
{
	if (loader == NULL) {
		return DUCHAMP_RESIDENT_ARGUMENT;
	}
	zero_bytes(loader, sizeof(*loader));
	if (staging == NULL || staging_capacity == 0 || result_buffer == NULL ||
	    result_capacity == 0 || generation == 0 ||
	    pointer_ranges_overlap(staging, staging_capacity,
	    result_buffer, result_capacity)) {
		return DUCHAMP_RESIDENT_ARGUMENT;
	}
	loader->version = DUCHAMP_RESIDENT_PROTOCOL_VERSION;
	loader->state = DUCHAMP_RESIDENT_EMPTY;
	loader->generation = generation;
	loader->staging = staging;
	loader->staging_capacity = staging_capacity;
	loader->result = result_buffer;
	loader->result_capacity = result_capacity;
	return DUCHAMP_RESIDENT_OK;
}

unsigned
duchamp_resident_begin(struct duchamp_resident_loader *loader,
	size_t payload_size)
{
	if (!valid(loader)) {
		return DUCHAMP_RESIDENT_ARGUMENT;
	}
	if (terminal(loader)) {
		return DUCHAMP_RESIDENT_RELOAD_REQUIRED;
	}
	if (loader->state != DUCHAMP_RESIDENT_EMPTY) {
		return fail(loader, DUCHAMP_RESIDENT_STATE);
	}
	if (payload_size == 0 || payload_size > loader->staging_capacity) {
		return fail(loader, DUCHAMP_RESIDENT_CAPACITY);
	}
	loader->expected_size = payload_size;
	loader->received_size = 0;
	loader->payload_receipt = 0;
	loader->result_receipt = 0;
	loader->result_code = 0;
	loader->result_size = 0;
	loader->detail = 0;
	loader->last_error = DUCHAMP_RESIDENT_OK;
	loader->state = DUCHAMP_RESIDENT_RECEIVING;
	return DUCHAMP_RESIDENT_OK;
}

unsigned
duchamp_resident_receive(struct duchamp_resident_loader *loader,
	size_t offset, const void *data, size_t size)
{
	if (!valid(loader)) {
		return DUCHAMP_RESIDENT_ARGUMENT;
	}
	if (terminal(loader)) {
		return DUCHAMP_RESIDENT_RELOAD_REQUIRED;
	}
	if (loader->state != DUCHAMP_RESIDENT_RECEIVING) {
		return fail(loader, DUCHAMP_RESIDENT_STATE);
	}
	if (offset != loader->received_size) {
		return fail(loader, DUCHAMP_RESIDENT_ORDER);
	}
	if (data == NULL || size == 0 ||
	    size > loader->expected_size - loader->received_size) {
		return fail(loader, DUCHAMP_RESIDENT_CAPACITY);
	}
	if (pointer_ranges_overlap(data, size, loader->staging,
	    loader->staging_capacity)) {
		return fail(loader, DUCHAMP_RESIDENT_ARGUMENT);
	}
	copy_bytes(loader->staging + loader->received_size, data, size);
	loader->received_size += size;
	if (loader->received_size == loader->expected_size) {
		loader->payload_receipt = duchamp_resident_receipt(loader->staging,
		    loader->expected_size);
		loader->state = DUCHAMP_RESIDENT_READY;
	}
	return DUCHAMP_RESIDENT_OK;
}

unsigned
duchamp_resident_run(struct duchamp_resident_loader *loader,
	const struct duchamp_resident_ops *ops, void *context)
{
	struct duchamp_resident_target target = {0, 0};
	unsigned result;

	if (!valid(loader)) {
		return DUCHAMP_RESIDENT_ARGUMENT;
	}
	if (terminal(loader)) {
		return DUCHAMP_RESIDENT_RELOAD_REQUIRED;
	}
	if (loader->state != DUCHAMP_RESIDENT_READY ||
	    loader->received_size != loader->expected_size) {
		return fail(loader, DUCHAMP_RESIDENT_INCOMPLETE);
	}
	if (ops == NULL || ops->prepare == NULL || ops->enter == NULL ||
	    context == NULL) {
		return fail(loader, DUCHAMP_RESIDENT_ARGUMENT);
	}
	if (duchamp_resident_receipt(loader->staging, loader->expected_size) !=
	    loader->payload_receipt) {
		return fail(loader, DUCHAMP_RESIDENT_RECEIPT);
	}
	result = ops->prepare(context, loader->staging,
	    loader->expected_size, &target);
	loader->detail = result;
	if (result != 0 || target.entry == 0 || target.boot_args == 0) {
		return fail(loader, DUCHAMP_RESIDENT_PREPARE);
	}
	loader->state = DUCHAMP_RESIDENT_RUNNING;
	loader->run_count++;
	result = ops->enter(context, &target);
	loader->detail = result;
	if (loader->state == DUCHAMP_RESIDENT_RETURNED && result == 0) {
		return DUCHAMP_RESIDENT_OK;
	}
	if (loader->state == DUCHAMP_RESIDENT_FAILED) {
		return loader->last_error;
	}
	return fail(loader, DUCHAMP_RESIDENT_UNEXPECTED_RETURN);
}

unsigned
duchamp_resident_complete(struct duchamp_resident_loader *loader,
	uint64_t code, const void *result_data, size_t result_size)
{
	if (!valid(loader)) {
		return DUCHAMP_RESIDENT_ARGUMENT;
	}
	if (loader->state != DUCHAMP_RESIDENT_RUNNING) {
		return terminal(loader) ? DUCHAMP_RESIDENT_RELOAD_REQUIRED :
		    fail(loader, DUCHAMP_RESIDENT_STATE);
	}
	if ((result_size != 0 && result_data == NULL) ||
	    result_size > loader->result_capacity) {
		return fail(loader, DUCHAMP_RESIDENT_RESULT_RANGE);
	}
	if (result_size != 0) {
		copy_bytes(loader->result, result_data, result_size);
	}
	loader->result_size = result_size;
	loader->result_code = code;
	loader->result_receipt = duchamp_resident_receipt(loader->result,
	    result_size);
	loader->last_error = DUCHAMP_RESIDENT_OK;
	loader->state = DUCHAMP_RESIDENT_RETURNED;
	return DUCHAMP_RESIDENT_OK;
}

unsigned
duchamp_resident_get_status(const struct duchamp_resident_loader *loader,
	struct duchamp_resident_status *status)
{
	if (!valid(loader) || status == NULL) {
		return DUCHAMP_RESIDENT_ARGUMENT;
	}
	status->version = loader->version;
	status->state = loader->state;
	status->last_error = loader->last_error;
	status->detail = loader->detail;
	status->generation = loader->generation;
	status->payload_receipt = loader->payload_receipt;
	status->result_receipt = loader->result_receipt;
	status->result_code = loader->result_code;
	status->run_count = loader->run_count;
	status->staging_capacity = loader->staging_capacity;
	status->expected_size = loader->expected_size;
	status->received_size = loader->received_size;
	status->result_size = loader->result_size;
	return DUCHAMP_RESIDENT_OK;
}

unsigned
duchamp_resident_get_result(const struct duchamp_resident_loader *loader,
	struct duchamp_resident_result_view *result_view)
{
	if (!valid(loader) || result_view == NULL) {
		return DUCHAMP_RESIDENT_ARGUMENT;
	}
	if (loader->state != DUCHAMP_RESIDENT_RETURNED) {
		return terminal(loader) ? DUCHAMP_RESIDENT_RELOAD_REQUIRED :
		    DUCHAMP_RESIDENT_STATE;
	}
	result_view->code = loader->result_code;
	result_view->receipt = loader->result_receipt;
	result_view->data = loader->result;
	result_view->size = loader->result_size;
	return DUCHAMP_RESIDENT_OK;
}
