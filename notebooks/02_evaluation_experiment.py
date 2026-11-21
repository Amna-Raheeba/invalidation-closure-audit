"""Notebook 02 - evaluation experiment.

Runs a reduced slice of the full evaluation (2 seeds x 2 graph
sizes) and prints the summary table, so the experiment design can be
inspected quickly. The shipped results/ come from the full
configuration in invalidation_closure.evaluate.
Runnable as a plain script: python notebooks/02_evaluation_experiment.py
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from invalidation_closure.evaluate import headline_numbers, run_evaluation
from invalidation_closure.report import render_evaluation_summary


def main():
    evaluation = run_evaluation(seeds=(301, 302), sizes=(60, 150))
    headline = headline_numbers(evaluation)
    print(render_evaluation_summary(evaluation, headline))
    print(
        "Deep staleness (depth >= 3): negation-only %.3f, "
        "recency %.3f, closure %.3f, oracle %.3f"
        % (
            headline["staleness_deep_negation_only"],
            headline["staleness_deep_recency_wins"],
            headline["staleness_deep_dependency_closure"],
            headline["staleness_deep_oracle_closure"],
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
