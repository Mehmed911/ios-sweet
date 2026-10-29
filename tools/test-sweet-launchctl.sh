#!/bin/sh
# Check service management using pinned Procursus launchctl and original Apple launchd.
set -eu
if [ "$#" -lt 6 ] || [ "$#" -gt 7 ]; then
    echo "usage: test-sweet-launchctl.sh KERNEL ADT BASE_LAUNCHD_HFS RUNTIME_ROOT HFSPLUS NEW_OUTDIR [SECONDS]" >&2
    exit 2
fi
kernel=$1
adt=$2
base=$3
runtime=$(CDPATH= cd -- "$4" && pwd)
hfsplus=$5
out=$6
seconds=${7:-720}
src=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
if [ -e "$out" ]; then
    echo "refusing to overwrite previous results: $out" >&2
    exit 2
fi
mkdir -p "$out"
python3 "$src/tools/audit-darwin-runtime.py" "$runtime" "$out/runtime-audit.json" --entry /bin/launchctl
for program in sweet-launchd-service sweet-launchctl-control; do
    clang -target arm64-apple-ios16.5 -Wall -Wextra -Werror -O1 \
        -fno-stack-protector -fno-builtin -c "$src/tools/$program.c" -o "$out/$program.o"
    ld64.lld -arch arm64 -platform_version ios 16.5 16.5 -adhoc_codesign \
        -syslibroot "$runtime" -L"$runtime/usr/lib" -lSystem.B -e _main \
        -o "$out/$program" "$out/$program.o"
done
python3 "$src/tools/build-launchctl-root.py" --base "$base" --runtime "$runtime" \
    --audit "$out/runtime-audit.json" --service "$out/sweet-launchd-service" \
    --controller "$out/sweet-launchctl-control" --hfsplus "$hfsplus" --output "$out/root.hfs"
python3 "$src/tools/mkpayload.py" "$kernel" "$adt" "$out/payload.bin" --ramdisk "$out/root.hfs" \
    --cmdline 'debug=0xc serial=3 cpus=1 keepsyms=1 -enable_kprintf_spam -noprogress rd=md0 rootrw=1 sweet_console_fb=1 unentitled_ios_sim_launch=1 launchdsuffix=sweet launchd_log_serial=1'
qemu_status=0
python3 "$src/tools/qemu-sweet.py" "$out/payload.bin" "$out/run" --secs "$seconds" \
    --framebuffer duchamp --kernel "$kernel" --snapshot-interval 10 \
    --stop-on-text 'SWEET EARLY PANIC:' --stop-on-text 'SWEET launchctl: FAIL' \
    --stop-on-text 'SWEET launchctl: heartbeat=2 ' \
    --save-ramdisk --fail-on-panic || qemu_status=$?
python3 "$src/tools/verify-sweet-launchctl.py" "$out" --hfsplus "$hfsplus"
exit "$qemu_status"
