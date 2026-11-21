from invalidation_closure.evaluate import (
    headline_numbers,
    run_evaluation,
    run_single,
)
from invalidation_closure.models import POLICIES


def test_run_single_structure():
    result = run_single(7)
    assert result["n_beliefs"] == 80
    assert result["n_affected"] > 0
    for policy in POLICIES:
        assert policy in result["policies"]
        assert "rates" in result["policies"][policy]
    assert result["root_id"] in result["graph"].roots


def test_run_single_oracle_is_perfect():
    result = run_single(7)
    assert result["oracle"]["rates"]["staleness"] == 0.0
    assert result["oracle"]["rates"]["completeness"] == 1.0


def test_run_single_closure_beats_negation():
    result = run_single(7)
    closure = result["policies"]["dependency_closure"]["rates"]
    negation = result["policies"]["negation_only"]["rates"]
    assert closure["staleness"] < negation["staleness"]
    assert negation["staleness"] > 0.9


def test_run_single_stale_examples_match_counts():
    result = run_single(7)
    for policy in POLICIES:
        counts = result["policies"][policy]["counts"]
        assert len(result["stale_examples"][policy]) == counts["stale"]


def test_run_evaluation_small_config():
    evaluation = run_evaluation(seeds=(301,), sizes=(60,))
    assert evaluation["n_graphs"] == 1
    assert evaluation["n_updates"] >= 1
    assert evaluation["mean_affected_per_update"] > 0
    for policy in POLICIES:
        r = evaluation["policies"][policy]["rates"]
        assert 0.0 <= r["completeness"] <= 1.0
        assert 0.0 <= r["staleness"] <= 1.0


def test_headline_numbers_keys_and_ordering():
    evaluation = run_evaluation(seeds=(301,), sizes=(60,))
    headline = headline_numbers(evaluation)
    for key in (
        "staleness_negation_only",
        "staleness_deep_negation_only",
        "staleness_deep_dependency_closure",
        "staleness_recency_wins",
        "collateral_aggressive_flush",
        "completeness_dependency_closure",
        "staleness_oracle_closure",
    ):
        assert key in headline, key
    # The oracle control is exact, and recorded-edge closure sits
    # strictly between the oracle and the negation baseline at depth.
    assert headline["staleness_oracle_closure"] == 0.0
    assert (
        headline["staleness_deep_dependency_closure"]
        < headline["staleness_deep_negation_only"]
    )
    assert headline["collateral_aggressive_flush"] > 0.0
    assert headline["staleness_negation_only"] > 0.8
