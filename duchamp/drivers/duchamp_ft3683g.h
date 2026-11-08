#ifndef DUCHAMP_FT3683G_H
#define DUCHAMP_FT3683G_H

#include <stddef.h>
#include <stdint.h>

#define DFT_MAX_CONTACTS 10
#define DFT_WIRE_BYTES 100

enum dft_result {
	DFT_OK = 0,
	DFT_BAD_ARGUMENT = -1,
	DFT_TRANSFER_FAILED = -2,
	DFT_CONTROLLER_STATUS = -3,
	DFT_BAD_CRC = -4,
	DFT_UNSUPPORTED_REPORT = -5,
	DFT_BAD_REPORT = -6,
};

enum dft_contact_phase {
	DFT_DOWN = 0,
	DFT_UP = 1,
	DFT_MOVE = 2,
};

enum dft_report_format {
	DFT_STANDARD = 0,
	DFT_HIGH_RESOLUTION = 2,
};

struct dft_contact {
	uint16_t x;
	uint16_t y;
	uint8_t id;
	uint8_t phase;
};

struct dft_report {
	enum dft_report_format format;
	uint8_t count;
	struct dft_contact contacts[DFT_MAX_CONTACTS];
};

/*
 * A bound caller supplies a synchronous full-duplex transfer, with a single
 * chip select for the entire transaction. It must serialize access and
 * enforce its own deadline and inter-transaction chip-select timing. Zero
 * means exactly size bytes were transferred. The buffers cannot be retained.
 */
typedef int (*dft_exchange)(void *context, const uint8_t *tx, uint8_t *rx, size_t size);

/* Two 10-byte read transactions. The result is the raw identity, high byte
 * first. This does not enter bootloader mode or establish the panel variant.
 */
int dft_read_identity(dft_exchange exchange, void *context, uint16_t *out);

/* Reads register 0x01 once. Coordinates are in the controller's native units.
 * A failure leaves the caller's previous report untouched.
 */
int dft_read_report(dft_exchange exchange, void *context, struct dft_report *out);

#endif
