#include <errno.h>
#include <stdint.h>
#include <stdlib.h>

static size_t allocation_limit(void) {
    const char *value = getenv("RUSTIFY_ALLOCATION_LIMIT");
    return value ? strtoull(value, NULL, 10) : SIZE_MAX;
}

static void *bounded_malloc(size_t size) {
    if (size > allocation_limit()) { errno = ENOMEM; return NULL; }
    return malloc(size);
}

static void *bounded_calloc(size_t count, size_t size) {
    if (size && count > allocation_limit() / size) { errno = ENOMEM; return NULL; }
    return calloc(count, size);
}

static void *bounded_realloc(void *pointer, size_t size) {
    if (size > allocation_limit()) { errno = ENOMEM; return NULL; }
    return realloc(pointer, size);
}

__attribute__((used, section("__DATA,__interpose")))
static const struct { const void *replacement; const void *original; } interposers[] = {
    { bounded_malloc, malloc }, { bounded_calloc, calloc }, { bounded_realloc, realloc }
};
