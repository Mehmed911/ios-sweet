#!/bin/sh
set -eu

if [ "$#" -ne 3 ]; then
	echo "usage: $0 phone-fdt.bin payload.bin NEW-OUTPUT-DIR" >&2
	exit 2
fi

fdt=$(readlink -f "$1")
payload=$(readlink -f "$2")
out=$(readlink -m "$3")
cd "$(dirname "$0")"
if [ -e "$out" ]; then
	echo "refusing to overwrite output: $out" >&2
	exit 2
fi
mkdir -p "$out/native" "$out/aarch64" "$out/qemu"

host_cc=${HOST_CC:-clang}
"$host_cc" -std=c11 -O1 -g -Wall -Wextra -Werror \
	-fsanitize=address,undefined -fno-omit-frame-pointer \
	test_resident_protocol.c resident_protocol.c \
	-o "$out/native/test_resident_protocol"
ASAN_OPTIONS=detect_leaks=1 "$out/native/test_resident_protocol" \
	> "$out/native/protocol.log" 2>&1
cat "$out/native/protocol.log"

"$host_cc" -std=c11 -O2 -Wall -Wextra -Werror \
	test_resident_xnu.c resident_protocol.c resident_xnu.c \
	materialize.c plan.c guard.c -o "$out/native/test_resident_xnu"
"$out/native/test_resident_xnu" "$fdt" "$payload" \
	> "$out/native/xnu.log" 2>&1
cat "$out/native/xnu.log"

target_cc=${CC:-clang}
cflags="--target=aarch64-none-elf -O2 -ffreestanding -nostdlib -fno-pic -fno-builtin -mgeneral-regs-only -mstrict-align -fno-stack-protector -Wall -Wextra -Werror"
for source in resident_protocol.c resident_xnu.c materialize.c plan.c guard.c; do
	"$target_cc" $cflags -c "$source" -o "$out/aarch64/${source%.c}.o"
done
ld.lld -r "$out/aarch64/resident_protocol.o" \
	"$out/aarch64/resident_xnu.o" "$out/aarch64/materialize.o" \
	"$out/aarch64/plan.o" "$out/aarch64/guard.o" \
	-o "$out/aarch64/resident-loader.o"
if [ -n "$(llvm-nm -u "$out/aarch64/resident-loader.o")" ]; then
	echo "resident-loader.o has unresolved symbols" >&2
	llvm-nm -u "$out/aarch64/resident-loader.o" >&2
	exit 1
fi

"$target_cc" $cflags -c resident_qemu_start.S -o "$out/qemu/start.o"
"$target_cc" $cflags -c resident_qemu.c -o "$out/qemu/resident_qemu.o"
"$target_cc" $cflags -c resident_protocol.c -o "$out/qemu/resident_protocol.o"
"$target_cc" $cflags -fuse-ld=lld -static -T resident_qemu.ld \
	-Wl,--build-id=none -Wl,-N "$out/qemu/start.o" \
	"$out/qemu/resident_qemu.o" "$out/qemu/resident_protocol.o" \
	-o "$out/qemu/resident-protocol.elf"
llvm-objcopy -O binary "$out/qemu/resident-protocol.elf" "$out/qemu/Image"
image_start=$(llvm-nm "$out/qemu/resident-protocol.elf" | \
	awk '$3 == "_head" { print "0x" $1 }')
image_end=$(llvm-nm "$out/qemu/resident-protocol.elf" | \
	awk '$3 == "_end" { print "0x" $1 }')
image_size=$((image_end - image_start))
truncate -s "$((image_size))" "$out/qemu/Image"
python3 test_resident_qemu.py --image "$out/qemu/Image" \
	--memory 4G --wait 0.5 \
	--capture "$out/qemu/framebuffer.raw" > "$out/qemu/qemu.log" 2>&1
cat "$out/qemu/qemu.log"

sha256sum "$fdt" "$payload" "$out/aarch64/resident-loader.o" \
	"$out/qemu/Image" > "$out/SHA256SUMS"
printf '%s\n' 'resident-loader-suite: PASS' | tee "$out/result.txt"
