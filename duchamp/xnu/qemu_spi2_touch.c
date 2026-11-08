/* Replay the Duchamp SPI2 read protocol through XNU's existing HID service. */
#if defined(DUCHAMP)
#include <sys/systm.h>
#include <pexpert/device_tree.h>
#include <pexpert/pexpert.h>
#include "duchamp_ft3683g.h"

extern void sweet_hid_touch(int finger, int down, int x, int y);
int duchamp_qemu_spi2_touch_step(unsigned step);

enum {
	SPI2_ID_BYTES = 10,
	SPI2_MAX_REPORTS = 32,
	SPI2_PERIOD_MS = 25,
	SPI2_TEST_ID = 0x1234,
	FT_WIDTH = 1220 * 16,
	FT_HEIGHT = 2712 * 16,
	HID_WIDTH = 1080,
	HID_HEIGHT = 2400,
};

struct spi2_fixture {
	const uint8_t *id_high;
	const uint8_t *id_low;
	const uint8_t *report;
};

static int
fixture_exchange(void *context, const uint8_t *tx, uint8_t *rx, size_t size)
{
	const struct spi2_fixture *fixture = context;
	const uint8_t *reply;

	if (size == SPI2_ID_BYTES && tx[0] == 0xa3) {
		reply = fixture->id_high;
	} else if (size == SPI2_ID_BYTES && tx[0] == 0x9f) {
		reply = fixture->id_low;
	} else if (size == DFT_WIRE_BYTES && tx[0] == 0x01) {
		reply = fixture->report;
	} else {
		return -1;
	}
	if (!reply || tx[1] != 0xa0 || tx[2] || tx[3] != size - 9) {
		return -1;
	}
	for (size_t i = 4; i < size; i++) {
		if (tx[i]) {
			return -1;
		}
	}
	memcpy(rx, reply, size);
	return 0;
}

static int
finish_reports(void)
{
	for (unsigned id = 0; id < DFT_MAX_CONTACTS; id++) {
		sweet_hid_touch(id, 0, 0, 0);
	}
	return -1;
}

int
duchamp_qemu_spi2_touch_step(unsigned step)
{
	static const char compatible[] = "qemu,duchamp-spi2-touch-test-v1";
	struct spi2_fixture fixture = { 0 };
	const void *value, *reports;
	unsigned enabled = 0, size, reports_size;
	DTEntry node;
	uint64_t midr;

	if (!PE_parse_boot_argn("sweet-qemu-spi2", &enabled, sizeof(enabled)) || enabled != 1) {
		return 0;
	}
	__asm__ volatile("mrs %0, midr_el1" : "=r"(midr));
	if ((midr >> 24) != 0x41 || ((midr >> 4) & 0xfff) != 0xd0b ||
	    SecureDTLookupEntry(NULL, "/duchamp-qemu-spi2", &node) != kSuccess ||
	    SecureDTGetProperty(node, "compatible", &value, &size) != kSuccess ||
	    size != sizeof(compatible) || memcmp(value, compatible, size) ||
	    SecureDTGetProperty(node, "reports", &reports, &reports_size) != kSuccess ||
	    !reports_size || reports_size % DFT_WIRE_BYTES ||
	    reports_size > SPI2_MAX_REPORTS * DFT_WIRE_BYTES) {
		printf("DUCHAMP SPI2 QEMU FIXTURE REJECTED\n");
		return -1;
	}
	if (step == 0) {
		uint16_t identity;

		if (SecureDTGetProperty(node, "id-high-response", &value, &size) != kSuccess ||
		    size != SPI2_ID_BYTES) {
			return -1;
		}
		fixture.id_high = value;
		if (SecureDTGetProperty(node, "id-low-response", &value, &size) != kSuccess ||
		    size != SPI2_ID_BYTES) {
			return -1;
		}
		fixture.id_low = value;
		if (dft_read_identity(fixture_exchange, &fixture, &identity) != DFT_OK ||
		    identity != SPI2_TEST_ID) {
			printf("DUCHAMP SPI2 QEMU ID REJECTED\n");
			return -1;
		}
		printf("DUCHAMP SPI2 QEMU ID PASS 0x1234\n");
		return SPI2_PERIOD_MS;
	}
	if (step > reports_size / DFT_WIRE_BYTES) {
		printf("DUCHAMP SPI2 QEMU REPORT REPLAY COMPLETE\n");
		return finish_reports();
	}
	fixture.report = (const uint8_t *)reports + (step - 1) * DFT_WIRE_BYTES;
	struct dft_report report;
	const int status = dft_read_report(fixture_exchange, &fixture, &report);
	if (status == DFT_BAD_CRC) {
		printf("DUCHAMP SPI2 QEMU REPORT CRC REJECTED\n");
		return SPI2_PERIOD_MS;
	}
	if (status != DFT_OK || report.format != DFT_HIGH_RESOLUTION) {
		printf("DUCHAMP SPI2 QEMU REPORT REJECTED\n");
		return finish_reports();
	}
	for (unsigned i = 0; i < report.count; i++) {
		if (report.contacts[i].x >= FT_WIDTH || report.contacts[i].y >= FT_HEIGHT) {
			printf("DUCHAMP SPI2 QEMU COORDINATES REJECTED\n");
			return finish_reports();
		}
	}
	for (unsigned i = 0; i < report.count; i++) {
		const struct dft_contact *contact = &report.contacts[i];
		sweet_hid_touch(contact->id, contact->phase != DFT_UP,
		    (unsigned)contact->x * HID_WIDTH / FT_WIDTH,
		    (unsigned)contact->y * HID_HEIGHT / FT_HEIGHT);
	}
	return SPI2_PERIOD_MS;
}
#endif
