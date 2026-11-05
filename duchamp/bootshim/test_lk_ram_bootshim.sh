#!/bin/sh
set -eu

if [ "$#" -ne 4 ]; then
	echo "usage: $0 PHONE-FDT SWEETXNU-PAYLOAD STOCK-BOOT NEW-OUTPUT-DIR" >&2
	exit 2
fi

fdt=$(readlink -f "$1")
payload=$(readlink -f "$2")
stock=$(readlink -f "$3")
out=$(readlink -m "$4")
cd "$(dirname "$0")"
if [ -e "$out" ]; then
	echo "refusing to overwrite output: $out" >&2
	exit 2
fi
mkdir -p "$out/negative"

host_cc=${HOST_CC:-clang}
"$host_cc" -std=c11 -O1 -g -Wall -Wextra -Werror \
	-fsanitize=address,undefined -fno-omit-frame-pointer \
	../loader/test_mt6897_ram_provider.c \
	../loader/mt6897_ram_provider.c ../loader/mt6897_entry.c \
	-o "$out/test_mt6897_ram_provider"
ASAN_OPTIONS=detect_leaks=1 "$out/test_mt6897_ram_provider" \
	> "$out/ram-provider-host.log" 2>&1
cat "$out/ram-provider-host.log"

if SHIM_OUT="$out/negative/no-qemu" PAYLOAD="$payload" \
	LK_RAM_TRANSPORT=1 sh build.sh > "$out/negative/no-qemu.log" 2>&1; then
	echo "LK RAM build unexpectedly worked without QEMU_ONLY=1" >&2
	exit 1
fi
grep -q "requires QEMU_ONLY=1" "$out/negative/no-qemu.log"

if SHIM_OUT="$out/negative/jump" PAYLOAD="$payload" \
	LK_RAM_TRANSPORT=1 QEMU_ONLY=1 JUMP=1 sh build.sh \
	> "$out/negative/jump.log" 2>&1; then
	echo "LK RAM build unexpectedly accepted JUMP=1" >&2
	exit 1
fi
grep -q "separate QEMU-only path" "$out/negative/jump.log"

SHIM_OUT="$out/build" PAYLOAD="$payload" LK_RAM_TRANSPORT=1 \
	QEMU_ONLY=1 LK_RAM_GENERATION=0x20261105 sh build.sh \
	> "$out/build.log" 2>&1
cat "$out/build.log"

report_offset=$(llvm-nm "$out/build/duchamp-diagnostic.elf" | \
	awk '$3 == "duchamp_lk_ram_boot_report" { print "0x" $1 }')
if [ -z "$report_offset" ]; then
	echo "LK RAM report symbol is missing" >&2
	exit 1
fi
exception_offset=$(llvm-nm "$out/build/duchamp-diagnostic.elf" | \
	awk '$3 == "duchamp_bootshim_exception_record" { print "0x" $1 }')
if [ -z "$exception_offset" ]; then
	echo "bootshim exception record symbol is missing" >&2
	exit 1
fi
provider_offset=$(llvm-nm "$out/build/duchamp-diagnostic.elf" | \
	awk '$3 == "duchamp_bootshim_ram_provider_report" { print "0x" $1 }')
if [ -z "$provider_offset" ]; then
	echo "RAM provider report symbol is missing" >&2
	exit 1
fi
image_head=$(llvm-nm "$out/build/duchamp-diagnostic.elf" | \
	awk '$3 == "_head" { print "0x" $1 }')
if [ -z "$image_head" ]; then
	echo "bootshim image head symbol is missing" >&2
	exit 1
fi
report_pa=$((0x40200000 + report_offset - image_head))
exception_pa=$((0x40200000 + exception_offset - image_head))
provider_pa=$((0x40200000 + provider_offset - image_head))
if ! python3 test_qemu.py --image "$out/build/Image" --pattern lk-ram \
	--dtb "$fdt" --memory 8G --wait 15 \
	--lk-report-pa "$report_pa" --expect-lk-generation 0x20261105 \
	--lk-payload "$payload" \
	--ram-provider-report-pa "$provider_pa" \
	--exception-record-pa "$exception_pa" --expect-no-exception \
	--capture "$out/framebuffer.raw" > "$out/qemu.log" 2>&1; then
	cat "$out/qemu.log" >&2
	exit 1
fi
cat "$out/qemu.log"

python3 pack_boot.py --stock-boot "$stock" --kernel "$out/build/Image" \
	--out "$out/qemu-only-layout-not-for-phone.img" \
	--preserve-avb-container --lz4-legacy > "$out/pack.log" 2>&1
cat "$out/pack.log"

python3 verify_lk_ram_layout.py \
	--elf "$out/build/duchamp-diagnostic.elf" \
	--image "$out/build/Image" --capsule "$out/build/payload.lkram" \
	--payload "$payload" --fdt "$fdt" \
	--boot-image "$out/qemu-only-layout-not-for-phone.img" \
	--stock-boot "$stock" --json-out "$out/layout.json" \
	> "$out/layout.log" 2>&1
cat "$out/layout.log"

sha256sum "$fdt" "$payload" "$stock" "$out/build/payload.lkram" \
	"$out/build/duchamp-diagnostic.elf" "$out/build/Image" \
	"$out/qemu-only-layout-not-for-phone.img" "$out/framebuffer.raw" \
	"$out/layout.json" > "$out/SHA256SUMS"
printf '%s\n' 'mt6897-lk-ram-bootshim-suite: PASS qemu-only no-phone' | \
	tee "$out/result.txt"
