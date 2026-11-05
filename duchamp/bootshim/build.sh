#!/bin/sh
set -eu

if [ -n "${PAYLOAD:-}" ]; then
	payload_input=$(readlink -f "$PAYLOAD")
	if [ ! -f "$payload_input" ]; then
		echo "payload not found: $PAYLOAD" >&2
		exit 2
	fi
fi
if [ -n "${PHONE_CONTRACT:-}" ]; then
	phone_contract=$(readlink -f "$PHONE_CONTRACT")
	if [ ! -f "$phone_contract" ]; then
		echo "phone contract not found: $PHONE_CONTRACT" >&2
		exit 2
	fi
fi

cd "$(dirname "$0")"

out=${SHIM_OUT:-out}
cc=${CC:-clang}
objcopy=${OBJCOPY:-llvm-objcopy}
cflags="--target=aarch64-none-elf -O2 -ffreestanding -nostdlib -fno-pic -mgeneral-regs-only -mstrict-align -fno-stack-protector -Wall -Wextra -Werror ${EXTRA_CFLAGS:-}"
lk_ram=${LK_RAM_TRANSPORT:-}
phone_layout=${PHONE_LAYOUT:-}
ldflags=

if [ -n "$phone_layout" ]; then
	if [ -n "${QEMU_ONLY:-}${LK_RAM_TRANSPORT:-}${PAYLOAD:-}${MATERIALIZE:-}${READY:-}${JUMP:-}${RETURN:-}${TEST_XNU_RETURN:-}" ]; then
		echo "PHONE_LAYOUT is a separate no-payload, no-execution path" >&2
		exit 2
	fi
	if [ -z "${PHONE_CONTRACT:-}" ]; then
		echo "PHONE_LAYOUT requires PHONE_CONTRACT" >&2
		exit 2
	fi
	python3 ../../tools/verify-duchamp-phone-layout.py \
		--contract "$phone_contract"
	cflags="$cflags -DDUCHAMP_PHONE_LAYOUT_ONLY=1 -DDUCHAMP_TEST_NO_WATCHDOG=1"
	ldflags="-Wl,--defsym,DUCHAMP_IMAGE_BASE=0x40000000"
elif [ -n "$lk_ram" ]; then
	if [ "${QEMU_ONLY:-}" != 1 ]; then
		echo "LK_RAM_TRANSPORT requires QEMU_ONLY=1" >&2
		exit 2
	fi
	if [ -z "${PAYLOAD:-}" ]; then
		echo "LK_RAM_TRANSPORT requires PAYLOAD" >&2
		exit 2
	fi
	if [ -n "${MATERIALIZE:-}${READY:-}${JUMP:-}${RETURN:-}${TEST_XNU_RETURN:-}" ]; then
		echo "LK_RAM_TRANSPORT is a separate QEMU-only path" >&2
		exit 2
	fi
	cflags="$cflags -DDUCHAMP_LK_RAM_TRANSPORT=1 -DDUCHAMP_QEMU_ONLY=1 -DDUCHAMP_TEST_NO_WATCHDOG=1"
	ldflags="-Wl,--defsym,DUCHAMP_IMAGE_BASE=0x40200000"
elif [ -n "${PAYLOAD:-}" ]; then
	cflags="$cflags -DDUCHAMP_EMBED_PAYLOAD=1"
fi
if [ -n "${MATERIALIZE:-}" ]; then
	if [ -z "${PAYLOAD:-}" ]; then
		echo "MATERIALIZE requires PAYLOAD" >&2
		exit 2
	fi
	cflags="$cflags -DDUCHAMP_MATERIALIZE_PAYLOAD=1"
fi
if [ -n "${READY:-}" ]; then
	if [ -z "${MATERIALIZE:-}" ]; then
		echo "READY requires MATERIALIZE=1" >&2
		exit 2
	fi
	cflags="$cflags -DDUCHAMP_HANDOFF_READY=1"
fi
if [ -n "${JUMP:-}" ]; then
	if [ -z "${READY:-}" ]; then
		echo "JUMP requires READY=1" >&2
		exit 2
	fi
	cflags="$cflags -DDUCHAMP_XNU_JUMP=1"
fi
if [ -n "${RETURN:-}" ]; then
	cflags="$cflags -DDUCHAMP_XNU_RETURN=1 -DDUCHAMP_RETURN_CHECKPOINT=${RETURN_CHECKPOINT:-0}"
fi
if [ -n "${TEST_XNU_RETURN:-}" ]; then
	if [ -z "${RETURN:-}" ]; then
		echo "TEST_XNU_RETURN requires RETURN=1" >&2
		exit 2
	fi
	cflags="$cflags -DDUCHAMP_TEST_XNU_RETURN=1 -DDUCHAMP_TEST_NO_RETURN_RANGE=1"
fi

mkdir -p "$out"
$cc $cflags -c start.S -o "$out/start.o"
$cc $cflags -c shim.c -o "$out/shim.o"
$cc $cflags -c ../loader/mt6897_entry.c -o "$out/mt6897_entry.o"
objects="$out/start.o $out/shim.o $out/mt6897_entry.o"

if [ -n "$lk_ram" ]; then
	capsule="$out/payload.lkram"
	if [ -e "$capsule" ]; then
		echo "refusing to overwrite capsule: $capsule" >&2
		exit 2
	fi
	python3 ../../tools/mk-duchamp-lk-capsule.py "$payload_input" \
		"$capsule" --generation "${LK_RAM_GENERATION:-0x20261105}"
	cat > "$out/lkram.S" <<EOF
	.section .lkram, "a"
	.balign 16
	.incbin "$(readlink -f "$capsule")"
EOF
	$cc $cflags -c "$out/lkram.S" -o "$out/lkram.o"
	$cc $cflags -c lk_ram_boot.c -o "$out/lk_ram_boot.o"
	$cc $cflags -c ../loader/resident_protocol.c \
		-o "$out/resident_protocol.o"
	$cc $cflags -c ../loader/resident_transport.c \
		-o "$out/resident_transport.o"
	$cc $cflags -c ../loader/mt6897_lk_transport.c \
		-o "$out/mt6897_lk_transport.o"
	$cc $cflags -c ../loader/resident_xnu.c -o "$out/resident_xnu.o"
	$cc $cflags -c ../loader/guard.c -o "$out/guard.o"
	$cc $cflags -c ../loader/plan.c -o "$out/plan.o"
	$cc $cflags -c ../loader/materialize.c -o "$out/materialize.o"
	objects="$objects $out/lkram.o $out/lk_ram_boot.o $out/resident_protocol.o $out/resident_transport.o $out/mt6897_lk_transport.o $out/resident_xnu.o $out/guard.o $out/plan.o $out/materialize.o"
fi

if [ -n "${RETURN:-}" ]; then
	$cc $cflags -c xnu_return.c -o "$out/xnu_return.o"
	$cc $cflags -c ../loader/return_slot.c -o "$out/return_slot.o"
	objects="$objects $out/xnu_return.o $out/return_slot.o"
fi

if [ -n "${PAYLOAD:-}" ] && [ -z "$lk_ram" ]; then
	payload=$payload_input
	cat > "$out/payload.S" <<EOF
	.section .payload, "a"
	.balign 16
	.globl duchamp_embedded_payload_start
duchamp_embedded_payload_start:
	.incbin "$payload"
	.globl duchamp_embedded_payload_end
duchamp_embedded_payload_end:
EOF
	$cc $cflags -c payload_preflight.c \
		-o "$out/payload_preflight.o"
	$cc $cflags -c ../loader/guard.c -o "$out/guard.o"
	$cc $cflags -c "$out/payload.S" -o "$out/payload.o"
	objects="$objects $out/payload_preflight.o $out/guard.o $out/payload.o"
	if [ -n "${MATERIALIZE:-}" ]; then
		$cc $cflags -c ../loader/plan.c -o "$out/plan.o"
		$cc $cflags -c ../loader/materialize.c -o "$out/materialize.o"
		objects="$objects $out/plan.o $out/materialize.o"
		if [ -n "${READY:-}" ]; then
			$cc $cflags -c handoff_ready.c -o "$out/handoff_ready.o"
			objects="$objects $out/handoff_ready.o"
		fi
	fi
fi
$cc $cflags -fuse-ld=lld -static -T shim.ld -Wl,--build-id=none -Wl,-N \
	$ldflags \
	$objects -o "$out/duchamp-diagnostic.elf"
$objcopy -O binary "$out/duchamp-diagnostic.elf" "$out/Image"
head=$(llvm-nm "$out/duchamp-diagnostic.elf" | awk '$3 == "_head" { print "0x" $1 }')
end=$(llvm-nm "$out/duchamp-diagnostic.elf" | awk '$3 == "_end" { print "0x" $1 }')
truncate -s "$((end - head))" "$out/Image"
llvm-readelf -r "$out/duchamp-diagnostic.elf"
if [ -n "$phone_layout" ]; then
	python3 ../../tools/verify-duchamp-phone-layout.py \
		--contract "$phone_contract" \
		--elf "$out/duchamp-diagnostic.elf" --image "$out/Image"
fi
ls -l "$out/duchamp-diagnostic.elf" "$out/Image"
