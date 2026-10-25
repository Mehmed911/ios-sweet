#!/bin/sh
set -eu

if [ "$#" -ne 1 ]; then
	echo "usage: $0 LIVE_FDT" >&2
	exit 2
fi

fdt=$1
[ -r "$fdt" ] || { echo "error: FDT is not readable: $fdt" >&2; exit 2; }

tmp=$(mktemp)
trap 'rm -f "$tmp"' EXIT
dtc -q -I dtb -O dts -o "$tmp" "$fdt"

grep -Fq 'model = "MT6897"' "$tmp" || { echo "error: MT6897 model is missing" >&2; exit 1; }
grep -Fq 'compatible = "arm,psci-1.0"' "$tmp" || { echo "error: PSCI 1.0 node is missing" >&2; exit 1; }
grep -Fq 'method = "smc"' "$tmp" || { echo "error: PSCI SMC method is missing" >&2; exit 1; }
grep -Fq 'compatible = "arm,gic-v3"' "$tmp" || { echo "error: GICv3 node is missing" >&2; exit 1; }
grep -Fq 'compatible = "mediatek,mt6897-timer"' "$tmp" || { echo "error: MT6897 timer node is missing" >&2; exit 1; }

echo "duchamp live FDT preflight: PASS"
