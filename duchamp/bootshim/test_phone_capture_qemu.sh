#!/bin/sh
set -eu

if [ "$#" -ne 2 ]; then
	echo "usage: $0 HANDOFF_CONTRACT NEW_OUTPUT_DIRECTORY" >&2
	exit 2
fi

contract=$(readlink -f "$1")
out=$2
if [ ! -f "$contract" ]; then
	echo "missing handoff contract: $1" >&2
	exit 2
fi
if [ -e "$out" ]; then
	echo "preserve existing output: $out" >&2
	exit 2
fi
mkdir -p "$out"
out=$(readlink -f "$out")

cd "$(dirname "$0")"
if PHONE_CAPTURE=1 SHIM_OUT="$out/negative-no-contract" \
	sh build.sh >/dev/null 2>&1; then
	echo "PHONE_CAPTURE unexpectedly built without its pinned contract" >&2
	exit 1
fi
if PHONE_CAPTURE=1 PHONE_CONTRACT="$contract" QEMU_ONLY=1 \
	SHIM_OUT="$out/negative-qemu-mix" sh build.sh >/dev/null 2>&1; then
	echo "PHONE_CAPTURE unexpectedly accepted QEMU_ONLY" >&2
	exit 1
fi
if PHONE_CAPTURE=1 PHONE_CONTRACT="$contract" PAYLOAD="$contract" \
	SHIM_OUT="$out/negative-payload-mix" sh build.sh >/dev/null 2>&1; then
	echo "PHONE_CAPTURE unexpectedly accepted a payload" >&2
	exit 1
fi
PHONE_CAPTURE=1 PHONE_CONTRACT="$contract" SHIM_OUT="$out" sh build.sh

capture_offset=$(llvm-nm "$out/duchamp-diagnostic.elf" |
	awk '$3 == "duchamp_bootshim_phone_capture_record" { print $1 }')
if [ -z "$capture_offset" ]; then
	echo "capture record symbol missing" >&2
	exit 1
fi
capture_pa=$((0x40200000 + 0x$capture_offset))

set -- --image "$out/Image" --pattern pc-x0 --wait 3 \
	--capture-record-pa "$capture_pa" \
	--expect-capture-pc 0x40200000 --expect-capture-x0 0x48000000
if [ "${UFS_HANDOFF_PROBE:-}" = 1 ]; then
	probe_offset=$(llvm-nm "$out/duchamp-diagnostic.elf" |
		awk '$3 == "duchamp_bootshim_ufs_handoff_record" { print $1 }')
	if [ -z "$probe_offset" ]; then
		echo "UFS handoff record symbol missing" >&2
		exit 1
	fi
	set -- "$@" --ufs-handoff-record-pa "$((0x40200000 + 0x$probe_offset))"
fi
python3 test_qemu.py "$@"

set -- --contract "$contract" --elf "$out/duchamp-diagnostic.elf" \
	--image "$out/Image" --json-out "$out/verification.json"
if [ "${UFS_HANDOFF_PROBE:-}" = 1 ]; then
	set -- "$@" --ufs-handoff-probe
fi
python3 ../../tools/verify-duchamp-phone-capture.py "$@"

echo "phone-capture-qemu-suite: PASS output=$out record-pa=$(printf '0x%x' "$capture_pa")"
