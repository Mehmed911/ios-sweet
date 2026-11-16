#include "ufs_handoff_evidence.h"

#include <assert.h>
#include <stdio.h>
#include <stdlib.h>

static void
check(const unsigned char *fdt, size_t bytes, unsigned slot, unsigned declarations,
	const char *digest)
{
	struct duchamp_ufs_handoff_record r;
	const uint64_t pc = 0x40000000, x0 = 0x47c80000;
	const int valid = digest != NULL;
	duchamp_ufs_handoff_collect(&r, fdt, bytes, pc, x0);
	assert(r.magic == DUCHAMP_UFS_HANDOFF_MAGIC && r.version == 3 && r.size == sizeof(r));
	assert(r.slot_hint == slot && r.declarations == declarations);
	assert(r.entry_pc == pc && r.entry_x0 == x0);
	assert(r.blockers == (valid ? 0xffef : 0xffff));
	assert(r.fdt_bytes == (valid ? bytes : 0));
	assert(valid || r.fdt_fingerprint == 0);
	static const char hex[] = "0123456789abcdef";
	for (unsigned i = 0; i < sizeof(r.fdt_sha256); i++) {
		unsigned byte = r.fdt_sha256[i];
		if (valid) {
			assert(hex[byte >> 4] == digest[2 * i]);
			assert(hex[byte & 15] == digest[2 * i + 1]);
		} else {
			assert(!byte);
		}
	}
}

int
main(int argc, char **argv)
{
	assert(argc == 5);
	unsigned char *fdt = malloc(DUCHAMP_UFS_HANDOFF_FDT_MAX);
	assert(fdt);
	FILE *file = fopen(argv[1], "rb");
	assert(file);
	size_t bytes = fread(fdt, 1, DUCHAMP_UFS_HANDOFF_FDT_MAX, file);
	assert(!ferror(file) && feof(file) && bytes > 40);
	fclose(file);

	check(fdt, bytes, strtoul(argv[2], NULL, 0), strtoul(argv[3], NULL, 0), argv[4]);
	check(NULL, 0, 0, 0, NULL);
	check(fdt, 39, 0, 0, NULL);
	check(fdt, bytes - 1, 0, 0, NULL);
	unsigned char saved = fdt[0];
	fdt[0] = 0;
	check(fdt, bytes, 0, 0, NULL);
	fdt[0] = saved;
	/* A strings block that starts inside the structure is invalid. */
	for (unsigned i = 0; i < 4; i++) fdt[12 + i] = fdt[8 + i];
	check(fdt, bytes, 0, 0, NULL);
	free(fdt);
	puts("UFS HANDOFF METADATA PASS");
}
