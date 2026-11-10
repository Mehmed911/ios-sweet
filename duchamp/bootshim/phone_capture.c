#include "phone_capture.h"

#if defined(DUCHAMP_UFS_HANDOFF_PROBE)
#include "../loader/mt6897_entry.h"
#endif

#define GLYPH_WIDTH 5U
#define GLYPH_HEIGHT 7U
#define GLYPH_SCALE 8U
#define GLYPH_ADVANCE ((GLYPH_WIDTH + 1U) * GLYPH_SCALE)
#define LINE_CHARACTERS 21U
#define LINE_WIDTH ((LINE_CHARACTERS * (GLYPH_WIDTH + 1U) - 1U) * \
	GLYPH_SCALE)
#define COLOR_BLACK UINT32_C(0xff000000)
#define COLOR_WHITE UINT32_C(0xffffffff)
#define SCTLR_M UINT64_C(1)
#define SCTLR_C (UINT64_C(1) << 2)
#define SCTLR_I (UINT64_C(1) << 12)

static uint8_t
glyph_row(char character, unsigned row)
{
	static const uint8_t digits[10][GLYPH_HEIGHT] = {
		{ 0x0e, 0x11, 0x13, 0x15, 0x19, 0x11, 0x0e },
		{ 0x04, 0x0c, 0x04, 0x04, 0x04, 0x04, 0x0e },
		{ 0x0e, 0x11, 0x01, 0x02, 0x04, 0x08, 0x1f },
		{ 0x1e, 0x01, 0x01, 0x0e, 0x01, 0x01, 0x1e },
		{ 0x02, 0x06, 0x0a, 0x12, 0x1f, 0x02, 0x02 },
		{ 0x1f, 0x10, 0x10, 0x1e, 0x01, 0x01, 0x1e },
		{ 0x0e, 0x10, 0x10, 0x1e, 0x11, 0x11, 0x0e },
		{ 0x1f, 0x01, 0x02, 0x04, 0x08, 0x08, 0x08 },
		{ 0x0e, 0x11, 0x11, 0x0e, 0x11, 0x11, 0x0e },
		{ 0x0e, 0x11, 0x11, 0x0f, 0x01, 0x01, 0x0e },
	};
	static const uint8_t hex_letters[6][GLYPH_HEIGHT] = {
		{ 0x0e, 0x11, 0x11, 0x1f, 0x11, 0x11, 0x11 },
		{ 0x1e, 0x11, 0x11, 0x1e, 0x11, 0x11, 0x1e },
		{ 0x0f, 0x10, 0x10, 0x10, 0x10, 0x10, 0x0f },
		{ 0x1e, 0x11, 0x11, 0x11, 0x11, 0x11, 0x1e },
		{ 0x1f, 0x10, 0x10, 0x1e, 0x10, 0x10, 0x1f },
		{ 0x1f, 0x10, 0x10, 0x1e, 0x10, 0x10, 0x10 },
	};
	static const uint8_t glyph_c[GLYPH_HEIGHT] =
	    { 0x0f, 0x10, 0x10, 0x10, 0x10, 0x10, 0x0f };
	static const uint8_t glyph_p[GLYPH_HEIGHT] =
	    { 0x1e, 0x11, 0x11, 0x1e, 0x10, 0x10, 0x10 };
	static const uint8_t glyph_x[GLYPH_HEIGHT] =
	    { 0x11, 0x11, 0x0a, 0x04, 0x0a, 0x11, 0x11 };
	static const uint8_t glyph_equal[GLYPH_HEIGHT] =
	    { 0x00, 0x00, 0x1f, 0x00, 0x1f, 0x00, 0x00 };

	if (row >= GLYPH_HEIGHT) return 0;
	if (character >= '0' && character <= '9')
		return digits[(unsigned)(character - '0')][row];
	if (character >= 'A' && character <= 'F')
		return hex_letters[(unsigned)(character - 'A')][row];
	if (character == 'C') return glyph_c[row];
	if (character == 'P') return glyph_p[row];
	if (character == 'X') return glyph_x[row];
	if (character == '=') return glyph_equal[row];
	return 0;
}

static void
format_line(char line[LINE_CHARACTERS], char first, char second,
	uint64_t value)
{
	static const char hexadecimal[] = "0123456789ABCDEF";

	line[0] = first;
	line[1] = second;
	line[2] = '=';
	line[3] = '0';
	line[4] = 'X';
	for (unsigned index = 0; index < 16; index++) {
		unsigned shift = (15U - index) * 4U;
		line[5U + index] = hexadecimal[(value >> shift) & 0xfU];
	}
}

static void
fill_screen(volatile unsigned char *base, size_t stride, size_t width,
	size_t height, uint32_t color)
{
	for (size_t y = 0; y < height; y++) {
		volatile uint32_t *row =
		    (volatile uint32_t *)(void *)(base + y * stride);
		for (size_t x = 0; x < width; x++) row[x] = color;
	}
}

static void
draw_character(volatile unsigned char *base, size_t stride, size_t x,
	size_t y, char character)
{
	for (unsigned glyph_y = 0; glyph_y < GLYPH_HEIGHT; glyph_y++) {
		uint8_t bits = glyph_row(character, glyph_y);
		for (unsigned scale_y = 0; scale_y < GLYPH_SCALE; scale_y++) {
			volatile uint32_t *row = (volatile uint32_t *)(void *)(base +
			    (y + glyph_y * GLYPH_SCALE + scale_y) * stride);
			for (unsigned glyph_x = 0; glyph_x < GLYPH_WIDTH;
			    glyph_x++) {
				if ((bits & (UINT8_C(1) <<
				    (GLYPH_WIDTH - 1U - glyph_x))) == 0) continue;
				for (unsigned scale_x = 0; scale_x < GLYPH_SCALE;
				    scale_x++) {
					row[x + glyph_x * GLYPH_SCALE + scale_x] =
					    COLOR_WHITE;
				}
			}
		}
	}
}

static void
draw_line(volatile unsigned char *base, size_t stride, size_t x, size_t y,
	const char line[LINE_CHARACTERS])
{
	for (unsigned index = 0; index < LINE_CHARACTERS; index++)
		draw_character(base, stride, x + index * GLYPH_ADVANCE, y,
		    line[index]);
}

#if defined(DUCHAMP_UFS_HANDOFF_PROBE)
#define UFS_PROBE_FDT_BEGIN UINT64_C(0x40000000)
#define UFS_PROBE_FDT_END UINT64_C(0x80000000)
#define UFS_PROBE_FDT_MAX (2U * 1024U * 1024U)
#define UFS_PROBE_FDT_HEADER 40U
#define UFS_PROBE_MISSING_TRACE (UINT32_C(1) << 0)
#define UFS_PROBE_UNKNOWN_HCE (UINT32_C(1) << 1)
#define UFS_PROBE_UNKNOWN_QUEUES (UINT32_C(1) << 2)
#define UFS_PROBE_UNVERIFIED_DMA (UINT32_C(1) << 3)
#define UFS_PROBE_INVALID_FDT (UINT32_C(1) << 4)

struct duchamp_ufs_handoff_record {
	uint64_t magic;
	uint32_t version;
	uint32_t size;
	uint64_t fdt_fingerprint;
	uint32_t fdt_bytes;
	uint32_t blockers;
};

struct duchamp_ufs_handoff_record duchamp_bootshim_ufs_handoff_record;

static uint32_t
probe_be32(const volatile unsigned char *bytes)
{
	return ((uint32_t)bytes[0] << 24) | ((uint32_t)bytes[1] << 16) |
	    ((uint32_t)bytes[2] << 8) | bytes[3];
}

static void
capture_ufs_handoff(uint64_t fdt_address, unsigned entry_result)
{
	struct duchamp_ufs_handoff_record *record =
	    &duchamp_bootshim_ufs_handoff_record;
	/* The receiver has no firmware trace, resource grant or UFS access. */
	record->magic = UINT64_C(0x3153465548435544);
	record->version = 1;
	record->size = sizeof(*record);
	record->fdt_bytes = 0;
	record->fdt_fingerprint = 0;
	record->blockers = UFS_PROBE_MISSING_TRACE | UFS_PROBE_UNKNOWN_HCE |
	    UFS_PROBE_UNKNOWN_QUEUES | UFS_PROBE_UNVERIFIED_DMA |
	    UFS_PROBE_INVALID_FDT;
	if (entry_result != DUCHAMP_ENTRY_OK ||
	    fdt_address < UFS_PROBE_FDT_BEGIN ||
	    fdt_address > UFS_PROBE_FDT_END - UFS_PROBE_FDT_HEADER)
		return;
	const volatile unsigned char *fdt =
	    (const volatile unsigned char *)(uintptr_t)fdt_address;
	if (probe_be32(fdt) != UINT32_C(0xd00dfeed))
		return;
	uint32_t bytes = probe_be32(fdt + 4);
	if (bytes < UFS_PROBE_FDT_HEADER || bytes > UFS_PROBE_FDT_MAX ||
	    bytes > UFS_PROBE_FDT_END - fdt_address)
		return;

	/* For screen-to-RAM correlation only. This is not a trust token. */
	uint64_t fingerprint = UINT64_C(1469598103934665603);
	for (uint32_t i = 0; i < bytes; i++) {
		fingerprint ^= fdt[i];
		fingerprint *= UINT64_C(1099511628211);
	}
	record->fdt_bytes = bytes;
	record->fdt_fingerprint = fingerprint;
	record->blockers &= ~UFS_PROBE_INVALID_FDT;
}
#endif

uint64_t
duchamp_phone_capture_checksum(const struct duchamp_phone_capture_record *record)
{
	const unsigned char *bytes = (const unsigned char *)(const void *)record;
	uint64_t value = UINT64_C(1469598103934665603);

	for (size_t index = 0;
	    index < offsetof(struct duchamp_phone_capture_record, checksum);
	    index++) {
		value ^= bytes[index];
		value *= UINT64_C(1099511628211);
	}
	return value;
}

unsigned
duchamp_phone_capture_run(volatile void *framebuffer, size_t stride,
	size_t width, size_t height, uint64_t entry_pc, uint64_t entry_x0,
	uint64_t current_el, uint64_t sctlr, unsigned entry_result,
	struct duchamp_phone_capture_record *record)
{
	volatile unsigned char *base =
	    (volatile unsigned char *)(volatile void *)framebuffer;
	char pc_line[LINE_CHARACTERS];
	char x0_line[LINE_CHARACTERS];
	size_t first_y;
	size_t second_y;
	size_t start_x;

	if (record == NULL) return DUCHAMP_PHONE_CAPTURE_BAD_FRAMEBUFFER;
	record->magic = DUCHAMP_PHONE_CAPTURE_MAGIC;
	record->version = DUCHAMP_PHONE_CAPTURE_VERSION;
	record->size = sizeof(*record);
	record->entry_pc = entry_pc;
	record->entry_x0 = entry_x0;
	record->current_el = current_el;
	record->sctlr = sctlr;
	record->entry_result = entry_result;
	record->render_state = DUCHAMP_PHONE_CAPTURE_NOT_RENDERED;
	record->checksum = duchamp_phone_capture_checksum(record);

	if ((current_el != UINT64_C(4) && current_el != UINT64_C(8)) ||
	    (sctlr & (SCTLR_M | SCTLR_C | SCTLR_I)) != 0)
		return DUCHAMP_PHONE_CAPTURE_UNSAFE_ENTRY;
	if (base == NULL || stride < width * sizeof(uint32_t) ||
	    width < LINE_WIDTH || height < GLYPH_HEIGHT * GLYPH_SCALE * 3U)
		return DUCHAMP_PHONE_CAPTURE_BAD_FRAMEBUFFER;

	record->render_state = DUCHAMP_PHONE_CAPTURE_RENDERING;
	record->checksum = duchamp_phone_capture_checksum(record);
	format_line(pc_line, 'P', 'C', entry_pc);
	format_line(x0_line, 'X', '0', entry_x0);
	fill_screen(base, stride, width, height, COLOR_BLACK);
	start_x = (width - LINE_WIDTH) / 2U;
	first_y = height / 4U;
	second_y = first_y + GLYPH_HEIGHT * GLYPH_SCALE + 4U * GLYPH_SCALE;
	draw_line(base, stride, start_x, first_y, pc_line);
	draw_line(base, stride, start_x, second_y, x0_line);
#if defined(DUCHAMP_UFS_HANDOFF_PROBE)
	const size_t line_step = (GLYPH_HEIGHT + 4U) * GLYPH_SCALE;
	const size_t fourth_y = second_y + 2U * line_step;
	capture_ufs_handoff(entry_x0, entry_result);
	if (fourth_y + GLYPH_HEIGHT * GLYPH_SCALE <= height) {
		char line[LINE_CHARACTERS];
		format_line(line, 'D', '0',
		    duchamp_bootshim_ufs_handoff_record.fdt_fingerprint);
		draw_line(base, stride, start_x, second_y + line_step, line);
		format_line(line, 'D', '1',
		    duchamp_bootshim_ufs_handoff_record.blockers);
		draw_line(base, stride, start_x, fourth_y, line);
	}
#endif
#if defined(__aarch64__) && !defined(DUCHAMP_TEST_NO_ARCH_BARRIER)
	__asm__ volatile("dsb sy; isb" ::: "memory");
#endif
	record->render_state = DUCHAMP_PHONE_CAPTURE_COMPLETE;
	record->checksum = duchamp_phone_capture_checksum(record);
	return DUCHAMP_PHONE_CAPTURE_OK;
}
