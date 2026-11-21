"""Notebook 01 - demo run.

Runs one seeded belief graph (seed 7, 80 beliefs), fires its largest
root-fact update, and prints how each memory policy scores against
the ground-truth recomputation - including which beliefs the
negation-only policy leaves silently stale.
Runnable as a plain script: python notebooks/01_demo_run.py
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from invalidation_closure.evaluate import run_single
from invalidation_closure.report import render_single_report


def main():
    result = run_single(7)
    print(render_single_report(result))
    closure = result["policies"]["dependency_closure"]["rates"]
    negation = result["policies"]["negation_only"]["rates"]
    print(
        "Closure beats negation-only on staleness: %s (%.3f vs %.3f)"
        % (closure["staleness"] < negation["staleness"],
           closure["staleness"], negation["staleness"])
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
