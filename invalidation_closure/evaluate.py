"""Evaluation: seeded graphs, planted updates, pooled scoring.

Graphs of 50-300 beliefs with depths up to 5 are generated per seed;
each graph contributes up to three update events (largest, median,
and smallest qualifying blast radius, chosen deterministically).
Every policy runs on every update, and counts are pooled across all
runs before rates are computed. An oracle closure over the complete
edge set runs alongside as a control: it separates what the closure
*policy* loses from what the store's *provenance recording* loses.
"""

from .generate import choose_updates, generate_graph
from .models import POLICIES
from .policies import apply_oracle_closure, apply_policy
from .score import accumulate, empty_counts, rates, score_outcome

EVALUATION_SEEDS = (301, 302, 303, 304, 305, 306)
EVALUATION_SIZES = (60, 150, 300)
EVALUATION_MAX_DEPTH = 5
UPDATES_PER_GRAPH = 3


def run_single(seed=7, n_beliefs=80, max_depth=5):
    """One graph, its largest update, every policy scored.

    Used by the demo, the example, and the dashboard: small enough to
    inspect belief by belief.
    """
    graph = generate_graph(seed, n_beliefs, max_depth)
    updates = choose_updates(graph, count=1)
    root_id, new_value = updates[0]
    truth, affected = graph.affected_after(root_id, new_value)
    per_policy = {}
    stale_examples = {}
    for policy in POLICIES:
        stored, stats = apply_policy(graph, root_id, new_value, policy)
        counts = score_outcome(graph, root_id, truth, affected, stored, stats)
        per_policy[policy] = {
            "counts": counts,
            "rates": rates(counts),
        }
        stale_examples[policy] = sorted(
            belief_id
            for belief_id in affected
            if stored[belief_id] != truth[belief_id]
        )
    stored, stats = apply_oracle_closure(graph, root_id, new_value)
    oracle_counts = score_outcome(
        graph, root_id, truth, affected, stored, stats
    )
    return {
        "seed": seed,
        "n_beliefs": len(graph),
        "max_depth": max_depth,
        "root_id": root_id,
        "old_value": graph.by_id[root_id].value,
        "new_value": new_value,
        "root_cluster": graph.by_id[root_id].cluster,
        "n_affected": len(affected),
        "affected_by_depth": _affected_by_depth(graph, affected),
        "policies": per_policy,
        "oracle": {"counts": oracle_counts, "rates": rates(oracle_counts)},
        "stale_examples": stale_examples,
        "graph": graph,
    }


def _affected_by_depth(graph, affected):
    out = {}
    for belief_id in affected:
        depth = graph.by_id[belief_id].depth
        out[depth] = out.get(depth, 0) + 1
    return out


def run_evaluation(
    seeds=EVALUATION_SEEDS,
    sizes=EVALUATION_SIZES,
    max_depth=EVALUATION_MAX_DEPTH,
    updates_per_graph=UPDATES_PER_GRAPH,
):
    totals = dict((policy, empty_counts()) for policy in POLICIES)
    oracle_total = empty_counts()
    n_graphs = 0
    n_updates = 0
    total_affected = 0
    for seed in seeds:
        for size in sizes:
            graph = generate_graph(seed + size, size, max_depth)
            n_graphs += 1
            for root_id, new_value in choose_updates(
                graph, count=updates_per_graph
            ):
                n_updates += 1
                truth, affected = graph.affected_after(root_id, new_value)
                total_affected += len(affected)
                for policy in POLICIES:
                    stored, stats = apply_policy(
                        graph, root_id, new_value, policy
                    )
                    counts = score_outcome(
                        graph, root_id, truth, affected, stored, stats
                    )
                    accumulate(totals[policy], counts)
                stored, stats = apply_oracle_closure(
                    graph, root_id, new_value
                )
                counts = score_outcome(
                    graph, root_id, truth, affected, stored, stats
                )
                accumulate(oracle_total, counts)
    return {
        "seeds": list(seeds),
        "sizes": list(sizes),
        "max_depth": max_depth,
        "n_graphs": n_graphs,
        "n_updates": n_updates,
        "mean_affected_per_update": total_affected / n_updates
        if n_updates
        else 0.0,
        "policies": dict(
            (policy, {"counts": totals[policy], "rates": rates(totals[policy])})
            for policy in POLICIES
        ),
        "oracle": {"counts": oracle_total, "rates": rates(oracle_total)},
    }


def headline_numbers(evaluation):
    """Flatten an evaluation into the headline dict the README,
    HEADLINE.md, and the drift guard all read from."""
    out = {
        "n_graphs": evaluation["n_graphs"],
        "n_updates": evaluation["n_updates"],
        "mean_affected_per_update": evaluation[
            "mean_affected_per_update"
        ],
    }
    for policy in POLICIES:
        r = evaluation["policies"][policy]["rates"]
        out["completeness_%s" % policy] = r["completeness"]
        out["staleness_%s" % policy] = r["staleness"]
        out["collateral_%s" % policy] = r["collateral_rate"]
        out["recomputes_%s" % policy] = r["mean_recomputes"]
        out["staleness_deep_%s" % policy] = r["staleness_by_depth"]["3+"]
    out["staleness_oracle_closure"] = evaluation["oracle"]["rates"][
        "staleness"
    ]
    out["staleness_deep_oracle_closure"] = evaluation["oracle"]["rates"][
        "staleness_by_depth"
    ]["3+"]
    return out
