/* SPDX-License-Identifier: 0BSD */
/* QEMU lab hook for the stock BSD RAM-disk registration call. */
extern int mdevadd(int, unsigned long, unsigned int, int);
extern int SecureDTLookupEntry(const void *, const char *, void **);
extern int SecureDTGetProperty(const void *, const char *, const void **, unsigned int *);
extern unsigned long ml_static_ptovirt(unsigned long);
extern int printf(const char *, ...);

struct ram_range {
    unsigned long address, size;
};

int duchamp_var_register(int device, unsigned long pages, unsigned int count, int physical)
{
    int root = mdevadd(device, pages, count, physical);
    void *tree;
    const void *raw;
    unsigned int length;
    if (SecureDTLookupEntry(0, "/chosen/memory-map", &tree) != 1 ||
        SecureDTGetProperty(tree, "DuchampQemuVar", &raw, &length) != 1)
        return root;

    /* Both volumes are contiguous reservations made by the QEMU packager. */
    const struct ram_range *var = raw;
    if (length != sizeof(*var) || root < 0 || physical || count != 8192 ||
        var->size != 32UL * 1024 * 1024 || var->address != 0x1c4568000UL ||
        ml_static_ptovirt(var->address) != (pages + count) * 4096) {
        printf("VAR KERNEL: invalid QEMU RAM disk reservation\n");
        return root;
    }
    if (mdevadd(1, pages + count, (unsigned int)(var->size >> 12), 0) < 0) {
        printf("VAR KERNEL: md1 registration failed\n");
        return root;
    }
    printf("VAR KERNEL: md1 registered for writable var\n");
    return root;
}
