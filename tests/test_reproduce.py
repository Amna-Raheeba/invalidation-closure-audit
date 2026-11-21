import json
import os

RESULTS = os.path.join(os.path.dirname(__file__), "..", "results", "evaluation.json")


def test_stored_results_exist_and_parse():
    assert os.path.isfile(RESULTS)
    with open(RESULTS) as fh:
        payload = json.load(fh)
    for key in ("seeds", "sizes", "n_graphs", "n_updates",
                "mean_affected_per_update", "policies", "oracle",
                "headline"):
        assert key in payload, key


def test_stored_headline_keys():
    with open(RESULTS) as fh:
        payload = json.load(fh)
    headline = payload["headline"]
    for key in (
        "completeness_negation_only",
        "completeness_dependency_closure",
        "staleness_negation_only",
        "staleness_deep_negation_only",
        "staleness_deep_dependency_closure",
        "staleness_deep_recency_wins",
        "staleness_oracle_closure",
        "collateral_aggressive_flush",
        "recomputes_dependency_closure",
    ):
        assert key in headline, key


def test_stored_headline_values_sane():
    with open(RESULTS) as fh:
        payload = json.load(fh)
    headline = payload["headline"]
    # The negation baseline leaves almost everything stale, deep
    # beliefs worst of all.
    assert headline["staleness_negation_only"] > 0.85
    assert headline["staleness_deep_negation_only"] > 0.9
    # Recorded-edge closure removes most deep staleness; the oracle
    # control is exact, proving the remainder is a logging gap.
    assert headline["staleness_deep_dependency_closure"] < 0.4
    assert headline["staleness_oracle_closure"] == 0.0
    # The flush is the only policy with real collateral damage.
    assert headline["collateral_aggressive_flush"] > 0.02
    assert headline["collateral_dependency_closure"] < 0.005
