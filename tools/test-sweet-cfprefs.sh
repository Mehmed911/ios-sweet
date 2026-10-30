#!/bin/sh
# Distinct QEMU-only preferences scenario; never connects to a phone.
set -eu
if [ "$#" -lt 6 ] || [ "$#" -gt 7 ]; then
    echo 'usage: test-sweet-cfprefs.sh KERNEL ADT BASE_HFS RUNTIME HFSPLUS NEW_OUTDIR [SECONDS]' >&2
    exit 2
fi
kernel=$1 adt=$2 base=$3 runtime=$(CDPATH= cd -- "$4" && pwd) hfsplus=$5 out=$6
seconds=${7:-1500}
src=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
if [ -e "$out" ]; then echo "refusing to overwrite previous results: $out" >&2; exit 2; fi
mkdir -p "$out"
python3 "$src/tools/audit-darwin-runtime.py" "$runtime" "$out/runtime-audit.json" \
    --entry /bin/launchctl --entry /System/Library/Frameworks/Foundation.framework/Foundation \
    --entry /usr/sbin/syslogd --entry /usr/sbin/notifyd --entry /usr/sbin/cfprefsd \
    --entry /System/Library/Frameworks/MobileCoreServices.framework/MobileCoreServices
for program in sweet-launchd-service sweet-ipc-client sweet-launchctl-control; do
    source="$src/tools/sweet-cfprefs.m"
    set -- -fno-objc-arc -fobjc-exceptions
    case "$program" in
        sweet-launchd-service) set -- "$@" -DSWEET_PREFS_WRITER=1 ;;
        sweet-launchctl-control)
            source="$src/tools/sweet-launchctl-control.c"
            set -- -DSWEET_CFPREFS_TEST=1 ;;
    esac
    clang -target arm64-apple-ios16.5 -Wall -Wextra -Werror -O1 \
        -fno-stack-protector -fno-builtin "$@" -c "$source" -o "$out/$program.o"
    set --
    if [ "$program" != sweet-launchctl-control ]; then
        set -- -F"$runtime/System/Library/Frameworks" -framework Foundation -lobjc.A
    fi
    ld64.lld -arch arm64 -platform_version ios 16.5 16.5 -adhoc_codesign \
        -syslibroot "$runtime" -L"$runtime/usr/lib" -lSystem.B -e _main \
        -o "$out/$program" "$out/$program.o" "$@"
done
python3 "$src/tools/build-launchctl-root.py" --base "$base" --runtime "$runtime" \
    --audit "$out/runtime-audit.json" --service "$out/sweet-launchd-service" \
    --client "$out/sweet-ipc-client" --controller "$out/sweet-launchctl-control" \
    --hfsplus "$hfsplus" --output "$out/root.hfs" --scenario cfprefsd \
    --runtime-source "$runtime/../source.json"
python3 "$src/tools/mkpayload.py" "$kernel" "$adt" "$out/payload.bin" --ramdisk "$out/root.hfs" \
    --cmdline 'debug=0xc serial=3 cpus=1 keepsyms=1 -enable_kprintf_spam -noprogress rd=md0 rootrw=1 sweet_console_fb=1 unentitled_ios_sim_launch=1 launchdsuffix=sweet launchd_log_serial=1'
status=0
python3 "$src/tools/qemu-sweet.py" "$out/payload.bin" "$out/run" --secs "$seconds" \
    --framebuffer duchamp --kernel "$kernel" --snapshot-interval 10 \
    --stop-on-text 'SWEET EARLY PANIC:' --stop-on-text 'SWEET launchctl: FAIL' \
    --stop-on-text 'SWEET launchctl: heartbeat=2 ' \
    --stop-on-text 'SWEET ipc prefs-writer: FAIL' --stop-on-text 'PREFERENCES ERROR' \
    --stop-on-text 'Library not loaded:' --stop-on-text 'Symbol not found:' \
    --stop-on-text 'exited due to SIGSEGV' \
    --save-ramdisk --fail-on-panic || status=$?
python3 "$src/tools/verify-sweet-cfprefs.py" "$out" --hfsplus "$hfsplus"
exit "$status"
