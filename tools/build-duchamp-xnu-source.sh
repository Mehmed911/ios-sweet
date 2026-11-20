#!/usr/bin/env bash
# Stage the dirty source locally and build it on a Mac without a Git upload.
set -euo pipefail

usage() {
    echo "Usage: $0 prepare PINNED_IIG_ZIP NEW_WORKSPACE | build WORKSPACE" >&2
    exit 2
}

snapshot_hashes() {
    python3 -B - "$1" <<'PY'
import hashlib
from pathlib import Path
import sys

workspace = Path(sys.argv[1])
inputs = [p for p in (workspace / 'source').rglob('*') if p.is_file()]
inputs.append(workspace / 'pinned-iig.zip')
for path in sorted(inputs):
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    print(f'{sha}  {path.relative_to(workspace).as_posix()}')
PY
}

case ${1:-} in
prepare)
    [ "$#" -eq 3 ] || usage
    repo=$(cd "$(dirname "$0")/.." && pwd -P)
    mkdir "$3"
    workspace=$(cd "$3" && pwd -P)
    mkdir -p "$workspace/source/duchamp" "$workspace/source/xnu"
    cp -R "$repo/tools" "$workspace/source/"
    cp -R "$repo/duchamp/drivers" "$repo/duchamp/xnu" "$workspace/source/duchamp/"
    cp -R "$repo/xnu/patches" "$workspace/source/xnu/"
    cp "$2" "$workspace/pinned-iig.zip"
    git -C "$repo" rev-parse HEAD > "$workspace/baseline-commit.txt"
    python3 -B "$workspace/source/tools/duchamp-frozen-iig.py" stage \
        --archive "$workspace/pinned-iig.zip" --out "$workspace/iig-validation" \
        > "$workspace/iig-validation.json"
    snapshot_hashes "$workspace" > "$workspace/source.sha256"
    ;;
build)
    [ "$#" -eq 2 ] || usage
    if [ "$(uname -s)" != Darwin ]; then
        echo 'This build recipe needs a Darwin host with Xcode 16.4. The prepared inputs can be used on that host.' >&2
        exit 1
    fi
    workspace=$(cd "$2" && pwd -P)
    snapshot_hashes "$workspace" | cmp "$workspace/source.sha256" -
    export DEVELOPER_DIR=${DEVELOPER_DIR:-/Applications/Xcode_16.4.app/Contents/Developer}
    export KDKROOT=${KDKROOT:-/Library/Developer/KDKs/KDK_13.5_22G74.kdk}
    for command in git python3 xcrun xcodebuild brew jq gum xcodes cmake ninja; do
        command -v "$command" >/dev/null || { echo "Missing build dependency $command" >&2; exit 1; }
    done
    xcodebuild -version | grep -Fx 'Xcode 16.4'
    test "$(xcrun --sdk macosx --show-sdk-version)" = 15.5
    test -d "$KDKROOT" || { echo "Missing KDK $KDKROOT" >&2; exit 1; }
    scratch=$(mktemp -d /tmp/duchamp-xnu-build.XXXXXXXX)
    mkdir "$workspace/result"
    cp -R "$workspace/source/." "$scratch/"
    # Re-stage from the pinned ZIP so the validated cache never depends on transferred generated files.
    export IIG="$scratch/tools/duchamp-frozen-iig.py"
    export DUCHAMP_IIG_CACHE="$scratch/iig"
    export MACOS_VERSION=13.5 KERNEL_CONFIG=DEVELOPMENT ARCH_CONFIG=ARM64 MACHINE_CONFIG=SWEET
    export DXB_REPO=https://github.com/blacktop/darwin-xnu-build DXB_SHA=663906528d1cd5ea8fde7de6f16de73db9511549
    chmod +x "$IIG"
    python3 -B "$IIG" stage --archive "$workspace/pinned-iig.zip" --out "$DUCHAMP_IIG_CACHE"
    (
        printf 'Scratch: %s\nKDK: %s\n' "$scratch" "$KDKROOT"
        sw_vers
        xcodebuild -version
        xcrun --sdk macosx --show-sdk-path
        xcrun clang --version
        xcrun ld -v
    ) > "$workspace/result/toolchain.txt" 2>&1
    bash "$scratch/tools/prepare-duchamp-xnu-dxb.sh"
    (
        cd "$scratch/dxb"
        printf '%s\n' "MACOS_VERSION=$MACOS_VERSION KERNEL_CONFIG=$KERNEL_CONFIG ARCH_CONFIG=$ARCH_CONFIG MACHINE_CONFIG=$MACHINE_CONFIG bash build.sh"
        bash build.sh
    ) 2>&1 | tee "$workspace/result/build.log"
    kernel="$scratch/dxb/fakeroot/System/Library/Kernels/kernel.development.sweet"
    target="$scratch/dxb/build/xnu.obj/DEVELOPMENT_ARM64_SWEET"
    result="$workspace/result"
    python3 -B "$scratch/tools/duchamp_xnu_link.py" "$kernel" > "$result/kernel-layout.json"
    cp "$kernel" "$result/"
    cp "$target/.LDFLAGS" "$result/xnu.LDFLAGS"
    cp "$target/link.filelist" "$target/all-alias.exp" "$target/symbolsets.plist" "$result/"
    git -C "$scratch/dxb" rev-parse HEAD > "$result/dxb-commit.txt"
    git -C "$scratch/dxb/xnu" rev-parse HEAD > "$result/xnu-commit.txt"
    (
        cd "$result"
        shasum -a 256 kernel.development.sweet kernel-layout.json toolchain.txt build.log xnu.LDFLAGS \
            link.filelist all-alias.exp symbolsets.plist dxb-commit.txt xnu-commit.txt
    ) > "$result/build.sha256"
    ;;
*) usage ;;
esac
