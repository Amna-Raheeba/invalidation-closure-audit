# Invalidation Closure Audit

## 1. What this is

When one fact in an agent's memory changes, everything *derived
from it* should change too. Real memory stores rarely manage that.
They update the fact itself, maybe fix the beliefs that explicitly
contradict it, and stop - leaving derived beliefs quietly acting on
the old value. That is **silent staleness**, and it is worst exactly
where nobody looks: three, four, five derivations away from the
fact that changed.

This audit measures how far an update *should* propagate versus how
far it *does*, per memory policy. Memory is modelled as a seeded
dependency graph of beliefs with known ground truth, one root fact
is changed at a time, and five policies are scored on:

1. **invalidation completeness** - of the beliefs whose true value
   changed, the fraction left holding the new true value;
2. **silent staleness** - the complement, reported overall and per
   derivation depth;
3. **collateral damage** - beliefs whose true value did *not*
   change but the policy broke anyway;
4. **cost** - recomputations per update.

## 2. The novel mechanism

1. **Ground truth by construction.** Every derived belief is a
   deterministic function of its parents, so after any root update
   the whole graph's truth is recomputed exactly. Staleness is
   never estimated - it is counted, belief by belief, against the
   recomputation.
2. **Planted store imperfections.** The generator plants the three
   gaps real stores have: ~10% of dependency edges are never
   recorded (provenance gaps), explicit fact mentions are common at
   depth 1 (~65%) and rare deeper (~4%), and ~15% of beliefs carry a
   session-only input that lives only in their own record.
3. **Five policies, one event.** Root-only, explicit-negation-only,
   recency window, dependency closure, and aggressive cluster flush
   all face the same seeded updates on the same graphs.
4. **An oracle control that separates blame.** Closure over the
   *complete* edge set runs alongside the real policies. Whatever
   the oracle fixes but recorded-edge closure does not is a
   provenance-logging failure, not a policy failure - the audit
   prices the two separately.

## 3. Prior art and the differentiator

- **STALE** benchmarks whether live LLMs *notice* implicit
  conflicts in dialogue; **CICM** studies stale binding in-context;
  **RevisionTrace** tests dependency propagation in abstract
  arithmetic state with hand-built strategies. All three probe a
  model's behaviour around updates.
- **Governed Shared Memory** (a sibling project) governs concurrent
  writes to a shared store - who may write, with what provenance.
  This audit is about the other axis: one writer, one update, and
  what happens *inside* one memory over time.

**Differentiator:** no existing tool audits memory-store update
*policies* over a belief-dependency graph with planted ground
truth, scoring completeness, per-depth silent staleness, and
collateral damage together - and none separates the policy's share
of the staleness from the provenance logger's share.

## 4. The belief-graph simulator

- Seeded generator (`invalidation_closure/generate.py`): graphs of
  60 / 150 / 300 beliefs, ~20% root facts with values 2-9, derived
  beliefs combining 1-3 parents via `neg / inc / dbl / add / diff /
  mul / max / min`, clamped to [-500, 500]. Parent choice is
  depth-weighted and a forced chain guarantees depth 5 is reached.
- Beliefs sit in topic clusters (derived beliefs usually inherit
  their first parent's cluster; ~15% cross over).
- A refresh pass re-stores ~35% of derived beliefs at late write
  times, modelling a living memory that re-derives beliefs over
  time - so "recently written" cuts across depths.
- Update events are chosen deterministically per graph: the roots
  with the largest, median, and smallest qualifying blast radius
  (>= 4 affected beliefs), each changed by a fixed delta.

## 5. The five policies

1. **Root only** - the update writes the fact and stops. The lower
   bound.
2. **Explicit-negation only** - recomputes beliefs whose statement
   explicitly mentions the changed fact. No graph, no cascade: a
   mentioning belief whose parents are stale is recomputed *from
   stale parents*.
3. **Recency window** - revalidates dependents of the fact that
   sit among the most recent third of writes. A belief is truly
   repaired only if its whole chain back to the fact is in-window.
4. **Dependency closure** - recomputes the full transitive closure
   of the update, but only over edges the store actually recorded.
5. **Aggressive cluster flush** - deletes and rebuilds every belief
   in the fact's cluster. Total freshness inside the cluster;
   rebuilt beliefs lose their session-only input, and dependents
   in other clusters are never touched.

Plus the **oracle closure** control: closure over the complete edge
set - not deployable, present to price the logging gap.

## 6. Headline results (measured)

18 seeded graphs (6 seeds x sizes 60/150/300, max depth 5), 54
update events, 24.8 beliefs affected per update on average. Counts
pooled across all runs before rates are computed. Full tables in
`results/`.

| Policy | Completeness | Staleness | Stale @ depth 1 | Stale @ depth 2 | Stale @ depth >= 3 | Collateral | Recomputes |
|---|---|---|---|---|---|---|---|
| Root only | 0.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.0000 | 0.0 |
| Explicit-negation only | 0.063 | 0.937 | 0.266 | 0.882 | 0.975 | 0.0000 | 3.3 |
| Recency window | 0.068 | 0.932 | 0.594 | 0.779 | 0.959 | 0.0000 | 15.8 |
| Dependency closure | 0.747 | 0.253 | 0.109 | 0.191 | 0.264 | 0.0007 | 29.2 |
| Aggressive cluster flush | 0.230 | 0.770 | 0.344 | 0.500 | 0.808 | 0.0348 | 29.2 |
| Oracle closure (control) | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.0000 | 37.9 |

Reading the table:

- **Negation-only works exactly one hop deep.** It repairs ~73% of
  depth-1 dependents (where explicit mentions live) and 2.5% of
  depth >= 3. An audit that only checks direct dependents would
  certify this store.
- **The recency window spends 15.8 recomputations per update for
  almost nothing at depth** (95.9% deep staleness): each chain link
  is an independent window-membership coin flip, so repair
  probability decays geometrically while the work does not.
- **Closure's own depth gradient is the logging gap's signature.**
  Recorded-edge closure cuts deep staleness to 26.4%, rising with
  depth (0.109 -> 0.191 -> 0.264) exactly as a 10% unlogged-edge
  rate predicts - longer paths are likelier to contain a missing
  edge. The oracle scores 0.000 at every depth, so *all* of
  closure's residual staleness is unlogged provenance, none of it
  is the policy.
- **The flush fails in the opposite direction, and only it does.**
  It is the sole policy with collateral damage (3.48% of unaffected
  beliefs broken - the session-only inputs its rebuilds destroy),
  yet still leaves 80.8% of deep dependents stale, because deep
  chains cross cluster boundaries the flush never visits.
- Closure's collateral is 0.0007, not exactly zero: a handful of
  coincidentally-correct beliefs were recomputed from a stale
  sibling parent and moved off a value that happened to be right.
  Reported, not rounded away.

## 7. Honest limits

- Beliefs here are integer arithmetic; real beliefs are text, and
  real "recomputation" is a model call that can err on its own.
  The audit prices *propagation policy*, not derivation fidelity.
- The five policies are stylised archetypes of store designs, not
  any specific product's algorithm.
- The planted rates (10% unlogged edges, 65% / 4% explicit
  mentions, 15% session inputs, 35% refreshes, one-third recency
  window) are declared conventions. Absolute numbers move with
  them; the depth gradients and the policy ordering are the
  findings.
- One update at a time, single writer. Concurrent updates and
  conflicting writes are a different problem (see Governed Shared
  Memory).

## 8. Usage

```bash
pip install pytest streamlit   # tests + dashboard; runtime is stdlib only

python -m invalidation_closure demo       # one graph, one update, all policies
python -m invalidation_closure evaluate --out results
python examples/run_audit.py              # compact policy verdicts
python scripts/reproduce_results.py       # drift-guarded reproduction
streamlit run app.py                      # dashboard (3 tabs)
```

## 9. Repository layout

- `invalidation_closure/` - models, graph, generator, policies,
  scoring, evaluation, reports, CLI.
- `data/cases.json` - the demo graph and its update ground truth.
- `results/` - the shipped evaluation (JSON, CSV, summary,
  headline), reproduced by `scripts/reproduce_results.py`.
- `notebooks/` - runnable walkthroughs of the demo and a reduced
  evaluation slice.
- `tests/` - 66 tests: derivation semantics, graph reachability,
  generator invariants, per-policy behaviour on a hand-built graph
  with known truth, scoring, CLI, dashboard, and the stored-result
  guards.

MIT license. Author: Amna Raheeba.
