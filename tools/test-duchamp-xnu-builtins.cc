/* SPDX-License-Identifier: 0BSD */
/* Compile for arm64-apple-macos15.5, using the XNU-aware Clang. */
static_assert(__has_builtin(__builtin_xnu_type_signature), "signature trait");
static_assert(__has_builtin(__builtin_xnu_type_summary), "summary trait");
static_assert(__has_builtin(__builtin_xnu_types_compatible), "compatibility trait");

struct Mixed {
    unsigned long value;
    void *pointer;
};

struct SameLayout {
    long number;
    const char *address;
};

union Overlap {
    unsigned long value;
    void *pointer;
};

struct alignas(16) Padded {
    void *pointer;
};

struct Empty {};

constexpr bool equal(const char *left, const char *right)
{
    while (*left && *left == *right) {
        ++left;
        ++right;
    }
    return *left == *right;
}

template<typename T> constexpr const char *signature = __builtin_xnu_type_signature(T);
template<typename T> constexpr auto summary = __builtin_xnu_type_summary(T);

static_assert(equal(signature<Mixed>, "21"), "data and pointer occupy separate granules");
static_assert(summary<Mixed> == 6, "combined data and pointer summary");
static_assert(equal(signature<Overlap>, "3"), "union granules combine member encodings");
static_assert(summary<Overlap> == 8, "overlapping pointer and data summary");
static_assert(equal(signature<Padded>, "10"), "tail padding is a separate granule");
static_assert(summary<Padded> == 3, "padding contributes to the summary");
static_assert(equal(signature<Empty>, "") && summary<Empty> == 0, "empty records have no scalar granules");
static_assert(__builtin_xnu_types_compatible(Mixed, SameLayout), "equivalent allocation layout");
static_assert(!__builtin_xnu_types_compatible(Mixed, Padded), "different allocation layout");
static_assert(__builtin_xnu_types_compatible(void, void) &&
              !__builtin_xnu_types_compatible(void, Mixed), "void compatibility");

typedef unsigned long AnnotatedPointer __attribute__((xnu_usage_semantics("pointer")));
static_assert(equal(__builtin_xnu_type_signature(AnnotatedPointer), "1"), "direct typedef usage annotation");
static_assert(__builtin_xnu_type_summary(AnnotatedPointer) == 2, "direct typedef pointer summary");
static_assert(summary<AnnotatedPointer> == 4, "C++ template substitution desugars this typedef");
