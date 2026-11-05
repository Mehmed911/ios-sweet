#include <stdint.h>
#include <stdio.h>
#include <string.h>

#include "resident_protocol.h"

struct callbacks {
	struct duchamp_resident_loader *loader;
	unsigned prepare_calls;
	unsigned enter_calls;
	unsigned prepare_result;
	unsigned enter_result;
	int complete;
	const void *result_data;
	size_t result_size;
};

static unsigned
prepare(void *context_pointer, const void *payload, size_t payload_size,
	struct duchamp_resident_target *target)
{
	struct callbacks *context = context_pointer;
	const unsigned char *bytes = payload;
	context->prepare_calls++;
	if (context->prepare_result != 0) return context->prepare_result;
	if (payload_size != 8 || bytes[0] != 'S' || bytes[7] != 'U') return 99;
	target->entry = UINT64_C(0x1c1480488);
	target->boot_args = UINT64_C(0x1c256c000);
	return 0;
}

static unsigned
enter(void *context_pointer, const struct duchamp_resident_target *target)
{
	static const char result[] = "RETURNED";
	struct callbacks *context = context_pointer;
	context->enter_calls++;
	if (target->entry != UINT64_C(0x1c1480488) ||
	    target->boot_args != UINT64_C(0x1c256c000)) return 98;
	if (context->complete) {
		const void *data = context->result_data != NULL ?
		    context->result_data : result;
		size_t size = context->result_data != NULL ?
		    context->result_size : sizeof(result) - 1;
		if (duchamp_resident_complete(context->loader, 42, data,
		    size) != DUCHAMP_RESIDENT_OK) return 97;
	}
	return context->enter_result;
}

#define CHECK(condition) do { if (!(condition)) { \
	fprintf(stderr, "resident protocol check failed at line %d\n", __LINE__); \
	return 1; } checks++; } while (0)

static unsigned
load(struct duchamp_resident_loader *loader, unsigned char *staging,
	unsigned char *result, const unsigned char *payload)
{
	unsigned value;
	value = duchamp_resident_init(loader, staging, 32, result, 32, 7);
	if (value != 0) return value;
	value = duchamp_resident_begin(loader, 8);
	if (value != 0) return value;
	value = duchamp_resident_receive(loader, 0, payload, 3);
	if (value != 0) return value;
	return duchamp_resident_receive(loader, 3, payload + 3, 5);
}

int
main(void)
{
	static const unsigned char payload[8] = {'S','W','E','E','T','X','N','U'};
	const struct duchamp_resident_ops ops = {prepare, enter};
	struct duchamp_resident_loader loader;
	struct duchamp_resident_status status;
	struct duchamp_resident_result_view view;
	struct callbacks callbacks;
	unsigned char staging[32], result[32];
	unsigned checks = 0;
	struct duchamp_resident_loader alias_loader;
	unsigned char alias[64];
	unsigned char overlap_result[40] = "OVERLAP!";

	CHECK(duchamp_resident_init(&alias_loader, alias, 32, alias + 16,
	    16, 1) == DUCHAMP_RESIDENT_ARGUMENT);

	memset(&callbacks, 0, sizeof(callbacks));
	CHECK(load(&loader, staging, result, payload) == DUCHAMP_RESIDENT_OK);
	CHECK(loader.state == DUCHAMP_RESIDENT_READY && loader.payload_receipt != 0);
	callbacks.loader = &loader;
	callbacks.complete = 1;
	CHECK(duchamp_resident_run(&loader, &ops, &callbacks) == DUCHAMP_RESIDENT_OK);
	CHECK(callbacks.prepare_calls == 1 && callbacks.enter_calls == 1);
	CHECK(duchamp_resident_get_status(&loader, &status) == 0 &&
	    status.state == DUCHAMP_RESIDENT_RETURNED && status.run_count == 1 &&
	    status.result_code == 42 && status.result_size == 8);
	CHECK(duchamp_resident_get_result(&loader, &view) == 0 &&
	    view.code == 42 && view.size == 8 && view.receipt != 0 &&
	    memcmp(view.data, "RETURNED", 8) == 0);
	CHECK(duchamp_resident_run(&loader, &ops, &callbacks) ==
	    DUCHAMP_RESIDENT_RELOAD_REQUIRED && callbacks.enter_calls == 1);
	CHECK(duchamp_resident_begin(&loader, 8) == DUCHAMP_RESIDENT_RELOAD_REQUIRED);

	CHECK(load(&loader, staging, overlap_result + 4, payload) == 0);
	memset(&callbacks, 0, sizeof(callbacks));
	callbacks.loader = &loader;
	callbacks.complete = 1;
	callbacks.result_data = overlap_result;
	callbacks.result_size = 8;
	CHECK(duchamp_resident_run(&loader, &ops, &callbacks) == 0 &&
	    memcmp(overlap_result + 4, "OVERLAP!", 8) == 0);

	CHECK(load(&loader, staging, result, payload) == 0);
	staging[4] ^= 1;
	memset(&callbacks, 0, sizeof(callbacks));
	callbacks.loader = &loader;
	CHECK(duchamp_resident_run(&loader, &ops, &callbacks) ==
	    DUCHAMP_RESIDENT_RECEIPT && callbacks.prepare_calls == 0 &&
	    loader.state == DUCHAMP_RESIDENT_FAILED);

	CHECK(duchamp_resident_init(&loader, staging, sizeof(staging), result,
	    sizeof(result), 8) == 0 && duchamp_resident_begin(&loader, 8) == 0);
	CHECK(duchamp_resident_receive(&loader, 1, payload, 1) ==
	    DUCHAMP_RESIDENT_ORDER && loader.state == DUCHAMP_RESIDENT_FAILED);
	CHECK(duchamp_resident_init(&loader, staging, sizeof(staging), result,
	    sizeof(result), 8) == 0 && duchamp_resident_begin(&loader, 8) == 0);
	CHECK(duchamp_resident_receive(&loader, 0, staging, 1) ==
	    DUCHAMP_RESIDENT_ARGUMENT && loader.state == DUCHAMP_RESIDENT_FAILED);
	CHECK(duchamp_resident_init(&loader, staging, sizeof(staging), result,
	    sizeof(result), 8) == 0 && duchamp_resident_begin(&loader, 8) == 0);
	loader.received_size = 9;
	CHECK(duchamp_resident_receive(&loader, 9, payload, 1) ==
	    DUCHAMP_RESIDENT_ARGUMENT && loader.state == DUCHAMP_RESIDENT_RECEIVING);
	loader.received_size = 0;
	loader.state = DUCHAMP_RESIDENT_FAILED + 1;
	CHECK(duchamp_resident_get_status(&loader, &status) ==
	    DUCHAMP_RESIDENT_ARGUMENT);

	CHECK(load(&loader, staging, result, payload) == 0);
	memset(&callbacks, 0, sizeof(callbacks));
	callbacks.loader = &loader;
	callbacks.prepare_result = 77;
	CHECK(duchamp_resident_run(&loader, &ops, &callbacks) ==
	    DUCHAMP_RESIDENT_PREPARE && callbacks.prepare_calls == 1 &&
	    callbacks.enter_calls == 0 && loader.detail == 77);

	CHECK(load(&loader, staging, result, payload) == 0);
	memset(&callbacks, 0, sizeof(callbacks));
	callbacks.loader = &loader;
	CHECK(duchamp_resident_run(&loader, &ops, &callbacks) ==
	    DUCHAMP_RESIDENT_UNEXPECTED_RETURN && callbacks.enter_calls == 1 &&
	    loader.state == DUCHAMP_RESIDENT_FAILED);

	CHECK(duchamp_resident_init(&loader, staging, sizeof(staging), result,
	    4, 9) == 0 && duchamp_resident_begin(&loader, 8) == 0 &&
	    duchamp_resident_receive(&loader, 0, payload, 8) == 0);
	memset(&callbacks, 0, sizeof(callbacks));
	callbacks.loader = &loader;
	callbacks.complete = 1;
	CHECK(duchamp_resident_run(&loader, &ops, &callbacks) ==
	    DUCHAMP_RESIDENT_RESULT_RANGE && loader.state == DUCHAMP_RESIDENT_FAILED);

	CHECK(duchamp_resident_init(&loader, staging, sizeof(staging), result,
	    sizeof(result), 10) == 0 && duchamp_resident_begin(&loader, 8) == 0 &&
	    duchamp_resident_receive(&loader, 0, payload, 4) == 0);
	memset(&callbacks, 0, sizeof(callbacks));
	callbacks.loader = &loader;
	CHECK(duchamp_resident_run(&loader, &ops, &callbacks) ==
	    DUCHAMP_RESIDENT_INCOMPLETE && callbacks.prepare_calls == 0);

	printf("resident-protocol-tests: PASS checks=%u\n", checks);
	return 0;
}
