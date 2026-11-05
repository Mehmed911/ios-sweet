#include <stdio.h>
#include <stdlib.h>

#include "payload_preflight.h"
#include "../loader/guard.h"

#define XNU_PAGE UINT64_C(0x4000)

static uint32_t
read_le32(const unsigned char *p)
{
	return (uint32_t)p[0] | (uint32_t)p[1] << 8 |
	    (uint32_t)p[2] << 16 | (uint32_t)p[3] << 24;
}

static uint64_t
read_le64(const unsigned char *p)
{
	return (uint64_t)read_le32(p) | (uint64_t)read_le32(p + 4) << 32;
}

static unsigned char *
read_file(const char *path, size_t *size)
{
	FILE *f = fopen(path, "rb");
	unsigned char *data;
	long length;
	if (!f || fseek(f, 0, SEEK_END) || (length = ftell(f)) <= 0 ||
	    fseek(f, 0, SEEK_SET)) {
		return 0;
	}
	data = malloc((size_t)length);
	if (!data || fread(data, 1, (size_t)length, f) != (size_t)length) {
		return 0;
	}
	fclose(f);
	*size = (size_t)length;
	return data;
}

int
main(int argc, char **argv)
{
	unsigned char *fdt, *payload;
	size_t fdt_size, payload_size;
	struct duchamp_payload_preflight p;
	uint64_t virt_base, virtual_entry, kernel_end, adt_size;
	uint64_t expected_entry, expected_adt, expected_boot_args;
	unsigned expected_segment_count, result;
	if (argc != 3) return 2;
	fdt = read_file(argv[1], &fdt_size);
	payload = read_file(argv[2], &payload_size);
	if (!fdt || !payload) return 2;
	virt_base = read_le64(payload + 0x10);
	virtual_entry = read_le64(payload + 0x18);
	adt_size = read_le64(payload + 0x28);
	kernel_end = read_le64(payload + 0x30);
	expected_segment_count = read_le32(payload + 12);
	expected_entry = DUCHAMP_PAYLOAD_EXPECTED_BASE + virtual_entry - virt_base;
	expected_adt = DUCHAMP_PAYLOAD_EXPECTED_BASE + kernel_end - virt_base;
	expected_boot_args = (expected_adt + adt_size + XNU_PAGE - 1) &
	    ~(XNU_PAGE - 1);
	result = duchamp_bootshim_payload_preflight(fdt, fdt_size,
	    payload, payload_size, &p);
	printf("result=%u segments=%u base=%#llx size=%#llx entry=%#llx "
	    "adt=%#llx boot_args=%#llx top=%#llx\n", result,
	    p.segment_count, (unsigned long long)p.phys_base,
	    (unsigned long long)p.memory_size, (unsigned long long)p.entry,
	    (unsigned long long)p.adt, (unsigned long long)p.boot_args,
	    (unsigned long long)p.top);
	if (result != DUCHAMP_GUARD_OK ||
	    p.segment_count != expected_segment_count ||
	    p.phys_base != DUCHAMP_PAYLOAD_EXPECTED_BASE ||
	    p.memory_size != DUCHAMP_PAYLOAD_EXPECTED_SIZE ||
	    p.entry != expected_entry || p.adt != expected_adt ||
	    p.boot_args != expected_boot_args ||
	    p.top != expected_boot_args + XNU_PAGE) {
		fprintf(stderr, "unexpected Duchamp preflight plan\n");
		return 1;
	}

	payload[0] ^= 0xff;
	result = duchamp_bootshim_payload_preflight(fdt, fdt_size,
	    payload, payload_size, &p);
	payload[0] ^= 0xff;
	if (result != DUCHAMP_GUARD_PAYLOAD_HEADER) {
		fprintf(stderr, "corrupt payload accepted: result=%u\n", result);
		return 1;
	}

	fdt[0] ^= 0xff;
	result = duchamp_bootshim_payload_preflight(fdt, fdt_size,
	    payload, payload_size, &p);
	if (result != DUCHAMP_GUARD_FDT_HEADER) {
		fprintf(stderr, "corrupt FDT accepted: result=%u\n", result);
		return 1;
	}

	free(payload);
	free(fdt);
	puts("payload-preflight-tests: PASS");
	return 0;
}
