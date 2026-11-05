#ifndef DUCHAMP_BOOTSHIM_XNU_RETURN_H
#define DUCHAMP_BOOTSHIM_XNU_RETURN_H

#include <stddef.h>
#include <stdint.h>

#define DUCHAMP_XNU_RETURN_MAGIC UINT64_C(0x4455434858524554)
#define DUCHAMP_XNU_RETURN_VERSION UINT32_C(1)
#define DUCHAMP_XNU_RETURN_LOG_BYTES (64u * 1024u)

enum duchamp_xnu_return_result {
	DUCHAMP_XNU_RETURN_OK = 0,
	DUCHAMP_XNU_RETURN_ARGUMENT = 1,
};

struct duchamp_xnu_return_record {
	uint64_t magic;
	uint32_t version;
	uint32_t size;
	uint32_t result;
	uint32_t reserved;
	uint64_t reason;
	uint64_t code;
	uint64_t elr;
	uint64_t far;
	uint64_t log_pa;
	uint64_t log_length;
	uint64_t copied;
	uint64_t head_bytes;
	uint64_t tail_bytes;
	uint64_t checksum;
};

unsigned duchamp_xnu_return_capture(uint64_t log_pa, uint64_t log_length,
	const void *log_source, uint64_t reason, uint64_t code, uint64_t elr,
	uint64_t far, void *saved_log, size_t saved_log_size,
	struct duchamp_xnu_return_record *record);

#endif
