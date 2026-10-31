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
        if ! grep -Fq 'QEMU RAM BLOCK READY' "${WORK_DIR}/xnu/iokit/bsddev/IOKitBSDInit.cpp"; then
            running "Applying mandatory semantic Duchamp BSD checkpoints"
            python3 "${WORK_DIR}/../tools/apply-duchamp-bsd-checkpoints.py" "${WORK_DIR}/xnu"
        fi
        if ! grep -Fq 'INIT EXEC ACCEPTED' "${WORK_DIR}/xnu/bsd/kern/kern_exec.c"; then
            running "Applying Duchamp process-1 exec checkpoints"
            python3 "${WORK_DIR}/../tools/apply-duchamp-init-exec-checkpoints.py" "${WORK_DIR}/xnu"
        fi
        if ! grep -Fq 'PID1 CONSOLE OPEN OK' "${WORK_DIR}/xnu/bsd/vfs/vfs_syscalls.c"; then
            running "Applying Duchamp PID 1 syscall checkpoints"
            python3 "${WORK_DIR}/../tools/apply-duchamp-pid1-syscall-checkpoints.py" "${WORK_DIR}/xnu"
        fi
        if ! grep -Fq 'DEVFS CONSOLE READY' "${WORK_DIR}/xnu/bsd/kern/bsd_init.c"; then
            running "Applying Duchamp RAM-root devfs console setup"
            python3 "${WORK_DIR}/../tools/apply-duchamp-devfs-console.py" "${WORK_DIR}/xnu"
        fi
        if ! grep -Fq 'SWEET USERSPACE PID1 RUNNING' "${WORK_DIR}/xnu/bsd/dev/arm/systemcalls.c"; then
            running "Applying Duchamp PID 1 console write checkpoints"
            python3 "${WORK_DIR}/../tools/apply-duchamp-pid1-write-checkpoints.py" "${WORK_DIR}/xnu"
        fi
        if ! grep -Fq 'PID1 HEARTBEAT RETURNED' "${WORK_DIR}/xnu/bsd/dev/arm/systemcalls.c"; then
            running "Applying Duchamp PID 1 heartbeat and console framebuffer support"
            python3 "${WORK_DIR}/../tools/apply-duchamp-pid1-heartbeat-console.py" "${WORK_DIR}/xnu"
        fi
        running "Staging opt-in Duchamp QEMU UFS read transport"
        python3 "${WORK_DIR}/../tools/stage-duchamp-qemu-ufs.py" "${WORK_DIR}/xnu"
        running "Staging opt-in Duchamp QEMU backend/table selftest"
        python3 "${WORK_DIR}/../tools/stage-duchamp-qemu-backends.py" "${WORK_DIR}/xnu"
        running "Staging bounded Duchamp GIC redistributor discovery and wake"
        python3 "${WORK_DIR}/../tools/stage-duchamp-gic-boot.py" "${WORK_DIR}/xnu"
        cd "${WORK_DIR}"
    fi
}
'''

if source.count(needle) != 1:
    raise SystemExit("unexpected dxb patch-loop layout")

path.write_text(source.replace(needle, replacement))
