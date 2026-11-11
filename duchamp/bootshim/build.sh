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
phone_capture=${PHONE_CAPTURE:-}
ufs_handoff_probe=${UFS_HANDOFF_PROBE:-}
kpd_probe=${KPD_PROBE:-}
kpd_probe_qemu=${KPD_PROBE_QEMU:-}
pmif_probe=${PMIF_PROBE:-}
pmif_probe_qemu=${PMIF_PROBE_QEMU:-}
boot_menu=${BOOT_MENU:-}
entry_keys=${BOOT_MENU_ENTRY_KEYS:-}
boot_once=${BOOT_ONCE:-}
if [ -n "$boot_once" ]; then
	if [ "$boot_once:$boot_menu:${QEMU_ONLY:-}" != 1:1:1 ] ||
	    [ -n "${PAYLOAD:-}$entry_keys" ]; then
		echo "BOOT_ONCE=1 requires the QEMU menu preview without a payload or entry-key fixture" >&2
		exit 2
	fi
	cflags="$cflags -DDUCHAMP_BOOT_ONCE=1"
fi
if [ -n "$entry_keys" ]; then
	if [ "$entry_keys:$boot_menu:${QEMU_ONLY:-}" != 1:1:1 ] || [ -n "${PAYLOAD:-}" ]; then
		echo "BOOT_MENU_ENTRY_KEYS=1 requires the QEMU menu preview without a payload" >&2
		exit 2
	fi
	cflags="$cflags -DDUCHAMP_BOOT_MENU_ENTRY_KEYS=1"
fi
if [ -n "$ufs_handoff_probe" ]; then
	if [ "$ufs_handoff_probe" != 1 ] || [ "$phone_capture" != 1 ]; then
		echo "UFS_HANDOFF_PROBE=1 requires PHONE_CAPTURE=1" >&2
		exit 2
	fi
	cflags="$cflags -DDUCHAMP_UFS_HANDOFF_PROBE=1"
fi
if [ -n "$kpd_probe$kpd_probe_qemu" ]; then
	if [ "$kpd_probe:$phone_capture" != 1:1 ] || [ -n "$ufs_handoff_probe" ]; then
		echo "KPD_PROBE=1 requires the isolated PHONE_CAPTURE=1 profile" >&2
		exit 2
	fi
	cflags="$cflags -DDUCHAMP_KPD_PROBE=1"
	if [ -n "$kpd_probe_qemu" ]; then
		if [ "$kpd_probe_qemu" != 1 ]; then
			echo "KPD_PROBE_QEMU must be exactly 1" >&2
			exit 2
		fi
		cflags="$cflags -DDUCHAMP_KPD_PROBE_QEMU=1"
	fi
fi
if [ -n "$pmif_probe$pmif_probe_qemu" ]; then
	if [ "$pmif_probe:$phone_capture" != 1:1 ] || [ -n "$ufs_handoff_probe$kpd_probe" ]; then
		echo "PMIF_PROBE=1 requires the isolated PHONE_CAPTURE=1 profile" >&2
		exit 2
	fi
	cflags="$cflags -DDUCHAMP_PMIF_PROBE=1"
	if [ -n "$pmif_probe_qemu" ]; then
		if [ "$pmif_probe_qemu" != 1 ]; then
			echo "PMIF_PROBE_QEMU must be exactly 1" >&2
			exit 2
		fi
		cflags="$cflags -DDUCHAMP_PMIF_PROBE_QEMU=1"
	fi
fi
ldflags="-Wl,--defsym,DUCHAMP_IMAGE_BASE=0"

if [ -n "$boot_menu" ]; then
	if [ "$boot_menu" != 1 ] || [ "${QEMU_ONLY:-}" != 1 ]; then
		echo "BOOT_MENU=1 requires QEMU_ONLY=1" >&2
		exit 2
	fi
	if [ -n "$phone_capture$phone_layout$lk_ram${PHONE_CONTRACT:-}${RETURN:-}" ]; then
		echo "BOOT_MENU is separate from phone and firmware diagnostics" >&2
		exit 2
	fi
	if [ -n "${PAYLOAD:-}" ]; then
		if [ "${MATERIALIZE:-}:${READY:-}:${JUMP:-}" != 1:1:1 ]; then
			echo "BOOT_MENU with PAYLOAD requires MATERIALIZE=1 READY=1 JUMP=1" >&2
			exit 2
		fi
		cflags="$cflags -DDUCHAMP_EMBED_PAYLOAD=1"
	fi
	cflags="$cflags -DDUCHAMP_BOOT_MENU=1 -DDUCHAMP_QEMU_ONLY=1 -DDUCHAMP_TEST_NO_WATCHDOG=1"
	ldflags="-Wl,--defsym,DUCHAMP_IMAGE_BASE=0x40200000"
elif [ -n "$phone_capture" ]; then
	if [ "$phone_capture" != 1 ]; then
		echo "PHONE_CAPTURE must be exactly 1" >&2
		exit 2
	fi
	if [ -n "${PHONE_LAYOUT:-}${QEMU_ONLY:-}${LK_RAM_TRANSPORT:-}${PAYLOAD:-}${MATERIALIZE:-}${READY:-}${JUMP:-}${RETURN:-}${TEST_XNU_RETURN:-}" ]; then
		echo "PHONE_CAPTURE is a separate RAM-only, no-payload path" >&2
		exit 2
	fi
	if [ -z "${PHONE_CONTRACT:-}" ]; then
		echo "PHONE_CAPTURE requires PHONE_CONTRACT" >&2
		exit 2
	fi
	python3 ../../tools/verify-duchamp-phone-capture.py \
		--contract "$phone_contract"
	cflags="$cflags -DDUCHAMP_PHONE_CAPTURE=1"
	ldflags="-Wl,--defsym,DUCHAMP_IMAGE_BASE=0"
elif [ -n "$phone_layout" ]; then
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
$cc $cflags -c ../loader/mt6897_entry.c -o "$out/mt6897_entry.o"
if [ -n "$phone_capture" ]; then
	$cc $cflags -c phone_capture.c -o "$out/phone_capture.o"
	$cc $cflags -c phone_capture_entry.c -o "$out/phone_capture_entry.o"
	objects="$out/start.o $out/phone_capture.o $out/phone_capture_entry.o $out/mt6897_entry.o"
else
	$cc $cflags -c shim.c -o "$out/shim.o"
	objects="$out/start.o $out/shim.o $out/mt6897_entry.o"
fi
if [ -n "$boot_menu" ]; then
	$cc $cflags -c boot_menu.c -o "$out/boot_menu.o"
	$cc $cflags -c boot_menu_keys.c -o "$out/boot_menu_keys.o"
	objects="$objects $out/boot_menu.o $out/boot_menu_keys.o"
fi

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
	$cc $cflags -c ../loader/mt6897_ram_provider.c \
		-o "$out/mt6897_ram_provider.o"
	$cc $cflags -c ../loader/resident_xnu.c -o "$out/resident_xnu.o"
	$cc $cflags -c ../loader/guard.c -o "$out/guard.o"
	$cc $cflags -c ../loader/plan.c -o "$out/plan.o"
	$cc $cflags -c ../loader/materialize.c -o "$out/materialize.o"
	objects="$objects $out/lkram.o $out/lk_ram_boot.o $out/resident_protocol.o $out/resident_transport.o $out/mt6897_lk_transport.o $out/mt6897_ram_provider.o $out/resident_xnu.o $out/guard.o $out/plan.o $out/materialize.o"
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
if [ -n "$phone_capture" ]; then
	set -- \
		--contract "$phone_contract" \
		--elf "$out/duchamp-diagnostic.elf" --image "$out/Image"
	if [ -n "$ufs_handoff_probe" ]; then
		set -- "$@" --ufs-handoff-probe
	fi
	if [ -n "$kpd_probe" ]; then
		set -- "$@" --kpd-probe
	fi
	if [ -n "$pmif_probe" ]; then
		set -- "$@" --pmif-probe
	fi
	python3 ../../tools/verify-duchamp-phone-capture.py "$@"
fi
ls -l "$out/duchamp-diagnostic.elf" "$out/Image"
