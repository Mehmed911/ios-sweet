#include "guard.h"

#define DUCHAMP_ALIGN UINT64_C(0x2000000)
#define XNU_PAGE UINT64_C(0x4000)
#define FDT_MAGIC UINT32_C(0xd00dfeed)
#define FDT_BEGIN_NODE 1u
#define FDT_END_NODE 2u
#define FDT_PROP 3u
#define FDT_NOP 4u
#define FDT_END 9u

static uint32_t
be32(const unsigned char *pointer)
{
	return (uint32_t)pointer[0] << 24 | (uint32_t)pointer[1] << 16 |
	       (uint32_t)pointer[2] << 8 | pointer[3];
}

static uint64_t
be64(const unsigned char *pointer)
{
	return (uint64_t)be32(pointer) << 32 | be32(pointer + 4);
}

static uint32_t
le32(const unsigned char *pointer)
{
	return (uint32_t)pointer[0] | (uint32_t)pointer[1] << 8 |
	       (uint32_t)pointer[2] << 16 | (uint32_t)pointer[3] << 24;
}

static uint64_t
le64(const unsigned char *pointer)
{
	return (uint64_t)le32(pointer) | (uint64_t)le32(pointer + 4) << 32;
}

static int
add_ok(uint64_t start, uint64_t size, uint64_t *end)
{
	*end = start + size;
	return *end >= start;
}

static int
range_inside(uint64_t start, uint64_t size, uint64_t outer_start, uint64_t outer_size)
{
	uint64_t end, outer_end;
	return add_ok(start, size, &end) && add_ok(outer_start, outer_size, &outer_end) &&
	       start >= outer_start && end <= outer_end;
}

static int
range_overlaps(uint64_t first_start, uint64_t first_size, uint64_t second_start, uint64_t second_size)
{
	uint64_t first_end, second_end;
	return first_size != 0 && second_size != 0 &&
	       add_ok(first_start, first_size, &first_end) &&
	       add_ok(second_start, second_size, &second_end) &&
	       first_start < second_end && second_start < first_end;
}

static int
bytes_equal(const unsigned char *value, size_t size, const char *text)
{
	size_t index = 0;
	while (text[index] != '\0') {
		if (index >= size || value[index] != (unsigned char)text[index]) {
			return 0;
		}
		index++;
	}
	return index < size && value[index] == 0;
}

static int
string_list_contains(const unsigned char *value, size_t size, const char *text)
{
	size_t offset = 0;
	while (offset < size) {
		size_t length = 0;
		while (offset + length < size && value[offset + length] != 0) {
			length++;
		}
		if (offset + length >= size) {
			return 0;
		}
		if (bytes_equal(value + offset, length + 1, text)) {
			return 1;
		}
		offset += length + 1;
	}
	return 0;
}

unsigned
duchamp_payload_plan_check(const void *payload_pointer, size_t payload_size,
    struct duchamp_payload_plan *plan)
{
	const unsigned char *payload = payload_pointer;
	uint64_t virt_base, entry, adt_offset, adt_size, kernel_end, phys_base, memory_size;
	uint64_t greatest_end, adt, after_adt, boot_args, top;
	unsigned segment_count, index, previous;
	int entry_mapped = 0;
	static const unsigned char magic[8] = {'S', 'W', 'E', 'E', 'T', 'X', 'N', 'U'};

	if (payload == NULL || plan == NULL || payload_size < 0x2a8) {
		return DUCHAMP_GUARD_ARGUMENT;
	}
	plan->entry = plan->adt = plan->boot_args = plan->top = 0;
	for (index = 0; index < sizeof(magic); index++) {
		if (payload[index] != magic[index]) {
			return DUCHAMP_GUARD_PAYLOAD_HEADER;
		}
	}
	segment_count = le32(payload + 12);
	if (le32(payload + 8) != 1 || segment_count == 0 || segment_count > 32 ||
	    payload_size < 0x2a8 + (uint64_t)segment_count * 32) {
		return DUCHAMP_GUARD_PAYLOAD_HEADER;
	}
	virt_base = le64(payload + 0x10);
	entry = le64(payload + 0x18);
	adt_offset = le64(payload + 0x20);
	adt_size = le64(payload + 0x28);
	kernel_end = le64(payload + 0x30);
	phys_base = le64(payload + 0x38);
	memory_size = le64(payload + 0x40);
	if (memory_size == 0 || ((phys_base | memory_size | virt_base) & (DUCHAMP_ALIGN - 1)) != 0 ||
	    !range_inside(kernel_end, 0, virt_base, memory_size) || (kernel_end & (XNU_PAGE - 1)) != 0 ||
	    adt_size == 0 || adt_size > 2 * 1024 * 1024 ||
	    adt_offset < 0x2a8 + (uint64_t)segment_count * 32 ||
	    !range_inside(adt_offset, adt_size, 0, payload_size)) {
		return DUCHAMP_GUARD_PAYLOAD_LAYOUT;
	}
	greatest_end = virt_base;
	for (index = 0; index < segment_count; index++) {
		const unsigned char *segment = payload + 0x2a8 + index * 32;
		uint64_t virtual = le64(segment), virtual_size = le64(segment + 8);
		uint64_t file_offset = le64(segment + 16), file_size = le64(segment + 24);
		uint64_t virtual_end;
		if (virtual_size == 0 || (virtual & (XNU_PAGE - 1)) != 0 || file_size > virtual_size ||
		    !range_inside(virtual, virtual_size, virt_base, memory_size) ||
		    !add_ok(virtual, virtual_size, &virtual_end) || virtual_end > kernel_end ||
		    file_offset < 0x2a8 + (uint64_t)segment_count * 32 ||
		    !range_inside(file_offset, file_size, 0, payload_size) ||
		    range_overlaps(file_offset, file_size, adt_offset, adt_size)) {
			return DUCHAMP_GUARD_PAYLOAD_LAYOUT;
		}
		if (range_inside(entry, 4, virtual, file_size)) {
			entry_mapped = 1;
		}
		if (virtual_end > greatest_end) {
			greatest_end = virtual_end;
		}
		for (previous = 0; previous < index; previous++) {
			const unsigned char *other = payload + 0x2a8 + previous * 32;
			if (range_overlaps(virtual, virtual_size, le64(other), le64(other + 8)) ||
			    range_overlaps(file_offset, file_size, le64(other + 16), le64(other + 24))) {
				return DUCHAMP_GUARD_PAYLOAD_LAYOUT;
			}
		}
	}
	if (!entry_mapped || (entry & 3) != 0 || greatest_end != kernel_end) {
		return DUCHAMP_GUARD_PAYLOAD_LAYOUT;
	}
	adt = phys_base + kernel_end - virt_base;
	if (!add_ok(adt, adt_size, &after_adt) || after_adt > UINT64_MAX - (XNU_PAGE - 1)) {
		return DUCHAMP_GUARD_PAYLOAD_LAYOUT;
	}
	boot_args = (after_adt + XNU_PAGE - 1) & ~(XNU_PAGE - 1);
	if (!add_ok(boot_args, XNU_PAGE, &top) || !range_inside(adt, adt_size, phys_base, memory_size) ||
	    !range_inside(boot_args, XNU_PAGE, phys_base, memory_size)) {
		return DUCHAMP_GUARD_PAYLOAD_LAYOUT;
	}
	plan->entry = phys_base + entry - virt_base;
	plan->adt = adt;
	plan->boot_args = boot_args;
	plan->top = top;
	return DUCHAMP_GUARD_OK;
}

unsigned
duchamp_fdt_window_check(const void *fdt_pointer, size_t fdt_size,
    uint64_t window_start, uint64_t window_size,
    const struct duchamp_range *occupied, unsigned occupied_count)
{
	const unsigned char *fdt = fdt_pointer;
	uint32_t total, structure_offset, strings_offset, reserve_offset, strings_size, structure_size;
	uint32_t position, structure_end, token, depth = 0;
	int root_board = 0, root_model = 0, root_cells = 0, reserved_cells = 0, reserved_ranges_identity = 1;
	int window_in_memory = 0, in_memory = 0, in_reserved = 0, in_reserved_child = 0;
	int child_reg = 0, child_size = 0, child_alloc_ranges = 0, child_alloc_overlap = 0;
	unsigned index;

	if (fdt == NULL || window_size == 0 || (window_start | window_size) & (DUCHAMP_ALIGN - 1) ||
	    occupied_count > 32 || (occupied_count != 0 && occupied == NULL)) {
		return DUCHAMP_GUARD_ARGUMENT;
	}
	if (fdt_size < 40 || be32(fdt) != FDT_MAGIC || be32(fdt + 20) != 17) {
		return DUCHAMP_GUARD_FDT_HEADER;
	}
	total = be32(fdt + 4);
	structure_offset = be32(fdt + 8);
	strings_offset = be32(fdt + 12);
	reserve_offset = be32(fdt + 16);
	strings_size = be32(fdt + 32);
	structure_size = be32(fdt + 36);
	if (total < 40 || total > fdt_size || total > 2 * 1024 * 1024 || structure_offset < 40 ||
	    (structure_offset & 3) != 0 || structure_offset + structure_size > total ||
	    strings_offset < 40 || strings_offset + strings_size > total || reserve_offset < 40 ||
	    (reserve_offset & 7) != 0) {
		return DUCHAMP_GUARD_FDT_HEADER;
	}
	for (position = reserve_offset; position + 16 <= total; position += 16) {
		uint64_t start = be64(fdt + position), size = be64(fdt + position + 8), end;
		if (start == 0 && size == 0) {
			break;
		}
		if (size == 0 || !add_ok(start, size, &end) || range_overlaps(window_start, window_size, start, size)) {
			return DUCHAMP_GUARD_FDT_RESERVED;
		}
	}
	if (position + 16 > total) {
		return DUCHAMP_GUARD_FDT_HEADER;
	}
	for (index = 0; index < occupied_count; index++) {
		uint64_t end;
		if (occupied[index].size == 0 || !add_ok(occupied[index].start, occupied[index].size, &end) ||
		    range_overlaps(window_start, window_size, occupied[index].start, occupied[index].size)) {
			return DUCHAMP_GUARD_OCCUPIED;
		}
	}
	position = structure_offset;
	structure_end = structure_offset + structure_size;
	while (position + 4 <= structure_end) {
		token = be32(fdt + position);
		position += 4;
		if (token == FDT_BEGIN_NODE) {
			uint32_t start = position;
			while (position < structure_end && fdt[position] != 0) {
				position++;
			}
			if (position >= structure_end || depth >= 64) {
				return DUCHAMP_GUARD_FDT_STRUCTURE;
			}
			depth++;
			if (depth == 2) {
				in_memory = position - start >= 6 && fdt[start] == 'm' && fdt[start + 1] == 'e' &&
				    fdt[start + 2] == 'm' && fdt[start + 3] == 'o' && fdt[start + 4] == 'r' && fdt[start + 5] == 'y';
				in_reserved = bytes_equal(fdt + start, position - start + 1, "reserved-memory");
			}
			if (depth == 3 && in_reserved) {
				in_reserved_child = 1;
				child_reg = child_size = child_alloc_ranges = child_alloc_overlap = 0;
			}
			position = (position + 4) & ~3u;
		} else if (token == FDT_END_NODE) {
			if (depth == 0) {
				return DUCHAMP_GUARD_FDT_STRUCTURE;
			}
			if (depth == 3 && in_reserved_child) {
				if ((!child_reg && !child_size) || (child_size && (!child_alloc_ranges || child_alloc_overlap))) {
					return DUCHAMP_GUARD_FDT_RESERVED;
				}
				in_reserved_child = 0;
			}
			if (depth == 2) {
				in_memory = in_reserved = 0;
			}
			depth--;
		} else if (token == FDT_PROP) {
			uint32_t size, name_offset, name_end, value_offset;
			const unsigned char *name, *value;
			if (depth == 0 || position + 8 > structure_end) {
				return DUCHAMP_GUARD_FDT_STRUCTURE;
			}
			size = be32(fdt + position);
			name_offset = be32(fdt + position + 4);
			position += 8;
			value_offset = position;
			if (position + size > structure_end || name_offset >= strings_size) {
				return DUCHAMP_GUARD_FDT_STRUCTURE;
			}
			name_end = strings_offset + name_offset;
			while (name_end < strings_offset + strings_size && fdt[name_end] != 0) {
				name_end++;
			}
			if (name_end >= strings_offset + strings_size) {
				return DUCHAMP_GUARD_FDT_STRUCTURE;
			}
			name = fdt + strings_offset + name_offset;
			value = fdt + value_offset;
			if (depth == 1 && bytes_equal(name, name_end - (strings_offset + name_offset) + 1, "compatible")) {
				root_board = string_list_contains(value, size, "mediatek,MT6897");
			} else if (depth == 1 && bytes_equal(name, name_end - (strings_offset + name_offset) + 1, "model")) {
				root_model = bytes_equal(value, size, "MT6897");
			} else if (depth == 1 && size == 4 &&
			    (bytes_equal(name, name_end - (strings_offset + name_offset) + 1, "#address-cells") ||
			    bytes_equal(name, name_end - (strings_offset + name_offset) + 1, "#size-cells"))) {
				root_cells += be32(value) == 2;
			} else if (depth == 2 && in_memory &&
			    bytes_equal(name, name_end - (strings_offset + name_offset) + 1, "reg")) {
				uint32_t offset;
				if (size == 0 || size % 16 != 0) return DUCHAMP_GUARD_FDT_MEMORY;
				for (offset = 0; offset < size; offset += 16)
					window_in_memory |= range_inside(window_start, window_size, be64(value + offset), be64(value + offset + 8));
			} else if (depth == 2 && in_reserved && size == 4 &&
			    (bytes_equal(name, name_end - (strings_offset + name_offset) + 1, "#address-cells") ||
			    bytes_equal(name, name_end - (strings_offset + name_offset) + 1, "#size-cells"))) {
				reserved_cells += be32(value) == 2;
			} else if (depth == 2 && in_reserved &&
			    bytes_equal(name, name_end - (strings_offset + name_offset) + 1, "ranges")) {
				reserved_ranges_identity = size == 0;
			} else if (depth == 3 && in_reserved_child &&
			    bytes_equal(name, name_end - (strings_offset + name_offset) + 1, "reg")) {
				uint32_t offset;
				if (size == 0 || size % 16 != 0) return DUCHAMP_GUARD_FDT_RESERVED;
				child_reg = 1;
				for (offset = 0; offset < size; offset += 16)
					if (range_overlaps(window_start, window_size, be64(value + offset), be64(value + offset + 8)))
						return DUCHAMP_GUARD_FDT_RESERVED;
			} else if (depth == 3 && in_reserved_child &&
			    bytes_equal(name, name_end - (strings_offset + name_offset) + 1, "size")) {
				if (size != 8 || be64(value) == 0) return DUCHAMP_GUARD_FDT_RESERVED;
				child_size = 1;
			} else if (depth == 3 && in_reserved_child &&
			    bytes_equal(name, name_end - (strings_offset + name_offset) + 1, "alloc-ranges")) {
				uint32_t offset;
				if (size == 0 || size % 16 != 0) return DUCHAMP_GUARD_FDT_RESERVED;
				child_alloc_ranges = 1;
				for (offset = 0; offset < size; offset += 16)
					child_alloc_overlap |= range_overlaps(window_start, window_size, be64(value + offset), be64(value + offset + 8));
			}
			position = (position + size + 3) & ~3u;
		} else if (token == FDT_NOP) {
			continue;
		} else if (token == FDT_END) {
			if (depth != 0) return DUCHAMP_GUARD_FDT_STRUCTURE;
			break;
		} else {
			return DUCHAMP_GUARD_FDT_STRUCTURE;
		}
	}
	if (token != FDT_END || (!root_board && !root_model)) return DUCHAMP_GUARD_FDT_BOARD;
	if (root_cells != 2 || reserved_cells != 2 || !reserved_ranges_identity) return DUCHAMP_GUARD_FDT_STRUCTURE;
	if (!window_in_memory) return DUCHAMP_GUARD_FDT_MEMORY;
	return DUCHAMP_GUARD_OK;
}

unsigned
duchamp_loader_plan_check(const void *fdt, size_t fdt_size,
    const void *payload, size_t payload_size,
    const struct duchamp_range *occupied, unsigned occupied_count,
    struct duchamp_payload_plan *plan)
{
	const unsigned char *bytes = payload;
	unsigned result = duchamp_payload_plan_check(payload, payload_size, plan);
	if (result != DUCHAMP_GUARD_OK) return result;
	result = duchamp_fdt_window_check(fdt, fdt_size, le64(bytes + 0x38), le64(bytes + 0x40), occupied, occupied_count);
	if (result != DUCHAMP_GUARD_OK) {
		plan->entry = plan->adt = plan->boot_args = plan->top = 0;
	}
	return result;
}
