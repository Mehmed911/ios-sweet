#include <errno.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>

#include "diagnostic.h"
#include "../loader/mt6897_entry.h"

#define FDT_BASE UINT64_C(0x40000000)
#define FDT_MAP_SIZE UINT64_C(0x200000)
#define FB_BASE UINT64_C(0xfcc2f000)
#define FB_STRIDE UINT64_C(4992)
#define FB_WIDTH UINT64_C(1220)
#define FB_ROWS UINT64_C(12)
#define FB_HEIGHT UINT64_C(2712)
#define BAND_HEIGHT (FB_HEIGHT / FB_ROWS)
#define SENTINEL UINT32_C(0x11223344)
#define PASS UINT32_C(0xff00ff00)
#define FAIL UINT32_C(0xffff0000)
#define SIG_A UINT32_C(0xff00ffff)
#define SIG_B UINT32_C(0xffff00ff)

extern struct duchamp_mt6897_entry_state duchamp_bootshim_entry_state;
void duchamp_bootshim_main(void);

static uint64_t
expected_checksum(void)
{
	const uint64_t *words =
	    (const uint64_t *)(const void *)&duchamp_bootshim_diagnostic;
	size_t count = offsetof(struct duchamp_bootshim_diagnostic, checksum) /
	    sizeof(*words);
	uint64_t value = UINT64_C(0x9e3779b97f4a7c15);
	for (size_t i = 0; i < count; i++) {
		value ^= words[i] + UINT64_C(0x9e3779b97f4a7c15) +
		    (value << 6) + (value >> 2);
	}
	return value;
}

static void
expect_diagnostic(const char *name, unsigned result, unsigned marker,
	uint32_t fdt_magic, uint32_t fdt_size)
{
	const struct duchamp_bootshim_diagnostic *d = &duchamp_bootshim_diagnostic;
	if (d->magic != DUCHAMP_DIAGNOSTIC_MAGIC ||
	    d->version != DUCHAMP_DIAGNOSTIC_VERSION || d->size != sizeof(*d) ||
	    d->entry_result != result || d->marker != marker ||
	    d->fdt_magic != fdt_magic || d->fdt_size != fdt_size ||
	    d->entry.entry_x0 != duchamp_bootshim_entry_state.entry_x0 ||
	    d->checksum != expected_checksum()) {
		fprintf(stderr, "%s diagnostic mismatch\n", name);
		exit(1);
	}
}

static void *
map_fixed(uint64_t address, size_t size)
{
	void *result = mmap((void *)(uintptr_t)address, size,
	    PROT_READ | PROT_WRITE,
	    MAP_PRIVATE | MAP_ANONYMOUS | MAP_FIXED_NOREPLACE, -1, 0);
	if (result == MAP_FAILED) {
		fprintf(stderr, "mmap %#llx: %s\n",
		    (unsigned long long)address, strerror(errno));
		exit(1);
	}
	return result;
}

static void
put_be32(volatile unsigned char *p, uint32_t value)
{
	p[0] = (unsigned char)(value >> 24);
	p[1] = (unsigned char)(value >> 16);
	p[2] = (unsigned char)(value >> 8);
	p[3] = (unsigned char)value;
}

static void
reset_state(void)
{
	volatile uint32_t *fb = (volatile uint32_t *)(uintptr_t)FB_BASE;
	size_t words = FB_STRIDE * FB_HEIGHT / sizeof(*fb);
	for (size_t i = 0; i < words; i++) {
		fb[i] = SENTINEL;
	}
	memset((void *)(uintptr_t)FDT_BASE, 0, FDT_MAP_SIZE);
	memset(&duchamp_bootshim_entry_state, 0,
	    sizeof(duchamp_bootshim_entry_state));
	memset(&duchamp_bootshim_diagnostic, 0,
	    sizeof(duchamp_bootshim_diagnostic));
	duchamp_bootshim_entry_state.current_el = 4;
	duchamp_bootshim_entry_state.entry_x0 = FDT_BASE;
}

static void
expect_unchanged(const char *name)
{
	volatile uint32_t *fb = (volatile uint32_t *)(uintptr_t)FB_BASE;
	size_t words = FB_STRIDE * FB_HEIGHT / sizeof(*fb);
	for (size_t i = 0; i < words; i++) {
		if (fb[i] != SENTINEL) {
			fprintf(stderr, "%s changed framebuffer word %zu\n", name, i);
			exit(1);
		}
	}
}

static void
expect_marker(const char *name, const uint32_t colors[FB_ROWS])
{
	volatile uint32_t *fb = (volatile uint32_t *)(uintptr_t)FB_BASE;
	size_t stride_words = FB_STRIDE / sizeof(*fb);
	for (size_t y = 0; y < FB_HEIGHT; y++) {
		size_t band = y / BAND_HEIGHT;
		for (size_t x = 0; x < stride_words; x++) {
			uint32_t expected = x < FB_WIDTH ? colors[band] : SENTINEL;
			if (fb[y * stride_words + x] != expected) {
				fprintf(stderr, "%s mismatch at row %zu word %zu\n",
				    name, y, x);
				exit(1);
			}
		}
	}
}

int
main(void)
{
	volatile unsigned char *fdt =
	    (volatile unsigned char *)(uintptr_t)FDT_BASE;
	const uint32_t bad_fdt[FB_ROWS] = {
		FAIL, PASS, PASS, PASS, PASS, PASS, FAIL, FAIL,
		SIG_A, SIG_B, SIG_A, SIG_B,
	};
	const uint32_t valid_fdt[FB_ROWS] = {
		PASS, PASS, PASS, PASS, PASS, PASS, PASS, PASS,
		SIG_A, SIG_B, SIG_A, SIG_B,
	};
	const uint32_t oversize_fdt[FB_ROWS] = {
		FAIL, PASS, PASS, PASS, PASS, PASS, PASS, FAIL,
		SIG_A, SIG_B, SIG_A, SIG_B,
	};
	const uint32_t el2_safe[FB_ROWS] = {
		FAIL, FAIL, PASS, PASS, PASS, FAIL, FAIL, FAIL,
		SIG_A, SIG_B, SIG_A, SIG_B,
	};

	map_fixed(FDT_BASE, FDT_MAP_SIZE);
	map_fixed(FB_BASE, FB_STRIDE * FB_HEIGHT);

	reset_state();
	duchamp_bootshim_entry_state.current_el = 8;
	duchamp_bootshim_main();
	expect_marker("EL2", el2_safe);
	expect_diagnostic("EL2", DUCHAMP_ENTRY_EXCEPTION_LEVEL,
	    DUCHAMP_MARKER_FAILURE, 0, 0);

	reset_state();
	duchamp_bootshim_entry_state.current_el = 8;
	duchamp_bootshim_entry_state.sctlr_el1 = 1;
	duchamp_bootshim_main();
	expect_unchanged("EL2-MMU-on");
	expect_diagnostic("EL2-MMU-on", DUCHAMP_ENTRY_EXCEPTION_LEVEL,
	    DUCHAMP_MARKER_NONE, 0, 0);

	reset_state();
	duchamp_bootshim_entry_state.sctlr_el1 = 1;
	duchamp_bootshim_main();
	expect_unchanged("MMU-on");
	expect_diagnostic("MMU-on", DUCHAMP_ENTRY_TRANSLATION_STATE,
	    DUCHAMP_MARKER_NONE, 0, 0);

	reset_state();
	duchamp_bootshim_main();
	expect_marker("bad-FDT", bad_fdt);
	expect_diagnostic("bad-FDT", DUCHAMP_ENTRY_OK, DUCHAMP_MARKER_FAILURE,
	    0, 0);

	reset_state();
	put_be32(fdt, UINT32_C(0xd00dfeed));
	put_be32(fdt + 4, 40);
	duchamp_bootshim_main();
	expect_marker("valid-FDT", valid_fdt);
	expect_diagnostic("valid-FDT", DUCHAMP_ENTRY_OK, DUCHAMP_MARKER_SUCCESS,
	    UINT32_C(0xd00dfeed), 40);

	reset_state();
	put_be32(fdt, UINT32_C(0xd00dfeed));
	put_be32(fdt + 4, UINT32_C(0x200001));
	duchamp_bootshim_main();
	expect_marker("oversize-FDT", oversize_fdt);
	expect_diagnostic("oversize-FDT", DUCHAMP_ENTRY_OK,
	    DUCHAMP_MARKER_FAILURE, UINT32_C(0xd00dfeed), UINT32_C(0x200001));

	puts("bootshim-host-tests: PASS");
	return 0;
}
