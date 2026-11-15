#include "ufs_handoff_evidence.h"

#include <assert.h>
#include <stdio.h>
#include <stdlib.h>

static void
check(const unsigned char *fdt, size_t bytes, unsigned slot, unsigned declarations, int valid)
{
	struct duchamp_ufs_handoff_record r;
	duchamp_ufs_handoff_collect(&r, fdt, bytes);
	assert(r.magic == DUCHAMP_UFS_HANDOFF_MAGIC && r.version == 2 && r.size == sizeof(r));
	assert(r.slot_hint == slot && r.declarations == declarations);
	assert(r.blockers == (valid ? 0x7ef : 0x7ff));
	assert(r.fdt_bytes == (valid ? bytes : 0));
	assert(valid || r.fdt_fingerprint == 0);
}

int
main(int argc, char **argv)
{
	assert(argc == 4);
	unsigned char *fdt = malloc(DUCHAMP_UFS_HANDOFF_FDT_MAX);
	assert(fdt);
	FILE *file = fopen(argv[1], "rb");
	assert(file);
	size_t bytes = fread(fdt, 1, DUCHAMP_UFS_HANDOFF_FDT_MAX, file);
	assert(!ferror(file) && feof(file) && bytes > 40);
	fclose(file);

	check(fdt, bytes, strtoul(argv[2], NULL, 0), strtoul(argv[3], NULL, 0), 1);
	check(NULL, 0, 0, 0, 0);
	check(fdt, 39, 0, 0, 0);
	check(fdt, bytes - 1, 0, 0, 0);
	unsigned char saved = fdt[0];
	fdt[0] = 0;
	check(fdt, bytes, 0, 0, 0);
	fdt[0] = saved;
	/* A strings block that starts inside the structure is invalid. */
	for (unsigned i = 0; i < 4; i++) fdt[12 + i] = fdt[8 + i];
	check(fdt, bytes, 0, 0, 0);
	free(fdt);
	puts("UFS HANDOFF METADATA PASS");
}
