from invalidation_closure.generate import (
    choose_updates,
    generate_graph,
    update_delta,
)


def _signature(graph):
    return [belief.to_dict() for belief in graph.beliefs]


def test_generation_is_deterministic():
    first = generate_graph(11, 60, 5)
    second = generate_graph(11, 60, 5)
    assert _signature(first) == _signature(second)


def test_different_seeds_differ():
    first = generate_graph(11, 60, 5)
    second = generate_graph(12, 60, 5)
    assert _signature(first) != _signature(second)


def test_graph_size_and_roots():
    graph = generate_graph(3, 120, 5)
    assert len(graph) == 120
    assert len(graph.roots) == 24
    for root in graph.roots:
        assert graph.by_id[root].depth == 0


def test_topological_order():
    graph = generate_graph(3, 120, 5)
    for belief in graph.beliefs:
        for parent in belief.parents:
            assert parent < belief.id
            assert graph.by_id[parent].depth < belief.depth


def test_depth_reaches_max_and_never_exceeds():
    graph = generate_graph(3, 120, 5)
    depths = [belief.depth for belief in graph.beliefs]
    assert max(depths) == 5
    assert all(d <= 5 for d in depths)


def test_values_within_clamp():
    graph = generate_graph(3, 300, 5)
    for belief in graph.beliefs:
        assert -500 <= belief.value <= 500


def test_explicit_refs_are_root_ancestors():
    graph = generate_graph(3, 120, 5)
    for belief in graph.beliefs:
        if belief.kind == "derived":
            assert belief.explicit_refs <= graph.root_ancestors(belief.id)


def test_recorded_edge_rate_near_ninety_percent():
    graph = generate_graph(3, 300, 5)
    flags = []
    for belief in graph.beliefs:
        flags.extend(belief.edge_recorded)
    assert flags
    rate = sum(1 for f in flags if f) / len(flags)
    assert 0.84 < rate < 0.96


def test_session_inputs_and_refreshes_planted():
    graph = generate_graph(3, 300, 5)
    derived = [b for b in graph.beliefs if b.kind == "derived"]
    assert any(b.unrecoverable for b in derived)
    assert any(b.write_time >= len(graph) for b in derived)
    share = sum(1 for b in derived if b.unrecoverable) / len(derived)
    assert 0.05 < share < 0.25


def test_choose_updates_deterministic_and_spread():
    graph = generate_graph(3, 120, 5)
    first = choose_updates(graph, count=3)
    second = choose_updates(graph, count=3)
    assert first == second
    assert 1 <= len(first) <= 3
    for root_id, new_value in first:
        assert root_id in graph.roots
        assert new_value != graph.by_id[root_id].value
        _, affected = graph.affected_after(root_id, new_value)
        assert len(affected) >= 4


def test_update_delta_always_changes_value():
    for value in range(1, 13):
        assert update_delta(value) != value
