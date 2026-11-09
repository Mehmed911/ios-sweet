/* Exercised only by the QEMU ADT fixture. The provider has no device access. */
#if defined(DUCHAMP)
#include <sys/systm.h>
#include "mt6897_spi2_probe.h"

extern void CleanPoC_DcacheRegion(uintptr_t, size_t);
extern void FlushPoC_DcacheRegion(uintptr_t, unsigned);

int duchamp_qemu_spi2_dma_probe(const uint8_t *wire, struct dft_report *out);

struct spi2_model {
	_Alignas(MT6897_SPI2_CACHE_LINE) uint8_t tx[MT6897_SPI2_BUFFER_BYTES];
	_Alignas(MT6897_SPI2_CACHE_LINE) uint8_t rx[MT6897_SPI2_BUFFER_BYTES];
	const uint8_t *wire;
	unsigned resources;
	unsigned syncs;
	unsigned transfers;
	unsigned releases;
};

static int
model_acquire(void *context, struct mt6897_spi2_grant *grant)
{
	struct spi2_model *model = context;
	uint64_t ctr;
	__asm__ volatile("mrs %0, ctr_el0" : "=r"(ctr));
	*grant = (struct mt6897_spi2_grant){
		.generation = 1, .resources = model->resources,
		.cache_line = 4u << ((ctr >> 16) & 15), .dma_bits = 36,
		.route = MT6897_SPI2_DMA_IOMMU,
		/* Synthetic PA/IOVA labels for ordinary RAM. */
		.tx = { model->tx, 0x50000000, UINT64_C(0x100000000) },
		.rx = { model->rx, 0x50001000, UINT64_C(0x100001000) },
	};
	return 0;
}

static int
model_touch(void *context, unsigned timeout_ms)
{
	struct spi2_model *model = context;
	return !model->wire || timeout_ms != MT6897_SPI2_MAX_WAIT_MS;
}

static int
model_sync(void *context, enum mt6897_spi2_sync action,
    const struct mt6897_spi2_buffer *buffer)
{
	struct spi2_model *model = context;
	if (model->syncs != (unsigned)action) {
		return -1;
	}
	switch (action) {
	case MT6897_SPI2_CLEAN_TX:
		CleanPoC_DcacheRegion((uintptr_t)buffer->cpu, MT6897_SPI2_BUFFER_BYTES);
		break;
	case MT6897_SPI2_PREPARE_RX:
		FlushPoC_DcacheRegion((uintptr_t)buffer->cpu, MT6897_SPI2_BUFFER_BYTES);
		break;
	case MT6897_SPI2_INVALIDATE_RX:
		for (unsigned offset = 0; offset < MT6897_SPI2_BUFFER_BYTES;
		    offset += MT6897_SPI2_CACHE_LINE) {
			__asm__ volatile("dc ivac, %0" :: "r"(buffer->cpu + offset) : "memory");
		}
		break;
	default:
		__asm__ volatile("dsb sy" ::: "memory");
		break;
	}
	++model->syncs;
	return 0;
}

static int
model_transfer(void *context, uint64_t tx, uint64_t rx, size_t size, unsigned timeout_ms)
{
	struct spi2_model *model = context;
	static const uint8_t command[DFT_WIRE_BYTES] = { 0x01, 0xa0, 0, 91 };
	if (model->transfers || model->syncs != MT6897_SPI2_COMPLETE_DMA ||
	    tx != UINT64_C(0x100000000) || rx != UINT64_C(0x100001000) ||
	    size != sizeof(command) || timeout_ms != MT6897_SPI2_MAX_WAIT_MS ||
	    memcmp(model->tx, command, size)) {
		return -1;
	}
	/* Publish the fixture as simulated device output before the CPU invalidates. */
	memcpy(model->rx, model->wire, size);
	CleanPoC_DcacheRegion((uintptr_t)model->rx, MT6897_SPI2_BUFFER_BYTES);
	__asm__ volatile("dsb sy" ::: "memory");
	++model->transfers;
	return 0;
}

static void
model_release(void *context, enum mt6897_spi2_release disposition)
{
	struct spi2_model *model = context;
	if (disposition == MT6897_SPI2_RELEASE_IDLE) {
		++model->releases;
	}
}

int
duchamp_qemu_spi2_dma_probe(const uint8_t *wire, struct dft_report *out)
{
	static const struct mt6897_spi2_provider ops = {
		model_acquire, model_touch, model_sync, model_transfer, model_release,
	};
	struct mt6897_spi2_probe denied = { 0 }, allowed = { 0 };
	struct spi2_model model = { .wire = wire };
	model.resources = MT6897_SPI2_REQUIRED & ~MT6897_SPI2_CACHE_OWNER;
	if (mt6897_spi2_read_touch_once(&denied, 1, &ops, &model, out) != MT6897_SPI2_DENIED ||
	    model.syncs || model.transfers || model.releases != 1) {
		return DFT_TRANSFER_FAILED;
	}
	model.resources = MT6897_SPI2_REQUIRED;
	enum mt6897_spi2_result result = mt6897_spi2_read_touch_once(&allowed, 1, &ops, &model, out);
	if (result != MT6897_SPI2_OK || model.syncs != 6 ||
	    model.transfers != 1 || model.releases != 2) {
		printf("DUCHAMP SPI2 QEMU DMA PROBE FAIL result=%u syncs=%u transfers=%u\n",
		    result, model.syncs, model.transfers);
		return DFT_TRANSFER_FAILED;
	}
	printf("DUCHAMP SPI2 QEMU DMA PROBE PASS denied=1 syncs=6 transfer=1 contacts=%u\n",
	    out->count);
	return DFT_OK;
}
#endif
