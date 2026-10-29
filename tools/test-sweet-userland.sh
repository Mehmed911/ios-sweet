#!/bin/sh
# Build and verify the complete fork/exec/wait/restart scenario in QEMU.
set -eu
if [ "$#" -lt 5 ] || [ "$#" -gt 6 ]; then
    echo "usage: test-sweet-userland.sh KERNEL ADT BASE_HFS BASE_INIT NEW_OUTDIR [SECONDS]" >&2
    exit 2
fi
kernel=$1
adt=$2
base_hfs=$3
base_init=$4
out=$5
seconds=${6:-90}
src=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
if [ -e "$out" ]; then
    echo "refusing to overwrite previous results: $out" >&2
    exit 2
fi
sh "$src/tools/build-sweet-userland.sh" "$out"
python3 "$src/tools/replace-embedded-file.py" "$base_hfs" "$base_init" "$out/launchd" "$out/root.hfs"
python3 "$src/tools/mkpayload.py" "$kernel" "$adt" "$out/payload.bin" \
    --ramdisk "$out/root.hfs" \
    --cmdline 'debug=0xc serial=3 cpus=1 keepsyms=1 -enable_kprintf_spam -noprogress rd=md0 rootrw=1 sweet_console_fb=1'
python3 "$src/tools/qemu-sweet.py" "$out/payload.bin" "$out/run" \
    --secs "$seconds" --framebuffer duchamp --kernel "$kernel" --fail-on-panic
python3 "$src/tools/verify-sweet-userland.py" "$out/run" \
    --kernel "$kernel" --init "$out/launchd" --worker "$out/sweet-worker.macho" \
    --root "$out/root.hfs" --payload "$out/payload.bin"
