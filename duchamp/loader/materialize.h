#ifndef DUCHAMP_LOADER_MATERIALIZE_H
#define DUCHAMP_LOADER_MATERIALIZE_H

#include "plan.h"

unsigned duchamp_loader_materialize(const void *fdt, size_t fdt_size,
    const void *payload, size_t payload_size,
    const struct duchamp_range *occupied, unsigned occupied_count,
    const struct duchamp_framebuffer *framebuffer,
    void *window, size_t window_size,
    struct duchamp_dry_run_plan *completed_plan);

#endif
