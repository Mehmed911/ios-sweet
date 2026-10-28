#!/usr/bin/env python3
"""Make the Duchamp BSD checkpoint patch dxb's mandatory final patch."""

from pathlib import Path
import sys


path = Path(sys.argv[1])
source = path.read_text()
needle = '''        done
        cd "${WORK_DIR}"
    fi
}
'''
replacement = '''        done
        if ! grep -Fq 'PRE UFS BACKEND' "${WORK_DIR}/xnu/iokit/bsddev/IOKitBSDInit.cpp"; then
            running "Applying mandatory semantic Duchamp BSD checkpoints"
            python3 "${WORK_DIR}/../tools/apply-duchamp-bsd-checkpoints.py" "${WORK_DIR}/xnu"
        fi
        cd "${WORK_DIR}"
    fi
}
'''

if source.count(needle) != 1:
    raise SystemExit("unexpected dxb patch-loop layout")

path.write_text(source.replace(needle, replacement))
