/* cache_aos: array-of-structs layout that wastes cache bandwidth.
 *
 * Each particle is 64 bytes but the hot loop only reads 4 of them (x).
 * Every cache line fetched delivers one useful float. Expected perf
 * signature: high cache-misses and L1-dcache-load-misses per instruction,
 * memory bandwidth bound.
 *
 * Known fix: struct-of-arrays, so x[] is contiguous and the loop streams
 * through 16 useful floats per line (and vectorizes).
 *
 * usage: cache_aos [n=1<<22] [seed=1] [reps=16]
 */
#include "harness.h"

typedef struct {
    float x, y, z, w;
    float vx, vy, vz, vw;
    float mass, charge, radius, life;
    uint32_t id, flags, pad0, pad1;
} particle_t;   /* 64 bytes */

static double sum_x(const particle_t *p, size_t n) {
    double s = 0.0;
    for (size_t i = 0; i < n; ++i) s += p[i].x;   /* hot spot: 1/16 of each line used */
    return s;
}

int main(int argc, char **argv) {
    size_t n = (size_t)arg_u64(argc, argv, 1, 1u << 22);
    uint64_t seed = arg_u64(argc, argv, 2, 1);
    int reps = (int)arg_u64(argc, argv, 3, 16);

    particle_t *p = malloc(n * sizeof *p);
    if (!p) return 1;
    for (size_t i = 0; i < n; ++i) {
        uint64_t r = rng_next(&seed);
        p[i].x = (float)(r & 0xffff) / 65536.0f;
        p[i].y = p[i].z = p[i].w = 0.0f;
        p[i].vx = p[i].vy = p[i].vz = p[i].vw = 0.0f;
        p[i].mass = 1.0f; p[i].charge = 0.0f; p[i].radius = 0.5f; p[i].life = 1.0f;
        p[i].id = (uint32_t)i; p[i].flags = 0; p[i].pad0 = p[i].pad1 = 0;
    }

    double t0 = now_ms();
    double total = 0.0;
    for (int r = 0; r < reps; ++r) total += sum_x(p, n);
    double t1 = now_ms();

    /* Quantize so the checksum is stable across equivalent summation orders. */
    uint64_t checksum = (uint64_t)(total * 16.0);
    report(checksum, t1 - t0);
    free(p);
    return 0;
}
