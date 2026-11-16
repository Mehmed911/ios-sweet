#include "ufs_handoff_evidence.h"

enum { FDT_BEGIN_NODE = 1, FDT_END_NODE = 2, FDT_PROP = 3, FDT_NOP = 4, FDT_END = 9 };
#define MAX_PROPERTY_NAME 128u
enum node_kind { OTHER, ROOT, CHOSEN, SOC, UFS };

static uint32_t
be32(const volatile unsigned char *value)
{
	return (uint32_t)value[0] << 24 | (uint32_t)value[1] << 16 |
	    (uint32_t)value[2] << 8 | value[3];
}

/* FIPS 180-4 sections 5 and 6.2. Kept local to the passive FDT recorder. */
static uint32_t
rotr(uint32_t value, unsigned shift)
{
	return (value >> shift) | (value << (32 - shift));
}

static void
sha256_block(uint32_t state[8], const unsigned char block[64])
{
	static const uint32_t constants[64] = {
		0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
		0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
		0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
		0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
		0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
		0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
		0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
		0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2,
	};
	uint32_t words[64];
	for (unsigned i = 0; i < 16; i++)
		words[i] = be32(block + 4 * i);
	for (unsigned i = 16; i < 64; i++) {
		uint32_t x = words[i - 15], y = words[i - 2];
		uint32_t sigma0 = rotr(x, 7) ^ rotr(x, 18) ^ (x >> 3);
		uint32_t sigma1 = rotr(y, 17) ^ rotr(y, 19) ^ (y >> 10);
		words[i] = words[i - 16] + sigma0 + words[i - 7] + sigma1;
	}

	uint32_t a = state[0], b = state[1], c = state[2], d = state[3];
	uint32_t e = state[4], f = state[5], g = state[6], h = state[7];
	for (unsigned i = 0; i < 64; i++) {
		uint32_t sum1 = rotr(e, 6) ^ rotr(e, 11) ^ rotr(e, 25);
		uint32_t choose = (e & f) ^ (~e & g);
		uint32_t t1 = h + sum1 + choose + constants[i] + words[i];
		uint32_t sum0 = rotr(a, 2) ^ rotr(a, 13) ^ rotr(a, 22);
		uint32_t majority = (a & b) ^ (a & c) ^ (b & c);
		h = g;
		g = f;
		f = e;
		e = d + t1;
		d = c;
		c = b;
		b = a;
		a = t1 + sum0 + majority;
	}
	state[0] += a;
	state[1] += b;
	state[2] += c;
	state[3] += d;
	state[4] += e;
	state[5] += f;
	state[6] += g;
	state[7] += h;
}

static uint64_t
digest_fdt(const volatile unsigned char *fdt, uint32_t bytes, unsigned char *digest)
{
	/* Explicit stores keep the freestanding entry free of a libc copy. */
	uint32_t state[8];
	state[0] = 0x6a09e667;
	state[1] = 0xbb67ae85;
	state[2] = 0x3c6ef372;
	state[3] = 0xa54ff53a;
	state[4] = 0x510e527f;
	state[5] = 0x9b05688c;
	state[6] = 0x1f83d9ab;
	state[7] = 0x5be0cd19;
	unsigned char block[64];
	unsigned used = 0;
	uint64_t fingerprint = UINT64_C(1469598103934665603);
	for (uint32_t i = 0; i < bytes; i++) {
		unsigned char byte = fdt[i];
		fingerprint = (fingerprint ^ byte) * UINT64_C(1099511628211);
		block[used++] = byte;
		if (used == sizeof(block)) {
			sha256_block(state, block);
			used = 0;
		}
	}

	block[used++] = 0x80;
	if (used > 56) {
		while (used < sizeof(block)) block[used++] = 0;
		sha256_block(state, block);
		used = 0;
	}
	while (used < 56) block[used++] = 0;
	const uint64_t bits = (uint64_t)bytes * 8;
	for (unsigned i = 0; i < 8; i++)
		block[56 + i] = (unsigned char)(bits >> (56 - 8 * i));
	sha256_block(state, block);
	for (unsigned i = 0; i < DUCHAMP_UFS_FDT_DIGEST_BYTES; i++)
		digest[i] = (unsigned char)(state[i / 4] >> (24 - 8 * (i % 4)));
	return fingerprint;
}

static int
equals(const volatile unsigned char *bytes, size_t size, const char *text)
{
	size_t i = 0;
	while (i < size && text[i] && bytes[i] == (unsigned char)text[i])
		i++;
	return i == size && !text[i];
}

static int
space(unsigned char value)
{
	return value == ' ' || value == '\t' || value == '\n' || value == '\r';
}

static void
record_slot(const volatile unsigned char *value, uint32_t size, uint32_t *hint)
{
	static const char key[] = "androidboot.slot_suffix=";
	const size_t key_size = sizeof(key) - 1;
	if (!size || value[size - 1] != 0) {
		*hint = DUCHAMP_UFS_SLOT_INVALID;
		return;
	}
	for (size_t pos = 0; pos + 1 < size;) {
		if (!value[pos]) {
			*hint = DUCHAMP_UFS_SLOT_INVALID;
			return;
		}
		if (space(value[pos])) {
			pos++;
			continue;
		}
		size_t start = pos;
		while (pos + 1 < size && value[pos] && !space(value[pos]))
			pos++;
		size_t length = pos - start;
		if (length < key_size || !equals(value + start, key_size, key))
			continue;
		uint32_t seen = DUCHAMP_UFS_SLOT_INVALID;
		if (length == key_size + 2 && value[start + key_size] == '_') {
			switch (value[start + key_size + 1]) {
			case 'a': seen = DUCHAMP_UFS_SLOT_A; break;
			case 'b': seen = DUCHAMP_UFS_SLOT_B; break;
			}
		}
		*hint = !*hint || *hint == seen ? seen : DUCHAMP_UFS_SLOT_INVALID;
	}
}

static uint32_t
declaration(const volatile unsigned char *name, uint32_t length,
	const volatile unsigned char *value, uint32_t size)
{
	if (equals(name, length, "reg"))
		return size == 16 && !be32(value) && be32(value + 4) == 0x112b0000 &&
		    !be32(value + 8) && be32(value + 12) == 0x3000 ?
		    DUCHAMP_UFS_DECL_HCI_REG : 0;
	if (equals(name, length, "mediatek,ufs-rtff-mtcmos"))
		return !size ? DUCHAMP_UFS_DECL_RTFF_MTCMOS : 0;
	if (equals(name, length, "dma-coherent"))
		return !size ? DUCHAMP_UFS_DECL_DMA_COHERENT : 0;
	if (!size || (size & 3) || !be32(value))
		return 0;
	if (equals(name, length, "clocks")) return DUCHAMP_UFS_DECL_CLOCKS;
	if (equals(name, length, "phys")) return DUCHAMP_UFS_DECL_PHY;
	if (equals(name, length, "power-domains")) return DUCHAMP_UFS_DECL_POWER_DOMAIN;
	if (equals(name, length, "resets")) return DUCHAMP_UFS_DECL_RESETS;
	if (equals(name, length, "iommus")) return DUCHAMP_UFS_DECL_IOMMUS;
	if (size != 4) return 0;
	if (equals(name, length, "vcc-supply")) return DUCHAMP_UFS_DECL_VCC;
	if (equals(name, length, "vccq-supply")) return DUCHAMP_UFS_DECL_VCCQ;
	return 0;
}

/* Narrow FDT v17 reader. These are property observations under exact paths.
 * It does not resolve or enable any of the referenced providers.
 */
static int
inspect_fdt(const volatile unsigned char *fdt, uint32_t total,
	uint32_t *slot, uint32_t *declared)
{
	uint32_t pos = be32(fdt + 8), strings = be32(fdt + 12);
	uint32_t string_bytes = be32(fdt + 32), tokens = be32(fdt + 36);
	if (be32(fdt + 20) != 17 || pos < 40 || (pos & 3) ||
	    pos > total || tokens > total - pos || tokens < 4 ||
	    strings < 40 || strings > total || string_bytes > total - strings ||
	    (pos < strings + string_bytes && strings < pos + tokens))
		return 0;
	uint32_t end = pos + tokens, names_end = strings + string_bytes;
	enum node_kind nodes[64];
	unsigned depth = 0, visited = 0;

	while (end - pos >= 4) {
		uint32_t token = be32(fdt + pos);
		pos += 4;
		switch (token) {
		case FDT_BEGIN_NODE: {
			uint32_t start = pos;
			while (pos < end && fdt[pos])
				pos++;
			if (pos == end || depth == sizeof(nodes) / sizeof(nodes[0]))
				return 0;
			uint32_t length = pos - start;
			enum node_kind kind = OTHER;
			if (!depth) {
				if (length) return 0;
				kind = ROOT;
			} else if (nodes[depth - 1] == ROOT) {
				if (equals(fdt + start, length, "chosen")) kind = CHOSEN;
				if (equals(fdt + start, length, "soc")) kind = SOC;
			} else if (nodes[depth - 1] == SOC &&
			    equals(fdt + start, length, "ufshci@112b0000")) {
				kind = UFS;
			}
			if (kind != OTHER && (visited & (1u << kind)))
				return 0;
			visited |= 1u << kind;
			nodes[depth++] = kind;
			pos = (pos + 4) & ~3u;
			break;
		}
		case FDT_END_NODE:
			if (!depth) return 0;
			depth--;
			break;
		case FDT_PROP: {
			if (!depth || end - pos < 8) return 0;
			uint32_t size = be32(fdt + pos);
			uint32_t name = be32(fdt + pos + 4);
			pos += 8;
			if (name >= string_bytes || size > end - pos) return 0;
			name += strings;
			uint32_t term = name;
			while (term < names_end && term - name < MAX_PROPERTY_NAME && fdt[term])
				term++;
			if (term == names_end || term - name == MAX_PROPERTY_NAME) return 0;
			enum node_kind kind = nodes[depth - 1];
			if (kind == CHOSEN &&
			    (equals(fdt + name, term - name, "bootargs") ||
			    equals(fdt + name, term - name, "bootargs_ext")))
				record_slot(fdt + pos, size, slot);
			if (kind == UFS)
				*declared |= declaration(fdt + name, term - name, fdt + pos, size);
			pos = (pos + size + 3) & ~3u;
			break;
		}
		case FDT_NOP:
			break;
		case FDT_END:
			return !depth && (visited & (1u << ROOT)) && pos == end;
		default:
			return 0;
		}
		if (pos > end) return 0;
	}
	return 0;
}

void
duchamp_ufs_handoff_collect(struct duchamp_ufs_handoff_record *record,
	const volatile unsigned char *fdt, size_t available,
	uint64_t entry_pc, uint64_t entry_x0)
{
	record->magic = DUCHAMP_UFS_HANDOFF_MAGIC;
	record->version = DUCHAMP_UFS_HANDOFF_VERSION;
	record->size = sizeof(*record);
	record->fdt_fingerprint = 0;
	record->fdt_bytes = 0;
	record->blockers = DUCHAMP_UFS_NO_TRACE | DUCHAMP_UFS_HCE_UNKNOWN |
	    DUCHAMP_UFS_QUEUES_UNKNOWN | DUCHAMP_UFS_DMA_UNVERIFIED |
	    DUCHAMP_UFS_FDT_INVALID | DUCHAMP_UFS_SLOT_UNVERIFIED |
	    DUCHAMP_UFS_OWNER_UNVERIFIED | DUCHAMP_UFS_POWER_UNVERIFIED |
	    DUCHAMP_UFS_CLOCKS_UNVERIFIED | DUCHAMP_UFS_MMIO_UNVERIFIED |
	    DUCHAMP_UFS_PHY_UNVERIFIED | DUCHAMP_UFS_RESET_UNVERIFIED |
	    DUCHAMP_UFS_IOMMU_UNVERIFIED | DUCHAMP_UFS_CACHE_UNVERIFIED |
	    DUCHAMP_UFS_BOOT_ID_UNBOUND | DUCHAMP_UFS_FIRMWARE_ID_UNVERIFIED;
	record->slot_hint = DUCHAMP_UFS_SLOT_UNKNOWN;
	record->declarations = 0;
	record->entry_pc = entry_pc;
	record->entry_x0 = entry_x0;
	for (size_t i = 0; i < sizeof(record->fdt_sha256); i++)
		record->fdt_sha256[i] = 0;
	if (!fdt || available < 40 || be32(fdt) != 0xd00dfeed)
		return;
	uint32_t bytes = be32(fdt + 4), slot = 0, declared = 0;
	if (bytes < 40 || bytes > available || bytes > DUCHAMP_UFS_HANDOFF_FDT_MAX ||
	    !inspect_fdt(fdt, bytes, &slot, &declared))
		return;

	/* Both values describe the observed bytes only. */
	record->fdt_fingerprint = digest_fdt(fdt, bytes, record->fdt_sha256);
	record->fdt_bytes = bytes;
	record->slot_hint = slot;
	record->declarations = declared;
	record->blockers &= ~DUCHAMP_UFS_FDT_INVALID;
}
