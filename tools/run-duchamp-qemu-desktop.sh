#!/bin/sh
set -eu

port=$1
run=$2
case "$run" in
    setup-run-desktop-*) ;;
    *) echo 'Expected a desktop run name.' >&2; exit 2 ;;
esac
case "$run" in
    *[!a-zA-Z0-9-]*) echo 'Invalid desktop run name.' >&2; exit 2 ;;
esac

base="$HOME/.cache/duchamp-qemu-tests/quartzcore-replay-v1"
scratch="$base/setup-session-tmpfs"
[ "$(findmnt -n -o FSTYPE -T "$scratch")" = tmpfs ]
if [ "$#" -eq 4 ]; then
    exec 9>"$scratch/windows-desktop-launch.lock"
else
    exec 9>"$scratch/desktop-launch.lock"
fi
flock -n 9

# Reclaim only our own RAM backing files after the corresponding VM ended.
for previous in "$scratch"/setup-run-desktop-*; do
    if [ -f "$previous/result.json" ] && [ -f "$previous.bin" ] && [ ! -L "$previous.bin" ]; then
        rm -- "$previous.bin"
    fi
done
release_ram() {
    if [ -f "$scratch/$run/result.json" ] && [ -f "$scratch/$run.bin" ] && [ ! -L "$scratch/$run.bin" ]; then
        rm -- "$scratch/$run.bin"
    fi
}
trap release_ram EXIT

export SWEET_QEMU_SETUP_TRACE=1 SWEET_QEMU_SETUP_SESSION=1 SWEET_QEMU_SETUP_WITHOUT_PROXIMITY=1
export SWEET_QEMU_SOFTWARE_RENDERER=1 SWEET_QEMU_SETUP_SOFTWARE_SCANOUT=1
export SWEET_QEMU_SETUP_SWIPE=1 SWEET_QEMU_SETUP_REGION=1 SWEET_QEMU_SETUP_INTERACTIVE=1
export SWEET_QEMU_SETUP_FONTS="$base/setup-fonts-20F66-v2"
export SWEET_QEMU_SETUP_HID_PLUGIN="$base/setup-hid-plugin-20F66"
export SWEET_QEMU_SETUP_HFS_SLICE="$base/setup-hfs-write-slice.so"
export SWEET_QEMU_SETUP_HFSPLUS="$base/setup-hfs-build/hfs/hfsplus"
if [ "$#" -eq 4 ]; then
    exec python3 tools/duchamp-qemu-display.py --native-windows --port "$port" "$scratch/$run" \
        python3 -u tools/duchamp-qemu-windows.py --linux "$base" "$scratch/$run" "$3" "$4"
fi
python3 tools/duchamp-qemu-display.py --port "$port" "$scratch/$run" \
    python3 -u work/run-setup-watchdog-replay.py "$base/setup-run-v6" \
    "$base/setup-root-watchdog-v1" "$scratch/$run" "$scratch" 3600
