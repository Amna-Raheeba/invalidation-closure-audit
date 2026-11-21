from invalidation_closure.evaluate import (
    headline_numbers,
    run_evaluation,
    run_single,
)
from invalidation_closure.report import (
    render_evaluation_summary,
    render_single_report,
)


def test_single_report_names_policies_and_update():
    result = run_single(7)
    text = render_single_report(result)
    assert "Dependency closure" in text
    assert "Explicit-negation only" in text
    assert "Oracle closure (control)" in text
    assert "root fact %d" % result["root_id"] in text
    assert "silently stale" in text


def test_single_report_is_deterministic():
    result = run_single(7)
    assert render_single_report(result) == render_single_report(result)


def test_evaluation_summary_table():
    evaluation = run_evaluation(seeds=(301,), sizes=(60,))
    text = render_evaluation_summary(
        evaluation, headline_numbers(evaluation)
    )
    assert "| Policy | Completeness |" in text
    assert "Aggressive cluster flush" in text
    assert "provenance-logging gap" in text


def test_evaluation_summary_mentions_scale():
    evaluation = run_evaluation(seeds=(301,), sizes=(60,))
    text = render_evaluation_summary(
        evaluation, headline_numbers(evaluation)
    )
    assert "%d update events" % evaluation["n_updates"] in text
