/* dep_chain: a long serial dependency chain that starves the out-of-order core.
 *
 * Runs a multiply-add recurrence where every iteration depends on the one
 * before it, so the CPU cannot overlap iterations. Expected perf signature:
 * no cache or branch problems, but IPC stuck near 1/latency of the mul.
 *
 * Known fix: split into K independent accumulators (loop unrolling with
 * interleaving) when the recurrence is associative enough, or restructure
 * the algorithm so there is more independent work per iteration.
 *
 * usage: dep_chain [iters=1<<28] [seed=1]
 */
#include "harness.h"

static uint64_t recur(uint64_t x, uint64_t iters) {
    for (uint64_t i = 0; i < iters; ++i) {
        x = x * 6364136223846793005ULL + 1442695040888963407ULL;   /* hot spot */
        x ^= x >> 29;
    }
    return x;
}

int main(int argc, char **argv) {
    uint64_t iters = arg_u64(argc, argv, 1, 1u << 28);
    uint64_t seed = arg_u64(argc, argv, 2, 1);

    double t0 = now_ms();
    uint64_t checksum = recur(seed, iters);
    double t1 = now_ms();

    report(checksum, t1 - t0);
    return 0;
}
