#!/bin/sh
# Boot an unchanged original launchd as PID 1 with one persistent C service.
set -eu
if [ "$#" -lt 7 ] || [ "$#" -gt 8 ]; then
    echo "usage: test-sweet-launchd.sh KERNEL ADT BASE_DYNAMIC_HFS APPLE_ROOT RUNTIME_ROOT HFSPLUS NEW_OUTDIR [SECONDS]" >&2
    exit 2
fi
kernel=$1
adt=$2
base=$3
apple=$4
runtime=$(CDPATH= cd -- "$5" && pwd)
hfsplus=$6
out=$7
seconds=${8:-180}
src=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
if [ -e "$out" ]; then
    echo "refusing to overwrite previous results: $out" >&2
    exit 2
fi
mkdir -p "$out"
python3 "$src/tools/audit-darwin-runtime.py" "$runtime" "$out/runtime-audit.json"
clang -target arm64-apple-ios16.5 -c "$src/tools/sweet-launchd-bootstrap.S" -o "$out/bootstrap.o"
python3 "$src/tools/mkinit.py" "$out/bootstrap.o" "$out/bootstrap"
clang -target arm64-apple-ios16.5 -Wall -Wextra -Werror -O1 \
    -fno-stack-protector -fno-builtin -c "$src/tools/sweet-launchd-service.c" -o "$out/service.o"
ld64.lld -arch arm64 -platform_version ios 16.5 16.5 -adhoc_codesign \
    -syslibroot "$runtime" -L"$runtime/usr/lib" -lSystem.B -e _main \
    -o "$out/service" "$out/service.o"
python3 "$src/tools/build-launchd-root.py" --base "$base" --apple "$apple" \
    --bootstrap "$out/bootstrap" --service "$out/service" --hfsplus "$hfsplus" --output "$out/root.hfs"
python3 "$src/tools/mkpayload.py" "$kernel" "$adt" "$out/payload.bin" --ramdisk "$out/root.hfs" \
    --cmdline 'debug=0xc serial=3 cpus=1 keepsyms=1 -enable_kprintf_spam -noprogress rd=md0 rootrw=1 sweet_console_fb=1 unentitled_ios_sim_launch=1 launchdsuffix=sweet launchd_log_serial=1'
qemu_status=0
python3 "$src/tools/qemu-sweet.py" "$out/payload.bin" "$out/run" --secs "$seconds" \
    --framebuffer duchamp --kernel "$kernel" --snapshot-interval 10 --fail-on-panic || qemu_status=$?
python3 "$src/tools/verify-sweet-launchd.py" "$out"
exit "$qemu_status"
