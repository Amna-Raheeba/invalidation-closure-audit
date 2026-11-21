"""Human-readable renderings of single runs and evaluations."""

from .models import POLICIES, POLICY_LABELS


def _policy_row(name, r):
    return "%-28s complete %.3f | stale %.3f (depth>=3 %.3f) | collateral %.4f | recomputes %.1f" % (
        name,
        r["completeness"],
        r["staleness"],
        r["staleness_by_depth"]["3+"],
        r["collateral_rate"],
        r["mean_recomputes"],
    )


def render_single_report(result):
    lines = []
    lines.append("Invalidation closure audit - single update")
    lines.append(
        "Graph: %d beliefs (seed %d, max depth %d)"
        % (result["n_beliefs"], result["seed"], result["max_depth"])
    )
    lines.append(
        "Update: root fact %d changes %d -> %d (cluster %d); %d derived beliefs change in truth"
        % (
            result["root_id"],
            result["old_value"],
            result["new_value"],
            result["root_cluster"],
            result["n_affected"],
        )
    )
    by_depth = result["affected_by_depth"]
    lines.append(
        "Affected by depth: %s"
        % ", ".join(
            "depth %d: %d" % (d, by_depth[d]) for d in sorted(by_depth)
        )
    )
    lines.append("")
    for policy in POLICIES:
        lines.append(
            _policy_row(
                POLICY_LABELS[policy], result["policies"][policy]["rates"]
            )
        )
    lines.append(
        _policy_row(
            "Oracle closure (control)", result["oracle"]["rates"]
        )
    )
    lines.append("")
    for policy in ("negation_only", "dependency_closure"):
        stale = result["stale_examples"][policy]
        shown = ", ".join(str(s) for s in stale[:8])
        lines.append(
            "%s leaves %d beliefs silently stale (first ids: %s)"
            % (POLICY_LABELS[policy], len(stale), shown if shown else "-")
        )
    return "\n".join(lines) + "\n"


def render_evaluation_summary(evaluation, headline):
    lines = []
    lines.append("# Evaluation summary")
    lines.append("")
    lines.append(
        "Seeded belief graphs (sizes %s, max depth %d), %d graphs, "
        "%d update events, %.1f beliefs affected per update on "
        "average. Counts are pooled across all runs before rates "
        "are computed."
        % (
            ", ".join(str(s) for s in evaluation["sizes"]),
            evaluation["max_depth"],
            evaluation["n_graphs"],
            evaluation["n_updates"],
            evaluation["mean_affected_per_update"],
        )
    )
    lines.append("")
    lines.append(
        "| Policy | Completeness | Staleness | Staleness depth>=3 | Collateral | Recomputes/update |"
    )
    lines.append("|---|---|---|---|---|---|")
    for policy in POLICIES:
        r = evaluation["policies"][policy]["rates"]
        lines.append(
            "| %s | %.3f | %.3f | %.3f | %.4f | %.1f |"
            % (
                POLICY_LABELS[policy],
                r["completeness"],
                r["staleness"],
                r["staleness_by_depth"]["3+"],
                r["collateral_rate"],
                r["mean_recomputes"],
            )
        )
    r = evaluation["oracle"]["rates"]
    lines.append(
        "| %s | %.3f | %.3f | %.3f | %.4f | %.1f |"
        % (
            "Oracle closure (control)",
            r["completeness"],
            r["staleness"],
            r["staleness_by_depth"]["3+"],
            r["collateral_rate"],
            r["mean_recomputes"],
        )
    )
    lines.append("")
    lines.append(
        "Reading: the negation-only baseline works at depth 1 "
        "(where explicit mentions live) and collapses below it; the "
        "recency window decays the same way, one window-membership "
        "coin flip per chain link. Recorded-edge closure removes "
        "most deep staleness, its own depth gradient is the "
        "signature of the 10% unlogged-edge rate, and the oracle "
        "control shows the remainder is a provenance-logging gap "
        "rather than a policy gap. The aggressive flush is the only "
        "policy that damages beliefs the update never touched."
    )
    return "\n".join(lines) + "\n"
