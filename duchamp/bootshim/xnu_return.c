#include "xnu_return.h"

static void
copy_bytes(unsigned char *to, const unsigned char *from, uint64_t size)
{
	uint64_t i;

	for (i = 0; i < size; i++) to[i] = from[i];
}

static void
zero_bytes(unsigned char *to, size_t size)
{
	size_t i;

	for (i = 0; i < size; i++) to[i] = 0;
}

static uint64_t
checksum_bytes(uint64_t value, const unsigned char *bytes, size_t size)
{
	size_t i;

	for (i = 0; i < size; i++) {
		value ^= bytes[i];
		value *= UINT64_C(1099511628211);
	}
	return value;
}

unsigned
duchamp_xnu_return_capture(uint64_t log_pa, uint64_t log_length,
	const void *log_source_pointer, uint64_t reason, uint64_t code,
	uint64_t elr, uint64_t far, void *saved_log_pointer,
	size_t saved_log_size, struct duchamp_xnu_return_record *record)
{
	const unsigned char *source = log_source_pointer;
	unsigned char *saved = saved_log_pointer;
	uint64_t head = 0, tail = 0, copied = 0, checksum;
	unsigned result = DUCHAMP_XNU_RETURN_OK;

	if (record == NULL || (saved_log_size != 0 && saved == NULL)) {
		return DUCHAMP_XNU_RETURN_ARGUMENT;
	}
	zero_bytes((unsigned char *)record, sizeof(*record));
	record->magic = DUCHAMP_XNU_RETURN_MAGIC;
	record->version = DUCHAMP_XNU_RETURN_VERSION;
	record->size = sizeof(*record);
	record->reason = reason;
	record->code = code;
	record->elr = elr;
	record->far = far;
	record->log_pa = log_pa;
	record->log_length = log_length;
	if (saved_log_size != 0) zero_bytes(saved, saved_log_size);
	if (log_length != 0 && source == NULL) {
		result = DUCHAMP_XNU_RETURN_ARGUMENT;
	} else if (log_length <= saved_log_size) {
		head = log_length;
		copy_bytes(saved, source, head);
		copied = head;
	} else if (saved_log_size != 0) {
		head = saved_log_size / 4;
		tail = saved_log_size - head;
		copy_bytes(saved, source, head);
		copy_bytes(saved + head, source + log_length - tail, tail);
		copied = head + tail;
	}
	record->result = result;
	record->copied = copied;
	record->head_bytes = head;
	record->tail_bytes = tail;
	checksum = checksum_bytes(UINT64_C(1469598103934665603),
	    (const unsigned char *)record,
	    offsetof(struct duchamp_xnu_return_record, checksum));
	checksum = checksum_bytes(checksum, saved, (size_t)copied);
	record->checksum = checksum;
	return result;
}
