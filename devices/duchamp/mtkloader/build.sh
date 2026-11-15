#!/bin/sh
# Offline adapter, matching the reference script name. Existing entry remains
# canonical; no MT6768 addresses, firmware, flash or reboot scripts are used.
set -eu
here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
repo=$(CDPATH= cd -- "$here/../../.." && pwd)
if [ "${DUCHAMP_TARGET:-}" != qemu ]; then
    echo 'DUCHAMP_TARGET=qemu required; physical Android fallback is not validated' >&2
    exit 2
fi
: "${SHIM_OUT:?choose a new offline output directory}"
if [ -e "$SHIM_OUT" ]; then
    echo 'refusing existing output directory' >&2
    exit 2
fi
QEMU_ONLY=1 BOOT_MENU=1 sh "$repo/duchamp/bootshim/build.sh"
