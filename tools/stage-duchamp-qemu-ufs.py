#!/usr/bin/env python3
"""Stage the portable read core and the opt-in QEMU BSD adapter into XNU."""
import argparse
import hashlib
import json
from pathlib import Path


def replace_once(text,old,new,label):
    if text.count(old)!=1:
        raise ValueError(f'{label}: expected exactly one source anchor')
    return text.replace(old,new,1)


def stage(root):
    repo=Path(__file__).resolve().parent.parent
    paths={
        'bsd/dev/ufs_readonly.h':repo/'duchamp/drivers/ufs_readonly.h',
        'bsd/dev/duchamp_ufs_core.c':repo/'duchamp/drivers/ufs_readonly.c',
        'bsd/dev/ufs_gpt.h':repo/'duchamp/drivers/ufs_gpt.h',
        'bsd/dev/duchamp_ufs_gpt.c':repo/'duchamp/drivers/ufs_gpt.c',
        'bsd/dev/duchamp_qemu_ufs.c':repo/'duchamp/xnu/qemu_ufs.c',
        'bsd/dev/duchamp_qemu_ufs_handoff.c':repo/'duchamp/xnu/qemu_ufs_handoff.c',
        'bsd/dev/duchamp_qemu_ufs_mcq.c':repo/'duchamp/xnu/qemu_ufs_mcq.c',
    }
    config=root/'bsd/conf/files'
    iokit=root/'iokit/bsddev/IOKitBSDInit.cpp'
    arm_init=root/'osfmk/arm/arm_init.c'
    original_config=config.read_text(); original_iokit=iokit.read_text()
    original_arm=arm_init.read_text()
    entry_call='duchamp_qemu_ufs_handoff_enter();'
    def arm_hook(text, anchor, call):
        symbol=call.split('(')[0]
        return replace_once(text, anchor,
            anchor + '\n#if defined(DUCHAMP)\n\textern void ' + symbol +
            '(void);\n\t' + call + '\n#endif', symbol)
    marker='DUCHAMP QUFS ROOT SELECTED'
    additions=('bsd/dev/duchamp_ufs_core.c\t\tstandard\n'
               'bsd/dev/duchamp_ufs_gpt.c\t\tstandard\n'
               'bsd/dev/duchamp_qemu_ufs.c\t\tstandard\n'
               'bsd/dev/duchamp_qemu_ufs_handoff.c\t\tstandard\n'
               'bsd/dev/duchamp_qemu_ufs_mcq.c\t\tstandard\n')
    hashes={name:hashlib.sha256(source.read_bytes()).hexdigest() for name,source in paths.items()}
    if marker in original_iokit:
        if (additions not in original_config or original_arm.count(entry_call)!=1 or
                any(not (root/name).is_file() or
                (root/name).read_bytes()!=source.read_bytes() for name,source in paths.items())):
            raise ValueError('partial or changed existing QEMU UFS integration')
        return {'already_staged':True,'files':hashes}
    if 'QEMU RAM BLOCK READY' not in original_iokit or 'MT6897 BACKEND STUB' not in original_iokit:
        raise ValueError('apply the established Duchamp BSD root checkpoints first')
    if any((root/name).exists() for name in paths):
        raise ValueError('refusing to overwrite pre-existing adapter source')
    anchor='bsd/dev/sweet_ufs.c\t\t\tstandard\n'
    new_config=replace_once(original_config,anchor,anchor+additions,'BSD source list')
    anchor='\tif (strcmp(rdBootVar, "ufsroot0") == 0) {'
    branch='''#if defined(DUCHAMP)
\tif (strcmp(rdBootVar, "qufs0") == 0) {
\t\textern int duchamp_qemu_ufs_rootdev(dev_t *dev);
\t\tOSSafeReleaseNULL(matching);
\t\tint qufs_error = duchamp_qemu_ufs_rootdev(root);
\t\tif (qufs_error) {
\t\t\tpanic("DUCHAMP QUFS root unavailable: %d", qufs_error);
\t\t}
\t\tstrlcpy(rootName, "qufs0", rootNameSize);
\t\t*oflags = 0;
\t\tIOLog("DUCHAMP QUFS ROOT SELECTED major=%d minor=%d\\n", major(*root), minor(*root));
\t\tgoto iofrootx;
\t}
#endif
'''
    new_iokit=replace_once(original_iokit,anchor,branch+anchor,'opt-in root selector')
    new_arm=arm_hook(original_arm, '\tPE_init_platform(FALSE, args); /* Get platform expert set up */',
                     entry_call)
    # Validate every anchor before writing; no edits to the legacy UFS driver.
    for name,source in paths.items():
        (root/name).write_bytes(source.read_bytes())
    config.write_text(new_config); iokit.write_text(new_iokit); arm_init.write_text(new_arm)
    return {'already_staged':False,'files':hashes}


def main():
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument('xnu',type=Path)
    args=ap.parse_args()
    try:
        print(json.dumps(stage(args.xnu.resolve()),indent=2))
    except (OSError,ValueError) as e:
        ap.exit(1,f'QEMU UFS staging failed: {e}\n')


if __name__=='__main__':
    main()
