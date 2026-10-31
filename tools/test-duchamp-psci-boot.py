#!/usr/bin/env python3
"""Test the fail-closed PSCI CPU_ON core natively and on ARM64 QEMU."""
import argparse,hashlib,json,re,subprocess
from pathlib import Path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output",type=Path)
    args=parser.parse_args()
    output=args.output.resolve();output.mkdir(parents=True,exist_ok=False)
    repo=Path(__file__).resolve().parent.parent;drivers=repo/"duchamp/drivers"
    test=drivers/"test_duchamp_psci_boot.c"
    start=drivers/"test_mt6897_model_start.S"
    runtime=drivers/"test_mt6897_model_runtime.c"
    paths=[test,start,runtime,drivers/"duchamp_psci_boot.h",Path(__file__).resolve()]
    before={str(path.relative_to(repo)):sha(path) for path in paths}
    commands=[]
    def run(command,**kwargs):
        commands.append(command)
        (output/"commands.json").write_text(json.dumps(commands,indent=2)+"\n")
        try:
            return subprocess.run(command,capture_output=True,text=True,check=True,**kwargs)
        except (subprocess.CalledProcessError,subprocess.TimeoutExpired) as error:
            text=lambda value:value.decode(errors="replace") if isinstance(value,bytes) else value or ""
            (output/"failure.log").write_text(text(error.stdout)+text(error.stderr))
            raise
    native=output/"native"
    run(["clang","-std=c11","-Wall","-Wextra","-Werror","-O1","-g",
         "-fsanitize=address,undefined","-fno-sanitize-recover=all",str(test),"-o",str(native)])
    result=run([str(native)]);(output/"native.log").write_text(result.stdout+result.stderr)
    match=re.fullmatch(r"(\d+) bounded PSCI CPU_ON checks passed\n",result.stdout)
    if not match or result.stderr:
        raise ValueError("native PSCI checks failed")
    linker=output/"test.ld"
    linker.write_text("ENTRY(_start)\nSECTIONS { . = 0x40200000; .text : { *(.text.boot) *(.text*) }\n"
        ".rodata : { *(.rodata*) } .data : { *(.data*) } . = ALIGN(4096);\n"
        ".bss (NOLOAD) : { _bss_start = .; *(.bss*) *(COMMON) . = ALIGN(16); _bss_end = .; }\n"
        ". += 0x40000; _stack_top = .; }\n")
    elf=output/"test.elf"
    run(["clang","-target","aarch64-none-elf","-std=c11","-O2","-ffreestanding",
         "-fno-builtin","-mgeneral-regs-only","-mstrict-align","-Wall","-Wextra","-Werror",
         "-DMT6897_MODEL_FREESTANDING","-nostdlib","-fuse-ld=lld","-Wl,-T,"+str(linker),
         str(test),str(start),str(runtime),"-o",str(elf)])
    arm=run(["qemu-system-aarch64","-M","virt,gic-version=3","-cpu","cortex-a76",
             "-m","64M","-nographic","-monitor","none","-nic","none",
             "-semihosting-config","enable=on,target=native","-kernel",str(elf)],timeout=30)
    (output/"qemu.log").write_text(arm.stdout+arm.stderr)
    if result.stdout not in arm.stdout or "MT6897 ARM64 MODEL PASS" not in arm.stdout:
        raise ValueError("ARM64 PSCI model failed")
    if before!={str(path.relative_to(repo)):sha(path) for path in paths}:
        raise ValueError("test sources changed")
    report={"passed":True,"native_checks":int(match[1]),"arm64_checks":int(match[1]),
        "elf_sha256":sha(elf),"source_sha256":before,
        "physical_psci_authorized":False,"smc_executed":False,
        "scope":"callback model only; no installed firmware, phone, SMC or physical CPU start"}
    (output/"result.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))


if __name__=="__main__":
    main()
