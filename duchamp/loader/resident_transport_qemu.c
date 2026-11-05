#include <stddef.h>
#include <stdint.h>

#include "mt6897_lk_transport.h"

#define FB_BASE UINT64_C(0xfcc2f000)
#define FB_STRIDE UINT64_C(4992)
#define FB_WIDTH UINT64_C(1220)
#define FB_HEIGHT UINT64_C(2712)
#define BAND_HEIGHT (FB_HEIGHT / 12)
#define COLOR_PASS UINT32_C(0xff00ff00)
#define COLOR_FAIL UINT32_C(0xffff0000)
#define COLOR_A UINT32_C(0xff00ffff)
#define COLOR_B UINT32_C(0xffff00ff)

struct entry_state {
	uint64_t current_el, sctlr_el1, x0, x1, x2, x3, sp;
};

struct entry_state duchamp_bootshim_entry_state;

struct callback_state {
	struct duchamp_resident_loader *loader;
	unsigned prepare_calls;
	unsigned enter_calls;
};

static void
draw_row(unsigned row, uint32_t color)
{
	volatile uint32_t *framebuffer =
	    (volatile uint32_t *)(uintptr_t)FB_BASE;
	uint64_t line, column;
	for (line = row * BAND_HEIGHT; line < (row + 1) * BAND_HEIGHT;
	    line++) {
		volatile uint32_t *pixels = (volatile uint32_t *)
		    ((uintptr_t)framebuffer + line * FB_STRIDE);
		for (column = 0; column < FB_WIDTH; column++) {
			pixels[column] = color;
		}
	}
}

static void
put_le32(unsigned char *bytes, uint32_t value)
{
	unsigned index;
	for (index = 0; index < 4; index++) {
		bytes[index] = (unsigned char)(value >> (index * 8));
	}
}

static void
put_le64(unsigned char *bytes, uint64_t value)
{
	unsigned index;
	for (index = 0; index < 8; index++) {
		bytes[index] = (unsigned char)(value >> (index * 8));
	}
}

static unsigned
prepare(void *context_pointer, const void *payload, size_t payload_size,
	struct duchamp_resident_target *target)
{
	struct callback_state *context = context_pointer;
	const unsigned char *bytes = payload;
	context->prepare_calls++;
	if (payload_size != 8 || bytes[0] != 'S' || bytes[7] != 'U') {
		return 1;
	}
	target->entry = UINT64_C(0x1c1480488);
	target->boot_args = UINT64_C(0x1c256c000);
	return 0;
}

static unsigned
enter(void *context_pointer, const struct duchamp_resident_target *target)
{
	static const unsigned char result[4] = {'P', 'A', 'S', 'S'};
	struct callback_state *context = context_pointer;
	context->enter_calls++;
	if (target->entry != UINT64_C(0x1c1480488) ||
	    target->boot_args != UINT64_C(0x1c256c000)) {
		return 1;
	}
	return duchamp_resident_complete(context->loader, 42, result,
	    sizeof(result));
}

void
duchamp_bootshim_exception(uint64_t kind, uint64_t esr, uint64_t elr,
	uint64_t far, uint64_t sp)
{
	unsigned row;
	(void)kind;
	(void)esr;
	(void)elr;
	(void)far;
	(void)sp;
	for (row = 0; row < 12; row++) {
		draw_row(row, COLOR_FAIL);
	}
}

void
duchamp_bootshim_main(void)
{
	static const unsigned char payload[8] = {
	    'S', 'W', 'E', 'E', 'T', 'X', 'N', 'U'
	};
	static unsigned char capsule[DUCHAMP_MT6897_LK_CAPSULE_HEADER_SIZE + 8];
	static unsigned char staging[32], result[32], scratch[3];
	static struct duchamp_resident_loader loader;
	static struct duchamp_resident_transport transport;
	static struct duchamp_mt6897_lk_source source;
	static struct callback_state callbacks;
	static struct duchamp_resident_transport_status status;
	static struct duchamp_resident_result_view view;
	const struct duchamp_resident_ops run_ops = {prepare, enter};
	unsigned pass[8] = {0, 0, 0, 0, 0, 0, 0, 0};
	unsigned row, index;

	for (index = 0; index < 8; index++) {
		capsule[index] = ((const unsigned char *)"DUCHLKR1")[index];
	}
	put_le32(capsule + 8, DUCHAMP_MT6897_LK_CAPSULE_VERSION);
	put_le32(capsule + 12, DUCHAMP_MT6897_LK_CAPSULE_HEADER_SIZE);
	put_le64(capsule + 16, sizeof(capsule));
	put_le64(capsule + 24, 7);
	put_le64(capsule + 32, DUCHAMP_MT6897_LK_CAPSULE_HEADER_SIZE);
	put_le64(capsule + 40, sizeof(payload));
	put_le64(capsule + 48,
	    duchamp_resident_receipt(payload, sizeof(payload)));
	put_le64(capsule + 56, DUCHAMP_MT6897_LK_CAPSULE_FLAG_IMMUTABLE);
	for (index = 0; index < sizeof(payload); index++) {
		capsule[DUCHAMP_MT6897_LK_CAPSULE_HEADER_SIZE + index] =
		    payload[index];
	}
	pass[0] = duchamp_resident_init(&loader, staging, sizeof(staging),
	    result, sizeof(result), 7) == 0;
	callbacks.loader = &loader;
	pass[1] = pass[0] && duchamp_mt6897_lk_source_init(&source, capsule,
	    sizeof(capsule)) == 0;
	pass[2] = pass[1] && duchamp_resident_transport_init(&transport,
	    &loader, &run_ops, &callbacks, &duchamp_mt6897_lk_source_ops,
	    &source, scratch, sizeof(scratch)) == 0;
	pass[3] = pass[2] && duchamp_resident_transport_run(&transport) == 0;
	pass[4] = pass[3] && callbacks.prepare_calls == 1 &&
	    callbacks.enter_calls == 1 && source.read_calls == 3;
	pass[5] = pass[4] && duchamp_resident_transport_get_status(&transport,
	    &status) == 0 && status.state == DUCHAMP_TRANSPORT_COMPLETE &&
	    status.bytes_read == sizeof(payload);
	pass[6] = pass[5] && duchamp_resident_get_result(&loader, &view) == 0 &&
	    view.size == 4 && ((const unsigned char *)view.data)[0] == 'P' &&
	    ((const unsigned char *)view.data)[3] == 'S';
	pass[7] = pass[6] && duchamp_resident_transport_run(&transport) ==
	    DUCHAMP_TRANSPORT_RELOAD_REQUIRED && source.read_calls == 3;
	for (row = 0; row < 8; row++) {
		draw_row(row, pass[row] ? COLOR_PASS : COLOR_FAIL);
	}
	draw_row(8, COLOR_A);
	draw_row(9, COLOR_B);
	draw_row(10, COLOR_A);
	draw_row(11, COLOR_B);
	__asm__ volatile("dsb sy; isb" ::: "memory");
}
