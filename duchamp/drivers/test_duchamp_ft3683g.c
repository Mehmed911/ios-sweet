#include "duchamp_ft3683g.h"

#ifdef MT6897_MODEL_FREESTANDING
void model_assert_fail(const char *, unsigned) __attribute__((noreturn));
int printf(const char *, ...);
#define assert(x) ((x) ? (void)0 : model_assert_fail(#x, __LINE__))
#else
#include <assert.h>
#include <stdio.h>
#endif

static unsigned checks;
#define CHECK(x) do { ++checks; assert(x); } while (0)

struct fixture {
	uint8_t wire[100];
	unsigned calls;
	int error;
};

static int
transfer(void *context, const uint8_t *tx, uint8_t *rx, size_t size)
{
	struct fixture *f = context;

	CHECK(size == sizeof(f->wire));
	CHECK(tx[0] == 0x01 && tx[1] == 0xa0 && tx[2] == 0 && tx[3] == 91);
	for (size_t i = 4; i < size; ++i) {
		assert(tx[i] == 0);
	}
	++f->calls;
	for (size_t i = 0; i < size; ++i) {
		rx[i] = f->wire[i];
	}
	return f->error;
}

static uint8_t
reverse_byte(uint8_t value)
{
	uint8_t reversed = 0;

	for (unsigned i = 0; i < 8; ++i) {
		reversed = (reversed << 1) | (value & 1);
		value >>= 1;
	}
	return reversed;
}

/* Independent forward CRC-CCITT with bit reversal for the wire encoding. */
static void
set_crc(struct fixture *f)
{
	uint16_t crc = 0xffff;

	for (unsigned i = 7; i < 98; ++i) {
		crc ^= (uint16_t)reverse_byte(f->wire[i]) << 8;
		for (unsigned bit = 0; bit < 8; ++bit) {
			crc = (crc & 0x8000 ? 0x1021 : 0) ^ (crc << 1);
		}
	}
	f->wire[98] = reverse_byte(crc >> 8);
	f->wire[99] = reverse_byte(crc & 0xff);
}

static void
assert_contact(const struct dft_contact *c, unsigned id, unsigned phase, unsigned x, unsigned y)
{
	CHECK(c->id == id && c->phase == phase && c->x == x && c->y == y);
}

static void
assert_rejected(struct fixture *f, int expected)
{
	struct dft_report out = { .count = 123, .contacts = { { .x = 0xffff } } };
	const unsigned prior_calls = f->calls;

	CHECK(dft_read_report(transfer, f, &out) == expected);
	CHECK(f->calls == prior_calls + 1);
	CHECK(out.count == 123 && out.contacts[0].x == 0xffff);
}

struct id_fixture {
	unsigned calls;
	unsigned fail_call;
};

static int
id_transfer(void *context, const uint8_t *tx, uint8_t *rx, size_t size)
{
	struct id_fixture *f = context;
	const unsigned index = f->calls++;
	static const uint8_t responses[2][3] = { { 0x12, 0x14, 0x3c }, { 0x34, 0x20, 0x78 } };

	CHECK(size == 10 && index < 2);
	CHECK(tx[0] == (index ? 0x9f : 0xa3));
	CHECK(tx[1] == 0xa0 && tx[2] == 0 && tx[3] == 1);
	for (unsigned i = 4; i < size; ++i) {
		CHECK(tx[i] == 0);
	}
	for (unsigned i = 0; i < 7; ++i) {
		rx[i] = 0;
	}
	for (unsigned i = 0; i < 3; ++i) {
		rx[7 + i] = responses[index][i];
	}
	if (f->calls == f->fail_call) {
		rx[9] ^= 1;
	}
	return 0;
}

static void
test_identity(void)
{
	struct id_fixture id = { 0 };
	uint16_t value = 0xffff;

	CHECK(dft_read_identity(0, &id, &value) == DFT_BAD_ARGUMENT);
	CHECK(dft_read_identity(id_transfer, &id, 0) == DFT_BAD_ARGUMENT);
	CHECK(id.calls == 0);
	CHECK(dft_read_identity(id_transfer, &id, &value) == DFT_OK);
	CHECK(id.calls == 2 && value == 0x1234);
	for (unsigned fail = 1; fail <= 2; ++fail) {
		id = (struct id_fixture){ .fail_call = fail };
		value = 0xffff;
		CHECK(dft_read_identity(id_transfer, &id, &value) == DFT_BAD_CRC);
		CHECK(id.calls == fail && value == 0xffff);
	}
}

int
main(void)
{
	struct dft_report report;
	/* Status at byte 3, payload at 7. Standard active contact, then a
	 * release for a different slot. The next slot is the sentinel.
	 */
	struct fixture standard = {
		.wire = { [8] = 0x01, [9] = 0x04, [10] = 0xc3, [11] = 0x2a, [12] = 0x97,
		    [15] = 0x41, [16] = 0x11, [17] = 0x60, [18] = 0x22, [23] = 0xf0 },
	};
	struct fixture high = {
		.wire = { [8] = 0x22, [11] = 0x84, [12] = 0xc3, [13] = 0x9a, [14] = 0x97,
		    [15] = 0x5e, [19] = 0x40, [20] = 0x20, [21] = 0x10, [22] = 0x30,
		    [23] = 0x1f },
	};
	struct fixture malformed;

	test_identity();

	CHECK(dft_read_report(0, &standard, &report) == DFT_BAD_ARGUMENT);
	CHECK(dft_read_report(transfer, &standard, 0) == DFT_BAD_ARGUMENT);
	CHECK(standard.calls == 0);

	set_crc(&standard);
	CHECK(dft_read_report(transfer, &standard, &report) == DFT_OK);
	CHECK(standard.calls == 1 && report.format == DFT_STANDARD && report.count == 2);
	assert_contact(&report.contacts[0], 2, DFT_DOWN, 0x4c3, 0xa97);
	assert_contact(&report.contacts[1], 6, DFT_UP, 0x111, 0x022);

	set_crc(&high);
	CHECK(dft_read_report(transfer, &high, &report) == DFT_OK);
	CHECK(high.calls == 1 && report.format == DFT_HIGH_RESOLUTION && report.count == 2);
	assert_contact(&report.contacts[0], 9, DFT_MOVE, 0x4c35, 0xa97e);
	assert_contact(&report.contacts[1], 1, DFT_UP, 0x0201, 0x030f);

	malformed = high;
	malformed.error = -1;
	assert_rejected(&malformed, DFT_TRANSFER_FAILED);
	malformed = high;
	malformed.wire[3] = 0x20;
	assert_rejected(&malformed, DFT_CONTROLLER_STATUS);
	malformed.wire[3] = 0x80;
	assert_rejected(&malformed, DFT_CONTROLLER_STATUS);
	malformed = high;
	malformed.wire[15] ^= 1;
	assert_rejected(&malformed, DFT_BAD_CRC);
	malformed = high;
	malformed.wire[8] = 0x82;
	set_crc(&malformed);
	assert_rejected(&malformed, DFT_UNSUPPORTED_REPORT);
	malformed.wire[8] = 0x20;
	set_crc(&malformed);
	assert_rejected(&malformed, DFT_BAD_REPORT);
	malformed.wire[8] = 0x2b;
	set_crc(&malformed);
	assert_rejected(&malformed, DFT_BAD_REPORT);
	malformed = high;
	malformed.wire[21] = 0x90;
	set_crc(&malformed);
	assert_rejected(&malformed, DFT_BAD_REPORT);
	malformed.wire[21] = 0xa0;
	set_crc(&malformed);
	assert_rejected(&malformed, DFT_BAD_REPORT);
	malformed = high;
	malformed.wire[19] = 0xc0;
	set_crc(&malformed);
	assert_rejected(&malformed, DFT_BAD_REPORT);
	malformed = standard;
	malformed.wire[8] = 0;
	set_crc(&malformed);
	assert_rejected(&malformed, DFT_BAD_REPORT);
	malformed.wire[9] = 0x44;
	set_crc(&malformed);
	CHECK(dft_read_report(transfer, &malformed, &report) == DFT_OK && report.count == 2);

	malformed = high;
	malformed.wire[8] = 0x2a;
	for (unsigned id = 0; id < 10; ++id) {
		malformed.wire[11 + 8 * id] = 0;
		malformed.wire[13 + 8 * id] = id << 4;
	}
	set_crc(&malformed);
	CHECK(dft_read_report(transfer, &malformed, &report) == DFT_OK && report.count == 10);
	CHECK(report.contacts[9].id == 9);

	printf("%u FocalTech report checks passed\n", checks);
	return 0;
}
