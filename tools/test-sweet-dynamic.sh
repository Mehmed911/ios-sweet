#!/bin/sh
# Standalone dyld/libSystem and C test on a fresh HFS RAM root, using existing XNU.
set -eu
if [ "$#" -lt 6 ] || [ "$#" -gt 7 ]; then
    echo "usage: test-sweet-dynamic.sh KERNEL ADT BASE_HFS RUNTIME_ROOT HFSPLUS NEW_OUTDIR [SECONDS]" >&2
    exit 2
fi
kernel=$1
adt=$2
base=$3
runtime=$(CDPATH= cd -- "$4" && pwd)
hfsplus=$5
out=$6
seconds=${7:-90}
src=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
if [ -e "$out" ]; then
    echo "refusing to overwrite previous results: $out" >&2
    exit 2
fi
mkdir -p "$out"
python3 "$src/tools/audit-darwin-runtime.py" "$runtime" "$out/runtime-audit.json"
clang -target arm64-apple-ios16.5 -Wall -Wextra -Werror -O1 \
    -fno-stack-protector -fno-builtin -c "$src/tools/sweet-c-runtime.c" -o "$out/c-runtime.o"
ld64.lld -arch arm64 -platform_version ios 16.5 16.5 -adhoc_codesign \
    -syslibroot "$runtime" -L"$runtime/usr/lib" -lSystem.B -e _main \
    -o "$out/c-runtime-test" "$out/c-runtime.o"
clang -target arm64-apple-ios16.5 -c "$src/tools/sweet-dynamic-init.S" -o "$out/init.o"
python3 "$src/tools/mkinit.py" "$out/init.o" "$out/launchd"
python3 "$src/tools/build-dynamic-root.py" --base "$base" --runtime "$runtime" \
    --audit "$out/runtime-audit.json" --init "$out/launchd" --program "$out/c-runtime-test" \
    --hfsplus "$hfsplus" --output "$out/root.hfs"
python3 "$src/tools/mkpayload.py" "$kernel" "$adt" "$out/payload.bin" \
    --ramdisk "$out/root.hfs" \
    --cmdline 'debug=0xc serial=3 cpus=1 keepsyms=1 -enable_kprintf_spam -noprogress rd=md0 rootrw=1 sweet_console_fb=1 unentitled_ios_sim_launch=1'
python3 "$src/tools/qemu-sweet.py" "$out/payload.bin" "$out/run" --secs "$seconds" \
    --framebuffer duchamp --kernel "$kernel" --fail-on-panic
python3 "$src/tools/verify-sweet-dynamic.py" "$out/run" --kernel "$kernel" \
    --init "$out/launchd" --program "$out/c-runtime-test" --root "$out/root.hfs" \
    --payload "$out/payload.bin" --audit "$out/runtime-audit.json"
