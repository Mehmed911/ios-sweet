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
	if (!size || (size & 3) || !be32(value))
		return 0;
	if (equals(name, length, "clocks")) return DUCHAMP_UFS_DECL_CLOCKS;
	if (equals(name, length, "phys")) return DUCHAMP_UFS_DECL_PHY;
	if (equals(name, length, "power-domains")) return DUCHAMP_UFS_DECL_POWER_DOMAIN;
	if (equals(name, length, "resets")) return DUCHAMP_UFS_DECL_RESETS;
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
	const volatile unsigned char *fdt, size_t available)
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
	    DUCHAMP_UFS_PHY_UNVERIFIED;
	record->slot_hint = DUCHAMP_UFS_SLOT_UNKNOWN;
	record->declarations = 0;
	if (!fdt || available < 40 || be32(fdt) != 0xd00dfeed)
		return;
	uint32_t bytes = be32(fdt + 4), slot = 0, declared = 0;
	if (bytes < 40 || bytes > available || bytes > DUCHAMP_UFS_HANDOFF_FDT_MAX ||
	    !inspect_fdt(fdt, bytes, &slot, &declared))
		return;

	/* Screen-to-RAM correlation only. This is not a trust token. */
	uint64_t fingerprint = UINT64_C(1469598103934665603);
	for (uint32_t i = 0; i < bytes; i++) {
		fingerprint ^= fdt[i];
		fingerprint *= UINT64_C(1099511628211);
	}
	record->fdt_bytes = bytes;
	record->fdt_fingerprint = fingerprint;
	record->slot_hint = slot;
	record->declarations = declared;
	record->blockers &= ~DUCHAMP_UFS_FDT_INVALID;
}
