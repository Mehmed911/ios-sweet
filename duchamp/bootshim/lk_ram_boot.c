#include "lk_ram_boot.h"

#include "../loader/mt6897_lk_transport.h"
#include "../loader/resident_xnu.h"

#define XNU_WINDOW_BASE UINT64_C(0x1c0000000)
#define XNU_WINDOW_SIZE UINT64_C(0x20000000)
#define FRAMEBUFFER_BASE UINT64_C(0xfcc2f000)

extern const unsigned char _head[];
extern const unsigned char _end[];

struct duchamp_lk_ram_boot_report duchamp_lk_ram_boot_report;

static struct duchamp_resident_loader resident_loader;
static struct duchamp_resident_transport resident_transport;
static struct duchamp_mt6897_lk_source lk_source;
static unsigned char transfer_scratch[DUCHAMP_MT6897_LK_MAX_READ];
static unsigned char result_buffer[64];

struct run_context {
	struct duchamp_resident_loader *loader;
	struct duchamp_resident_xnu_context xnu;
	struct duchamp_resident_target target;
};

static void
clear_bytes(void *pointer, size_t size)
{
	unsigned char *bytes = pointer;
	size_t index;
	for (index = 0; index < size; index++) {
		bytes[index] = 0;
	}
}

static uint64_t
report_checksum(const struct duchamp_lk_ram_boot_report *report)
{
	const unsigned char *bytes = (const unsigned char *)report;
	uint64_t value = UINT64_C(1469598103934665603);
	size_t index;
	for (index = 0; index < sizeof(*report) - sizeof(report->checksum);
	    index++) {
		value ^= bytes[index];
		value *= UINT64_C(1099511628211);
	}
	return value;
}

static unsigned
prepare(void *context_pointer, const void *payload, size_t payload_size,
	struct duchamp_resident_target *target)
{
	struct run_context *context = context_pointer;
	return duchamp_resident_xnu_prepare(&context->xnu, payload,
	    payload_size, target);
}

static unsigned
enter(void *context_pointer, const struct duchamp_resident_target *target)
{
	static const unsigned char result[] = "LK-RAM-QEMU";
	struct run_context *context = context_pointer;
	context->target = *target;
	return duchamp_resident_complete(context->loader,
	    UINT64_C(0x4c4b52414d51454d), result, sizeof(result) - 1);
}

unsigned
duchamp_lk_ram_boot_run(const void *fdt, size_t fdt_size,
	const void *capsule, size_t capsule_size)
{
	const struct duchamp_resident_ops run_ops = {prepare, enter};
	struct duchamp_resident_source_description description;
	struct duchamp_resident_transport_status transport_status;
	struct duchamp_range occupied;
	struct run_context context;
	struct duchamp_lk_ram_boot_report *report =
	    &duchamp_lk_ram_boot_report;
	unsigned result;

	clear_bytes(report, sizeof(*report));
	report->magic = DUCHAMP_LK_RAM_BOOT_REPORT_MAGIC;
	report->version = DUCHAMP_LK_RAM_BOOT_REPORT_VERSION;
	report->size = sizeof(*report);
	clear_bytes(&context, sizeof(context));
	clear_bytes(&description, sizeof(description));
	result = duchamp_mt6897_lk_source_init(&lk_source, capsule,
	    capsule_size);
	if (result != DUCHAMP_TRANSPORT_OK) {
		report->result = result;
		report->checksum = report_checksum(report);
		return result;
	}
	result = duchamp_mt6897_lk_source_describe(&lk_source, &description);
	if (result != DUCHAMP_TRANSPORT_OK ||
	    description.payload_size > DUCHAMP_LK_RAM_BOOT_STAGING_CAPACITY) {
		report->result = result != DUCHAMP_TRANSPORT_OK ? result :
		    DUCHAMP_TRANSPORT_RANGE;
		report->generation = description.generation;
		report->checksum = report_checksum(report);
		return report->result;
	}
	result = duchamp_resident_init(&resident_loader,
	    (void *)(uintptr_t)DUCHAMP_LK_RAM_BOOT_STAGING_BASE,
	    (size_t)description.payload_size, result_buffer,
	    sizeof(result_buffer), description.generation);
	if (result != DUCHAMP_RESIDENT_OK) {
		report->result = DUCHAMP_TRANSPORT_PROTOCOL;
		report->transport_detail = result;
		report->generation = description.generation;
		report->checksum = report_checksum(report);
		return report->result;
	}
	occupied.start = (uint64_t)(uintptr_t)_head;
	occupied.size = (uint64_t)(_end - _head);
	context.loader = &resident_loader;
	context.xnu.fdt = fdt;
	context.xnu.fdt_size = fdt_size;
	context.xnu.fdt_physical = (uint64_t)(uintptr_t)fdt;
	context.xnu.staging =
	    (const void *)(uintptr_t)DUCHAMP_LK_RAM_BOOT_STAGING_BASE;
	context.xnu.staging_capacity = (size_t)description.payload_size;
	context.xnu.staging_physical = DUCHAMP_LK_RAM_BOOT_STAGING_BASE;
	context.xnu.occupied = &occupied;
	context.xnu.occupied_count = 1;
	context.xnu.framebuffer.base = FRAMEBUFFER_BASE;
	context.xnu.framebuffer.stride = 4992;
	context.xnu.framebuffer.width = 1220;
	context.xnu.framebuffer.height = 2712;
	context.xnu.framebuffer.depth = 32;
	context.xnu.window = (void *)(uintptr_t)XNU_WINDOW_BASE;
	context.xnu.window_physical = XNU_WINDOW_BASE;
	context.xnu.window_size = XNU_WINDOW_SIZE;
	result = duchamp_resident_transport_init(&resident_transport,
	    &resident_loader, &run_ops, &context,
	    &duchamp_mt6897_lk_source_ops, &lk_source, transfer_scratch,
	    sizeof(transfer_scratch));
	if (result == DUCHAMP_TRANSPORT_OK) {
		result = duchamp_resident_transport_run(&resident_transport);
	}
	clear_bytes(&transport_status, sizeof(transport_status));
	(void)duchamp_resident_transport_get_status(&resident_transport,
	    &transport_status);
	report->result = result;
	report->transport_state = transport_status.state;
	report->transport_error = transport_status.last_error;
	report->transport_detail = transport_status.detail;
	report->prepare_result = context.xnu.prepare_result;
	report->generation = description.generation;
	report->bytes_read = transport_status.bytes_read;
	report->source_reads = lk_source.read_calls;
	report->entry = context.target.entry;
	report->boot_args = context.target.boot_args;
	report->segment_count = context.xnu.completed_plan.segment_count;
	report->checksum = report_checksum(report);
	return result;
}
