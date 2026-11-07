/* Shared timing and checksum helpers for the calibration kernels.
 *
 * Every kernel prints exactly two lines to stdout:
 *   checksum: <hex>
 *   elapsed_ms: <float>
 * The checksum is the correctness oracle; the rewritten binary must print
 * the same checksum for the same arguments. elapsed_ms is for quick local
 * sanity checks only; real numbers come from perf on the lab server.
 */
#ifndef HARNESS_H
#define HARNESS_H

/* clock_gettime needs POSIX visibility under -std=c11 */
#ifndef _POSIX_C_SOURCE
#define _POSIX_C_SOURCE 200809L
#endif

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

static inline double now_ms(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (double)ts.tv_sec * 1e3 + (double)ts.tv_nsec / 1e6;
}

/* xorshift64*: deterministic, fast, good enough for benchmark inputs. */
static inline uint64_t rng_next(uint64_t *s) {
    uint64_t x = *s;
    x ^= x >> 12;
    x ^= x << 25;
    x ^= x >> 27;
    *s = x;
    return x * 0x2545F4914F6CDD1DULL;
}

static inline uint64_t arg_u64(int argc, char **argv, int i, uint64_t def) {
    return (argc > i) ? strtoull(argv[i], NULL, 10) : def;
}

static inline void report(uint64_t checksum, double ms) {
    printf("checksum: %016llx\n", (unsigned long long)checksum);
    printf("elapsed_ms: %.3f\n", ms);
}

#endif
