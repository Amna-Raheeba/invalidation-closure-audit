"""Scoring a policy outcome against ground truth.

Three numbers tell the whole story of an update:

- **completeness** - of the beliefs whose true value changed, the
  fraction the policy left holding the new true value;
- **silent staleness** - the complement: beliefs still acting on the
  old fact, reported overall and per depth bucket, because a stale
  belief three derivations away from the fact is the one nobody
  thinks to check;
- **collateral damage** - of the beliefs whose true value did *not*
  change, the fraction the policy broke anyway. This is the flush
  family's failure direction, and any audit that reports only
  staleness will always crown the most destructive policy.

The **closure gap** is reported as reach: how many affected beliefs
the policy never even touched, versus how many it touched but still
left wrong (recomputed from stale parents, or rebuilt without a
session input).
"""

from .models import DEPTH_BUCKETS, depth_bucket


def empty_counts():
    return {
        "affected": 0,
        "correct": 0,
        "stale": 0,
        "touched_wrong": 0,
        "untouched_stale": 0,
        "unaffected": 0,
        "damaged": 0,
        "recomputes": 0,
        "runs": 0,
        "by_depth": dict(
            (bucket, {"affected": 0, "stale": 0}) for bucket in DEPTH_BUCKETS
        ),
    }


def score_outcome(graph, root_id, truth, affected, stored, stats):
    """Score one policy on one update. Returns a counts dict that
    ``accumulate`` can pool across runs (rates are computed from
    pooled counts, never averaged per-run, so big blast radii weigh
    more than small ones - as they should)."""
    counts = empty_counts()
    counts["runs"] = 1
    counts["recomputes"] = stats["recomputes"]
    touched = stats["touched"]
    for belief in graph.beliefs:
        if belief.kind != "derived":
            continue
        bucket = depth_bucket(belief.depth)
        if belief.id in affected:
            counts["affected"] += 1
            counts["by_depth"][bucket]["affected"] += 1
            if stored[belief.id] == truth[belief.id]:
                counts["correct"] += 1
            else:
                counts["stale"] += 1
                counts["by_depth"][bucket]["stale"] += 1
                if belief.id in touched:
                    counts["touched_wrong"] += 1
                else:
                    counts["untouched_stale"] += 1
        else:
            counts["unaffected"] += 1
            if stored[belief.id] != truth[belief.id]:
                counts["damaged"] += 1
    return counts


def accumulate(total, counts):
    total["affected"] += counts["affected"]
    total["correct"] += counts["correct"]
    total["stale"] += counts["stale"]
    total["touched_wrong"] += counts["touched_wrong"]
    total["untouched_stale"] += counts["untouched_stale"]
    total["unaffected"] += counts["unaffected"]
    total["damaged"] += counts["damaged"]
    total["recomputes"] += counts["recomputes"]
    total["runs"] += counts["runs"]
    for bucket in DEPTH_BUCKETS:
        total["by_depth"][bucket]["affected"] += counts["by_depth"][bucket][
            "affected"
        ]
        total["by_depth"][bucket]["stale"] += counts["by_depth"][bucket][
            "stale"
        ]
    return total


def rates(counts):
    """Convert pooled counts into the reported rates."""
    affected = counts["affected"]
    unaffected = counts["unaffected"]
    out = {
        "completeness": (counts["correct"] / affected) if affected else 1.0,
        "staleness": (counts["stale"] / affected) if affected else 0.0,
        "collateral_rate": (counts["damaged"] / unaffected)
        if unaffected
        else 0.0,
        "mean_recomputes": counts["recomputes"] / counts["runs"]
        if counts["runs"]
        else 0.0,
        "touched_wrong_share": (counts["touched_wrong"] / counts["stale"])
        if counts["stale"]
        else 0.0,
        "staleness_by_depth": {},
    }
    for bucket in DEPTH_BUCKETS:
        cell = counts["by_depth"][bucket]
        out["staleness_by_depth"][bucket] = (
            cell["stale"] / cell["affected"] if cell["affected"] else 0.0
        )
    return out
