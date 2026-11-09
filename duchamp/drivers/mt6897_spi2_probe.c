#include "mt6897_spi2_probe.h"

struct touch_exchange {
	const struct mt6897_spi2_provider *provider;
	void *context;
	const struct mt6897_spi2_grant *grant;
	enum mt6897_spi2_result result;
};

static int
range_valid(uint64_t address, uint64_t limit)
{
	return address && (address & (MT6897_SPI2_CACHE_LINE - 1)) == 0 &&
	    address <= limit - (MT6897_SPI2_BUFFER_BYTES - 1);
}

static int
disjoint(uint64_t a, uint64_t b)
{
	return a < b ? b - a >= MT6897_SPI2_BUFFER_BYTES :
	    a - b >= MT6897_SPI2_BUFFER_BYTES;
}

static int
grant_valid(const struct mt6897_spi2_grant *grant, uint64_t generation)
{
	const struct mt6897_spi2_buffer *tx = &grant->tx, *rx = &grant->rx;

	if (grant->generation != generation ||
	    grant->resources != MT6897_SPI2_REQUIRED ||
	    grant->cache_line != MT6897_SPI2_CACHE_LINE ||
	    grant->dma_bits < 32 || grant->dma_bits > 36 ||
	    (grant->route != MT6897_SPI2_DMA_DIRECT &&
	    grant->route != MT6897_SPI2_DMA_IOMMU)) {
		return 0;
	}
	const uint64_t limit = (UINT64_C(1) << grant->dma_bits) - 1;
	return range_valid((uintptr_t)tx->cpu, UINTPTR_MAX) &&
	    range_valid((uintptr_t)rx->cpu, UINTPTR_MAX) &&
	    disjoint((uintptr_t)tx->cpu, (uintptr_t)rx->cpu) &&
	    range_valid(tx->pa, UINT64_MAX) && range_valid(rx->pa, UINT64_MAX) &&
	    disjoint(tx->pa, rx->pa) &&
	    range_valid(tx->dma, limit) && range_valid(rx->dma, limit) &&
	    disjoint(tx->dma, rx->dma);
}

static int
exchange_report(void *context, const uint8_t *tx, uint8_t *rx, size_t bytes)
{
	struct touch_exchange *exchange = context;
	const struct mt6897_spi2_provider *provider = exchange->provider;
	const struct mt6897_spi2_grant *grant = exchange->grant;
	void *io = exchange->context;

	if (bytes != DFT_WIRE_BYTES || tx[0] != 0x01 || tx[1] != 0xa0 ||
	    tx[2] != 0 || tx[3] != DFT_WIRE_BYTES - 9) {
		return -1;
	}
	for (size_t i = 0; i < MT6897_SPI2_BUFFER_BYTES; ++i) {
		grant->tx.cpu[i] = i < bytes ? tx[i] : 0;
		grant->rx.cpu[i] = 0;
	}
	exchange->result = MT6897_SPI2_SYNC_FAILED;
	if (provider->sync(io, MT6897_SPI2_CLEAN_TX, &grant->tx) ||
	    provider->sync(io, MT6897_SPI2_PREPARE_RX, &grant->rx) ||
	    provider->sync(io, MT6897_SPI2_PUBLISH_DMA, NULL)) {
		return -1;
	}
	if (provider->transfer(io, grant->tx.dma, grant->rx.dma, bytes,
	    MT6897_SPI2_MAX_WAIT_MS)) {
		exchange->result = MT6897_SPI2_DMA_UNCERTAIN;
		return -1;
	}
	if (provider->sync(io, MT6897_SPI2_COMPLETE_DMA, NULL) ||
	    provider->sync(io, MT6897_SPI2_INVALIDATE_RX, &grant->rx) ||
	    provider->sync(io, MT6897_SPI2_PUBLISH_CPU, NULL)) {
		return -1;
	}
	for (size_t i = 0; i < bytes; ++i) {
		rx[i] = grant->rx.cpu[i];
	}
	exchange->result = MT6897_SPI2_BAD_REPORT;
	return 0;
}

enum mt6897_spi2_result
mt6897_spi2_read_touch_once(struct mt6897_spi2_probe *probe, uint64_t generation,
    const struct mt6897_spi2_provider *provider, void *context,
    struct dft_report *out)
{
	if (!probe || !out) {
		return MT6897_SPI2_DENIED;
	}
	if (__atomic_exchange_n(&probe->attempted, 1, __ATOMIC_ACQ_REL)) {
		return MT6897_SPI2_ALREADY_ATTEMPTED;
	}
	if (!generation || !provider || !provider->acquire || !provider->wait_touch ||
	    !provider->sync || !provider->transfer || !provider->release) {
		return MT6897_SPI2_DENIED;
	}
	struct mt6897_spi2_grant grant = { 0 };
	if (provider->acquire(context, &grant)) {
		return MT6897_SPI2_DENIED;
	}
	enum mt6897_spi2_result result = MT6897_SPI2_DENIED;
	struct dft_report report;
	if (grant_valid(&grant, generation)) {
		result = MT6897_SPI2_NO_TOUCH;
		if (!provider->wait_touch(context, MT6897_SPI2_MAX_WAIT_MS)) {
			struct touch_exchange exchange = {
				provider, context, &grant, MT6897_SPI2_BAD_REPORT
			};
			const int decoded = dft_read_report(exchange_report, &exchange, &report);
			result = exchange.result;
			if (decoded == DFT_OK && report.format == DFT_HIGH_RESOLUTION) {
				result = MT6897_SPI2_OK;
				for (unsigned i = 0; i < report.count; ++i) {
					if (report.contacts[i].x >= 1220 * 16 ||
					    report.contacts[i].y >= 2712 * 16) {
						result = MT6897_SPI2_BAD_REPORT;
						break;
					}
				}
			}
		}
	}
	provider->release(context, result == MT6897_SPI2_DMA_UNCERTAIN ?
	    MT6897_SPI2_QUARANTINE_DMA : MT6897_SPI2_RELEASE_IDLE);
	if (result == MT6897_SPI2_OK) {
		*out = report;
	}
	return result;
}
