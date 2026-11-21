"""The five memory policies under audit.

Each policy receives the same update event - one root fact changes -
and returns the stored state it would leave behind, plus how much
work it did. Policies differ only in *which* beliefs they choose to
recompute; all recompute honestly from the stored values of the
parents (in topological order, so a recomputed parent is seen fresh
by its children).

- ``none``: the update writes the root and stops. Every dependent
  keeps the value it derived from the old fact.
- ``negation_only``: the store scans for beliefs whose statement
  explicitly mentions the changed fact and recomputes those. It has
  no dependency graph, so nothing cascades: a recomputed belief's
  children are left alone unless they also mention the fact, and a
  mentioning belief whose parents are stale is recomputed *from
  stale parents* - touched, but still wrong.
- ``recency_wins``: the store keeps version records only for the
  most recently written beliefs (creation and later refresh writes
  both count). An update revalidates every dependent of the fact
  that sits inside that window, recomputing it from its parents'
  current stored values. A belief is truly repaired only when its
  whole chain back to the fact is in-window: an out-of-window
  parent feeds its stale value in, and the belief comes out
  touched but still wrong.
- ``dependency_closure``: the store follows its dependency graph
  and recomputes the full transitive closure of the update - but
  only over edges it actually recorded. Dependents reachable only
  through an unlogged edge are never visited.
- ``aggressive_flush``: the store deletes every belief in the
  updated fact's cluster and rebuilds them from the graph. Freshness
  inside the cluster is total, but a rebuilt belief loses its
  session-only input contribution, and dependents living in other
  clusters are never touched.
"""

from .models import POLICIES


def recency_window_size(n_beliefs):
    """How many of the most recent writes keep version records."""
    return max(12, n_beliefs // 3)


def apply_policy(graph, root_id, new_value, policy):
    """Run one policy on one update.

    Returns ``(stored, stats)`` where ``stored`` is the full stored
    value list after the policy ran and ``stats`` carries the number
    of recomputations and the set of beliefs the policy touched.
    """
    if policy not in POLICIES:
        raise ValueError("unknown policy: %s" % policy)
    stored = [b.value for b in graph.beliefs]
    stored[root_id] = new_value
    stats = {"recomputes": 0, "touched": set()}
    if policy == "none":
        return stored, stats
    if policy == "aggressive_flush":
        return _apply_flush(graph, root_id, stored, stats)

    if policy == "dependency_closure":
        reachable = graph.reachable(root_id, recorded_only=True)
    if policy == "recency_wins":
        by_recency = sorted(
            graph.beliefs, key=lambda b: (b.write_time, b.id)
        )
        window = set(
            b.id for b in by_recency[-recency_window_size(len(graph)):]
        )
        reachable = graph.reachable(root_id, recorded_only=False)
    changed = set([root_id])

    for belief in graph.beliefs:
        if belief.kind != "derived":
            continue
        if policy == "negation_only":
            candidate = root_id in belief.explicit_refs
        elif policy == "recency_wins":
            candidate = belief.id in window and belief.id in reachable
        else:  # dependency_closure
            candidate = belief.id in reachable
        if not candidate:
            continue
        parent_values = [stored[p] for p in belief.parents]
        new_stored = belief.recompute(parent_values)
        stats["recomputes"] += 1
        stats["touched"].add(belief.id)
        if new_stored != stored[belief.id]:
            stored[belief.id] = new_stored
            changed.add(belief.id)
    return stored, stats


def _apply_flush(graph, root_id, stored, stats):
    """Delete and rebuild every belief in the root's cluster.

    Rebuilds run in topological order from stored parent values, but
    a rebuilt belief loses its session-only contribution - the
    record that held it is gone. Beliefs outside the cluster are
    never candidates, however stale they become.
    """
    cluster = graph.by_id[root_id].cluster
    for belief in graph.beliefs:
        if belief.kind != "derived" or belief.cluster != cluster:
            continue
        parent_values = [stored[p] for p in belief.parents]
        stored[belief.id] = belief.recompute(
            parent_values, keep_session=False
        )
        stats["recomputes"] += 1
        stats["touched"].add(belief.id)
    return stored, stats


def apply_oracle_closure(graph, root_id, new_value):
    """Control condition: closure over the *complete* edge set.

    Not a deployable policy - it assumes provenance recording the
    real store does not have. It exists to separate policy failure
    from recording failure: any staleness the oracle avoids but the
    recorded-edge closure does not is priced as a logging problem,
    not an algorithm problem.
    """
    stored = [b.value for b in graph.beliefs]
    stored[root_id] = new_value
    reachable = graph.reachable(root_id, recorded_only=False)
    stats = {"recomputes": 0, "touched": set()}
    for belief in graph.beliefs:
        if belief.kind != "derived" or belief.id not in reachable:
            continue
        parent_values = [stored[p] for p in belief.parents]
        stored[belief.id] = belief.recompute(parent_values)
        stats["recomputes"] += 1
        stats["touched"].add(belief.id)
    return stored, stats
