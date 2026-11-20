#!/bin/sh
# Build the 0BSD Darwin probes and boot a separate 32 MiB HFS+ RAM root in QEMU.
set -eu
if [ "$#" -ne 6 ]; then
    echo "usage: $0 KERNEL ADT BASE_HFS RESTORE_RUNTIME HFSPLUS NEW_OUTDIR" >&2
    exit 2
fi
kernel=$1
adt=$2
base=$3
runtime=$(CDPATH= cd -- "$4" && pwd)
hfsplus=$5
out=$6
src=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)

if [ "$(wc -c < "$base")" -ne 33554432 ]; then
    echo "expected a 32 MiB base HFS+ image" >&2
    exit 2
fi
mkdir "$out"
sha256sum "$kernel" "$adt" "$base" "$hfsplus" > "$out/inputs.sha256"
python3 "$src/audit-darwin-runtime.py" "$runtime" "$out/runtime-audit.json"
clang -target arm64-apple-ios16.5 -Wall -Wextra -Werror -O1 -fno-builtin \
    -fno-stack-protector -c "$src/duchamp-ramroot-userland.c" -o "$out/userland.o"
ld64.lld -arch arm64 -platform_version ios 16.5 16.5 -adhoc_codesign \
    -syslibroot "$runtime" -L"$runtime/usr/lib" -lSystem.B -e _main \
    -o "$out/c-runtime-test" "$out/userland.o"
clang -target arm64-apple-ios16.5 -c "$src/duchamp-ramroot-static.S" -o "$out/static.o"
python3 "$src/mkinit.py" "$out/static.o" "$out/ramroot-static"
clang -target arm64-apple-ios16.5 -c "$src/sweet-dynamic-init.S" -o "$out/init.o"
python3 "$src/mkinit.py" "$out/init.o" "$out/launchd"
printf '%s\n' 'Duchamp Darwin HFS+ read-only fixture' > "$out/ramroot-fixture.txt"
python3 "$src/build-dynamic-root.py" --base "$base" --runtime "$runtime" --devfs-mountpoint \
    --audit "$out/runtime-audit.json" --init "$out/launchd" --program "$out/c-runtime-test" \
    --install /sbin/ramroot-static "$out/ramroot-static" \
    --install /sbin/ramroot-fixture.txt "$out/ramroot-fixture.txt" \
    --hfsplus "$hfsplus" --output "$out/root.hfs"

cmdline='debug=0xc serial=3 cpus=1 keepsyms=1 -enable_kprintf_spam -noprogress rd=md0 rootrw=0 sweet_console_fb=1 duchamp_timer_irq_ack=1 unentitled_ios_sim_launch=1'
python3 "$src/mkpayload.py" "$kernel" "$adt" "$out/payload.bin" \
    --ramdisk "$out/root.hfs" --cmdline "$cmdline" > "$out/payload-build.log"
python3 "$src/mkpayload.py" "$kernel" "$adt" "$out/payload.rebuild.bin" \
    --ramdisk "$out/root.hfs" --cmdline "$cmdline" > "$out/payload-rebuild.log"
cmp "$out/payload.bin" "$out/payload.rebuild.bin"
python3 "$src/qemu-sweet.py" "$out/payload.bin" "$out/run" --secs 150 \
    --framebuffer duchamp --kernel "$kernel" --save-ramdisk --snapshot-interval 5 \
    --fail-on-panic --stop-on-text 'SWEET dynamic init: still alive' \
    --stop-on-text 'RAMROOT USER: FAIL' --stop-on-text 'SWEET dynamic init: TEST FAILED' \
    --stop-on-text 'DEVFS MOUNT FAILED' \
    --stop-on-text 'Library not loaded:' --stop-on-text 'Symbol not found:'
sha256sum -c "$out/inputs.sha256"
python3 "$src/verify-duchamp-darwin-ramroot.py" "$out"
