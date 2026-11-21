from invalidation_closure.score import (
    accumulate,
    empty_counts,
    rates,
    score_outcome,
)


def _run(graph, stored, touched, root=0, new_value=7):
    truth, affected = graph.affected_after(root, new_value)
    stats = {"recomputes": len(touched), "touched": set(touched)}
    return score_outcome(graph, root, truth, affected, stored, stats)


def test_score_perfect_outcome(hand_graph):
    truth, _ = hand_graph.affected_after(0, 7)
    counts = _run(hand_graph, truth, touched={2, 3, 4, 5})
    r = rates(counts)
    assert r["completeness"] == 1.0
    assert r["staleness"] == 0.0
    assert r["collateral_rate"] == 0.0


def test_score_nothing_done(hand_graph):
    stored = [b.value for b in hand_graph.beliefs]
    stored[0] = 7
    counts = _run(hand_graph, stored, touched=set())
    r = rates(counts)
    assert counts["affected"] == 4
    assert counts["stale"] == 4
    assert counts["untouched_stale"] == 4
    assert r["staleness"] == 1.0


def test_score_collateral_counts_only_unaffected(hand_graph):
    truth, _ = hand_graph.affected_after(0, 7)
    stored = list(truth)
    stored[6] = 5  # belief 6 was unaffected; now broken
    counts = _run(hand_graph, stored, touched={2, 3, 4, 5, 6})
    r = rates(counts)
    assert counts["damaged"] == 1
    assert counts["unaffected"] == 1
    assert r["collateral_rate"] == 1.0
    # Damaging an unaffected belief does not touch completeness.
    assert r["completeness"] == 1.0


def test_score_depth_buckets(hand_graph):
    stored = [b.value for b in hand_graph.beliefs]
    stored[0] = 7
    counts = _run(hand_graph, stored, touched=set())
    # Affected: 2 (depth 1), 4 (depth 1), 3 (depth 2), 5 (depth 3).
    assert counts["by_depth"]["1"] == {"affected": 2, "stale": 2}
    assert counts["by_depth"]["2"] == {"affected": 1, "stale": 1}
    assert counts["by_depth"]["3+"] == {"affected": 1, "stale": 1}


def test_accumulate_pools_counts():
    total = empty_counts()
    first = empty_counts()
    first.update({"affected": 4, "correct": 1, "stale": 3, "runs": 1})
    first["by_depth"]["1"] = {"affected": 2, "stale": 1}
    second = empty_counts()
    second.update({"affected": 6, "correct": 6, "stale": 0, "runs": 1})
    second["by_depth"]["1"] = {"affected": 3, "stale": 0}
    accumulate(total, first)
    accumulate(total, second)
    r = rates(total)
    assert total["runs"] == 2
    # Pooled, not averaged: 7 correct of 10 affected.
    assert r["completeness"] == 0.7
    assert r["staleness_by_depth"]["1"] == 0.2


def test_rates_with_no_affected_beliefs():
    r = rates(empty_counts())
    assert r["completeness"] == 1.0
    assert r["staleness"] == 0.0
    assert r["collateral_rate"] == 0.0
    assert r["mean_recomputes"] == 0.0
