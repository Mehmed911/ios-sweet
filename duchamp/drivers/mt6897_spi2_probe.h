#ifndef MT6897_SPI2_PROBE_H
#define MT6897_SPI2_PROBE_H

#include "duchamp_ft3683g.h"

#define MT6897_SPI2_CACHE_LINE 64u
#define MT6897_SPI2_BUFFER_BYTES 128u
#define MT6897_SPI2_MAX_WAIT_MS 250u

enum mt6897_spi2_resources {
	MT6897_SPI2_HANDOFF = 1u << 0,
	MT6897_SPI2_CONTROLLER = 1u << 1,
	MT6897_SPI2_CLOCKS = 1u << 2,
	MT6897_SPI2_PINS = 1u << 3,
	MT6897_SPI2_SUPPLIES = 1u << 4,
	MT6897_SPI2_IRQS = 1u << 5,
	MT6897_SPI2_DMA_MAPPING = 1u << 6,
	MT6897_SPI2_CACHE_OWNER = 1u << 7,
	MT6897_SPI2_NO_BOUNCE = 1u << 8,
	MT6897_SPI2_REQUIRED = (1u << 9) - 1,
};

enum mt6897_spi2_dma_route {
	MT6897_SPI2_DMA_DIRECT = 1,
	MT6897_SPI2_DMA_IOMMU,
};

struct mt6897_spi2_buffer {
	uint8_t *cpu;
	uint64_t pa;
	uint64_t dma;
};

struct mt6897_spi2_grant {
	uint64_t generation;
	unsigned resources;
	unsigned cache_line;
	unsigned dma_bits;
	enum mt6897_spi2_dma_route route;
	struct mt6897_spi2_buffer tx;
	struct mt6897_spi2_buffer rx;
};

enum mt6897_spi2_sync {
	MT6897_SPI2_CLEAN_TX,
	MT6897_SPI2_PREPARE_RX, /* clean and invalidate */
	MT6897_SPI2_PUBLISH_DMA, /* complete both operations before start */
	MT6897_SPI2_COMPLETE_DMA, /* order controller completion before invalidating */
	MT6897_SPI2_INVALIDATE_RX,
	MT6897_SPI2_PUBLISH_CPU, /* complete invalidation before parsing */
};

enum mt6897_spi2_release {
	MT6897_SPI2_RELEASE_IDLE,
	MT6897_SPI2_QUARANTINE_DMA,
};

/*
 * Only a trusted platform provider may issue a grant. Acquire checks ownership
 * and pins exclusive mappings for two disjoint 128-byte buffers. It performs
 * no device I/O or cache operations and returns with nothing held on failure.
 * DT, boot arguments and Linux runtime observations cannot issue a grant.
 * A successful grant holds the resources and addresses stable until release.
 *
 * Wait arms/observes GPIO9 only after admission. Transfer uses SPI2 CS0, mode
 * 0, 8-bit words, a single CS assertion and exactly wire_bytes. Both waits
 * must enforce their timeouts. Transfer success requires confirmed completion
 * and an idle DMA engine. On transfer failure, quarantine retains ownership
 * and prevents the mappings/buffers from being reused until proven idle.
 * Sync operates on the entire isolated buffer when it receives one.
 */
struct mt6897_spi2_provider {
	int (*acquire)(void *, struct mt6897_spi2_grant *);
	int (*wait_touch)(void *, unsigned timeout_ms);
	int (*sync)(void *, enum mt6897_spi2_sync, const struct mt6897_spi2_buffer *);
	int (*transfer)(void *, uint64_t tx_dma, uint64_t rx_dma, size_t wire_bytes,
	    unsigned timeout_ms);
	void (*release)(void *, enum mt6897_spi2_release);
};

enum mt6897_spi2_result {
	MT6897_SPI2_OK = 0,
	MT6897_SPI2_DENIED,
	MT6897_SPI2_ALREADY_ATTEMPTED,
	MT6897_SPI2_NO_TOUCH,
	MT6897_SPI2_SYNC_FAILED,
	MT6897_SPI2_DMA_UNCERTAIN,
	MT6897_SPI2_BAD_REPORT,
};

/* Zero-initialize once per boot. The first attempt consumes the diagnostic. */
struct mt6897_spi2_probe {
	unsigned attempted;
};

enum mt6897_spi2_result mt6897_spi2_read_touch_once(
	struct mt6897_spi2_probe *probe, uint64_t generation,
	const struct mt6897_spi2_provider *provider, void *context,
	struct dft_report *out);

#endif
