import pytest

from invalidation_closure.graph import BeliefGraph
from invalidation_closure.policies import (
    apply_oracle_closure,
    apply_policy,
    recency_window_size,
)
from invalidation_closure.score import rates, score_outcome
from conftest import make_belief


def _score(graph, stored, stats, root=0, new_value=7):
    truth, affected = graph.affected_after(root, new_value)
    counts = score_outcome(graph, root, truth, affected, stored, stats)
    return counts, rates(counts)


def test_root_is_always_updated(hand_graph):
    for policy in (
        "none",
        "negation_only",
        "recency_wins",
        "dependency_closure",
        "aggressive_flush",
    ):
        stored, _ = apply_policy(hand_graph, 0, 7, policy)
        assert stored[0] == 7, policy


def test_none_policy_leaves_everything_stale(hand_graph):
    stored, stats = apply_policy(hand_graph, 0, 7, "none")
    counts, r = _score(hand_graph, stored, stats)
    assert r["completeness"] == 0.0
    assert r["staleness"] == 1.0
    assert stats["recomputes"] == 0


def test_closure_repairs_recorded_reachable_only(hand_graph):
    stored, stats = apply_policy(hand_graph, 0, 7, "dependency_closure")
    counts, r = _score(hand_graph, stored, stats)
    # 2, 3, 4 repaired; 5 hides behind the unrecorded 3 -> 5 edge.
    assert stored[2] == 14
    assert stored[3] == 17
    assert stored[4] == 9
    assert stored[5] == -11
    assert r["completeness"] == 0.75
    assert counts["touched_wrong"] == 0


def test_oracle_closure_repairs_everything(hand_graph):
    stored, stats = apply_oracle_closure(hand_graph, 0, 7)
    _, r = _score(hand_graph, stored, stats)
    assert r["completeness"] == 1.0
    assert r["staleness"] == 0.0


def test_negation_only_repairs_mentions_and_touches_one_wrong(hand_graph):
    stored, stats = apply_policy(hand_graph, 0, 7, "negation_only")
    counts, r = _score(hand_graph, stored, stats)
    # Belief 2 mentions root 0 and has the root as parent: repaired.
    assert stored[2] == 14
    # Belief 5 mentions root 0 but is recomputed from stale parent 3:
    # touched, still wrong. 3 and 4 never touched.
    assert stored[5] == -11
    assert counts["touched_wrong"] == 1
    assert counts["untouched_stale"] == 2
    assert r["completeness"] == 0.25


def test_flush_rebuilds_cluster_and_loses_session_input(hand_graph):
    stored, stats = apply_policy(hand_graph, 0, 7, "aggressive_flush")
    counts, r = _score(hand_graph, stored, stats)
    # Cluster 0 rebuilt from structure: 2, 3, 5 all repaired (flush
    # does not need the recorded edge), 4 sits in cluster 1: stale.
    assert stored[2] == 14
    assert stored[3] == 17
    assert stored[5] == -17
    assert stored[4] == 6
    # Belief 6 was fine and is not a dependent of root 0, but the
    # flush deleted its record and rebuilt it without its session
    # input: collateral damage.
    assert stored[6] == 5
    assert counts["damaged"] == 1
    assert r["collateral_rate"] > 0.0


def test_flush_leaves_other_clusters_untouched(hand_graph):
    stored, stats = apply_policy(hand_graph, 0, 7, "aggressive_flush")
    assert 4 not in stats["touched"]
    assert stored[1] == 2


def _chain_graph(write_times):
    """Root 0 (value 1) and 20 derived beliefs in an inc chain."""
    beliefs = [
        make_belief(0, kind="root", value=1, depth=0, write_time=0)
    ]
    value = 1
    for idx in range(1, 21):
        value = value + 3
        beliefs.append(
            make_belief(
                idx,
                op="inc",
                parents=(idx - 1,),
                value=value,
                depth=idx,
                write_time=write_times[idx],
            )
        )
    return BeliefGraph(beliefs)


def test_recency_window_size():
    assert recency_window_size(10) == 12
    assert recency_window_size(300) == 100


def test_recency_repairs_only_inside_window():
    # The first twelve chain links carry the newest write times.
    write_times = [0] + [100 - idx for idx in range(1, 21)]
    graph = _chain_graph(write_times)
    stored, stats = apply_policy(graph, 0, 5, "recency_wins")
    counts, r = _score(graph, stored, stats, new_value=5)
    # Window holds the 12 most recent writes: links 1..12 repair,
    # links 13..20 are never touched.
    assert r["completeness"] == pytest.approx(12 / 20)
    assert counts["untouched_stale"] == 8


def test_recency_beyond_broken_chain_is_touched_but_wrong():
    # Only the deepest twelve links are recent; the chain into them
    # runs through old links, so they recompute from stale parents.
    write_times = [0] + [idx for idx in range(1, 21)]
    graph = _chain_graph(write_times)
    stored, stats = apply_policy(graph, 0, 5, "recency_wins")
    counts, r = _score(graph, stored, stats, new_value=5)
    assert r["completeness"] == 0.0
    assert counts["touched_wrong"] > 0


def test_unknown_policy_rejected(hand_graph):
    with pytest.raises(ValueError):
        apply_policy(hand_graph, 0, 7, "wishful_thinking")


def test_policies_do_not_mutate_graph(hand_graph):
    before = [b.value for b in hand_graph.beliefs]
    for policy in (
        "none",
        "negation_only",
        "recency_wins",
        "dependency_closure",
        "aggressive_flush",
    ):
        apply_policy(hand_graph, 0, 7, policy)
    assert [b.value for b in hand_graph.beliefs] == before
