#!/bin/sh
set -eu

if [ "$#" -ne 1 ]; then
    echo "usage: build-sweet-userland.sh OUTDIR" >&2
    exit 2
fi

src=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
out=$1
mkdir -p "$out"
out=$(CDPATH= cd -- "$out" && pwd)

clang -target arm64-apple-ios16.0 -c "$src/tools/sweet-worker.S" -o "$out/worker.o"
python3 "$src/tools/mkinit.py" "$out/worker.o" "$out/sweet-worker.macho"
# init reconstructs the worker from its first 4K, three zero pages, and its
# signature. Refuse a worker that has grown into the omitted region.
python3 - "$out/sweet-worker.macho" <<'PY'
from pathlib import Path
import sys
data = Path(sys.argv[1]).read_bytes()
assert data[4096:16384] == bytes(12288), 'worker exceeds embedded 4K header/code'
PY
(cd "$out" && clang -target arm64-apple-ios16.0 -c "$src/tools/sweet-init.S" -o init.o)
python3 "$src/tools/mkinit.py" "$out/init.o" "$out/launchd"

echo "launchd=$out/launchd"
echo "worker=$out/sweet-worker.macho"
