#!/bin/sh
set -eu

if [ "$#" -eq 2 ]; then
	fdt_path=$(readlink -f "$1")
	payload_path=$(readlink -f "$2")
elif [ "$#" -ne 0 ]; then
	echo "usage: $0 [phone-fdt.bin payload.bin]" >&2
	exit 2
fi

cd "$(dirname "$0")"

out=${SHIM_TEST_OUT:-out-test}
cc=${HOST_CC:-cc}
mkdir -p "$out"

"$cc" -std=c11 -D_GNU_SOURCE -DDUCHAMP_TEST_NO_WATCHDOG=1 \
	-O2 -Wall -Wextra -Werror \
	test_bootshim.c shim.c ../loader/mt6897_entry.c \
	-o "$out/test_bootshim"
"$out/test_bootshim"

"$cc" -std=c11 -O2 -Wall -Wextra -Werror \
	-DDUCHAMP_TEST_NO_ARCH_BARRIER=1 \
	test_handoff_ready.c handoff_ready.c -o "$out/test_handoff_ready"
"$out/test_handoff_ready"

"$cc" -std=c11 -O2 -Wall -Wextra -Werror \
	test_xnu_return.c xnu_return.c -o "$out/test_xnu_return"
"$out/test_xnu_return"

"$cc" -std=c11 -O2 -Wall -Wextra -Werror \
	-DDUCHAMP_TEST_NO_ARCH_BARRIER=1 \
	test_phone_capture.c phone_capture.c -o "$out/test_phone_capture"
"$out/test_phone_capture"

"$cc" -std=c11 -O2 -Wall -Wextra -Werror \
	test_payload_preflight.c payload_preflight.c ../loader/guard.c \
	-o "$out/test_payload_preflight"

if [ "$#" -eq 2 ]; then
	"$out/test_payload_preflight" "$fdt_path" "$payload_path"
fi
