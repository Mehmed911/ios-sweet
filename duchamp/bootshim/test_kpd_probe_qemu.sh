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
	python3 test_qemu.py --image "$out/$profile/Image" --pattern pc-x0 --wait 20 \
	    --capture-record-pa "$(record_pa "$profile" duchamp_bootshim_phone_capture_record)" \
	    --expect-capture-pc 0x40200000 --expect-capture-x0 0x48000000 \
	    --kpd-record-pa "$(record_pa "$profile" duchamp_bootshim_kpd_probe_record)" "$@"
}

run phone --kpd-expected 0 0 0 0 0 0 0
run fixture --kpd-fixture 0 0xfffe --kpd-expected 2 0 0 0 0 0 0
run fixture --kpd-fixture 0xffff 0xfffe --kpd-expected 2 0xffff 0 0 0 0 0
run fixture --kpd-fixture 1 0xffff --kpd-expected 9 1 0xffff 0xffff 0 0 0xffff \
    >"$out/no-press.log" 2>&1 &
no_press=$!
run fixture --kpd-fixture 1 0xfffe --kpd-expected 9 1 0xfffe 0xfffe 0 0 0xfffe \
    >"$out/held.log" 2>&1 &
held=$!
run fixture --kpd-fixture 1 0xffff --kpd-transitions press-only \
    --kpd-expected 0xa 1 0xfffe 0xffff 0xfffe 0 0xfdfe >"$out/press-only.log" 2>&1 &
press_only=$!
run fixture --kpd-fixture 1 0xffff --kpd-transitions late-press-release \
    --kpd-expected 8 1 0xffff 0xffff 0xfffe 0xffff 0xffff >"$out/late-press-release.log" 2>&1 &
late=$!
result=0
run fixture --kpd-fixture 1 0xffff --kpd-transitions press-release \
    --kpd-expected 8 1 0xffff 0xffff 0xfffe 0xffff 0xffff || result=1
run fixture --kpd-fixture 1 0xfffe --kpd-transitions held-then-press \
    --kpd-expected 8 1 0xffff 0xfffe 0xfffe 0xffff 0xffff || result=1
for pid in "$no_press" "$held" "$press_only" "$late"; do
	wait "$pid" || result=1
done
cat "$out/no-press.log" "$out/held.log" "$out/press-only.log" "$out/late-press-release.log"
test "$result" -eq 0
echo "keypad-probe-qemu-suite: PASS 9 cases output=$out"
