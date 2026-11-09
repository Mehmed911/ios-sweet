#!/usr/bin/env python3
"""Inspect Duchamp's stock SPI2 binding, optionally read two FocalTech ID registers."""
import argparse
from pathlib import Path
import shutil
import subprocess

# Stream the device code through stdin. The default mode only inspects state.
PROBE = r"""
export LC_ALL=C
fail() { echo "Duchamp SPI2: $*" >&2; exit 1; }
hex() { od -An -v -tx1 "$1" | tr -d ' \n'; }
expect_hex() {
    [ -r "$1" ] && [ "$(hex "$1")" = "$2" ] || fail "unexpected or unreadable $1"
}

[ "$(id -u)" = 0 ] || fail "root is required for stock driver evidence"
[ "$(getprop ro.product.device)" = duchamp ] &&
    [ "$(getprop ro.boot.hardware)" = mt6897 ] || fail "wrong device or SoC"
tree=/sys/firmware/devicetree/base
dt="$tree/soc/spi2@11012000"
pin="$tree/soc/pinctrl@10005000"
vtp="$tree/soc/spmi@1cc04000/second_pmic@5/regulators/vtp"
touch="$dt/xiaomi_touch@0"
expect_hex "$dt/compatible" 6d6564696174656b2c6d74363938352d73706900
expect_hex "$dt/reg" 00000000110120000000000000000100
expect_hex "$dt/clocks" 000000690000008c00000069000000480000001b0000000e
expect_hex "$touch/compatible" 7869616f6d692c746f7563682d73706900666f63616c746563682c6e3131612d33363833672d73706900
expect_hex "$touch/reg" 00000000
expect_hex "$touch/spi-max-frequency" 00e4e1c0
expect_hex "$touch/focaltech,reset-gpio" 000000200000003c00000000
expect_hex "$touch/focaltech,irq-gpio" 000000200000000900002008
expect_hex "$touch/goodix,avdd-gpio" 000000200000004900000000
expect_hex "$touch/iovdd-supply" 000002a2
expect_hex "$tree/syscon@10000000/phandle" 00000069
expect_hex "$tree/syscon@11036000/phandle" 0000001b
expect_hex "$pin/phandle" 00000020
expect_hex "$touch/pinctrl-2" 0000039e
expect_hex "$pin/ts_spimode/phandle" 0000039e
expect_hex "$pin/ts_spimode/pins_cmd_dat/pinmux" 00000d0100000c0100000e0100000b01
expect_hex "$vtp/phandle" 000002a2
expect_hex "$vtp/regulator-min-microvolt" 001b7740
expect_hex "$vtp/regulator-max-microvolt" 001b7740

dev=
for candidate in /sys/bus/spi/devices/spi*; do
    [ -L "$candidate/of_node" ] || continue
    [ "$(readlink -f "$candidate/of_node")" = "$touch" ] || continue
    [ -z "$dev" ] || fail "multiple Linux SPI devices match the touch node"
    dev=$(readlink -f "$candidate") || fail "cannot resolve touch device"
done
[ -n "$dev" ] || fail "touch node is not enumerated by the running kernel"
[ "$(readlink -f "$dev/driver")" = /sys/bus/spi/drivers/focaltech_ts ] ||
    fail "FocalTech is not the bound touch driver"
[ "$(readlink -f "$dev/driver/module")" = /sys/module/focaltech_touch ] ||
    fail "unexpected touch module owner"

host=${dev%/*}
while [ "$host" != /sys/devices ]; do
    case "$host" in /sys/devices/*) ;; *) fail "unexpected SPI device path";; esac
    if [ -L "$host/driver" ] && [ -L "$host/of_node" ] &&
       [ "$(readlink -f "$host/of_node")" = "$dt" ]; then
        break
    fi
    host=${host%/*}
done
[ "$host" != /sys/devices ] || fail "cannot resolve the SPI2 platform controller"
[ "$(readlink -f "$host/driver")" = /sys/bus/platform/drivers/mtk-spi ] &&
    [ "$(readlink -f "$host/driver/module")" = /sys/module/spi_mt65xx ] ||
    fail "unexpected SPI2 controller owner"

# Verify the loaded modules' ELF notes, rather than a copy on disk.
note=040000001400000003000000474e5500
expect_hex /sys/module/focaltech_touch/notes/.note.gnu.build-id \
    "${note}ee8087174b06587905ce285014b589105a892a85"
expect_hex /sys/module/spi_mt65xx/notes/.note.gnu.build-id \
    "${note}0e21c14365b22d56c7edfc0aed0a4423f6d72783"

echo "bound SPI2 controller: $host"
echo "bound FocalTech device: $dev"
if [ -r "$dev/fts_boot_mode" ]; then
    printf 'FocalTech software debug flag: '
    cat "$dev/fts_boot_mode"
fi
if [ -r "$dev/fts_driver_info" ]; then
    echo "FocalTech driver state (IC ID is cached):"
    cat "$dev/fts_driver_info"
fi
for rail in /sys/class/regulator/regulator.*; do
    [ -r "$rail/name" ] && [ "$(cat "$rail/name")" = mt6368_vtp ] || continue
    for attr in state microvolts num_users; do
        if [ -r "$rail/$attr" ]; then
            printf 'MT6368 VTP %s: ' "$attr"
            cat "$rail/$attr"
        fi
    done
done
if [ -r "$host/power/runtime_status" ]; then
    printf 'SPI2 runtime PM: '
    cat "$host/power/runtime_status"
fi

snapshot() {
    if [ -r "$1" ]; then
        grep -E "$2" "$1" || echo "no matching entries in $1"
    else
        echo "unavailable: $1"
    fi
}
debug=/sys/kernel/debug
snapshot "$debug/clk/clk_summary" '(^|[[:space:]])(univpll_d6_d2|spi2_sel|spi2_ck|peraop_spi2_bclk)([[:space:]]|$)'
snapshot "$debug/regulator/regulator_summary" '(^|[[:space:]])mt6368_vtp([[:space:]]|$)'
snapshot "$debug/gpio" 'fts_(avdd|reset|irq)_gpio'
snapshot /proc/mtk_gpio/soc.pinctrl '^pins base|^PIN:|^[[:space:]]*(009|011|012|013|014|060|073):'
snapshot /proc/interrupts '(^|[[:space:]])focaltech_ts([[:space:]]|$)'
for pins in "$debug"/pinctrl/*10005000*/pinmux-pins; do
    snapshot "$pins" '^pin (9|11|12|13|14|60|73) '
done

[ "$PROBE_MODE" = read-id ] || exit 0
dumpsys power | grep -E '^[[:space:]]*mWakefulness=Awake[[:space:]]*$' >/dev/null ||
    fail "Android is not awake"
# fts_boot_mode reflects a debug flag. The version attribute reads A6 over SPI
# with status and CRC validation, and rejects 00 and FF.
version=$(cat "$dev/fts_fw_version") || fail "cannot read the touch firmware version"
case "$version" in
    00|[Ff][Ff]) fail "invalid touch firmware version" ;;
    [0-9A-Fa-f][0-9A-Fa-f]) echo "fresh FocalTech firmware version: 0x$version" ;;
    *) fail "invalid touch firmware version" ;;
esac
reg="$dev/fts_wr_reg"
[ -f "$reg" ] && [ ! -L "$reg" ] && [ -r "$reg" ] && [ -w "$reg" ] ||
    fail "stock FocalTech register endpoint is unavailable"

read_id_byte() {
    # The shipped handler requires the explicit read prefix and one-byte
    # length. Reblock the request into one sysfs write, including the newline.
    case "$1" in A3|9F) ;; *) fail "invalid ID register" ;; esac
    printf '1%s01\n' "$1" | dd ibs=1 obs=6 count=6 status=none > "$reg" ||
        fail "could not request $1"
    reply=$(cat "$reg") || fail "could not read the result for $1"
    case "$reply" in
        "Read $1: "[0-9A-F][0-9A-F]) printf '%s\n' "${reply##* }" ;;
        *) fail "failed or stale result for $1" ;;
    esac
}
high=$(read_id_byte A3) || exit 1
low=$(read_id_byte 9F) || exit 1
echo "fresh application-mode chip ID: 0x$high$low (A3=$high, 9F=$low)"
[ "$high$low" = 5672 ] || fail "ID differs from the pinned FT3683G driver table"
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--adb", type=Path, help="path to the platform-tools adb executable")
    parser.add_argument("--serial", help="ADB device selector when multiple devices are connected")
    parser.add_argument("--read-id", action="store_true", help="request fresh A3 and 9F reads after preflight")
    args = parser.parse_args()
    adb = str(args.adb.resolve()) if args.adb else shutil.which("adb")
    if not adb:
        parser.error("adb was not found, use --adb")
    mode = "read-id" if args.read_id else "preflight"
    target = ["-s", args.serial] if args.serial else []
    command = [adb, *target, "shell", "-T", "su -c 'timeout -k 2 20 sh -s'"]
    try:
        return subprocess.run(command, input=f"PROBE_MODE={mode}\n{PROBE}".encode("ascii"), timeout=30).returncode
    except (OSError, subprocess.TimeoutExpired) as error:
        parser.exit(1, f"Duchamp SPI2: {error}\n")


if __name__ == "__main__":
    raise SystemExit(main())
