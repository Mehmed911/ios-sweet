#!/bin/sh
set -eu

if [ "$#" -ne 2 ]; then
	echo "usage: $0 phone-fdt.bin payload.bin" >&2
	exit 2
fi
fdt=$(readlink -f "$1")
payload=$(readlink -f "$2")
cd "$(dirname "$0")"
mkdir -p out-test
${HOST_CC:-cc} -std=c11 -O2 -Wall -Wextra -Werror \
	test_materialize.c materialize.c plan.c guard.c \
	-o out-test/test_materialize
out-test/test_materialize "$fdt" "$payload"

${HOST_CC:-cc} -std=c11 -O2 -Wall -Wextra -Werror \
	test_return_slot.c return_slot.c -o out-test/test_return_slot
out-test/test_return_slot
