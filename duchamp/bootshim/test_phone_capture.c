#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

#include "phone_capture.h"
#include "../loader/mt6897_entry.h"

#define WIDTH 1100U
#define HEIGHT 256U
#define STRIDE (WIDTH * sizeof(uint32_t) + 16U)
#define BLACK UINT32_C(0xff000000)
#define WHITE UINT32_C(0xffffffff)

static uint32_t
pixel(const unsigned char *framebuffer, size_t x, size_t y)
{
	return *(const uint32_t *)(const void *)(framebuffer + y * STRIDE +
	    x * sizeof(uint32_t));
}

int
main(void)
{
	unsigned char *framebuffer = calloc(HEIGHT, STRIDE);
	struct duchamp_phone_capture_record record;
	uint64_t pc = UINT64_C(0x0123456789abcdef);
	uint64_t x0 = UINT64_C(0xfedcba9876543210);
	size_t white = 0;
	size_t black = 0;
	unsigned result;

	if (framebuffer == NULL) return 1;
	result = duchamp_phone_capture_run(framebuffer, STRIDE, WIDTH, HEIGHT,
	    pc, x0, 4, 0, DUCHAMP_ENTRY_FDT, &record);
	if (result != DUCHAMP_PHONE_CAPTURE_OK ||
	    record.magic != DUCHAMP_PHONE_CAPTURE_MAGIC ||
	    record.version != DUCHAMP_PHONE_CAPTURE_VERSION ||
	    record.size != sizeof(record) || record.entry_pc != pc ||
	    record.entry_x0 != x0 || record.current_el != 4 ||
	    record.sctlr != 0 || record.entry_result != DUCHAMP_ENTRY_FDT ||
	    record.render_state != DUCHAMP_PHONE_CAPTURE_COMPLETE ||
	    record.checksum != duchamp_phone_capture_checksum(&record)) {
		fprintf(stderr, "capture record mismatch\n");
		free(framebuffer);
		return 1;
	}
	for (size_t y = 0; y < HEIGHT; y++) {
		for (size_t x = 0; x < WIDTH; x++) {
			uint32_t value = pixel(framebuffer, x, y);
			if (value == WHITE) white++;
			else if (value == BLACK) black++;
			else {
				fprintf(stderr, "unexpected pixel %#x at %zu,%zu\n",
				    value, x, y);
				free(framebuffer);
				return 1;
			}
		}
		for (size_t offset = WIDTH * sizeof(uint32_t);
		    offset < STRIDE; offset++) {
			if (framebuffer[y * STRIDE + offset] != 0) {
				fprintf(stderr, "stride padding changed\n");
				free(framebuffer);
				return 1;
			}
		}
	}
	if (white < 10000 || black == 0 || pixel(framebuffer, 0, 0) != BLACK) {
		fprintf(stderr, "capture glyph coverage mismatch: white=%zu black=%zu\n",
		    white, black);
		free(framebuffer);
		return 1;
	}

	record.render_state = 99;
	result = duchamp_phone_capture_run(framebuffer, STRIDE, WIDTH, HEIGHT,
	    pc, x0, 4, 1, DUCHAMP_ENTRY_TRANSLATION_STATE, &record);
	if (result != DUCHAMP_PHONE_CAPTURE_UNSAFE_ENTRY ||
	    record.render_state != DUCHAMP_PHONE_CAPTURE_NOT_RENDERED ||
	    record.checksum != duchamp_phone_capture_checksum(&record)) {
		fprintf(stderr, "unsafe entry did not fail closed\n");
		free(framebuffer);
		return 1;
	}

	free(framebuffer);
	puts("phone-capture-host-test: PASS");
	return 0;
}
