#include "duchamp_ft3683g.h"

/* Wire layout recovered from the pinned Duchamp focaltech_touch module. */
enum {
	TOUCH_DATA_REGISTER = 0x01,
	CHIP_ID_HIGH_REGISTER = 0xa3,
	CHIP_ID_LOW_REGISTER = 0x9f,
	READ_WITH_CRC = 0xa0,
	STATUS_ERROR_MASK = 0xa0,
	PAYLOAD_OFFSET = 7,
	PAYLOAD_BYTES = DFT_WIRE_BYTES - PAYLOAD_OFFSET - 2,
	STANDARD_POINT_OFFSET = 2,
	STANDARD_POINT_BYTES = 6,
	HIGH_RES_POINT_OFFSET = 4,
	HIGH_RES_POINT_BYTES = 8,
};

static uint16_t
payload_crc(const uint8_t *payload, size_t size)
{
	uint16_t crc = UINT16_MAX;

	for (size_t i = 0; i < size; ++i) {
		crc ^= payload[i];
		for (unsigned bit = 0; bit < 8; ++bit) {
			crc = (crc >> 1) ^ ((crc & 1) ? 0x8408 : 0);
		}
	}
	return crc;
}

static int
read_register(dft_exchange exchange, void *context, uint8_t address, uint8_t *rx,
    uint8_t payload_size)
{
	const uint8_t tx[DFT_WIRE_BYTES] = { address, READ_WITH_CRC, 0, payload_size };
	const uint8_t *payload = rx + PAYLOAD_OFFSET;
	const size_t transfer_size = PAYLOAD_OFFSET + payload_size + 2;
	uint16_t crc;

	if (exchange(context, tx, rx, transfer_size)) {
		return DFT_TRANSFER_FAILED;
	}
	if (rx[3] & STATUS_ERROR_MASK) {
		return DFT_CONTROLLER_STATUS;
	}
	crc = (uint16_t)payload[payload_size] | (uint16_t)(payload[payload_size + 1] << 8);
	if (crc != payload_crc(payload, payload_size)) {
		return DFT_BAD_CRC;
	}
	return DFT_OK;
}

static int
decode_report(const uint8_t *payload, struct dft_report *out)
{
	struct dft_report report = { 0 };
	const uint8_t format = payload[1] >> 4;
	const uint8_t advertised = payload[1] & 0xf;
	unsigned offset, stride, limit;
	unsigned seen = 0;

	if (format == DFT_STANDARD) {
		offset = STANDARD_POINT_OFFSET;
		stride = STANDARD_POINT_BYTES;
		limit = DFT_MAX_CONTACTS;
	} else if (format == DFT_HIGH_RESOLUTION) {
		offset = HIGH_RES_POINT_OFFSET;
		stride = HIGH_RES_POINT_BYTES;
		limit = advertised;
		if (!limit) {
			return DFT_BAD_REPORT;
		}
	} else {
		return DFT_UNSUPPORTED_REPORT;
	}
	if (advertised > DFT_MAX_CONTACTS || offset + limit * stride > PAYLOAD_BYTES) {
		return DFT_BAD_REPORT;
	}

	report.format = (enum dft_report_format)format;
	for (unsigned i = 0; i < limit; ++i) {
		const uint8_t *point = payload + offset + i * stride;
		const unsigned id = point[2] >> 4;
		const unsigned phase = point[0] >> 6;
		struct dft_contact *contact;

		if (format == DFT_STANDARD && id >= DFT_MAX_CONTACTS) {
			break;
		}
		if (id >= DFT_MAX_CONTACTS || (seen & (1u << id)) ||
		    phase > DFT_MOVE || (format == DFT_STANDARD && !advertised && phase != DFT_UP)) {
			return DFT_BAD_REPORT;
		}
		seen |= 1u << id;
		contact = &report.contacts[report.count++];
		contact->id = id;
		contact->phase = phase;
		contact->x = (uint16_t)((point[0] & 0xf) << 8) | point[1];
		contact->y = (uint16_t)((point[2] & 0xf) << 8) | point[3];
		if (format == DFT_HIGH_RESOLUTION) {
			contact->x = (contact->x << 4) | (point[4] >> 4);
			contact->y = (contact->y << 4) | (point[4] & 0xf);
		}
	}
	if (!report.count) {
		return DFT_BAD_REPORT;
	}
	*out = report;
	return DFT_OK;
}

int
dft_read_identity(dft_exchange exchange, void *context, uint16_t *out)
{
	uint8_t rx[PAYLOAD_OFFSET + 1 + 2] = { 0 };
	uint8_t high;
	int result;

	if (!exchange || !out) {
		return DFT_BAD_ARGUMENT;
	}
	result = read_register(exchange, context, CHIP_ID_HIGH_REGISTER, rx, 1);
	if (result != DFT_OK) {
		return result;
	}
	high = rx[PAYLOAD_OFFSET];
	result = read_register(exchange, context, CHIP_ID_LOW_REGISTER, rx, 1);
	if (result != DFT_OK) {
		return result;
	}
	*out = (uint16_t)(high << 8) | rx[PAYLOAD_OFFSET];
	return DFT_OK;
}

int
dft_read_report(dft_exchange exchange, void *context, struct dft_report *out)
{
	uint8_t rx[DFT_WIRE_BYTES] = { 0 };
	int result;

	if (!exchange || !out) {
		return DFT_BAD_ARGUMENT;
	}
	result = read_register(exchange, context, TOUCH_DATA_REGISTER, rx, PAYLOAD_BYTES);
	return result == DFT_OK ? decode_report(rx + PAYLOAD_OFFSET, out) : result;
}
