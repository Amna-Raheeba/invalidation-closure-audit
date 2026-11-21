"""Example: audit one update under each policy and print verdicts.

Fast path - one graph, one update. Shows the spread between the
policies on the same event: how much each leaves silently stale,
what the flush breaks, and what each costs in recomputations.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from invalidation_closure.evaluate import run_single
from invalidation_closure.models import POLICIES, POLICY_LABELS


def main():
    result = run_single(7)
    print(
        "Root fact %d: %d -> %d; %d beliefs affected in truth"
        % (
            result["root_id"],
            result["old_value"],
            result["new_value"],
            result["n_affected"],
        )
    )
    for policy in POLICIES:
        r = result["policies"][policy]["rates"]
        print(
            "%-28s stale %.3f (deep %.3f) | collateral %.4f | recomputes %.0f"
            % (
                POLICY_LABELS[policy],
                r["staleness"],
                r["staleness_by_depth"]["3+"],
                r["collateral_rate"],
                r["mean_recomputes"],
            )
        )
    r = result["oracle"]["rates"]
    print(
        "%-28s stale %.3f (deep %.3f) | collateral %.4f | recomputes %.0f"
        % (
            "Oracle closure (control)",
            r["staleness"],
            r["staleness_by_depth"]["3+"],
            r["collateral_rate"],
            r["mean_recomputes"],
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
