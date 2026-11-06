#!/bin/sh
# Reuse the phone-proven kernel for the saved notifyd/syslogd RAM-root batch.
set -eu
if [ "$#" -ne 1 ]; then
    echo "usage: $0 NEW-OUTPUT-DIRECTORY" >&2
    exit 2
fi
out=$(readlink -m "$1")
repo=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$repo"
if [ -e "$out" ]; then
    echo "preserve existing output: $out" >&2
    exit 2
fi

pin() {
    actual=$(sha256sum "$1" | cut -d ' ' -f 1)
    if [ "$actual" != "$2" ]; then
        echo "input SHA-256 mismatch: $1" >&2
        exit 1
    fi
}
kernel=work/ci-41543710742-kernel/artifact/kernel.development.sweet
qemu_adt=research/mt6897-boot/bsd-service-split-ci41543710742-qemu-authorized.adt
phone_adt=research/mt6897-live-phone-gic-trial-v1/boot.adt
fixture=work/launchctl-notifyd-v3
hfsplus=research/libdmg-hfsplus-build/hfsplus
pin "$kernel" e465723a540844817a5b9cb36c14984d660f9a8e41f6638240527b469189182b
pin "$qemu_adt" a881410d04a3cec3b7ebd9bee91f510c755683b94f5a26d71c47301fff7417d8
pin "$phone_adt" 6ae3d3c054676a78d33c02ff89c6d19b6e851df63c74e973e599dd04aaa541c0
pin "$hfsplus" be041fa07ae8cbe040a2ec3811241af993eea597e8d46917f6c32359b2cd8b1b
pin "$fixture/root.hfs" 3e800f071990192fefd69684477618532c85ab85accbd74f750a51c2f70e6baf
pin "$fixture/launchctl-root-manifest.json" 352289bc48c649c62e888cf1dac9f7bef6a6a491ec1f25b93ee73a928d57c8f7
pin "$fixture/runtime-audit.json" 4b8590888b0b88e6d1cd8873f02f51695441f60f9e9b97f7fc00bd0de79668d8
pin "$fixture/sweet-launchd-service" d75e313663319e78e301954ece5698e8fc2c4f7527b8324494a9c82ff0003267
pin "$fixture/sweet-ipc-client" 4c75ae7555275a5cc7a906c408cb6944451979aafab3bdd56f62f0ef38555f7f
pin "$fixture/sweet-launchctl-control" f364f0dee8bef980589bdff407e35d7bb77e134248234967f9c7519513d23b28

mkdir -p "$out"
task_runtime=$(mktemp -d /tmp/duchamp-services-proof-XXXXXX)
# Keep allocation, execution and export in one Linux process: /tmp may be
# cleared when an otherwise idle WSL instance shuts down between invocations.
export_evidence() {
    mkdir -p "$out/qemu-proof"
    cp -a "$task_runtime/." "$out/qemu-proof/"
}
trap export_evidence EXIT
cp "$kernel" "$task_runtime/kernel"
cp "$qemu_adt" "$task_runtime/qemu.adt"
cp "$phone_adt" "$task_runtime/phone.adt"
cp "$hfsplus" "$task_runtime/hfsplus"
cp "$fixture/root.hfs" "$fixture/launchctl-root-manifest.json" \
    "$fixture/runtime-audit.json" "$fixture/sweet-launchd-service" \
    "$fixture/sweet-ipc-client" "$fixture/sweet-launchctl-control" \
    "$task_runtime/"
cmdline='debug=0xc serial=3 cpus=1 keepsyms=1 -enable_kprintf_spam -noprogress rd=md0 rootrw=1 sweet_console_fb=1 duchamp_timer_irq_ack=1 unentitled_ios_sim_launch=1 launchdsuffix=sweet launchd_log_serial=1'
echo 'duchamp-services-batch: phase=build-qemu-payload phone-access=false'
python3 tools/mkpayload.py "$task_runtime/kernel" "$task_runtime/qemu.adt" \
    "$task_runtime/payload.bin" --ramdisk "$task_runtime/root.hfs" \
    --cmdline "$cmdline" > "$task_runtime/payload-build.log"
echo 'duchamp-services-batch: phase=run-qemu'
if ! python3 tools/qemu-sweet.py "$task_runtime/payload.bin" \
    "$task_runtime/run" --secs 900 --framebuffer duchamp \
    --kernel "$task_runtime/kernel" --snapshot-interval 5 \
    --save-ramdisk --fail-on-panic \
    --stop-on-text 'SWEET EARLY PANIC:' \
    --stop-on-text 'SWEET launchctl: FAIL' \
    --stop-on-text 'SWEET launchctl: heartbeat=2 ' \
    --stop-on-text 'SWEET ipc asl1: FAIL' \
    --stop-on-text 'SWEET ipc asl2: FAIL' \
    --stop-on-text 'Library not loaded:' --stop-on-text 'Symbol not found:' \
    --stop-on-text 'BUG IN LIBNOTIFY:' \
    --stop-on-text 'bootstrap_check_in failed' \
    > "$task_runtime/runner.log" 2>&1; then
    cat "$task_runtime/runner.log" >&2
    exit 1
fi
echo 'duchamp-services-batch: phase=verify-saved-guest'
if ! python3 tools/verify-sweet-syslogd.py "$task_runtime" \
    --hfsplus "$task_runtime/hfsplus" --notifyd \
    > "$task_runtime/verifier.log" 2>&1; then
    cat "$task_runtime/verifier.log" >&2
    exit 1
fi
python3 -c 'import json,sys; r=json.load(open(sys.argv[1])); assert r["passed"] and len(r["checks"]) == 74 and all(r["checks"].values()); print("duchamp-services-batch: PASS checks=74 elapsed_host_seconds=" + str(r["elapsed_host_seconds"]))' \
    "$task_runtime/run/verification.json"
python3 tools/mkpayload.py "$task_runtime/kernel" "$task_runtime/phone.adt" \
    "$out/payload-phone.bin" --ramdisk "$task_runtime/root.hfs" \
    --cmdline "$cmdline" > "$out/phone-payload-build.log"
cp "$task_runtime/payload.bin" "$out/payload-qemu.bin"
sha256sum "$kernel" "$phone_adt" "$qemu_adt" "$fixture/root.hfs" \
    "$out/payload-phone.bin" "$out/payload-qemu.bin" \
    > "$out/SHA256SUMS"
