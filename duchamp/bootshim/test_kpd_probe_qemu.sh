#!/bin/sh
set -eu

if [ "$#" -ne 2 ] || [ ! -f "$1" ] || [ -e "$2" ]; then
	echo "usage: $0 HANDOFF_CONTRACT NEW_OUTPUT_DIRECTORY" >&2
	exit 2
fi
contract=$(readlink -f "$1")
mkdir -p "$2"
out=$(readlink -f "$2")
cd "$(dirname "$0")"

if KPD_PROBE=1 SHIM_OUT="$out/rejected" sh build.sh >"$out/rejected.log" 2>&1; then
	echo "KPD probe built outside the isolated capture profile" >&2
	exit 1
fi
PHONE_CAPTURE=1 KPD_PROBE=1 PHONE_CONTRACT="$contract" SHIM_OUT="$out/phone" sh build.sh
PHONE_CAPTURE=1 KPD_PROBE=1 KPD_PROBE_QEMU=1 PHONE_CONTRACT="$contract" \
	SHIM_OUT="$out/fixture" sh build.sh

record_pa()
{
	offset=$(llvm-nm "$out/$1/duchamp-diagnostic.elf" |
	    awk -v name="$2" '$3 == name { print $1 }')
	test -n "$offset"
	printf '0x%x\n' "$((0x40200000 + 0x$offset))"
}

run()
{
	profile=$1
	shift
	python3 test_qemu.py --image "$out/$profile/Image" --pattern pc-x0 --wait 5 \
	    --capture-record-pa "$(record_pa "$profile" duchamp_bootshim_phone_capture_record)" \
	    --expect-capture-pc 0x40200000 --expect-capture-x0 0x48000000 \
	    --kpd-record-pa "$(record_pa "$profile" duchamp_bootshim_kpd_probe_record)" "$@"
}

run phone --kpd-expected 0 0 0
run fixture --kpd-fixture 0 0xfffe --kpd-expected 2 0 0
run fixture --kpd-fixture 0xffff 0xfffe --kpd-expected 2 0xffff 0
run fixture --kpd-fixture 1 0xffff --kpd-expected 4 1 0xffff
run fixture --kpd-fixture 1 0xfffe --kpd-expected 5 1 0xfffe
echo "keypad-probe-qemu-suite: PASS 5 cases output=$out"
