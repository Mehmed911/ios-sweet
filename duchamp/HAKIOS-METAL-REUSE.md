# HakiOS Metal reference: what can help Duchamp

Inspected 2026-10-30 at the fixed upstream commit
[54a46fadec5bd9684ebd77f3a0834c84b5eb01a6](https://github.com/oosexgang/hakios-metal/tree/54a46fadec5bd9684ebd77f3a0834c84b5eb01a6).
The checkout and build outputs remain in the local ignored directory
research/hakios-metal-54a46fa. No upstream implementation has been
integrated into ios-sweet by this inspection.

## Actual local test

After reviewing the Makefile and host test sources, ran in WSL:

```sh
cd research/hakios-metal-54a46fa
make test CXX=clang++
```

Result: **21 tests, 0 failed checks**, exit 0. Compiler flags included
C++17, -O2, -Wall, -Wextra and -Werror. Output is saved in
research/hakios-metal-host-tests.log. The reference checkout stayed clean.
This was a Linux host run using FakeGpu. No sanitizer, iOS build, real
GPU or phone test was performed in this run.

The passing cases cover the C API, copy/fill results and alignment,
completion order, command-buffer reuse, bad-stream rejection, large-copy
packet splitting, metallib bounds/universal AIR64 handling, PM4 parity
and packet layout.

## Reuse boundaries established from source

| Component | Useful part | Integration requirement |
| --- | --- | --- |
| include/hakios-metal/metallib.hpp and src/metallib.cpp | Bounded container parsing, function lookup and AIR bitcode extraction | Best isolated candidate: bring over with MIT attribution and parser tests, then check actual local libraries. Parsing does not compile or execute shaders. |
| command.hpp / command.cpp | Command-buffer states, completion ordering, error propagation and host tests | Separate these concepts from the current PM4 blit encoder before targeting another GPU. The whole implementation is not device-neutral. |
| fake_gpu.hpp / fake_gpu.cpp | Repeatable transport/error tests on the host | The interpreter understands Adreno PM4. Passing it is not Mali hardware evidence. |
| gpu.hpp / gpu.cpp | An explicit transport boundary for buffers, queues and fences | Its actual structures and request numbers are MSM DRM, including GEM allocation/submission. MT6897 needs its own contract. |
| src/iokit_transport.cpp | Example of an IOKit service/user-client and mapped buffers | It opens the exact service HakiosGPU, calls IOConnectCallStructMethod with MSM request selectors, and maps memory by handle. This requires the corresponding kernel service; copying this file cannot create an MT6897 GPU driver. |
| pm4.hpp / pm4.cpp | A checked Adreno command-stream reference | Do not emit these packets to the Duchamp GPU. |

The upstream README describes Adreno and explicitly lists shader
execution as unfinished in this repository. Its proposed AIR/NIR/ir3
connection is not a working shader pipeline verified by our host test.
Its reported POCO X5 Pro probe results are upstream claims, not tests
performed on Duchamp here.

MediaTek specifies Mali-G615 MC6 for the
[Dimensity 8300](https://www.mediatek.com/products/smartphones/mediatek-dimensity-8300).
Consequently the MSM/Adreno transport and PM4 path do not establish
compatibility with this target. The confirmed framebuffer console also
does not establish an accelerated Metal/CoreAnimation path.

## Staged use

1. Keep the parser and command-state tests as reference material while
   completing the native platform/storage work.
2. If importing the parser, retain its MIT license/copyright and run both
   its malformed-container cases and actual local-library fixtures.
3. Establish a separate MediaTek GPU/user-client ABI and memory ownership
   contract before implementing allocation, submission or MMIO.
4. Verify the shader/rendering and iOS framework interfaces independently;
   the current reference's copy/fill tests are not a SpringBoard boot.

This inspection identifies reusable source and concrete gaps. It does
not provide a ready iOS image or authorize any device operation.
