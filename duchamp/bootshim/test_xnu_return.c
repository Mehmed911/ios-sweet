#include <stdio.h>
#include <string.h>

#include "xnu_return.h"

int
main(void)
{
	unsigned char source[100], saved[32];
	struct duchamp_xnu_return_record record;
	unsigned i;

	for (i = 0; i < sizeof(source); i++) source[i] = (unsigned char)i;
	if (duchamp_xnu_return_capture(UINT64_C(0x1c0100000), sizeof(source),
	    source, 1, UINT64_C(0x96000010), UINT64_C(0x1c1481000),
	    UINT64_C(0x1c0001000), saved, sizeof(saved), &record) != 0) return 1;
	if (record.copied != sizeof(saved) || record.head_bytes != 8 ||
	    record.tail_bytes != 24 || memcmp(saved, source, 8) != 0 ||
	    memcmp(saved + 8, source + 76, 24) != 0 || record.checksum == 0) return 2;
	if (duchamp_xnu_return_capture(UINT64_C(0x1c0100000), 1, NULL,
	    1, 0, 0, 0, saved, sizeof(saved), &record) !=
	    DUCHAMP_XNU_RETURN_ARGUMENT || record.result !=
	    DUCHAMP_XNU_RETURN_ARGUMENT) return 3;
	if (duchamp_xnu_return_capture(0, 0, NULL, 2, 27, 0, 0,
	    saved, sizeof(saved), &record) != 0 || record.copied != 0) return 4;
	puts("xnu-return-tests: PASS");
	return 0;
}
