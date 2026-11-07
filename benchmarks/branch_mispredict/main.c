/* branch_mispredict: a data-dependent branch the predictor cannot learn.
 *
 * Filters a random array, copying every element above a threshold into an
 * output buffer. Half the elements pass, in random order, so the branch is
 * a coin flip. The conditional store is what keeps the compiler from
 * if-converting the branch into a cmov (a plain conditional sum gets
 * if-converted at -O2 and shows no mispredictions at all; this was the
 * first version of this kernel). Expected perf signature: branch-misses
 * around N/2 per rep, IPC well under 1.
 *
 * Known fix (what the agent should find): branch-free compaction, i.e.
 * always store and advance the index by the comparison result, or sort /
 * partition the input first.
 *
 * usage: branch_mispredict [n=1<<24] [seed=1] [reps=4]
 */
#include "harness.h"

static size_t filter_above(const uint32_t *in, uint32_t *out, size_t n, uint32_t threshold) {
    size_t k = 0;
    for (size_t i = 0; i < n; ++i) {
        if (in[i] > threshold) {   /* hot spot */
            out[k++] = in[i];
        }
    }
    return k;
}

int main(int argc, char **argv) {
    size_t n = (size_t)arg_u64(argc, argv, 1, 1u << 24);
    uint64_t seed = arg_u64(argc, argv, 2, 1);
    int reps = (int)arg_u64(argc, argv, 3, 4);

    uint32_t *in = malloc(n * sizeof *in);
    uint32_t *out = malloc(n * sizeof *out);
    if (!in || !out) return 1;
    for (size_t i = 0; i < n; ++i) in[i] = (uint32_t)rng_next(&seed);

    double t0 = now_ms();
    uint64_t checksum = 0;
    for (int r = 0; r < reps; ++r) {
        size_t k = filter_above(in, out, n, 0x80000000u + (uint32_t)r);
        uint64_t h = (uint64_t)k;
        for (size_t i = 0; i < k; i += 4096) h = h * 1099511628211ULL + out[i];
        checksum = checksum * 31 + h;
    }
    double t1 = now_ms();

    report(checksum, t1 - t0);
    free(in);
    free(out);
    return 0;
}
