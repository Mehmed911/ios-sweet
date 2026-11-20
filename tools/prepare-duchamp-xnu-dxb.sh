#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
repo=${DXB_REPO:-https://github.com/blacktop/darwin-xnu-build}
revision=${DXB_SHA:-663906528d1cd5ea8fde7de6f16de73db9511549}
mkdir dxb
git -C dxb init -q
git -C dxb fetch -q --depth 1 "$repo" "$revision"
git -C dxb checkout -q FETCH_HEAD
test "$(git -C dxb rev-parse HEAD)" = "$revision"
cp xnu/patches/*.patch xnu/patches/*.sh dxb/patches/
mv dxb/patches/0208-duchamp-bsd-pre-root-stage.patch dxb/patches/zzzz-duchamp-bsd-pre-root-stage.patch
python3 tools/force-dxb-final-patch.py dxb/build.sh

# SWEET uses plain arm64. Build that slice of libfirehose_kernel as well.
python3 - dxb/build.sh <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
source = path.read_text()
before = 'ARCHS="x86_64 arm64e" VALID_ARCHS="x86_64 arm64e"'
after = 'ARCHS="x86_64 arm64e arm64" VALID_ARCHS="x86_64 arm64e arm64"'
if source.count(before) != 1:
    raise SystemExit('Unexpected dxb libfirehose_kernel architecture flags')
path.write_text(source.replace(before, after))
PY
