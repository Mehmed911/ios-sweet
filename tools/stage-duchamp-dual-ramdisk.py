#!/usr/bin/env python3
"""Stage the Duchamp memory devices after the common XNU patches."""

import argparse
from pathlib import Path


def replace(source, before, after):
    if source.count(before) != 1:
        raise ValueError(f'unexpected XNU source near {before.splitlines()[0]!r}')
    return source.replace(before, after, 1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('xnu', type=Path)
    args = parser.parse_args()
    src = Path(__file__).resolve().parents[1] / 'duchamp/xnu'
    memdev = args.xnu / 'bsd/dev/memdev.c'
    root = args.xnu / 'iokit/bsddev/IOKitBSDInit.cpp'
    memdev_text, root_text = memdev.read_text(), root.read_text()
    include = '#include "duchamp_dual_ramdisk_init.inc"'
    hook = 'dual_registered = duchamp_dual_ramdisk_init(rdBootVar);'
    if (include in memdev_text) != (hook in root_text):
        raise ValueError('partially staged dual RAMDisk source')

    if include not in memdev_text:
        memdev_text = replace(memdev_text, '\tif (uio->uio_offset < 0) {', '''
\tif ((mdev[devid].mdFlags & mdRO) && uio_rw(uio) == UIO_WRITE) {
\t\treturn EROFS;
\t}
\tif (uio->uio_offset < 0) {'''.lstrip('\n'))
        memdev_text = replace(memdev_text, '\n\tblkoff = buf_blkno(bp)', '''
\tif ((mdev[devid].mdFlags & mdRO) && !(buf_flags(bp) & B_READ)) {
\t\tbuf_seterror(bp, EROFS);
\t\tbuf_biodone(bp);
\t\treturn;
\t}

\tblkoff = buf_blkno(bp)''')
        memdev_text = replace(memdev_text, 'case DKIOCISWRITABLE:\n\t\t*f = 1;',
                              'case DKIOCISWRITABLE:\n\t\t*f = !(mdev[devid].mdFlags & mdRO);')
        memdev_text = replace(memdev_text, 'dev_t\nmdevadd(int devid, uint64_t base, unsigned int size, int phys)',
                              'static dev_t\nmdevadd_with_flags(int devid, uint64_t base, unsigned int size, int flags)')
        memdev_text = replace(memdev_text, '\tif (phys) {\n'
                              '\t\tmdev[devid].mdFlags |= mdPhys;'
                              '                          /* Show that we are in physical memory */\n\t}',
                              '\tmdev[devid].mdFlags = flags;')
        memdev_text = replace(memdev_text, 'dev_t\nmdevlookup(int devid)', '''dev_t
mdevadd(int devid, uint64_t base, unsigned int size, int phys)
{
\treturn mdevadd_with_flags(devid, base, size, phys ? mdPhys : 0);
}

dev_t
mdevlookup(int devid)''')
        memdev_text = memdev_text.rstrip() + '\n\n' + include + '\n'
        root_text = replace(root_text, 'static int didRam = 0;', '''#if defined(ARM64_BOARD_CONFIG_SWEET)
extern "C" int duchamp_dual_ramdisk_init(const char *root_name);
#endif
static int didRam = 0;''')
        root_text = replace(root_text, '\t\tif ((regEntry = IORegistryEntry::fromPath( "/chosen/memory-map", gIODTPlane ))) {',
                            '''\t\tbool dual_registered = false;
#if defined(ARM64_BOARD_CONFIG_SWEET)
\t\tdual_registered = duchamp_dual_ramdisk_init(rdBootVar);
#endif
\t\tif (!dual_registered && (regEntry = IORegistryEntry::fromPath( "/chosen/memory-map", gIODTPlane ))) {''')

    for name in ('dual_ramdisk_bounds.h', 'dual_ramdisk_init.inc'):
        (memdev.parent / f'duchamp_{name}').write_bytes((src / name).read_bytes())
    memdev.write_text(memdev_text)
    root.write_text(root_text)


if __name__ == '__main__':
    main()
