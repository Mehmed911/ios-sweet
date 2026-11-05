#include "mt6897_ram_provider.h"

#include "mt6897_entry.h"

#define FDT_MAGIC UINT32_C(0xd00dfeed)

static uint32_t
read_be32(const unsigned char *bytes)
{
	return (uint32_t)bytes[0] << 24 | (uint32_t)bytes[1] << 16 |
	    (uint32_t)bytes[2] << 8 | (uint32_t)bytes[3];
}

static uint64_t
receipt(const unsigned char *bytes, size_t size)
{
	uint64_t value = UINT64_C(1469598103934665603);
	size_t index;

	for (index = 0; index < size; index++) {
		value ^= bytes[index];
		value *= UINT64_C(1099511628211);
	}
	return value;
}

static int
region_valid(const struct duchamp_mt6897_ram_region *region)
{
	return region->base != 0 && region->size != 0 &&
	    region->base <= UINT64_MAX - region->size;
}

static int
contains(const struct duchamp_mt6897_ram_region *outer,
	const struct duchamp_mt6897_ram_region *inner)
{
	return region_valid(outer) && region_valid(inner) &&
	    inner->base >= outer->base &&
	    inner->base - outer->base <= outer->size &&
	    inner->size <= outer->size - (inner->base - outer->base);
}

static int
contains_address(const struct duchamp_mt6897_ram_region *region,
	uint64_t address, uint64_t size)
{
	struct duchamp_mt6897_ram_region inner = {address, size};
	return contains(region, &inner);
}

static int
overlap(const struct duchamp_mt6897_ram_region *first,
	const struct duchamp_mt6897_ram_region *second)
{
	return first->base < second->base + second->size &&
	    second->base < first->base + first->size;
}

static void
clear_report(struct duchamp_mt6897_ram_provider_report *report)
{
	unsigned char *bytes = (unsigned char *)(void *)report;
	size_t index;

	for (index = 0; index < sizeof(*report); index++) bytes[index] = 0;
	report->magic = DUCHAMP_MT6897_RAM_PROVIDER_MAGIC;
	report->version = DUCHAMP_MT6897_RAM_PROVIDER_VERSION;
	report->size = sizeof(*report);
}

uint64_t
duchamp_mt6897_ram_provider_checksum(
	const struct duchamp_mt6897_ram_provider_report *report)
{
	return receipt((const unsigned char *)(const void *)report,
	    offsetof(struct duchamp_mt6897_ram_provider_report, checksum));
}

static unsigned
finish(struct duchamp_mt6897_ram_provider_report *report, unsigned result,
	unsigned detail)
{
	report->result = result;
	report->detail = detail;
	report->transport_allowed = result == DUCHAMP_MT6897_RAM_PROVIDER_OK;
	/* This validator deliberately never authorizes the architectural jump. */
	report->xnu_jump_allowed = 0;
	report->checksum = duchamp_mt6897_ram_provider_checksum(report);
	return result;
}

unsigned
duchamp_mt6897_ram_provider_validate(
	const struct duchamp_mt6897_ram_provider_contract *contract,
	const void *fdt_pointer, size_t fdt_available,
	unsigned allow_qemu_rehearsal,
	struct duchamp_mt6897_ram_provider_report *report)
{
	const unsigned char *fdt = fdt_pointer;
	struct duchamp_mt6897_entry_state entry;
	uint64_t fdt_size, fdt_receipt;
	unsigned entry_result;
	int capsule_in_image;

	if (report == NULL) return DUCHAMP_MT6897_RAM_PROVIDER_ARGUMENT;
	clear_report(report);
	if (contract == NULL || fdt == NULL || fdt_available < 40) {
		return finish(report, DUCHAMP_MT6897_RAM_PROVIDER_ARGUMENT, 0);
	}
	report->kind = contract->kind;
	report->flags = contract->flags;
	report->entry_pc = contract->entry_pc;
	report->entry_x0 = contract->entry_x0;
	report->fdt_pa = contract->fdt.base;
	report->image_base = contract->image.base;
	report->image_size = contract->image.size;
	report->capsule_base = contract->capsule.base;
	report->capsule_size = contract->capsule.size;
	report->staging_base = contract->staging.base;
	report->staging_size = contract->staging.size;
	report->xnu_base = contract->xnu.base;
	report->xnu_size = contract->xnu.size;

	if (contract->magic != DUCHAMP_MT6897_RAM_PROVIDER_MAGIC ||
	    contract->version != DUCHAMP_MT6897_RAM_PROVIDER_VERSION ||
	    contract->size != sizeof(*contract)) {
		return finish(report, DUCHAMP_MT6897_RAM_PROVIDER_BAD_VERSION, 0);
	}
	if (contract->kind != DUCHAMP_MT6897_RAM_PROVIDER_LK &&
	    contract->kind != DUCHAMP_MT6897_RAM_PROVIDER_UEFI &&
	    (contract->kind != DUCHAMP_MT6897_RAM_PROVIDER_QEMU_REHEARSAL ||
	    allow_qemu_rehearsal != 1)) {
		return finish(report, DUCHAMP_MT6897_RAM_PROVIDER_KIND,
		    contract->kind);
	}
	if ((contract->flags & DUCHAMP_MT6897_RAM_PROVIDER_REQUIRED_FLAGS) !=
	    DUCHAMP_MT6897_RAM_PROVIDER_REQUIRED_FLAGS ||
	    (contract->flags & ~DUCHAMP_MT6897_RAM_PROVIDER_ALL_FLAGS) != 0) {
		return finish(report, DUCHAMP_MT6897_RAM_PROVIDER_EVIDENCE,
		    contract->flags);
	}
	if (!region_valid(&contract->image) ||
	    !region_valid(&contract->fdt) ||
	    !region_valid(&contract->capsule) ||
	    !region_valid(&contract->staging) ||
	    !region_valid(&contract->xnu) ||
	    contract->capsule.size > contract->staging.size) {
		return finish(report, DUCHAMP_MT6897_RAM_PROVIDER_RANGE, 0);
	}
	if (!contains_address(&contract->image, contract->entry_pc, 4) ||
	    (contract->entry_pc & 3) != 0 ||
	    (contract->kind == DUCHAMP_MT6897_RAM_PROVIDER_LK &&
	    contract->entry_pc != contract->image.base)) {
		return finish(report, DUCHAMP_MT6897_RAM_PROVIDER_ENTRY, 0);
	}

	entry.current_el = contract->current_el;
	entry.sctlr_el1 = contract->sctlr_el1;
	entry.entry_x0 = contract->entry_x0;
	entry.entry_x1 = 0;
	entry.entry_x2 = 0;
	entry.entry_x3 = 0;
	entry.entry_sp = 0;
	entry_result = duchamp_mt6897_entry_check(&entry, contract->fdt.base,
	    contract->fdt.size);
	if (entry_result != DUCHAMP_ENTRY_OK ||
	    contract->entry_x0 != contract->fdt.base) {
		return finish(report, DUCHAMP_MT6897_RAM_PROVIDER_ENTRY,
		    entry_result);
	}
	if (read_be32(fdt) != FDT_MAGIC) {
		return finish(report, DUCHAMP_MT6897_RAM_PROVIDER_FDT, 1);
	}
	fdt_size = read_be32(fdt + 4);
	report->fdt_size = fdt_size;
	if (fdt_size < 40 || fdt_size > fdt_available ||
	    fdt_size > contract->fdt.size) {
		return finish(report, DUCHAMP_MT6897_RAM_PROVIDER_FDT, 2);
	}
	fdt_receipt = receipt(fdt, (size_t)fdt_size);
	report->fdt_receipt = fdt_receipt;
	if (contract->expected_fdt_receipt != 0 &&
	    contract->expected_fdt_receipt != fdt_receipt) {
		return finish(report, DUCHAMP_MT6897_RAM_PROVIDER_RECEIPT, 0);
	}

	capsule_in_image = (contract->flags &
	    DUCHAMP_MT6897_RAM_PROVIDER_CAPSULE_IN_IMAGE) != 0;
	if ((capsule_in_image && !contains(&contract->image,
	    &contract->capsule)) ||
	    (!capsule_in_image && overlap(&contract->image,
	    &contract->capsule))) {
		return finish(report, DUCHAMP_MT6897_RAM_PROVIDER_OVERLAP, 1);
	}
	if (overlap(&contract->image, &contract->fdt) ||
	    overlap(&contract->image, &contract->staging) ||
	    overlap(&contract->image, &contract->xnu) ||
	    overlap(&contract->fdt, &contract->capsule) ||
	    overlap(&contract->fdt, &contract->staging) ||
	    overlap(&contract->fdt, &contract->xnu) ||
	    overlap(&contract->capsule, &contract->staging) ||
	    overlap(&contract->capsule, &contract->xnu) ||
	    overlap(&contract->staging, &contract->xnu)) {
		return finish(report, DUCHAMP_MT6897_RAM_PROVIDER_OVERLAP, 2);
	}
	return finish(report, DUCHAMP_MT6897_RAM_PROVIDER_OK, 0);
}
