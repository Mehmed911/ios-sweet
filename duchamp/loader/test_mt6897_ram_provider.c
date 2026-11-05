#include <stdint.h>
#include <stdio.h>
#include <string.h>

#include "mt6897_ram_provider.h"

#define CHECK(condition) do { if (!(condition)) { \
	fprintf(stderr, "RAM provider check failed at line %d\n", __LINE__); \
	return 1; \
} checks++; } while (0)

static void
write_be32(unsigned char *bytes, uint32_t value)
{
	bytes[0] = (unsigned char)(value >> 24);
	bytes[1] = (unsigned char)(value >> 16);
	bytes[2] = (unsigned char)(value >> 8);
	bytes[3] = (unsigned char)value;
}

static struct duchamp_mt6897_ram_provider_contract
valid_contract(void)
{
	struct duchamp_mt6897_ram_provider_contract contract;

	memset(&contract, 0, sizeof(contract));
	contract.magic = DUCHAMP_MT6897_RAM_PROVIDER_MAGIC;
	contract.version = DUCHAMP_MT6897_RAM_PROVIDER_VERSION;
	contract.size = sizeof(contract);
	contract.kind = DUCHAMP_MT6897_RAM_PROVIDER_LK;
	contract.flags = DUCHAMP_MT6897_RAM_PROVIDER_REQUIRED_FLAGS |
	    DUCHAMP_MT6897_RAM_PROVIDER_CAPSULE_IN_IMAGE;
	contract.current_el = 4;
	contract.sctlr_el1 = 0;
	contract.entry_pc = UINT64_C(0x40000000);
	contract.entry_x0 = UINT64_C(0x47c80000);
	contract.image.base = UINT64_C(0x40000000);
	contract.image.size = UINT64_C(0x01000000);
	contract.fdt.base = UINT64_C(0x47c80000);
	contract.fdt.size = UINT64_C(0x00077000);
	contract.capsule.base = UINT64_C(0x40800000);
	contract.capsule.size = UINT64_C(0x00100000);
	contract.staging.base = UINT64_C(0x90000000);
	contract.staging.size = UINT64_C(0x20000000);
	contract.xnu.base = UINT64_C(0x1c0000000);
	contract.xnu.size = UINT64_C(0x20000000);
	return contract;
}

int
main(void)
{
	struct duchamp_mt6897_ram_provider_contract contract;
	struct duchamp_mt6897_ram_provider_report report;
	unsigned char fdt[64];
	unsigned checks = 0;
	uint64_t valid_receipt;

	memset(fdt, 0, sizeof(fdt));
	write_be32(fdt, UINT32_C(0xd00dfeed));
	write_be32(fdt + 4, sizeof(fdt));
	contract = valid_contract();
	CHECK(duchamp_mt6897_ram_provider_validate(&contract, fdt,
	    sizeof(fdt), 0, &report) == DUCHAMP_MT6897_RAM_PROVIDER_OK);
	CHECK(report.magic == DUCHAMP_MT6897_RAM_PROVIDER_MAGIC &&
	    report.version == DUCHAMP_MT6897_RAM_PROVIDER_VERSION &&
	    report.size == sizeof(report) && report.result == 0 &&
	    report.detail == 0 && report.transport_allowed == 1 &&
	    report.xnu_jump_allowed == 0 && report.entry_pc == contract.entry_pc &&
	    report.entry_x0 == contract.entry_x0 &&
	    report.fdt_pa == contract.fdt.base && report.fdt_size == sizeof(fdt) &&
	    report.fdt_receipt != 0 &&
	    report.checksum == duchamp_mt6897_ram_provider_checksum(&report));
	valid_receipt = report.fdt_receipt;

	contract = valid_contract();
	contract.flags &= ~DUCHAMP_MT6897_RAM_PROVIDER_ENTRY_PC_OBSERVED;
	CHECK(duchamp_mt6897_ram_provider_validate(&contract, fdt,
	    sizeof(fdt), 0, &report) == DUCHAMP_MT6897_RAM_PROVIDER_EVIDENCE &&
	    report.transport_allowed == 0 && report.xnu_jump_allowed == 0);

	contract = valid_contract();
	contract.entry_pc += contract.image.size;
	CHECK(duchamp_mt6897_ram_provider_validate(&contract, fdt,
	    sizeof(fdt), 0, &report) == DUCHAMP_MT6897_RAM_PROVIDER_ENTRY);

	contract = valid_contract();
	contract.entry_x0 += 8;
	CHECK(duchamp_mt6897_ram_provider_validate(&contract, fdt,
	    sizeof(fdt), 0, &report) == DUCHAMP_MT6897_RAM_PROVIDER_ENTRY);

	contract = valid_contract();
	contract.current_el = 8;
	CHECK(duchamp_mt6897_ram_provider_validate(&contract, fdt,
	    sizeof(fdt), 0, &report) == DUCHAMP_MT6897_RAM_PROVIDER_ENTRY);

	contract = valid_contract();
	contract.sctlr_el1 = 1;
	CHECK(duchamp_mt6897_ram_provider_validate(&contract, fdt,
	    sizeof(fdt), 0, &report) == DUCHAMP_MT6897_RAM_PROVIDER_ENTRY);

	contract = valid_contract();
	fdt[0] = 0;
	CHECK(duchamp_mt6897_ram_provider_validate(&contract, fdt,
	    sizeof(fdt), 0, &report) == DUCHAMP_MT6897_RAM_PROVIDER_FDT);
	fdt[0] = 0xd0;

	contract = valid_contract();
	write_be32(fdt + 4, sizeof(fdt) + 1);
	CHECK(duchamp_mt6897_ram_provider_validate(&contract, fdt,
	    sizeof(fdt), 0, &report) == DUCHAMP_MT6897_RAM_PROVIDER_FDT);
	write_be32(fdt + 4, sizeof(fdt));

	contract = valid_contract();
	contract.staging.base = contract.fdt.base;
	CHECK(duchamp_mt6897_ram_provider_validate(&contract, fdt,
	    sizeof(fdt), 0, &report) == DUCHAMP_MT6897_RAM_PROVIDER_OVERLAP);

	contract = valid_contract();
	contract.capsule.base = UINT64_C(0x50000000);
	CHECK(duchamp_mt6897_ram_provider_validate(&contract, fdt,
	    sizeof(fdt), 0, &report) == DUCHAMP_MT6897_RAM_PROVIDER_OVERLAP);

	contract = valid_contract();
	contract.expected_fdt_receipt = valid_receipt ^ 1;
	CHECK(duchamp_mt6897_ram_provider_validate(&contract, fdt,
	    sizeof(fdt), 0, &report) == DUCHAMP_MT6897_RAM_PROVIDER_RECEIPT);

	contract = valid_contract();
	contract.kind = DUCHAMP_MT6897_RAM_PROVIDER_QEMU_REHEARSAL;
	CHECK(duchamp_mt6897_ram_provider_validate(&contract, fdt,
	    sizeof(fdt), 0, &report) == DUCHAMP_MT6897_RAM_PROVIDER_KIND);
	CHECK(duchamp_mt6897_ram_provider_validate(&contract, fdt,
	    sizeof(fdt), 1, &report) == DUCHAMP_MT6897_RAM_PROVIDER_OK &&
	    report.transport_allowed == 1 && report.xnu_jump_allowed == 0);

	contract = valid_contract();
	contract.kind = DUCHAMP_MT6897_RAM_PROVIDER_UEFI;
	contract.entry_pc += 0x1000;
	CHECK(duchamp_mt6897_ram_provider_validate(&contract, fdt,
	    sizeof(fdt), 0, &report) == DUCHAMP_MT6897_RAM_PROVIDER_OK &&
	    report.xnu_jump_allowed == 0);

	contract = valid_contract();
	contract.capsule.size = contract.staging.size + 1;
	CHECK(duchamp_mt6897_ram_provider_validate(&contract, fdt,
	    sizeof(fdt), 0, &report) == DUCHAMP_MT6897_RAM_PROVIDER_RANGE);

	printf("mt6897-ram-provider: PASS checks=%u receipt=%#llx\n", checks,
	    (unsigned long long)valid_receipt);
	return 0;
}
