#include <stddef.h>
#include <stdint.h>

#include "boot_menu.h"
#include "../../shim/font.h"

#if !defined(DUCHAMP_QEMU_ONLY)
#error "The boot menu input backend requires QEMU virt"
#endif

#define QEMU_UART_BASE UINT64_C(0x09000000)
#define UART_DR 0x00
#define UART_FR 0x18
#define UART_IBRD 0x24
#define UART_FBRD 0x28
#define UART_LCRH 0x2c
#define UART_CR 0x30
#define UART_RX_EMPTY (1U << 4)
#define UART_TX_FULL (1U << 5)

#define BACKGROUND UINT32_C(0xff111923)
#define ROW_NORMAL UINT32_C(0xff1b2937)
#define ROW_SELECTED UINT32_C(0xff185c61)
#define TEXT UINT32_C(0xfff4f8fc)
#define MUTED UINT32_C(0xffb2c8d6)
#define ACCENT UINT32_C(0xff62ddd2)

#define MENU_SECONDS 10U
#define SLOT_ACK_SECONDS 2U
#define ROW_HEIGHT 152U
#define ROW_GAP 20U
#define MARGIN 90U

#if defined(DUCHAMP_XNU_JUMP)
/* Clang can lower the loader's boot-argument struct copy to a libc call. */
void *
memcpy(void *destination, const void *source, size_t size)
{
	volatile unsigned char *out = destination;
	const unsigned char *in = source;
	for (size_t i = 0; i < size; i++)
		out[i] = in[i];
	return destination;
}
#endif

static volatile uint32_t *
uart(unsigned offset)
{
	return (volatile uint32_t *)(uintptr_t)(QEMU_UART_BASE + offset);
}

static void
uart_log(const char *text)
{
	for (; *text != '\0'; text++) {
		while (*uart(UART_FR) & UART_TX_FULL)
			__asm__ volatile("yield");
		*uart(UART_DR) = (uint32_t)*text;
	}
}

static uint64_t
counter(void)
{
	uint64_t ticks;
	__asm__ volatile("mrs %0, cntpct_el0" : "=r"(ticks));
	return ticks;
}

static void
rectangle(const struct duchamp_framebuffer *fb, unsigned x, unsigned y,
    unsigned width, unsigned height, uint32_t color)
{
	for (unsigned j = 0; j < height; j++) {
		volatile uint32_t *row = (volatile uint32_t *)(uintptr_t)
		    (fb->base + (y + j) * fb->stride);
		for (unsigned i = 0; i < width; i++)
			row[x + i] = color;
	}
}

static void
draw_text(const struct duchamp_framebuffer *fb, unsigned x, unsigned y,
    unsigned scale, const char *text, uint32_t color)
{
	for (; *text != '\0'; text++, x += 8 * scale) {
		const unsigned char *glyph = font8x16[(unsigned char)*text - ' '];
		for (unsigned row = 0; row < 16; row++) {
			for (unsigned col = 0; col < 8; col++) {
				if (glyph[row] & (0x80U >> col))
					rectangle(fb, x + col * scale, y + row * scale,
					    scale, scale, color);
			}
		}
	}
}

static void
draw_choices(const struct duchamp_framebuffer *fb, unsigned y, unsigned focus)
{
	static const char *const names[] = {"Android", "XNU"};
	static const char *const slots[] = {"Slot A", "Slot B"};

	for (unsigned item = 0; item < 2; item++, y += ROW_HEIGHT + ROW_GAP) {
		rectangle(fb, MARGIN, y, (unsigned)fb->width - 2 * MARGIN,
		    ROW_HEIGHT, item == focus ? ROW_SELECTED : ROW_NORMAL);
		if (item == focus)
			rectangle(fb, MARGIN, y, 8, ROW_HEIGHT, ACCENT);
		draw_text(fb, MARGIN + 36, y + 24, 4, names[item], TEXT);
		draw_text(fb, MARGIN + 36, y + 96, 2, slots[item], MUTED);
	}
}

/* A QEMU host stands in for the firmware's next-slot selector and readback. */
static void
request_android(const struct duchamp_framebuffer *fb, unsigned y, uint64_t frequency)
{
	draw_text(fb, MARGIN, y, 3, "Requesting Android Slot A...", ACCENT);
	__asm__ volatile("dsb sy" ::: "memory");

	/* Discard any bytes buffered with the menu key before requesting readback. */
	for (unsigned i = 0; i < 16 && !(*uart(UART_FR) & UART_RX_EMPTY); i++)
		(void)*uart(UART_DR);
	uart_log("DUCHAMP ANDROID NEXT SLOT REQUEST A\n");
	const uint64_t start = counter();
	const char *failure = "DUCHAMP ANDROID BLOCKED NO READBACK\n";
	while (counter() - start < frequency * SLOT_ACK_SECONDS) {
		if (*uart(UART_FR) & UART_RX_EMPTY) {
			__asm__ volatile("yield");
			continue;
		}
		const uint32_t readback = *uart(UART_DR);
		if (readback == 'A') {
			uart_log("DUCHAMP ANDROID NEXT SLOT VERIFIED A\n");
			register uint64_t function __asm__("x0") = UINT64_C(0x84000009);
			__asm__ volatile("dsb sy; hvc #0" : "+r"(function) :: "memory");
			failure = "DUCHAMP ANDROID BLOCKED RESET RETURNED\n";
			break;
		}
		if (readback == 'B' || readback == '!') {
			failure = "DUCHAMP ANDROID BLOCKED NEXT SLOT\n";
			break;
		}
	}
	rectangle(fb, MARGIN, y, (unsigned)fb->width - 2 * MARGIN, 48, BACKGROUND);
	draw_text(fb, MARGIN, y, 3, "Android return unavailable", MUTED);
	__asm__ volatile("dsb sy" ::: "memory");
	uart_log(failure);
}

/* The only input is QEMU virt's PL011, standing in for the three phone keys. */
int
duchamp_boot_menu_qemu(const struct duchamp_framebuffer *fb, int xnu_available)
{
	uint64_t frequency;
	__asm__ volatile("mrs %0, cntfrq_el0" : "=r"(frequency));
	if (frequency == 0)
		return 0;

	*uart(UART_CR) = 0;
	*uart(UART_IBRD) = 13;
	*uart(UART_FBRD) = 1;
	*uart(UART_LCRH) = 0x70;
	*uart(UART_CR) = 0x301;

	const unsigned top = (unsigned)fb->height / 2 - 350;
	const unsigned rows = top + 196;
	unsigned focus = 0;
	rectangle(fb, 0, 0, (unsigned)fb->width, (unsigned)fb->height, BACKGROUND);
	draw_text(fb, MARGIN, top, 6, "Choose a system", TEXT);
	draw_text(fb, MARGIN, top + 122, 3, "Duchamp  /  QEMU", MUTED);
	draw_choices(fb, rows, focus);
	draw_text(fb, MARGIN, rows + 400, 3, "W / S to select   Enter to confirm", TEXT);
	draw_text(fb, MARGIN, rows + 460, 3, "Android is the default (10 sec)", MUTED);
	__asm__ volatile("dsb sy" ::: "memory");
	const uint64_t start = counter();
	uart_log("DUCHAMP MENU READY\n");

	while (counter() - start < frequency * MENU_SECONDS) {
		if (*uart(UART_FR) & UART_RX_EMPTY) {
			__asm__ volatile("yield");
			continue;
		}
		const uint32_t input = *uart(UART_DR);
		if (input == 'w' || input == 's') {
			focus ^= 1;
			draw_choices(fb, rows, focus);
			__asm__ volatile("dsb sy" ::: "memory");
			uart_log(focus ? "DUCHAMP MENU FOCUS B\n" : "DUCHAMP MENU FOCUS A\n");
		} else if (input == '\r' || input == '\n') {
			goto confirmed;
		}
	}

	focus = 0;
	draw_choices(fb, rows, focus);
	__asm__ volatile("dsb sy" ::: "memory");
	uart_log("DUCHAMP MENU CHOICE A TIMEOUT\n");
	request_android(fb, rows + 536, frequency);
	return 0;

confirmed:
	if (!focus) {
		uart_log("DUCHAMP MENU CHOICE A CONFIRMED\n");
		request_android(fb, rows + 536, frequency);
		return 0;
	}
	draw_text(fb, MARGIN, rows + 536, 3, "XNU selected", ACCENT);
	__asm__ volatile("dsb sy" ::: "memory");
	uart_log(xnu_available ? "DUCHAMP MENU CHOICE B XNU\n" :
	    "DUCHAMP MENU CHOICE B PREVIEW\n");
	return xnu_available;
}
