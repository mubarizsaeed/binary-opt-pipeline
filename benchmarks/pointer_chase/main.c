/* pointer_chase: a linked list walk the hardware prefetcher cannot follow.
 *
 * Builds a singly linked list of N nodes, shuffles the link order so each
 * next pointer lands in a random cache line, then walks it. Expected perf
 * signature: LLC-load-misses close to the number of hops, cycles dominated
 * by memory latency, IPC far below 1.
 *
 * Known fixes: software prefetch a few hops ahead when the structure allows
 * it, or re-lay the nodes out in traversal order (pointer-chase to array).
 *
 * usage: pointer_chase [n=1<<22] [seed=1] [hops=1<<24]
 */
#include "harness.h"

typedef struct node {
    struct node *next;
    uint64_t value;
    uint64_t pad[6];          /* one node per 64-byte cache line */
} node_t;

static uint64_t walk(const node_t *p, uint64_t hops) {
    uint64_t acc = 0;
    for (uint64_t i = 0; i < hops; ++i) {
        acc += p->value;      /* hot spot: load depends on previous load */
        p = p->next;
    }
    return acc;
}

int main(int argc, char **argv) {
    size_t n = (size_t)arg_u64(argc, argv, 1, 1u << 22);
    uint64_t seed = arg_u64(argc, argv, 2, 1);
    uint64_t hops = arg_u64(argc, argv, 3, 1u << 24);

    node_t *nodes = malloc(n * sizeof *nodes);
    size_t *perm = malloc(n * sizeof *perm);
    if (!nodes || !perm) return 1;

    /* Fisher-Yates permutation defines a single cycle through all nodes. */
    for (size_t i = 0; i < n; ++i) perm[i] = i;
    for (size_t i = n - 1; i > 0; --i) {
        size_t j = (size_t)(rng_next(&seed) % (i + 1));
        size_t t = perm[i]; perm[i] = perm[j]; perm[j] = t;
    }
    for (size_t i = 0; i < n; ++i) {
        nodes[perm[i]].next = &nodes[perm[(i + 1) % n]];
        nodes[perm[i]].value = rng_next(&seed) & 0xffff;
    }

    double t0 = now_ms();
    uint64_t checksum = walk(&nodes[perm[0]], hops);
    double t1 = now_ms();

    report(checksum, t1 - t0);
    free(perm);
    free(nodes);
    return 0;
}
