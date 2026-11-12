#include <stddef.h>
#include <stdint.h>

#include "diagnostic.h"
#include "../loader/mt6897_entry.h"
#if defined(DUCHAMP_BOOT_MENU)
#include "boot_menu.h"
#endif
#if defined(DUCHAMP_EMBED_PAYLOAD)
#include "payload_preflight.h"
#endif
#if defined(DUCHAMP_MATERIALIZE_PAYLOAD)
#include "../loader/materialize.h"
#endif
#if defined(DUCHAMP_XNU_RETURN)
#include "../loader/return_slot.h"
#include "xnu_return.h"
#endif
#if defined(DUCHAMP_HANDOFF_READY)
#include "handoff_ready.h"
#endif
#if defined(DUCHAMP_QEMU_BL31_RECEIVER)
#include "qemu_bl31_receiver.h"
#endif
#if defined(DUCHAMP_LK_RAM_TRANSPORT)
#if !defined(DUCHAMP_QEMU_ONLY)
#error "DUCHAMP_LK_RAM_TRANSPORT is restricted to QEMU-only builds"
#endif
#if defined(DUCHAMP_EMBED_PAYLOAD) || defined(DUCHAMP_XNU_JUMP)
#error "LK RAM transport cannot be combined with the legacy payload or jump"
#endif
#include "lk_ram_boot.h"
#include "../loader/mt6897_ram_provider.h"
#include "../loader/resident_transport.h"
#endif

#define FDT_LOW_BASE UINT64_C(0x40000000)
#define FDT_LOW_SIZE UINT64_C(0x40000000)
#define FDT_MAX_SIZE UINT32_C(0x200000)
#define FDT_MAGIC UINT32_C(0xd00dfeed)
#define FB_BASE UINT64_C(0xfcc2f000)
#define FB_STRIDE UINT64_C(4992)
#define FB_WIDTH UINT64_C(1220)
#define FB_HEIGHT UINT64_C(2712)
#define MARKER_ROWS UINT64_C(12)
#define BAND_HEIGHT (FB_HEIGHT / MARKER_ROWS)
#define COLOR_PASS UINT32_C(0xff00ff00)
#define COLOR_FAIL UINT32_C(0xffff0000)
#define COLOR_SIGNATURE_A UINT32_C(0xff00ffff)
#define COLOR_SIGNATURE_B UINT32_C(0xffff00ff)
#define WDT_BASE UINT64_C(0x1c00a000)
#define WDT_MODE_OFFSET UINT64_C(0)
#define WDT_MODE_ENABLE UINT32_C(1)
#define WDT_MODE_KEY UINT32_C(0x22000000)

struct duchamp_mt6897_entry_state duchamp_bootshim_entry_state;
struct duchamp_bootshim_diagnostic duchamp_bootshim_diagnostic;
#if defined(DUCHAMP_EMBED_PAYLOAD)
extern const unsigned char duchamp_embedded_payload_start[];
extern const unsigned char duchamp_embedded_payload_end[];
struct duchamp_payload_preflight duchamp_bootshim_payload_report;
#endif
#if defined(DUCHAMP_MATERIALIZE_PAYLOAD)
struct duchamp_dry_run_plan duchamp_bootshim_materialized_plan;
uint32_t duchamp_bootshim_materialize_result;
#endif
#if defined(DUCHAMP_XNU_RETURN)
struct duchamp_return_slot_report duchamp_bootshim_return_slot_report;
uint32_t duchamp_bootshim_return_slot_result;
struct duchamp_xnu_return_record duchamp_bootshim_xnu_return_record;
unsigned char duchamp_bootshim_xnu_log[DUCHAMP_XNU_RETURN_LOG_BYTES];
void duchamp_xnu_return_stub(void);
#ifndef DUCHAMP_RETURN_CHECKPOINT
#define DUCHAMP_RETURN_CHECKPOINT 0
#endif
#endif
#if defined(DUCHAMP_HANDOFF_READY)
struct duchamp_handoff_ready duchamp_bootshim_ready_report;
#if defined(DUCHAMP_XNU_JUMP)
__attribute__((noreturn)) void duchamp_enter_xnu(uint64_t entry,
	uint64_t boot_args);
#endif
#endif
#if defined(DUCHAMP_LK_RAM_TRANSPORT)
extern const unsigned char duchamp_lk_ram_capsule_start[];
extern const unsigned char duchamp_lk_ram_capsule_end[];
extern const unsigned char _head[];
extern const unsigned char _end[];
struct duchamp_mt6897_ram_provider_report
    duchamp_bootshim_ram_provider_report;
#endif

struct duchamp_exception_record {
	uint64_t kind;
	uint64_t esr;
	uint64_t elr;
	uint64_t far;
	uint64_t sp;
};
volatile struct duchamp_exception_record duchamp_bootshim_exception_record;

static uint64_t
diagnostic_checksum(const struct duchamp_bootshim_diagnostic *diagnostic)
{
	const uint64_t *words = (const uint64_t *)(const void *)diagnostic;
	size_t count = offsetof(struct duchamp_bootshim_diagnostic, checksum) /
	    sizeof(*words);
	uint64_t value = UINT64_C(0x9e3779b97f4a7c15);

	for (size_t i = 0; i < count; i++) {
		value ^= words[i] + UINT64_C(0x9e3779b97f4a7c15) +
		    (value << 6) + (value >> 2);
	}
	return value;
}

static uint32_t
read_be32(const volatile unsigned char *value)
{
	return (uint32_t)value[0] << 24 | (uint32_t)value[1] << 16 |
	       (uint32_t)value[2] << 8 | value[3];
}

static int
fdt_header_valid(uint64_t address)
{
	const volatile unsigned char *fdt =
	    (const volatile unsigned char *)(uintptr_t)address;
	uint32_t total;

	if (read_be32(fdt) != FDT_MAGIC) {
		return 0;
	}
	total = read_be32(fdt + 4);
	return total >= 40 && total <= FDT_MAX_SIZE &&
	       address - FDT_LOW_BASE <= FDT_LOW_SIZE &&
	       total <= FDT_LOW_SIZE - (address - FDT_LOW_BASE);
}

static void
draw_row(uint64_t y, uint32_t color)
{
	for (uint64_t line = y * BAND_HEIGHT;
	    line < (y + 1) * BAND_HEIGHT; line++) {
		volatile uint32_t *row = (volatile uint32_t *)(uintptr_t)
		    (FB_BASE + line * FB_STRIDE);
		for (uint64_t x = 0; x < FB_WIDTH; x++) {
			row[x] = color;
		}
	}
}

#if defined(DUCHAMP_XNU_RETURN)
#if !defined(DUCHAMP_TEST_NO_RETURN_RANGE)
static int
return_log_range_valid(uint64_t address, uint64_t size)
{
	uint64_t offset;

	if (size == 0) return 1;
	if (address < DUCHAMP_PAYLOAD_EXPECTED_BASE) return 0;
	offset = address - DUCHAMP_PAYLOAD_EXPECTED_BASE;
	return offset <= DUCHAMP_PAYLOAD_EXPECTED_SIZE &&
	    size <= DUCHAMP_PAYLOAD_EXPECTED_SIZE - offset;
}
#endif

void
duchamp_bootshim_xnu_return(uint64_t log_pa, uint64_t log_length,
	uint64_t reason, uint64_t code, uint64_t elr, uint64_t far)
{
	const void *source = NULL;
	unsigned result;

#if defined(DUCHAMP_TEST_NO_RETURN_RANGE)
	if (log_length != 0) source = (const void *)(uintptr_t)log_pa;
#else
	if (return_log_range_valid(log_pa, log_length) && log_length != 0)
		source = (const void *)(uintptr_t)log_pa;
#endif
	result = duchamp_xnu_return_capture(log_pa, log_length, source, reason,
	    code, elr, far, duchamp_bootshim_xnu_log,
	    sizeof(duchamp_bootshim_xnu_log),
	    &duchamp_bootshim_xnu_return_record);
	for (uint64_t row = 0; row < MARKER_ROWS; row++)
		draw_row(row, COLOR_FAIL);
	draw_row(0, result == DUCHAMP_XNU_RETURN_OK ? COLOR_PASS : COLOR_FAIL);
	draw_row(1, duchamp_bootshim_xnu_return_record.magic ==
	    DUCHAMP_XNU_RETURN_MAGIC ? COLOR_PASS : COLOR_FAIL);
	draw_row(2, duchamp_bootshim_xnu_return_record.version ==
	    DUCHAMP_XNU_RETURN_VERSION ? COLOR_PASS : COLOR_FAIL);
	draw_row(3, reason != 0 ? COLOR_PASS : COLOR_FAIL);
	draw_row(4, code != 0 ? COLOR_PASS : COLOR_FAIL);
	draw_row(5, duchamp_bootshim_xnu_return_record.copied != 0 ?
	    COLOR_PASS : COLOR_FAIL);
	draw_row(6, duchamp_bootshim_xnu_return_record.checksum != 0 ?
	    COLOR_PASS : COLOR_FAIL);
	draw_row(7, duchamp_bootshim_xnu_return_record.copied == log_length ?
	    COLOR_PASS : COLOR_FAIL);
	draw_row(8, COLOR_SIGNATURE_B);
	draw_row(9, COLOR_SIGNATURE_A);
	draw_row(10, COLOR_SIGNATURE_B);
	draw_row(11, COLOR_SIGNATURE_A);
	__asm__ volatile("dsb sy; isb" ::: "memory");
}
#endif

void
duchamp_bootshim_exception(uint64_t kind, uint64_t esr, uint64_t elr,
	uint64_t far, uint64_t sp)
{
	duchamp_bootshim_exception_record.kind = kind;
	duchamp_bootshim_exception_record.esr = esr;
	duchamp_bootshim_exception_record.elr = elr;
	duchamp_bootshim_exception_record.far = far;
	duchamp_bootshim_exception_record.sp = sp;
	for (uint64_t row = 0; row < MARKER_ROWS; row++)
		draw_row(row, COLOR_FAIL);
	draw_row(kind & 7, COLOR_SIGNATURE_B);
}

static void
draw_diagnostic(const struct duchamp_bootshim_diagnostic *diagnostic)
{
	uint64_t sctlr = diagnostic->entry.sctlr_el1;
	int fdt_range_ok = diagnostic->entry_result == DUCHAMP_ENTRY_OK;

	draw_row(0, diagnostic->marker == DUCHAMP_MARKER_SUCCESS ?
	    COLOR_PASS : COLOR_FAIL);
	draw_row(1, diagnostic->entry.current_el == 4 ? COLOR_PASS : COLOR_FAIL);
	draw_row(2, (sctlr & UINT64_C(1)) == 0 ? COLOR_PASS : COLOR_FAIL);
	draw_row(3, (sctlr & (UINT64_C(1) << 2)) == 0 ? COLOR_PASS : COLOR_FAIL);
	draw_row(4, (sctlr & (UINT64_C(1) << 12)) == 0 ? COLOR_PASS : COLOR_FAIL);
	draw_row(5, fdt_range_ok ? COLOR_PASS : COLOR_FAIL);
	draw_row(6, diagnostic->fdt_magic == FDT_MAGIC ? COLOR_PASS : COLOR_FAIL);
	draw_row(7, diagnostic->fdt_size >= 40 &&
	    diagnostic->fdt_size <= FDT_MAX_SIZE ? COLOR_PASS : COLOR_FAIL);
	draw_row(8, COLOR_SIGNATURE_A);
	draw_row(9, COLOR_SIGNATURE_B);
	draw_row(10, COLOR_SIGNATURE_A);
	draw_row(11, COLOR_SIGNATURE_B);
#if !defined(DUCHAMP_TEST_NO_WATCHDOG)
	__asm__ volatile("dsb sy; isb" ::: "memory");
#endif
}

#if defined(DUCHAMP_EMBED_PAYLOAD)
static void
draw_payload_report(const struct duchamp_payload_preflight *report)
{
	draw_row(8, report->result == 0 ? COLOR_PASS : COLOR_FAIL);
	draw_row(9, report->segment_count == 10 ? COLOR_PASS : COLOR_FAIL);
	draw_row(10, report->phys_base == DUCHAMP_PAYLOAD_EXPECTED_BASE &&
	    report->memory_size == DUCHAMP_PAYLOAD_EXPECTED_SIZE ?
	    COLOR_PASS : COLOR_FAIL);
	draw_row(11, COLOR_SIGNATURE_B);
#if !defined(DUCHAMP_TEST_NO_WATCHDOG)
	__asm__ volatile("dsb sy; isb" ::: "memory");
#endif
}
#endif

static void
stop_watchdog(struct duchamp_bootshim_diagnostic *diagnostic)
{
#if !defined(DUCHAMP_TEST_NO_WATCHDOG)
	volatile uint32_t *mode = (volatile uint32_t *)(uintptr_t)
	    (WDT_BASE + WDT_MODE_OFFSET);
	uint32_t before = *mode;
	uint32_t after = (before & ~WDT_MODE_ENABLE) | WDT_MODE_KEY;

	diagnostic->watchdog_mode_before = before;
	*mode = after;
	__asm__ volatile("dsb sy; isb" ::: "memory");
	diagnostic->watchdog_mode_after = *mode;
#else
	diagnostic->watchdog_mode_before = 0;
	diagnostic->watchdog_mode_after = 0;
#endif
}

void
duchamp_bootshim_main(void)
{
	unsigned result = duchamp_mt6897_entry_check(
	    &duchamp_bootshim_entry_state, FDT_LOW_BASE, FDT_LOW_SIZE);
	struct duchamp_bootshim_diagnostic *diagnostic =
	    &duchamp_bootshim_diagnostic;

	diagnostic->magic = DUCHAMP_DIAGNOSTIC_MAGIC;
	diagnostic->version = DUCHAMP_DIAGNOSTIC_VERSION;
	diagnostic->size = sizeof(*diagnostic);
	diagnostic->entry_result = result;
	diagnostic->marker = DUCHAMP_MARKER_NONE;
	diagnostic->fdt_magic = 0;
	diagnostic->fdt_size = 0;
	diagnostic->watchdog_mode_before = 0;
	diagnostic->watchdog_mode_after = 0;
	diagnostic->entry.current_el = duchamp_bootshim_entry_state.current_el;
	diagnostic->entry.sctlr_el1 = duchamp_bootshim_entry_state.sctlr_el1;
	diagnostic->entry.entry_x0 = duchamp_bootshim_entry_state.entry_x0;
	diagnostic->entry.entry_x1 = duchamp_bootshim_entry_state.entry_x1;
	diagnostic->entry.entry_x2 = duchamp_bootshim_entry_state.entry_x2;
	diagnostic->entry.entry_x3 = duchamp_bootshim_entry_state.entry_x3;
	diagnostic->entry.entry_sp = duchamp_bootshim_entry_state.entry_sp;

	if ((diagnostic->entry.current_el == 4 ||
	    diagnostic->entry.current_el == 8) &&
	    (diagnostic->entry.sctlr_el1 &
	    (UINT64_C(1) | (UINT64_C(1) << 2) | (UINT64_C(1) << 12))) == 0) {
		stop_watchdog(diagnostic);
	}

	if (result == DUCHAMP_ENTRY_TRANSLATION_STATE ||
	    (result == DUCHAMP_ENTRY_EXCEPTION_LEVEL &&
	    (diagnostic->entry.current_el != 8 ||
	    (diagnostic->entry.sctlr_el1 &
	    (UINT64_C(1) | (UINT64_C(1) << 2) | (UINT64_C(1) << 12))) != 0))) {
		diagnostic->checksum = diagnostic_checksum(diagnostic);
		return;
	}
	if (result == DUCHAMP_ENTRY_EXCEPTION_LEVEL) {
		diagnostic->marker = DUCHAMP_MARKER_FAILURE;
		diagnostic->checksum = diagnostic_checksum(diagnostic);
		draw_diagnostic(diagnostic);
		return;
	}
	if (result == DUCHAMP_ENTRY_OK) {
		const volatile unsigned char *fdt =
		    (const volatile unsigned char *)(uintptr_t)
		    duchamp_bootshim_entry_state.entry_x0;
		diagnostic->fdt_magic = read_be32(fdt);
		diagnostic->fdt_size = read_be32(fdt + 4);
	}
	if (result != DUCHAMP_ENTRY_OK ||
	    !fdt_header_valid(duchamp_bootshim_entry_state.entry_x0)) {
		diagnostic->marker = DUCHAMP_MARKER_FAILURE;
		diagnostic->checksum = diagnostic_checksum(diagnostic);
		draw_diagnostic(diagnostic);
		return;
	}
	diagnostic->marker = DUCHAMP_MARKER_SUCCESS;
	diagnostic->checksum = diagnostic_checksum(diagnostic);
#if defined(DUCHAMP_BOOT_MENU)
	const struct duchamp_framebuffer menu_framebuffer = {
		.base = FB_BASE,
		.stride = FB_STRIDE,
		.width = FB_WIDTH,
		.height = FB_HEIGHT,
		.depth = 32
	};
#if defined(DUCHAMP_XNU_JUMP)
	if (!duchamp_boot_menu_qemu(&menu_framebuffer, 1))
		return;
#else
	(void)duchamp_boot_menu_qemu(&menu_framebuffer, 0);
	return;
#endif
#endif
	draw_diagnostic(diagnostic);
#if defined(DUCHAMP_TEST_XNU_RETURN)
	{
		static const char sample[] = "SWEET XNU return channel test";
		duchamp_bootshim_xnu_return((uint64_t)(uintptr_t)sample,
		    sizeof(sample) - 1, 1, UINT64_C(0x96000010),
		    UINT64_C(0x1c1481000), UINT64_C(0x1c0001000));
		return;
	}
#endif
#if defined(DUCHAMP_TEST_TRIGGER_EXCEPTION)
	__asm__ volatile("brk #0");
#endif
#if defined(DUCHAMP_LK_RAM_TRANSPORT)
	{
		struct duchamp_mt6897_ram_provider_contract contract = {
			.magic = DUCHAMP_MT6897_RAM_PROVIDER_MAGIC,
			.version = DUCHAMP_MT6897_RAM_PROVIDER_VERSION,
			.size = sizeof(contract),
			.kind = DUCHAMP_MT6897_RAM_PROVIDER_QEMU_REHEARSAL,
			.flags = DUCHAMP_MT6897_RAM_PROVIDER_REQUIRED_FLAGS |
			    DUCHAMP_MT6897_RAM_PROVIDER_CAPSULE_IN_IMAGE,
			.current_el = duchamp_bootshim_entry_state.current_el,
			.sctlr_el1 = duchamp_bootshim_entry_state.sctlr_el1,
			.entry_pc = (uint64_t)(uintptr_t)_head,
			.entry_x0 = duchamp_bootshim_entry_state.entry_x0,
			.image = {
				(uint64_t)(uintptr_t)_head,
				(uint64_t)((uintptr_t)_end - (uintptr_t)_head)
			},
			.fdt = {
				duchamp_bootshim_entry_state.entry_x0,
				diagnostic->fdt_size
			},
			.capsule = {
				(uint64_t)(uintptr_t)duchamp_lk_ram_capsule_start,
				(uint64_t)(duchamp_lk_ram_capsule_end -
				    duchamp_lk_ram_capsule_start)
			},
			.staging = {
				DUCHAMP_LK_RAM_BOOT_STAGING_BASE,
				DUCHAMP_LK_RAM_BOOT_STAGING_CAPACITY
			},
			.xnu = {
				DUCHAMP_LK_RAM_BOOT_XNU_WINDOW_BASE,
				DUCHAMP_LK_RAM_BOOT_XNU_WINDOW_SIZE
			},
			.expected_fdt_receipt = 0,
		};
		const void *fdt = (const void *)(uintptr_t)
		    duchamp_bootshim_entry_state.entry_x0;
		unsigned provider_result = duchamp_mt6897_ram_provider_validate(
		    &contract, fdt, diagnostic->fdt_size, 1,
		    &duchamp_bootshim_ram_provider_report);
		unsigned transport_result = provider_result;
		if (provider_result == DUCHAMP_MT6897_RAM_PROVIDER_OK) {
			transport_result = duchamp_lk_ram_boot_run(fdt,
			    diagnostic->fdt_size, duchamp_lk_ram_capsule_start,
			    (size_t)(duchamp_lk_ram_capsule_end -
			    duchamp_lk_ram_capsule_start));
		}
		const struct duchamp_lk_ram_boot_report *report =
		    &duchamp_lk_ram_boot_report;
		draw_row(8, provider_result == DUCHAMP_MT6897_RAM_PROVIDER_OK &&
		    duchamp_bootshim_ram_provider_report.transport_allowed == 1 &&
		    duchamp_bootshim_ram_provider_report.xnu_jump_allowed == 0 ?
		    COLOR_PASS : COLOR_FAIL);
		draw_row(9, transport_result == DUCHAMP_TRANSPORT_OK &&
		    report->transport_state ==
		    DUCHAMP_TRANSPORT_COMPLETE && report->transport_error == 0 ?
		    COLOR_PASS : COLOR_FAIL);
		draw_row(10, report->prepare_result == 0 && report->entry != 0 &&
		    report->boot_args != 0 && report->segment_count != 0 ?
		    COLOR_PASS : COLOR_FAIL);
		draw_row(11, COLOR_SIGNATURE_A);
		__asm__ volatile("dsb sy; isb" ::: "memory");
		return;
	}
#endif
#if defined(DUCHAMP_EMBED_PAYLOAD)
	(void)duchamp_bootshim_payload_preflight(
	    (const void *)(uintptr_t)duchamp_bootshim_entry_state.entry_x0,
	    diagnostic->fdt_size, duchamp_embedded_payload_start,
	    (size_t)(duchamp_embedded_payload_end -
	    duchamp_embedded_payload_start), &duchamp_bootshim_payload_report);
	draw_payload_report(&duchamp_bootshim_payload_report);
#if defined(DUCHAMP_MATERIALIZE_PAYLOAD)
	if (duchamp_bootshim_payload_report.result == 0) {
#if defined(DUCHAMP_XNU_RETURN)
		int return_ready = 1;
#endif
		const struct duchamp_framebuffer framebuffer = {
			.base = FB_BASE,
			.stride = FB_STRIDE,
			.width = FB_WIDTH,
			.height = FB_HEIGHT,
			.depth = 32
		};
		draw_row(10, COLOR_SIGNATURE_A);
		draw_row(11, COLOR_SIGNATURE_A);
		duchamp_bootshim_materialize_result = duchamp_loader_materialize(
		    (const void *)(uintptr_t)duchamp_bootshim_entry_state.entry_x0,
		    diagnostic->fdt_size, duchamp_embedded_payload_start,
		    (size_t)(duchamp_embedded_payload_end -
		    duchamp_embedded_payload_start), 0, 0, &framebuffer,
		    (void *)(uintptr_t)DUCHAMP_PAYLOAD_EXPECTED_BASE,
		    DUCHAMP_PAYLOAD_EXPECTED_SIZE,
		    &duchamp_bootshim_materialized_plan);
		draw_row(10, duchamp_bootshim_materialize_result == 0 ?
		    COLOR_PASS : COLOR_FAIL);
		draw_row(11, COLOR_SIGNATURE_A);
#if defined(DUCHAMP_QEMU_BL31_RECEIVER)
		if (duchamp_bootshim_materialize_result == 0 &&
		    !duchamp_qemu_receive_bl31(&duchamp_bootshim_materialized_plan)) {
			draw_row(9, COLOR_FAIL);
			return;
		}
#endif
#if defined(DUCHAMP_XNU_RETURN)
		if (duchamp_bootshim_materialize_result == 0) {
			duchamp_bootshim_return_slot_result =
			    duchamp_loader_patch_return_slot(
			    (void *)(uintptr_t)DUCHAMP_PAYLOAD_EXPECTED_BASE,
			    DUCHAMP_PAYLOAD_EXPECTED_SIZE,
			    &duchamp_bootshim_materialized_plan,
			    (uint64_t)(uintptr_t)duchamp_xnu_return_stub,
			    DUCHAMP_RETURN_CHECKPOINT,
			    &duchamp_bootshim_return_slot_report);
			return_ready = duchamp_bootshim_return_slot_result ==
			    DUCHAMP_RETURN_SLOT_OK;
			draw_row(8, return_ready ? COLOR_PASS : COLOR_FAIL);
		} else {
			return_ready = 0;
		}
#endif
#if defined(DUCHAMP_HANDOFF_READY)
		if (duchamp_bootshim_materialize_result == 0
#if defined(DUCHAMP_XNU_RETURN)
		    && return_ready
#endif
		    ) {
			unsigned ready = duchamp_handoff_ready_check(
			    duchamp_bootshim_entry_state.current_el,
			    duchamp_bootshim_entry_state.sctlr_el1,
			    DUCHAMP_PAYLOAD_EXPECTED_BASE,
			    DUCHAMP_PAYLOAD_EXPECTED_SIZE,
			    duchamp_bootshim_materialized_plan.entry,
			    duchamp_bootshim_materialized_plan.boot_args.destination,
			    &duchamp_bootshim_ready_report);
			draw_row(9, ready == 0 ? COLOR_PASS : COLOR_FAIL);
			if (ready == 0) duchamp_handoff_barrier();
			draw_row(11, COLOR_SIGNATURE_B);
#if defined(DUCHAMP_XNU_JUMP)
			if (ready == 0) {
				duchamp_enter_xnu(
				    duchamp_bootshim_materialized_plan.entry,
				    duchamp_bootshim_materialized_plan.boot_args.destination);
			}
#endif
		}
#endif
	}
#endif
#endif
}
