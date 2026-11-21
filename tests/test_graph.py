def test_roots_listed(hand_graph):
    assert sorted(hand_graph.roots) == [0, 1]
    assert len(hand_graph) == 7


def test_dependents_adjacency(hand_graph):
    assert sorted(hand_graph.dependents[0]) == [2, 4]
    assert sorted(hand_graph.dependents[3]) == [5]


def test_recorded_adjacency_drops_unlogged_edge(hand_graph):
    # The 3 -> 5 edge was never recorded.
    assert hand_graph.recorded_dependents[3] == []
    assert sorted(hand_graph.recorded_dependents[0]) == [2, 4]


def test_reachable_full_vs_recorded(hand_graph):
    assert hand_graph.reachable(0) == {2, 3, 4, 5}
    assert hand_graph.reachable(0, recorded_only=True) == {2, 3, 4}


def test_root_ancestors(hand_graph):
    assert hand_graph.root_ancestors(5) == {0}
    assert hand_graph.root_ancestors(4) == {0, 1}
    assert hand_graph.root_ancestors(6) == {1}


def test_true_values_after_update(hand_graph):
    truth = hand_graph.true_values_after(0, 7)
    assert truth[0] == 7
    assert truth[2] == 14
    assert truth[3] == 17
    assert truth[4] == 9
    assert truth[5] == -17
    # Belief 6 does not depend on root 0 and keeps its session input.
    assert truth[6] == 9


def test_affected_after(hand_graph):
    truth, affected = hand_graph.affected_after(0, 7)
    assert set(affected) == {2, 3, 4, 5}
    assert affected[3] == 17
    assert truth[6] == 9


def test_update_with_same_value_affects_nothing(hand_graph):
    _, affected = hand_graph.affected_after(0, 4)
    assert affected == {}
