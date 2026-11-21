"""Streamlit dashboard for the Invalidation Closure Audit.

Three tabs:
1. One update - a single root-fact change on one seeded graph, and
   what each memory policy leaves behind: staleness, collateral,
   cost.
2. Depth profile - silent staleness by derivation depth per policy;
   the deep rows are where stale beliefs hide.
3. Evaluation - the aggregated multi-seed headline, including the
   oracle-closure control that prices the provenance-logging gap.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st

from invalidation_closure.evaluate import run_evaluation, run_single
from invalidation_closure.models import POLICIES, POLICY_LABELS


@st.cache_data(show_spinner=False)
def load_single(seed):
    return run_single(int(seed), n_beliefs=80)


@st.cache_data(show_spinner=False)
def load_evaluation():
    return run_evaluation(seeds=(301, 302), sizes=(60, 150))


def _rows(result):
    rows = []
    for policy in POLICIES:
        r = result["policies"][policy]["rates"]
        rows.append(
            {
                "policy": POLICY_LABELS[policy],
                "completeness": round(r["completeness"], 3),
                "staleness": round(r["staleness"], 3),
                "deep staleness": round(r["staleness_by_depth"]["3+"], 3),
                "collateral": round(r["collateral_rate"], 4),
                "recomputes": round(r["mean_recomputes"], 1),
            }
        )
    r = result["oracle"]["rates"]
    rows.append(
        {
            "policy": "Oracle closure (control)",
            "completeness": round(r["completeness"], 3),
            "staleness": round(r["staleness"], 3),
            "deep staleness": round(r["staleness_by_depth"]["3+"], 3),
            "collateral": round(r["collateral_rate"], 4),
            "recomputes": round(r["mean_recomputes"], 1),
        }
    )
    return rows


def tab_one_update():
    st.subheader("One root-fact update, five memory policies")
    seed = st.selectbox("Graph seed", [7, 21, 42], index=0)
    result = load_single(seed)
    st.write(
        "Root fact %d changes %d -> %d on an %d-belief graph; %d "
        "derived beliefs change in truth. Each policy is scored "
        "against that ground-truth recomputation."
        % (
            result["root_id"],
            result["old_value"],
            result["new_value"],
            result["n_beliefs"],
            result["n_affected"],
        )
    )
    chart = {
        "staleness": [
            result["policies"][p]["rates"]["staleness"] for p in POLICIES
        ]
        + [result["oracle"]["rates"]["staleness"]],
        "collateral": [
            result["policies"][p]["rates"]["collateral_rate"]
            for p in POLICIES
        ]
        + [result["oracle"]["rates"]["collateral_rate"]],
    }
    st.bar_chart(chart)
    st.write(
        "Policy order: %s, then the oracle control."
        % ", ".join(POLICY_LABELS[p] for p in POLICIES)
    )
    st.table(_rows(result))


def tab_depth_profile():
    st.subheader("Silent staleness by derivation depth")
    seed = st.selectbox("Graph seed", [7, 21, 42], index=0, key="depth_seed")
    result = load_single(seed)
    st.write(
        "A belief at depth 3 was derived from a derivation of a "
        "derivation. Policies that propagate one hop - or that only "
        "see explicit mentions - leave exactly these beliefs acting "
        "on the old fact."
    )
    chart = {}
    for policy in POLICIES:
        by_depth = result["policies"][policy]["rates"]["staleness_by_depth"]
        chart[POLICY_LABELS[policy]] = [
            by_depth["1"],
            by_depth["2"],
            by_depth["3+"],
        ]
    oracle = result["oracle"]["rates"]["staleness_by_depth"]
    chart["Oracle closure (control)"] = [
        oracle["1"],
        oracle["2"],
        oracle["3+"],
    ]
    st.bar_chart(chart)
    st.write("Rows are depth buckets 1, 2, 3+ in order.")
    stale = result["stale_examples"]["negation_only"]
    st.write(
        "Negation-only leaves %d beliefs silently stale on this "
        "update; the first ids are %s."
        % (len(stale), ", ".join(str(s) for s in stale[:10]) or "-")
    )


def tab_evaluation():
    st.subheader("Aggregated evaluation (reduced slice)")
    evaluation = load_evaluation()
    st.write(
        "%d graphs, %d update events, %.1f beliefs affected per "
        "update on average. The shipped results/ use the full "
        "6-seed x 3-size configuration."
        % (
            evaluation["n_graphs"],
            evaluation["n_updates"],
            evaluation["mean_affected_per_update"],
        )
    )
    st.table(_rows(evaluation))
    oracle = evaluation["oracle"]["rates"]
    closure = evaluation["policies"]["dependency_closure"]["rates"]
    st.write(
        "Recorded-edge closure leaves %.3f staleness; the oracle "
        "over the complete edge set leaves %.3f. The difference is "
        "the price of unlogged provenance - a logging problem, not "
        "a policy problem."
        % (closure["staleness"], oracle["staleness"])
    )


def main():
    st.title("Invalidation Closure Audit")
    st.write(
        "When one fact in an agent's memory changes, does everything "
        "derived from it change too? Pick a policy's numbers apart "
        "below."
    )
    tab1, tab2, tab3 = st.tabs(
        ["One update", "Depth profile", "Evaluation"]
    )
    with tab1:
        tab_one_update()
    with tab2:
        tab_depth_profile()
    with tab3:
        tab_evaluation()


if __name__ == "__main__":
    main()
