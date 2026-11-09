#include "ufs_gpt.h"

enum { GPT_HEADER_BYTES = 92, GPT_ENTRY_BYTES = 128, HFS_HEADER_OFFSET = 1024 };

struct gpt_header {
    uint64_t first, last, entries;
    uint32_t count;
    uint8_t disk_guid[DUFS_GPT_GUID_BYTES];
};

/* 48465300-0000-11AA-AA11-00306543ECAC, in GPT wire order. */
static const uint8_t hfs_type[DUFS_GPT_GUID_BYTES] = {
    0x00, 0x53, 0x46, 0x48, 0x00, 0x00, 0xaa, 0x11,
    0xaa, 0x11, 0x00, 0x30, 0x65, 0x43, 0xec, 0xac
};

static const uint8_t zero_guid[DUFS_GPT_GUID_BYTES];

static uint64_t
little_endian(const uint8_t *data, unsigned bytes)
{
    uint64_t value = 0;
    while (bytes) {
        value = (value << 8) | data[--bytes];
    }
    return value;
}

static int
equal(const uint8_t *a, const uint8_t *b, size_t bytes)
{
    while (bytes--) {
        if (*a++ != *b++) {
            return 0;
        }
    }
    return 1;
}

static uint32_t
gpt_crc(const uint8_t *data, size_t bytes)
{
    uint32_t crc = UINT32_MAX;
    while (bytes--) {
        crc ^= *data++;
        for (unsigned bit = 0; bit < 8; bit++) {
            crc = (crc >> 1) ^ ((crc & 1) ? UINT32_C(0xedb88320) : 0);
        }
    }
    return ~crc;
}

/* GPT sector size can differ from the controller's logical block size. */
static int
read_bytes(struct dufs_host *host, uint64_t offset, uint8_t *out, size_t bytes,
    uint8_t *block)
{
    while (bytes) {
        size_t within = offset % host->block_bytes;
        size_t take = host->block_bytes - within;
        int result = dufs_read(host, offset / host->block_bytes, 1, block,
            host->block_bytes);
        if (result) {
            return result;
        }
        if (take > bytes) {
            take = bytes;
        }
        for (size_t i = 0; i < take; i++) {
            out[i] = block[within + i];
        }
        bytes -= take;
        out += take;
        offset += take;
    }
    return DUFS_OK;
}

static int
read_gpt(struct dufs_host *host, uint32_t sector, uint64_t last_lba, int backup,
    struct gpt_header *header, uint8_t *entries, uint8_t *block)
{
    const uint64_t own_lba = backup ? last_lba : 1;
    const uint64_t alternate_lba = backup ? 1 : last_lba;
    /* A full sector fits in either table buffer before reading the entries. */
    int result = read_bytes(host, own_lba * sector, entries, sector, block);
    if (result) {
        return result;
    }

    if (!equal(entries, (const uint8_t *)"EFI PART", 8) ||
        little_endian(entries + 8, 4) != 0x10000 ||
        little_endian(entries + 12, 4) != GPT_HEADER_BYTES ||
        little_endian(entries + 20, 4) != 0 ||
        little_endian(entries + 24, 8) != own_lba ||
        little_endian(entries + 32, 8) != alternate_lba ||
        little_endian(entries + 84, 4) != GPT_ENTRY_BYTES) {
        return DUFS_GPT_INVALID;
    }
    uint32_t header_crc = (uint32_t)little_endian(entries + 16, 4);
    for (unsigned i = 16; i < 20; i++) {
        entries[i] = 0;
    }
    if (gpt_crc(entries, GPT_HEADER_BYTES) != header_crc) {
        return DUFS_GPT_INVALID;
    }

    header->first = little_endian(entries + 40, 8);
    header->last = little_endian(entries + 48, 8);
    header->entries = little_endian(entries + 72, 8);
    header->count = (uint32_t)little_endian(entries + 80, 4);
    for (size_t i = 0; i < sizeof(header->disk_guid); i++) {
        header->disk_guid[i] = entries[56 + i];
    }
    const uint32_t table_crc = (uint32_t)little_endian(entries + 88, 4);
    if (!header->count || header->count > DUFS_GPT_TABLE_BYTES / GPT_ENTRY_BYTES ||
        header->first < 2 || header->first > header->last ||
        header->last >= last_lba || equal(header->disk_guid, zero_guid,
        sizeof(zero_guid))) {
        return DUFS_GPT_INVALID;
    }
    const size_t bytes = header->count * GPT_ENTRY_BYTES;
    const size_t sectors = (bytes + sector - 1) / sector;
    const uint64_t lower = backup ? header->last + 1 : 2;
    const uint64_t upper = backup ? last_lba : header->first;
    if (header->entries < lower || header->entries >= upper ||
        sectors > upper - header->entries) {
        return DUFS_GPT_INVALID;
    }

    result = read_bytes(host, header->entries * sector, entries, bytes, block);
    if (result) {
        return result;
    }
    return gpt_crc(entries, bytes) == table_crc ? DUFS_OK : DUFS_GPT_INVALID;
}

int
dufs_gpt_find_hfs(struct dufs_host *host, uint32_t sector,
    const uint8_t guid[DUFS_GPT_GUID_BYTES], struct dufs_gpt_scratch *scratch,
    struct dufs_partition *partition)
{
    if (!host || !guid || !scratch || !partition || equal(guid, zero_guid,
        sizeof(zero_guid)) || (sector != 512 && sector != 4096)) {
        return DUFS_ARGUMENT;
    }
    if (!host->blocks) {
        return DUFS_STATE;
    }
    const uint32_t block_bytes = host->block_bytes;
    if ((block_bytes != 512 && block_bytes != 4096) ||
        host->blocks > UINT64_MAX / block_bytes) {
        return DUFS_GPT_INVALID;
    }
    const uint64_t bytes = host->blocks * block_bytes;
    if (bytes % sector || bytes / sector < 6) {
        return DUFS_GPT_INVALID;
    }

    struct gpt_header primary, backup;
    const uint64_t last_lba = bytes / sector - 1;
    int result = read_bytes(host, 0, scratch->primary, 512, scratch->block);
    if (result) {
        return result;
    }
    const uint8_t *mbr = scratch->primary;
    const uint64_t protective_size = last_lba < UINT32_MAX ? last_lba : UINT32_MAX;
    if (mbr[446] || mbr[450] != 0xee || little_endian(mbr + 454, 4) != 1 ||
        little_endian(mbr + 458, 4) != protective_size ||
        mbr[510] != 0x55 || mbr[511] != 0xaa) {
        return DUFS_GPT_INVALID;
    }
    for (size_t i = 462; i < 510; i++) {
        if (mbr[i]) {
            return DUFS_GPT_INVALID;
        }
    }

    result = read_gpt(host, sector, last_lba, 0, &primary, scratch->primary,
        scratch->block);
    if (result) {
        return result;
    }
    result = read_gpt(host, sector, last_lba, 1, &backup, scratch->backup,
        scratch->block);
    if (result) {
        return result;
    }
    if (primary.first != backup.first || primary.last != backup.last ||
        primary.count != backup.count ||
        !equal(primary.disk_guid, backup.disk_guid, sizeof(primary.disk_guid)) ||
        !equal(scratch->primary, scratch->backup, primary.count * GPT_ENTRY_BYTES)) {
        return DUFS_GPT_INVALID;
    }

    const uint8_t *target = NULL;
    uint64_t first = 0, last = 0;
    for (uint32_t i = 0; i < primary.count; i++) {
        const uint8_t *entry = scratch->primary + i * GPT_ENTRY_BYTES;
        if (equal(entry, zero_guid, sizeof(zero_guid))) {
            continue;
        }
        const uint64_t entry_first = little_endian(entry + 32, 8);
        const uint64_t entry_last = little_endian(entry + 40, 8);
        if (entry_first < primary.first || entry_last > primary.last ||
            entry_first > entry_last || equal(entry + 16, zero_guid,
            sizeof(zero_guid))) {
            return DUFS_GPT_INVALID;
        }
        if (equal(entry + 16, guid, DUFS_GPT_GUID_BYTES)) {
            if (target || !equal(entry, hfs_type, sizeof(hfs_type))) {
                return DUFS_GPT_INVALID;
            }
            target = entry;
            first = entry_first;
            last = entry_last;
        }
    }
    if (!target) {
        return DUFS_GPT_NOT_FOUND;
    }
    for (uint32_t i = 0; i < primary.count; i++) {
        const uint8_t *entry = scratch->primary + i * GPT_ENTRY_BYTES;
        if (entry != target && !equal(entry, zero_guid, sizeof(zero_guid)) &&
            little_endian(entry + 32, 8) <= last &&
            little_endian(entry + 40, 8) >= first) {
            return DUFS_GPT_INVALID;
        }
    }

    const uint64_t start = first * sector, length = (last - first + 1) * sector;
    if (start % block_bytes || length % block_bytes || length < HFS_HEADER_OFFSET + 512) {
        return DUFS_GPT_INVALID;
    }
    uint8_t signature[4];
    result = read_bytes(host, start + HFS_HEADER_OFFSET, signature, sizeof(signature),
        scratch->block);
    if (result) {
        return result;
    }
    if (!equal(signature, (const uint8_t *)"H+\0\4", sizeof(signature)) &&
        !equal(signature, (const uint8_t *)"HX\0\5", sizeof(signature))) {
        return DUFS_GPT_INVALID;
    }
    *partition = (struct dufs_partition){start / block_bytes, length / block_bytes};
    return DUFS_OK;
}

int
dufs_partition_read(struct dufs_host *host, const struct dufs_partition *part,
    uint64_t relative, uint32_t blocks, void *out, size_t bytes)
{
    if (!host || !part || !blocks || part->first_block >= host->blocks ||
        part->blocks > host->blocks - part->first_block ||
        relative >= part->blocks || blocks > part->blocks - relative) {
        return DUFS_ARGUMENT;
    }
    return dufs_read(host, part->first_block + relative, blocks, out, bytes);
}
