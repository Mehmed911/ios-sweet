#!/bin/sh
set -eu

if [ "$#" -ne 2 ]; then
	echo "usage: $0 embedded-build-dir payload.bin" >&2
	exit 2
fi

build=$(readlink -f "$1")
payload=$(readlink -f "$2")
start_hex=$(llvm-nm -n "$build/duchamp-diagnostic.elf" |
	awk '$3 == "duchamp_embedded_payload_start" { print $1 }')
end_hex=$(llvm-nm -n "$build/duchamp-diagnostic.elf" |
	awk '$3 == "duchamp_embedded_payload_end" { print $1 }')

if [ -z "$start_hex" ] || [ -z "$end_hex" ]; then
	echo "embedded payload symbols are missing" >&2
	exit 1
fi

start=$((0x$start_hex))
end=$((0x$end_hex))
size=$(stat -c %s "$payload")
if [ "$((end - start))" -ne "$size" ]; then
	echo "embedded payload size mismatch" >&2
	exit 1
fi

temporary=$(mktemp)
trap 'rm -f "$temporary"' EXIT
dd if="$build/Image" of="$temporary" bs=1M skip="$start" count="$size" \
	iflag=skip_bytes,count_bytes status=none
cmp "$temporary" "$payload"
echo "embedded-payload-byte-compare: PASS"
