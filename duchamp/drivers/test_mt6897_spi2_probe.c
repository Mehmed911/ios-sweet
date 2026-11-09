#include "mt6897_spi2_probe.h"

#ifdef MT6897_MODEL_FREESTANDING
void model_assert_fail(const char *, unsigned) __attribute__((noreturn));
int printf(const char *, ...);
#define assert(x) ((x) ? (void)0 : model_assert_fail(#x, __LINE__))
#else
#include <assert.h>
#include <stdio.h>
#endif

enum operation {
	ACQUIRE = 1, IRQ, CLEAN, PREPARE, TO_DMA, TRANSFER, COMPLETED,
	INVALIDATE, TO_CPU, RELEASE, QUARANTINE,
};

struct model {
	_Alignas(MT6897_SPI2_CACHE_LINE) uint8_t tx[MT6897_SPI2_BUFFER_BYTES];
	_Alignas(MT6897_SPI2_CACHE_LINE) uint8_t rx[MT6897_SPI2_BUFFER_BYTES];
	uint8_t device_tx[MT6897_SPI2_BUFFER_BYTES];
	uint8_t device_rx[MT6897_SPI2_BUFFER_BYTES];
	uint8_t wire[DFT_WIRE_BYTES];
	struct mt6897_spi2_grant grant;
	enum operation fault;
	unsigned stage;
	struct mt6897_spi2_probe probe;
};

static const uint64_t generation = 7;
static unsigned cases;

static int
acquire(void *context, struct mt6897_spi2_grant *grant)
{
	struct model *m = context;
	assert(++m->stage == ACQUIRE);
	*grant = m->grant;
	return m->fault == ACQUIRE;
}

static int
wait_touch(void *context, unsigned timeout)
{
	struct model *m = context;
	assert(++m->stage == IRQ && timeout == MT6897_SPI2_MAX_WAIT_MS);
	/* A reentrant caller cannot start a second transaction. */
	struct dft_report ignored;
	assert(mt6897_spi2_read_touch_once(&m->probe, generation, NULL, m, &ignored) ==
	    MT6897_SPI2_ALREADY_ATTEMPTED);
	return m->fault == IRQ;
}

static int
sync_buffer(void *context, enum mt6897_spi2_sync action,
    const struct mt6897_spi2_buffer *buffer)
{
	struct model *m = context;
	static const enum operation order[] = {
		CLEAN, PREPARE, TO_DMA, COMPLETED, INVALIDATE, TO_CPU,
	};
	assert(++m->stage == order[action]);
	if (m->fault == order[action]) {
		return -1;
	}
	if (action == MT6897_SPI2_CLEAN_TX) {
		assert(buffer && buffer->cpu == m->tx);
		for (size_t i = 0; i < sizeof(m->tx); ++i) {
			m->device_tx[i] = m->tx[i];
		}
	} else if (action == MT6897_SPI2_PREPARE_RX) {
		assert(buffer && buffer->cpu == m->rx);
		for (size_t i = 0; i < sizeof(m->rx); ++i) {
			assert(m->rx[i] == 0);
			m->device_rx[i] = m->rx[i];
		}
	} else if (action == MT6897_SPI2_INVALIDATE_RX) {
		assert(buffer && buffer->cpu == m->rx && m->rx[8] == 0);
		for (size_t i = 0; i < sizeof(m->rx); ++i) {
			m->rx[i] = m->device_rx[i];
		}
	} else {
		assert(buffer == NULL);
	}
	return 0;
}

static int
transfer(void *context, uint64_t tx, uint64_t rx, size_t bytes, unsigned timeout)
{
	struct model *m = context;
	assert(++m->stage == TRANSFER && timeout == MT6897_SPI2_MAX_WAIT_MS);
	assert(tx == m->grant.tx.dma && rx == m->grant.rx.dma && bytes == DFT_WIRE_BYTES);
	assert(m->device_tx[0] == 0x01 && m->device_tx[1] == 0xa0 &&
	    m->device_tx[2] == 0 && m->device_tx[3] == 91);
	for (size_t i = 4; i < sizeof(m->device_tx); ++i) {
		assert(m->device_tx[i] == 0);
	}
	for (size_t i = 0; i < bytes; ++i) {
		m->device_rx[i] = m->wire[i];
	}
	return m->fault == TRANSFER;
}

static void
release(void *context, enum mt6897_spi2_release disposition)
{
	struct model *m = context;
	assert(m->stage >= ACQUIRE && m->stage <= TO_CPU);
	const unsigned expected = disposition == MT6897_SPI2_QUARANTINE_DMA ?
	    QUARANTINE : RELEASE;
	assert((expected == QUARANTINE) == (m->fault == TRANSFER));
	m->stage |= expected << 8;
}

static const struct mt6897_spi2_provider ops = {
	acquire, wait_touch, sync_buffer, transfer, release,
};

#ifdef MT6897_SPI2_CAPTURE
#include "spi2-capture.h"
#else
/* Synthetic extended-format, single-contact reply. */
static const uint8_t wire[DFT_WIRE_BYTES] = {
	[8] = 0x21, [12] = 0x3e, [14] = 0x7d, [15] = 0x80,
	[98] = 0x7a, [99] = 0x31,
};
enum { EXPECTED_X = 1000, EXPECTED_Y = 2000 };
#endif

static void
init(struct model *m)
{
	*m = (struct model){ 0 };
	m->grant = (struct mt6897_spi2_grant){
		.generation = generation, .resources = MT6897_SPI2_REQUIRED,
		.cache_line = MT6897_SPI2_CACHE_LINE, .dma_bits = 36,
		.route = MT6897_SPI2_DMA_IOMMU,
		.tx = { m->tx, 0x50000000, UINT64_C(0x100000000) },
		.rx = { m->rx, 0x50001000, UINT64_C(0x100001000) },
	};
	for (size_t i = 0; i < sizeof(wire); ++i) {
		m->wire[i] = wire[i];
	}
}

static void
check_case(struct model *m, const struct mt6897_spi2_provider *provider,
    enum mt6897_spi2_result result, unsigned stage, unsigned finish)
{
	struct dft_report out = { .count = 255 };
	assert(mt6897_spi2_read_touch_once(&m->probe, generation, provider, m, &out) == result);
	assert(m->stage == (stage | (finish << 8)));
	if (result == MT6897_SPI2_OK) {
		assert(out.format == DFT_HIGH_RESOLUTION && out.count == 1);
		assert(out.contacts[0].id == 0 && out.contacts[0].phase == DFT_DOWN);
		assert(out.contacts[0].x == EXPECTED_X && out.contacts[0].y == EXPECTED_Y);
	} else {
		assert(out.count == 255);
	}
	assert(mt6897_spi2_read_touch_once(&m->probe, generation, provider, m, &out) ==
	    MT6897_SPI2_ALREADY_ATTEMPTED);
	assert(m->stage == (stage | (finish << 8)));
	++cases;
}

int
main(void)
{
	struct model m;
	init(&m);
	check_case(&m, NULL, MT6897_SPI2_DENIED, 0, 0);
	init(&m);
	m.fault = ACQUIRE;
	check_case(&m, &ops, MT6897_SPI2_DENIED, ACQUIRE, 0);
	for (unsigned bit = 1; bit <= MT6897_SPI2_NO_BOUNCE; bit <<= 1) {
		init(&m);
		m.grant.resources &= ~bit;
		check_case(&m, &ops, MT6897_SPI2_DENIED, ACQUIRE, RELEASE);
	}
	init(&m);
	m.grant.generation--;
	check_case(&m, &ops, MT6897_SPI2_DENIED, ACQUIRE, RELEASE);
	init(&m);
	m.grant.cache_line = 128;
	check_case(&m, &ops, MT6897_SPI2_DENIED, ACQUIRE, RELEASE);
	init(&m);
	m.grant.route = 0;
	check_case(&m, &ops, MT6897_SPI2_DENIED, ACQUIRE, RELEASE);
	init(&m);
	m.grant.dma_bits = 32;
	check_case(&m, &ops, MT6897_SPI2_DENIED, ACQUIRE, RELEASE);
	init(&m);
	m.grant.rx.dma = (UINT64_C(1) << 36) - MT6897_SPI2_CACHE_LINE;
	check_case(&m, &ops, MT6897_SPI2_DENIED, ACQUIRE, RELEASE);
	init(&m);
	m.grant.rx.cpu = m.tx;
	check_case(&m, &ops, MT6897_SPI2_DENIED, ACQUIRE, RELEASE);
	init(&m);
	m.grant.rx.pa = m.grant.tx.pa + MT6897_SPI2_CACHE_LINE;
	check_case(&m, &ops, MT6897_SPI2_DENIED, ACQUIRE, RELEASE);
	init(&m);
	m.grant.rx.dma = m.grant.tx.dma + MT6897_SPI2_CACHE_LINE;
	check_case(&m, &ops, MT6897_SPI2_DENIED, ACQUIRE, RELEASE);
	init(&m);
	m.grant.rx.dma++;
	check_case(&m, &ops, MT6897_SPI2_DENIED, ACQUIRE, RELEASE);
	init(&m);
	m.fault = IRQ;
	check_case(&m, &ops, MT6897_SPI2_NO_TOUCH, IRQ, RELEASE);
	for (enum operation op = CLEAN; op <= TO_CPU; ++op) {
		init(&m);
		m.fault = op;
		check_case(&m, &ops, op == TRANSFER ? MT6897_SPI2_DMA_UNCERTAIN :
		    MT6897_SPI2_SYNC_FAILED, op, op == TRANSFER ? QUARANTINE : RELEASE);
	}
	init(&m);
	m.wire[98] ^= 1;
	check_case(&m, &ops, MT6897_SPI2_BAD_REPORT, TO_CPU, RELEASE);
	init(&m);
	check_case(&m, &ops, MT6897_SPI2_OK, TO_CPU, RELEASE);
	init(&m);
	m.grant.route = MT6897_SPI2_DMA_DIRECT;
	m.grant.dma_bits = 32;
	m.grant.tx.dma = m.grant.tx.pa;
	m.grant.rx.dma = m.grant.rx.pa;
	check_case(&m, &ops, MT6897_SPI2_OK, TO_CPU, RELEASE);
	printf("%u SPI2 one-shot DMA scenarios passed\n", cases);
	return 0;
}
