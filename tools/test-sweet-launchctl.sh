#!/bin/sh
# Check service management using pinned Procursus launchctl and original Apple launchd.
set -eu
if [ "$#" -lt 6 ] || [ "$#" -gt 8 ]; then
    echo "usage: test-sweet-launchctl.sh KERNEL ADT BASE_LAUNCHD_HFS RUNTIME_ROOT HFSPLUS NEW_OUTDIR [SECONDS] [stop-restart|bootout-bootstrap|keepalive|ipc|xpc|foundation|foundation-xpc|foundation-xpc-batch|syslogd|notifyd]" >&2
    exit 2
fi
kernel=$1
adt=$2
base=$3
runtime=$(CDPATH= cd -- "$4" && pwd)
hfsplus=$5
out=$6
seconds=${7:-720}
scenario=${8:-stop-restart}
case "$scenario" in
    stop-restart|bootout-bootstrap|keepalive|ipc|xpc|foundation|foundation-xpc|foundation-xpc-batch|syslogd|notifyd) ;;
    *) echo "unknown launchctl scenario: $scenario" >&2; exit 2 ;;
esac
src=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
if [ -e "$out" ]; then
    echo "refusing to overwrite previous results: $out" >&2
    exit 2
fi
mkdir -p "$out"
set --
if [ "$scenario" = foundation ] || [ "$scenario" = foundation-xpc ] || [ "$scenario" = foundation-xpc-batch ]; then
    set -- --entry /System/Library/Frameworks/Foundation.framework/Foundation
fi
if [ "$scenario" = syslogd ] || [ "$scenario" = notifyd ]; then set -- --entry /usr/sbin/syslogd; fi
if [ "$scenario" = notifyd ]; then set -- "$@" --entry /usr/sbin/notifyd; fi
python3 "$src/tools/audit-darwin-runtime.py" "$runtime" "$out/runtime-audit.json" --entry /bin/launchctl "$@"
programs='sweet-launchd-service sweet-launchctl-control'
case "$scenario" in ipc|xpc|foundation-xpc|foundation-xpc-batch|syslogd|notifyd) programs="$programs sweet-ipc-client" ;; esac
for program in $programs; do
    set --
    source="$src/tools/$program.c"
    if [ "$scenario" = ipc ] && [ "$program" = sweet-launchd-service ]; then
        source="$src/tools/sweet-ipc-server.c"
    fi
    if [ "$scenario" = xpc ] || [ "$scenario" = foundation-xpc ]; then
        set -- -fblocks
        case "$program" in
            sweet-launchd-service) source="$src/tools/sweet-xpc-server.c" ;;
            sweet-ipc-client) source="$src/tools/sweet-xpc-client.c" ;;
            sweet-launchctl-control) set -- -fblocks -DSWEET_XPC_TEST=1 ;;
        esac
        if [ "$scenario" = foundation-xpc ]; then
            case "$program" in
                sweet-launchd-service|sweet-ipc-client)
                    set -- -fblocks -x objective-c -fno-objc-arc -fobjc-exceptions -DSWEET_FOUNDATION_XPC_TEST=1 ;;
                sweet-launchctl-control)
                    set -- -fblocks -DSWEET_XPC_TEST=1 -DSWEET_FOUNDATION_XPC_TEST=1 ;;
            esac
        fi
    fi
    if [ "$scenario" = foundation ]; then
        case "$program" in
            sweet-launchd-service)
                source="$src/tools/sweet-foundation.m"
                set -- -fno-objc-arc -fobjc-exceptions ;;
            sweet-launchctl-control) set -- -DSWEET_FOUNDATION_TEST=1 ;;
        esac
    fi
    if [ "$scenario" = foundation-xpc-batch ]; then
        case "$program" in
            sweet-launchd-service) source="$src/tools/sweet-xpc-batch-server.m" ;;
            sweet-ipc-client) source="$src/tools/sweet-xpc-batch-client.m" ;;
        esac
        case "$program" in
            sweet-launchctl-control) set -- -fblocks -DSWEET_XPC_BATCH_TEST=1 ;;
            *) set -- -fblocks -fno-objc-arc -fobjc-exceptions ;;
        esac
    fi
    if [ "$scenario" = bootout-bootstrap ] && [ "$program" = sweet-launchctl-control ]; then
        set -- -DSWEET_BOOTSTRAP_TEST=1
    elif [ "$scenario" = keepalive ] && [ "$program" = sweet-launchctl-control ]; then
        set -- -DSWEET_KEEPALIVE_TEST=1
    elif [ "$scenario" = ipc ] && [ "$program" = sweet-launchctl-control ]; then
        set -- -DSWEET_IPC_TEST=1
    fi
    if [ "$scenario" = syslogd ] || [ "$scenario" = notifyd ]; then
        case "$program" in
            sweet-launchctl-control) set -- -DSWEET_SYSLOGD_TEST=1 ;;
            *) source="$src/tools/sweet-syslogd-probe.c" ;;
        esac
        if [ "$scenario" = notifyd ]; then set -- "$@" -DSWEET_NOTIFYD_TEST=1; fi
    fi
    clang -target arm64-apple-ios16.5 -Wall -Wextra -Werror -O1 \
        -fno-stack-protector -fno-builtin "$@" -c "$source" -o "$out/$program.o"
    set --
    if [ "$scenario" = foundation ] && [ "$program" = sweet-launchd-service ]; then
        set -- -F"$runtime/System/Library/Frameworks" -framework Foundation -lobjc.A
    fi
    if { [ "$scenario" = foundation-xpc ] || [ "$scenario" = foundation-xpc-batch ]; } && [ "$program" != sweet-launchctl-control ]; then
        set -- -F"$runtime/System/Library/Frameworks" -framework Foundation -lobjc.A
    fi
    ld64.lld -arch arm64 -platform_version ios 16.5 16.5 -adhoc_codesign \
        -syslibroot "$runtime" -L"$runtime/usr/lib" -lSystem.B -e _main \
        -o "$out/$program" "$out/$program.o" "$@"
done
set --
case "$scenario" in ipc|xpc|foundation-xpc|foundation-xpc-batch|syslogd|notifyd) set -- --client "$out/sweet-ipc-client" ;; esac
if [ "$scenario" = foundation ] || [ "$scenario" = foundation-xpc ] || [ "$scenario" = foundation-xpc-batch ]; then
    set -- "$@" --runtime-source "$runtime/../source.json"
fi
if [ "$scenario" = syslogd ] || [ "$scenario" = notifyd ]; then set -- "$@" --runtime-source "$runtime/../source.json"; fi
python3 "$src/tools/build-launchctl-root.py" --base "$base" --runtime "$runtime" \
    --audit "$out/runtime-audit.json" --service "$out/sweet-launchd-service" \
    --controller "$out/sweet-launchctl-control" --hfsplus "$hfsplus" --output "$out/root.hfs" \
    --scenario "$scenario" "$@"
python3 "$src/tools/mkpayload.py" "$kernel" "$adt" "$out/payload.bin" --ramdisk "$out/root.hfs" \
    --cmdline 'debug=0xc serial=3 cpus=1 keepsyms=1 -enable_kprintf_spam -noprogress rd=md0 rootrw=1 sweet_console_fb=1 unentitled_ios_sim_launch=1 launchdsuffix=sweet launchd_log_serial=1'
qemu_status=0
set --
if [ "$scenario" = syslogd ] || [ "$scenario" = notifyd ]; then
    set -- --stop-on-text 'SWEET ipc asl1: FAIL' --stop-on-text 'SWEET ipc asl2: FAIL' \
        --stop-on-text 'Library not loaded:' --stop-on-text 'Symbol not found:'
fi
if [ "$scenario" = notifyd ]; then
    set -- "$@" --stop-on-text 'BUG IN LIBNOTIFY:' --stop-on-text 'Event publisher error' \
        --stop-on-text 'bootstrap_check_in failed'
fi
if [ "$scenario" = ipc ] || [ "$scenario" = xpc ] || [ "$scenario" = foundation-xpc ]; then
    set -- --stop-on-text 'SWEET ipc server: FAIL' --stop-on-text 'SWEET ipc client: FAIL'
fi
if [ "$scenario" = foundation-xpc ]; then
    set -- "$@" --stop-on-text 'Library not loaded:' --stop-on-text 'Symbol not found:'
fi
if [ "$scenario" = foundation-xpc-batch ]; then
    set -- --stop-on-text 'SWEET ipc batch-server1: FAIL' --stop-on-text 'SWEET ipc batch-server2: FAIL' \
        --stop-on-text 'SWEET ipc batch-client1: FAIL' --stop-on-text 'SWEET ipc batch-client2: FAIL' \
        --stop-on-text 'Library not loaded:' --stop-on-text 'Symbol not found:'
fi
if [ "$scenario" = foundation ]; then
    set -- --stop-on-text 'SWEET ipc foundation: FAIL' --stop-on-text 'Library not loaded:' --stop-on-text 'Symbol not found:'
fi
python3 "$src/tools/qemu-sweet.py" "$out/payload.bin" "$out/run" --secs "$seconds" \
    --framebuffer duchamp --kernel "$kernel" --snapshot-interval 10 \
    --stop-on-text 'SWEET EARLY PANIC:' --stop-on-text 'SWEET launchctl: FAIL' \
    --stop-on-text 'SWEET launchctl: heartbeat=2 ' \
    --save-ramdisk --fail-on-panic "$@" || qemu_status=$?
if [ "$scenario" = syslogd ] || [ "$scenario" = notifyd ]; then
    set --
    if [ "$scenario" = notifyd ]; then set -- --notifyd; fi
    python3 "$src/tools/verify-sweet-syslogd.py" "$out" --hfsplus "$hfsplus" "$@"
elif [ "$scenario" = foundation-xpc-batch ]; then
    python3 "$src/tools/verify-sweet-xpc-batch.py" "$out" --hfsplus "$hfsplus"
elif [ "$scenario" = foundation ]; then
    python3 "$src/tools/verify-sweet-foundation.py" "$out" --hfsplus "$hfsplus"
elif [ "$scenario" = ipc ] || [ "$scenario" = xpc ] || [ "$scenario" = foundation-xpc ]; then
    set --
    if [ "$scenario" = xpc ]; then set -- --transport xpc; fi
    if [ "$scenario" = foundation-xpc ]; then set -- --transport foundation-xpc; fi
    python3 "$src/tools/verify-sweet-ipc.py" "$out" --hfsplus "$hfsplus" "$@"
else
    python3 "$src/tools/verify-sweet-launchctl.py" "$out" --hfsplus "$hfsplus" --scenario "$scenario"
fi
exit "$qemu_status"
