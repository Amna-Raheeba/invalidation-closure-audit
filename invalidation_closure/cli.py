"""Command-line interface.

Usage:
    python -m invalidation_closure demo
    python -m invalidation_closure evaluate --out results_dir
"""

import argparse
import csv
import json
import os
import sys

from .evaluate import headline_numbers, run_evaluation, run_single
from .models import POLICIES
from .report import render_evaluation_summary, render_single_report


def _jsonable(obj):
    if isinstance(obj, dict):
        return dict((k, _jsonable(v)) for k, v in obj.items())
    if isinstance(obj, (list, tuple)):
        return [_jsonable(v) for v in obj]
    if isinstance(obj, (set, frozenset)):
        return sorted(obj)
    if isinstance(obj, float):
        return round(obj, 6)
    return obj


def _counts_jsonable(counts):
    out = dict(counts)
    out["by_depth"] = dict(
        (bucket, dict(cell)) for bucket, cell in counts["by_depth"].items()
    )
    return out


def cmd_demo(args):
    result = run_single(7)
    sys.stdout.write(render_single_report(result))
    return 0


def cmd_evaluate(args):
    evaluation = run_evaluation()
    headline = headline_numbers(evaluation)
    out_dir = args.out
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)
    slim = {
        "seeds": evaluation["seeds"],
        "sizes": evaluation["sizes"],
        "max_depth": evaluation["max_depth"],
        "n_graphs": evaluation["n_graphs"],
        "n_updates": evaluation["n_updates"],
        "mean_affected_per_update": evaluation["mean_affected_per_update"],
        "policies": dict(
            (
                policy,
                {
                    "counts": _counts_jsonable(
                        evaluation["policies"][policy]["counts"]
                    ),
                    "rates": evaluation["policies"][policy]["rates"],
                },
            )
            for policy in POLICIES
        ),
        "oracle": {
            "counts": _counts_jsonable(evaluation["oracle"]["counts"]),
            "rates": evaluation["oracle"]["rates"],
        },
        "headline": headline,
    }
    with open(os.path.join(out_dir, "evaluation.json"), "w") as fh:
        json.dump(_jsonable(slim), fh, indent=2, sort_keys=True)
    with open(os.path.join(out_dir, "evaluation.csv"), "w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(
            [
                "policy",
                "completeness",
                "staleness",
                "staleness_depth_1",
                "staleness_depth_2",
                "staleness_depth_3plus",
                "collateral_rate",
                "mean_recomputes",
            ]
        )
        for policy in POLICIES:
            r = evaluation["policies"][policy]["rates"]
            writer.writerow(
                [
                    policy,
                    "%.4f" % r["completeness"],
                    "%.4f" % r["staleness"],
                    "%.4f" % r["staleness_by_depth"]["1"],
                    "%.4f" % r["staleness_by_depth"]["2"],
                    "%.4f" % r["staleness_by_depth"]["3+"],
                    "%.4f" % r["collateral_rate"],
                    "%.2f" % r["mean_recomputes"],
                ]
            )
        r = evaluation["oracle"]["rates"]
        writer.writerow(
            [
                "oracle_closure",
                "%.4f" % r["completeness"],
                "%.4f" % r["staleness"],
                "%.4f" % r["staleness_by_depth"]["1"],
                "%.4f" % r["staleness_by_depth"]["2"],
                "%.4f" % r["staleness_by_depth"]["3+"],
                "%.4f" % r["collateral_rate"],
                "%.2f" % r["mean_recomputes"],
            ]
        )
    with open(os.path.join(out_dir, "evaluation_summary.md"), "w") as fh:
        fh.write(render_evaluation_summary(evaluation, headline))
    with open(os.path.join(out_dir, "HEADLINE.md"), "w") as fh:
        fh.write("# Headline results\n\n")
        fh.write(
            "Across %d seeded update events on belief graphs of "
            "%s beliefs (max depth %d, %.1f beliefs affected per "
            "update), explicit-negation-only memory leaves %.1f%% "
            "of affected beliefs silently stale - and %.1f%% of "
            "those at depth >= 3. Dependency closure over the "
            "store's recorded edges cuts deep staleness to %.1f%% "
            "(oracle closure over the complete edge set: %.1f%%, "
            "so the remainder is a provenance-logging gap, not a "
            "policy gap). The recency window spends %.1f "
            "recomputations per update for almost nothing at depth "
            "(%.1f%% deep staleness): it repairs only beliefs whose "
            "entire chain back to the fact sits inside its window, "
            "and leaves the rest touched but still wrong. The "
            "aggressive cluster flush "
            "is freshest inside its cluster but is the only policy "
            "that breaks beliefs the update never touched: "
            "collateral damage %.2f%% of unaffected beliefs. Cost "
            "per update: negation-only %.1f recomputations, "
            "recency %.1f, closure %.1f, flush %.1f.\n"
            % (
                evaluation["n_updates"],
                "/".join(str(s) for s in evaluation["sizes"]),
                evaluation["max_depth"],
                evaluation["mean_affected_per_update"],
                100.0 * headline["staleness_negation_only"],
                100.0 * headline["staleness_deep_negation_only"],
                100.0 * headline["staleness_deep_dependency_closure"],
                100.0 * headline["staleness_deep_oracle_closure"],
                headline["recomputes_recency_wins"],
                100.0 * headline["staleness_deep_recency_wins"],
                100.0 * headline["collateral_aggressive_flush"],
                headline["recomputes_negation_only"],
                headline["recomputes_recency_wins"],
                headline["recomputes_dependency_closure"],
                headline["recomputes_aggressive_flush"],
            )
        )
    sys.stdout.write("Wrote evaluation results to %s\n" % out_dir)
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(prog="invalidation_closure")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("demo")
    eval_parser = sub.add_parser("evaluate")
    eval_parser.add_argument("--out", default="results")
    args = parser.parse_args(argv)
    if args.command == "demo":
        return cmd_demo(args)
    if args.command == "evaluate":
        return cmd_evaluate(args)
    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
