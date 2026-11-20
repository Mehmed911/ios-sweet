/* SPDX-License-Identifier: 0BSD */
#ifndef DUCHAMP_IOKIT_CONTRACT_H
#define DUCHAMP_IOKIT_CONTRACT_H
#include "duchamp-iokit-wire.h"
/* A successful enumeration status does not make MACH_PORT_NULL an object. */
static inline int dg_object_valid(dg_u32 name) {
    return name != 0 && name != 0xffffffffu;
}
static inline int dg_method_request_valid(const dg_u64 *in, dg_u32 count,
        const void *bytes, dg_u32 length, void *output, const dg_u32 *output_length,
        dg_u64 *scalars, const dg_u32 *scalar_count) {
    return count <= 16 && length <= 4096 && (!count || in) && (!length || bytes) &&
        (!output_length || (*output_length <= 4096 && (!*output_length || output))) &&
        (!scalar_count || (*scalar_count <= 16 && (!*scalar_count || scalars)));
}
#endif
