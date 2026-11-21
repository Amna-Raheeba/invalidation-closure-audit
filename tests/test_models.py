import pytest

from invalidation_closure.models import (
    VALUE_MAX,
    VALUE_MIN,
    Belief,
    clamp,
    depth_bucket,
    derive,
)


def test_clamp_bounds():
    assert clamp(0) == 0
    assert clamp(VALUE_MAX + 10) == VALUE_MAX
    assert clamp(VALUE_MIN - 10) == VALUE_MIN


def test_derive_single_parent_ops():
    assert derive("neg", [5]) == -5
    assert derive("inc", [5]) == 8
    assert derive("dbl", [5]) == 10


def test_derive_multi_parent_ops():
    assert derive("add", [1, 2, 3]) == 6
    assert derive("diff", [10, 4]) == 6
    assert derive("mul", [3, 4]) == 12
    assert derive("max", [3, 9, 4]) == 9
    assert derive("min", [3, 9, 4]) == 3


def test_derive_clamps_results():
    assert derive("mul", [100, 100]) == VALUE_MAX
    assert derive("neg", [VALUE_MIN]) == VALUE_MAX


def test_derive_diff_single_value_degrades():
    assert derive("diff", [7]) == 7


def test_derive_rejects_empty_and_unknown():
    with pytest.raises(ValueError):
        derive("add", [])
    with pytest.raises(ValueError):
        derive("nope", [1])


def test_depth_bucket():
    assert depth_bucket(1) == "1"
    assert depth_bucket(2) == "2"
    assert depth_bucket(3) == "3+"
    assert depth_bucket(5) == "3+"


def _belief(offset=0):
    return Belief(
        id=9,
        kind="derived",
        op="inc",
        parents=(1,),
        value=10,
        depth=1,
        cluster=0,
        session_offset=offset,
    )


def test_recompute_keeps_session_by_default():
    belief = _belief(offset=4)
    # derive("inc", [5]) = 8; with the session contribution, 12.
    assert belief.recompute([5]) == 12
    assert belief.recompute([5], keep_session=False) == 8


def test_unrecoverable_property():
    assert _belief(offset=4).unrecoverable
    assert not _belief(offset=0).unrecoverable


def test_to_dict_round_trip_shape():
    belief = _belief(offset=4)
    payload = belief.to_dict()
    for key in (
        "id",
        "kind",
        "op",
        "parents",
        "value",
        "depth",
        "cluster",
        "explicit_refs",
        "session_offset",
        "edge_recorded",
        "write_time",
    ):
        assert key in payload, key
    assert payload["session_offset"] == 4
