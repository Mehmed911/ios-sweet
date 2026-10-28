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
        DUCHAMP_FINAL_PATCH="${PATCH_DIR}/zzzz-duchamp-bsd-pre-root-stage.patch"
        if ! grep -Fq 'DUCHAMP PRE ROOT SETCONF' "${WORK_DIR}/xnu/bsd/kern/bsd_init.c"; then
            running "Applying mandatory final Duchamp patch: ${DUCHAMP_FINAL_PATCH}"
            git apply --check "${DUCHAMP_FINAL_PATCH}"
            git apply "${DUCHAMP_FINAL_PATCH}"
        fi
        cd "${WORK_DIR}"
    fi
}
'''

if source.count(needle) != 1:
    raise SystemExit("unexpected dxb patch-loop layout")

path.write_text(source.replace(needle, replacement))
