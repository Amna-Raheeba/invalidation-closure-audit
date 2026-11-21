"""Seeded generation of belief graphs and update events.

Every graph is fully deterministic given its seed. The generator
plants the imperfections the audit is about:

- provenance gaps: ~10% of dependency edges are never recorded, so
  even a perfect closure policy cannot follow them;
- explicit references: a direct dependent mentions its root fact in
  its statement ~65% of the time, a deeper dependent only ~4% - the
  thin channel the negation-only policy lives on;
- session-only inputs: ~15% of derived beliefs carry a contribution
  that exists only in their own record, which a flush destroys;
- refresh writes: a living memory re-derives and re-stores beliefs
  over time, so ~35% of derived beliefs are refreshed to a late
  write time - the recency window therefore cuts across depths
  instead of simply meaning "the newest derivations".

Depths are enriched by weighting parent choice toward deeper
beliefs, and a forced chain guarantees the graph actually reaches
``max_depth`` - otherwise the deep-staleness headline would have
nothing to measure.
"""

import random

from .graph import BeliefGraph
from .models import (
    MULTI_PARENT_OPS,
    SINGLE_PARENT_OPS,
    Belief,
    clamp,
    derive,
)

UNRECORDED_EDGE_RATE = 0.10
DIRECT_REF_RATE = 0.65
DEEP_REF_RATE = 0.04
SESSION_INPUT_RATE = 0.15
CROSS_CLUSTER_RATE = 0.15
REFRESH_RATE = 0.35


def _pick_op(rng, n_parents):
    if n_parents == 1:
        return rng.choice(SINGLE_PARENT_OPS)
    return rng.choice(MULTI_PARENT_OPS)


def _session_offset(rng):
    return rng.choice((-5, -4, -3, -2, -1, 1, 2, 3, 4, 5))


def generate_graph(seed, n_beliefs=120, max_depth=5):
    rng = random.Random(seed)
    n_clusters = max(2, n_beliefs // 25)
    n_roots = max(5, n_beliefs // 5)
    beliefs = []

    for idx in range(n_roots):
        beliefs.append(
            Belief(
                id=idx,
                kind="root",
                op=None,
                parents=(),
                value=rng.randint(2, 9),
                depth=0,
                cluster=rng.randrange(n_clusters),
            )
        )

    def add_derived(parents):
        op = _pick_op(rng, len(parents))
        depth = 1 + max(beliefs[p].depth for p in parents)
        if rng.random() < CROSS_CLUSTER_RATE:
            cluster = rng.randrange(n_clusters)
        else:
            cluster = beliefs[parents[0]].cluster
        offset = 0
        if rng.random() < SESSION_INPUT_RATE:
            offset = _session_offset(rng)
        parent_values = [beliefs[p].value for p in parents]
        value = clamp(derive(op, parent_values) + offset)
        recorded = tuple(
            rng.random() >= UNRECORDED_EDGE_RATE for _ in parents
        )
        belief = Belief(
            id=len(beliefs),
            kind="derived",
            op=op,
            parents=tuple(parents),
            value=value,
            depth=depth,
            cluster=cluster,
            session_offset=offset,
            edge_recorded=recorded,
        )
        beliefs.append(belief)
        return belief

    # Forced chain: guarantees the graph reaches max_depth.
    chain_parent = rng.randrange(n_roots)
    for _ in range(max_depth):
        if len(beliefs) >= n_beliefs:
            break
        chain_parent = add_derived([chain_parent]).id

    while len(beliefs) < n_beliefs:
        candidates = [b for b in beliefs if b.depth < max_depth]
        weights = [b.depth + 1 for b in candidates]
        n_parents = rng.choice((1, 2, 2, 3))
        n_parents = min(n_parents, len(candidates))
        parents = []
        pool = list(candidates)
        pool_weights = list(weights)
        for _ in range(n_parents):
            pick = rng.choices(pool, weights=pool_weights)[0]
            parents.append(pick.id)
            idx = pool.index(pick)
            pool.pop(idx)
            pool_weights.pop(idx)
        add_derived(parents)

    # Write times: creation order, then a refresh pass - a living
    # memory re-derives and re-stores some beliefs long after they
    # were created, moving them into the recent-write window.
    for belief in beliefs:
        belief.write_time = belief.id
        if belief.kind == "derived" and rng.random() < REFRESH_RATE:
            belief.write_time = n_beliefs + rng.randrange(n_beliefs)

    graph = BeliefGraph(beliefs)

    # Explicit references: planted after the graph exists, because
    # they are defined over root ancestors.
    for belief in beliefs:
        if belief.kind != "derived":
            continue
        refs = set()
        direct_roots = [p for p in belief.parents if p in graph.roots]
        for root in direct_roots:
            if rng.random() < DIRECT_REF_RATE:
                refs.add(root)
        for root in graph.root_ancestors(belief.id):
            if root not in direct_roots and rng.random() < DEEP_REF_RATE:
                refs.add(root)
        belief.explicit_refs = frozenset(refs)

    return graph


def update_delta(root_value):
    """The canonical update applied to a root: a real change, kept
    inside the plausible fact range."""
    if root_value <= 7:
        return root_value + 2
    return root_value - 3


def choose_updates(graph, count=3, min_affected=4):
    """Pick up to ``count`` update events, spread by blast radius.

    Deterministic: roots are scored by how many beliefs their update
    affects, and the picks are the largest, the median, and the
    smallest qualifying root, so the evaluation covers both hub
    facts and peripheral ones. Falls back to the single largest root
    when nothing qualifies.
    """
    scored = []
    for root in graph.roots:
        new_value = update_delta(graph.by_id[root].value)
        _, affected = graph.affected_after(root, new_value)
        scored.append((len(affected), root, new_value))
    scored.sort()
    if not scored:
        return []
    qualifying = [s for s in scored if s[0] >= min_affected]
    if not qualifying:
        biggest = scored[-1]
        return [(biggest[1], biggest[2])]
    picks = [qualifying[-1], qualifying[len(qualifying) // 2], qualifying[0]]
    seen = set()
    updates = []
    for _, root, new_value in picks:
        if root not in seen:
            seen.add(root)
            updates.append((root, new_value))
    return updates[:count]
