#include "phone_capture.h"

#if defined(DUCHAMP_UFS_HANDOFF_PROBE)
#include "../loader/mt6897_entry.h"
#include "ufs_handoff_evidence.h"
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

#if defined(DUCHAMP_KPD_PROBE)
#if defined(DUCHAMP_KPD_PROBE_QEMU)
#define KPD_BASE UINT64_C(0x41000000)
#define KPD_ENTRY_PC UINT64_C(0x40200000)
#define KPD_ENTRY_X0 UINT64_C(0x48000000)
#else
#define KPD_BASE UINT64_C(0x1c00e000)
#define KPD_ENTRY_PC UINT64_C(0x40000000)
#define KPD_ENTRY_X0 UINT64_C(0x47c80000)
#endif
#define KP_MEM1 0x04U
#define KP_EN 0x24U
#define KPD_PRESS_WINDOW_SECONDS 12U
#define KPD_RELEASE_WINDOW_SECONDS 5U
#define KPD_SAMPLES_PER_SECOND 200U
#define KPD_STALLED_COUNTER_LIMIT 200000U

enum kpd_probe_stage {
	KPD_LAYOUT_REJECTED,
	KPD_READING_ENABLE,
	KPD_NOT_ENABLED,
	KPD_READING_MEM1,
	KPD_VOLUME_UP_RELEASED,
	KPD_VOLUME_UP_PRESSED,
	KPD_WAIT_PRESS,
	KPD_WAIT_RELEASE,
	KPD_PRESS_RELEASE,
	KPD_NO_PRESS,
	KPD_PRESS_ONLY,
	KPD_COUNTER_UNAVAILABLE,
};

/* D2 packs the initial, pressed, and released snapshots in that order. */
volatile struct kpd_probe_record {
	uint32_t stage;
	uint16_t enable;
	uint16_t mem1;
	uint16_t initial;
	uint16_t pressed;
	uint16_t released;
	uint16_t last_raw;
} duchamp_bootshim_kpd_probe_record;

static uint64_t
kpd_counter(void)
{
	uint64_t value;
	__asm__ volatile("mrs %0, cntpct_el0" : "=r"(value));
	return value;
}

static void
show_kpd_stage(volatile unsigned char *base, size_t stride, size_t x,
	size_t y, enum kpd_probe_stage stage)
{
	char line[LINE_CHARACTERS];
	const size_t step = (GLYPH_HEIGHT + 4U) * GLYPH_SCALE;
	const uint32_t raw = ((uint32_t)duchamp_bootshim_kpd_probe_record.enable << 16) |
	    duchamp_bootshim_kpd_probe_record.mem1;
	const uint64_t sequence =
	    ((uint64_t)duchamp_bootshim_kpd_probe_record.initial << 32) |
	    ((uint64_t)duchamp_bootshim_kpd_probe_record.pressed << 16) |
	    duchamp_bootshim_kpd_probe_record.released;

	fill_screen(base + y * stride + x * sizeof(uint32_t),
	    stride, LINE_WIDTH, 4U * step, COLOR_BLACK);
	format_line(line, 'D', '0', stage);
	draw_line(base, stride, x, y, line);
	format_line(line, 'D', '1', raw);
	draw_line(base, stride, x, y + step, line);
	format_line(line, 'D', '2', sequence);
	draw_line(base, stride, x, y + 2U * step, line);
	format_line(line, 'D', '3', duchamp_bootshim_kpd_probe_record.last_raw);
	draw_line(base, stride, x, y + 3U * step, line);
	duchamp_bootshim_kpd_probe_record.stage = stage;
	__asm__ volatile("dsb sy" ::: "memory");
}

static enum kpd_probe_stage
watch_kpd(volatile unsigned char *base, size_t stride, size_t x, size_t y,
	const volatile uint16_t *mem1_register, uint16_t initial)
{
	uint64_t frequency;
	__asm__ volatile("mrs %0, cntfrq_el0" : "=r"(frequency));
	if (frequency < KPD_SAMPLES_PER_SECOND)
		return KPD_COUNTER_UNAVAILABLE;

	/* The countdown starts after the wait marker is visible. */
	show_kpd_stage(base, stride, x, y, KPD_WAIT_PRESS);
	uint64_t phase_start = kpd_counter();
	uint64_t duration = frequency * KPD_PRESS_WINDOW_SECONDS;
	const uint64_t interval = frequency / KPD_SAMPLES_PER_SECOND;
	uint64_t last_sample = phase_start;
	uint64_t previous_tick = phase_start;
	unsigned stalled = 0;
	unsigned changed = 0;
	unsigned stable_released = initial & 1U;
	int armed = stable_released != 0;
	int saw_press = 0;

	for (;;) {
		const uint64_t now = kpd_counter();
		if (now - phase_start >= duration) {
			duchamp_bootshim_kpd_probe_record.last_raw = *mem1_register;
			return saw_press ? KPD_PRESS_ONLY : KPD_NO_PRESS;
		}
		stalled = now == previous_tick ? stalled + 1U : 0;
		if (stalled == KPD_STALLED_COUNTER_LIMIT)
			return KPD_COUNTER_UNAVAILABLE;
		previous_tick = now;
		if (now - last_sample < interval) {
			__asm__ volatile("yield");
			continue;
		}
		last_sample = now;
		const uint16_t mem1 = *mem1_register;
		duchamp_bootshim_kpd_probe_record.last_raw = mem1;
		const unsigned released = mem1 & 1U;
		if (released == stable_released) {
			changed = 0;
			continue;
		}
		if (++changed < 2U)
			continue;
		changed = 0;
		stable_released = released;
		duchamp_bootshim_kpd_probe_record.mem1 = mem1;
		if (released) {
			if (saw_press) {
				duchamp_bootshim_kpd_probe_record.released = mem1;
				return KPD_PRESS_RELEASE;
			}
			armed = 1;
			show_kpd_stage(base, stride, x, y, KPD_WAIT_PRESS);
		} else if (armed) {
			saw_press = 1;
			phase_start = now;
			duration = frequency * KPD_RELEASE_WINDOW_SECONDS;
			duchamp_bootshim_kpd_probe_record.pressed = mem1;
			show_kpd_stage(base, stride, x, y, KPD_WAIT_RELEASE);
		}
	}
}

static void
capture_kpd(volatile unsigned char *base, size_t stride, size_t x,
	size_t y, uint64_t entry_pc, uint64_t entry_x0)
{
	enum kpd_probe_stage stage = KPD_LAYOUT_REJECTED;

	if (entry_pc == KPD_ENTRY_PC && entry_x0 == KPD_ENTRY_X0) {
		show_kpd_stage(base, stride, x, y, KPD_READING_ENABLE);
		const uint16_t enabled =
		    *(const volatile uint16_t *)(uintptr_t)(KPD_BASE + KP_EN);
		duchamp_bootshim_kpd_probe_record.enable = enabled;
		stage = KPD_NOT_ENABLED;
		if (enabled == 1U) {
			show_kpd_stage(base, stride, x, y, KPD_READING_MEM1);
			const volatile uint16_t *mem1_register =
			    (const volatile uint16_t *)(uintptr_t)(KPD_BASE + KP_MEM1);
			const uint16_t mem1 = *mem1_register;
			duchamp_bootshim_kpd_probe_record.mem1 = mem1;
			duchamp_bootshim_kpd_probe_record.initial = mem1;
			duchamp_bootshim_kpd_probe_record.last_raw = mem1;
			stage = (mem1 & 1U) ? KPD_VOLUME_UP_RELEASED : KPD_VOLUME_UP_PRESSED;
			show_kpd_stage(base, stride, x, y, stage);
			stage = watch_kpd(base, stride, x, y, mem1_register, mem1);
		}
	}
	show_kpd_stage(base, stride, x, y, stage);
}
#endif

#if defined(DUCHAMP_PMIF_PROBE)
#if defined(DUCHAMP_PMIF_PROBE_QEMU)
#define PMIF_PROBE_BASE UINT64_C(0x41000000)
#define PMIF_ENTRY_PC UINT64_C(0x40200000)
#define PMIF_ENTRY_X0 UINT64_C(0x48000000)
#else
#define PMIF_PROBE_BASE UINT64_C(0x1cc04000)
#define PMIF_ENTRY_PC UINT64_C(0x40000000)
#define PMIF_ENTRY_X0 UINT64_C(0x47c80000)
#endif
#define PMIF_INIT_DONE 0x000U
#define PMIF_SWINF2_STA 0x8a8U

enum pmif_probe_stage {
	PMIF_LAYOUT_REJECTED,
	PMIF_READING_INIT,
	PMIF_INIT_UNAVAILABLE,
	PMIF_READING_SWINF2,
	PMIF_SWINF2_IDLE,
	PMIF_SWINF2_NONIDLE,
	PMIF_SWINF2_UNAVAILABLE,
};

volatile struct pmif_probe_record {
	uint32_t stage;
	uint32_t init_done;
	uint32_t swinf2_status;
} duchamp_bootshim_pmif_probe_record;

static void
show_pmif_stage(volatile unsigned char *base, size_t stride, size_t x,
	size_t y, enum pmif_probe_stage stage)
{
	char line[LINE_CHARACTERS];
	const size_t step = (GLYPH_HEIGHT + 4U) * GLYPH_SCALE;
	const uint64_t raw =
	    ((uint64_t)duchamp_bootshim_pmif_probe_record.init_done << 32) |
	    duchamp_bootshim_pmif_probe_record.swinf2_status;

	fill_screen(base + y * stride + x * sizeof(uint32_t),
	    stride, LINE_WIDTH, 2U * step, COLOR_BLACK);
	format_line(line, 'D', '0', stage);
	draw_line(base, stride, x, y, line);
	format_line(line, 'D', '1', raw);
	draw_line(base, stride, x, y + step, line);
	duchamp_bootshim_pmif_probe_record.stage = stage;
	__asm__ volatile("dsb sy" ::: "memory");
}

static void
capture_pmif(volatile unsigned char *base, size_t stride, size_t x,
	size_t y, uint64_t entry_pc, uint64_t entry_x0)
{
	enum pmif_probe_stage stage = PMIF_LAYOUT_REJECTED;

	if (entry_pc == PMIF_ENTRY_PC && entry_x0 == PMIF_ENTRY_X0) {
		show_pmif_stage(base, stride, x, y, PMIF_READING_INIT);
		const uint32_t init =
		    *(const volatile uint32_t *)(uintptr_t)(PMIF_PROBE_BASE + PMIF_INIT_DONE);
		duchamp_bootshim_pmif_probe_record.init_done = init;
		stage = PMIF_INIT_UNAVAILABLE;
		if (init != UINT32_MAX && (init & 1U) != 0) {
			show_pmif_stage(base, stride, x, y, PMIF_READING_SWINF2);
			const uint32_t status =
			    *(const volatile uint32_t *)(uintptr_t)(PMIF_PROBE_BASE + PMIF_SWINF2_STA);
			duchamp_bootshim_pmif_probe_record.swinf2_status = status;
			stage = PMIF_SWINF2_UNAVAILABLE;
			if (status != UINT32_MAX)
				stage = ((status >> 1) & 7U) == 0 ?
				    PMIF_SWINF2_IDLE : PMIF_SWINF2_NONIDLE;
		}
	}
	show_pmif_stage(base, stride, x, y, stage);
}
#endif

#if defined(DUCHAMP_UFS_HANDOFF_PROBE)
#define UFS_PROBE_FDT_BEGIN UINT64_C(0x40000000)
#define UFS_PROBE_FDT_END UINT64_C(0x80000000)

struct duchamp_ufs_handoff_record duchamp_bootshim_ufs_handoff_record;

static void
capture_ufs_handoff(uint64_t address, unsigned entry_result)
{
	const volatile unsigned char *fdt = NULL;
	size_t available = 0;
	if (entry_result == DUCHAMP_ENTRY_OK && address >= UFS_PROBE_FDT_BEGIN &&
	    address <= UFS_PROBE_FDT_END - 40) {
		fdt = (const volatile unsigned char *)(uintptr_t)address;
		available = UFS_PROBE_FDT_END - address;
	}
	duchamp_ufs_handoff_collect(&duchamp_bootshim_ufs_handoff_record,
	    fdt, available);
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
#if defined(DUCHAMP_PMIF_PROBE)
	const size_t pmif_step = (GLYPH_HEIGHT + 4U) * GLYPH_SCALE;
	if (second_y + 3U * pmif_step <= height)
		capture_pmif(base, stride, start_x, second_y + pmif_step,
		    entry_pc, entry_x0);
#endif
#if defined(DUCHAMP_KPD_PROBE)
	const size_t kpd_step = (GLYPH_HEIGHT + 4U) * GLYPH_SCALE;
	if (second_y + 5U * kpd_step <= height)
		capture_kpd(base, stride, start_x, second_y + kpd_step,
		    entry_pc, entry_x0);
#endif
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
		const size_t fifth_y = fourth_y + line_step;
		if (fifth_y + GLYPH_HEIGHT * GLYPH_SCALE <= height) {
			const struct duchamp_ufs_handoff_record *evidence =
			    &duchamp_bootshim_ufs_handoff_record;
			format_line(line, 'D', '2',
			    (uint64_t)evidence->slot_hint << 32 | evidence->declarations);
			draw_line(base, stride, start_x, fifth_y, line);
		}
	}
#endif
#if defined(__aarch64__) && !defined(DUCHAMP_TEST_NO_ARCH_BARRIER)
	__asm__ volatile("dsb sy; isb" ::: "memory");
#endif
	record->render_state = DUCHAMP_PHONE_CAPTURE_COMPLETE;
	record->checksum = duchamp_phone_capture_checksum(record);
	return DUCHAMP_PHONE_CAPTURE_OK;
}
