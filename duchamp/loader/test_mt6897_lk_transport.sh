#!/bin/sh
set -eu

if [ "$#" -ne 1 ] && [ "$#" -ne 3 ]; then
	echo "usage: $0 NEW-OUTPUT-DIR [PHONE-FDT SWEETXNU-PAYLOAD]" >&2
	exit 2
fi

out=$(readlink -m "$1")
if [ "$#" -eq 3 ]; then
	fdt=$(readlink -f "$2")
	payload=$(readlink -f "$3")
fi
cd "$(dirname "$0")"
if [ -e "$out" ]; then
	echo "refusing to overwrite output: $out" >&2
	exit 2
fi
mkdir -p "$out/native" "$out/aarch64" "$out/qemu"

host_cc=${HOST_CC:-clang}
"$host_cc" -std=c11 -O1 -g -Wall -Wextra -Werror \
	-fsanitize=address,undefined -fno-omit-frame-pointer \
	test_resident_transport.c resident_protocol.c resident_transport.c \
	mt6897_lk_transport.c -o "$out/native/test_resident_transport"
ASAN_OPTIONS=detect_leaks=1 "$out/native/test_resident_transport" \
	> "$out/native/transport.log" 2>&1
cat "$out/native/transport.log"

python3 ../../tools/test-mk-duchamp-lk-capsule.py \
	> "$out/native/packer.log" 2>&1
cat "$out/native/packer.log"

if [ "$#" -eq 3 ]; then
	python3 ../../tools/mk-duchamp-lk-capsule.py "$payload" \
		"$out/native/payload.lkram" --generation 0x20261105 \
		> "$out/native/real-packer.log" 2>&1
	cat "$out/native/real-packer.log"
	"$host_cc" -std=c11 -O2 -Wall -Wextra -Werror \
		test_mt6897_lk_transport_xnu.c resident_protocol.c \
		resident_transport.c mt6897_lk_transport.c resident_xnu.c \
		materialize.c plan.c guard.c \
		-o "$out/native/test_mt6897_lk_transport_xnu"
	"$out/native/test_mt6897_lk_transport_xnu" "$fdt" \
		"$out/native/payload.lkram" > "$out/native/real-xnu.log" 2>&1
	cat "$out/native/real-xnu.log"
fi

target_cc=${CC:-clang}
cflags="--target=aarch64-none-elf -O2 -ffreestanding -nostdlib -fno-pic -fno-builtin -mgeneral-regs-only -mstrict-align -fno-stack-protector -Wall -Wextra -Werror"
for source in resident_protocol.c resident_transport.c mt6897_lk_transport.c; do
	"$target_cc" $cflags -c "$source" -o "$out/aarch64/${source%.c}.o"
done
ld.lld -r "$out/aarch64/resident_protocol.o" \
	"$out/aarch64/resident_transport.o" \
	"$out/aarch64/mt6897_lk_transport.o" \
	-o "$out/aarch64/mt6897-lk-transport.o"
if [ -n "$(llvm-nm -u "$out/aarch64/mt6897-lk-transport.o")" ]; then
	echo "mt6897-lk-transport.o has unresolved symbols" >&2
	llvm-nm -u "$out/aarch64/mt6897-lk-transport.o" >&2
	exit 1
fi

"$target_cc" $cflags -c resident_qemu_start.S -o "$out/qemu/start.o"
"$target_cc" $cflags -c resident_transport_qemu.c \
	-o "$out/qemu/resident_transport_qemu.o"
for source in resident_protocol.c resident_transport.c mt6897_lk_transport.c; do
	"$target_cc" $cflags -c "$source" -o "$out/qemu/${source%.c}.o"
done
"$target_cc" $cflags -fuse-ld=lld -static -T resident_qemu.ld \
	-Wl,--build-id=none -Wl,-N "$out/qemu/start.o" \
	"$out/qemu/resident_transport_qemu.o" \
	"$out/qemu/resident_protocol.o" "$out/qemu/resident_transport.o" \
	"$out/qemu/mt6897_lk_transport.o" \
	-o "$out/qemu/mt6897-lk-transport.elf"
llvm-objcopy -O binary "$out/qemu/mt6897-lk-transport.elf" \
	"$out/qemu/Image"
image_start=$(llvm-nm "$out/qemu/mt6897-lk-transport.elf" | \
	awk '$3 == "_head" { print "0x" $1 }')
image_end=$(llvm-nm "$out/qemu/mt6897-lk-transport.elf" | \
	awk '$3 == "_end" { print "0x" $1 }')
image_size=$((image_end - image_start))
truncate -s "$image_size" "$out/qemu/Image"
python3 test_resident_qemu.py --image "$out/qemu/Image" \
	--memory 4G --wait 0.5 --capture "$out/qemu/framebuffer.raw" \
	> "$out/qemu/qemu.log" 2>&1
cat "$out/qemu/qemu.log"

if [ "$#" -eq 3 ]; then
	sha256sum "$fdt" "$payload" "$out/native/payload.lkram" \
		"$out/aarch64/mt6897-lk-transport.o" "$out/qemu/Image" \
		> "$out/SHA256SUMS"
else
	sha256sum "$out/aarch64/mt6897-lk-transport.o" \
		"$out/qemu/Image" > "$out/SHA256SUMS"
fi
printf '%s\n' 'mt6897-lk-transport-suite: PASS' | tee "$out/result.txt"
