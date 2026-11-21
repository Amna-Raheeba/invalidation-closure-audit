# Changelog

## 0.1.0 - 2026-11-22

- Initial release: seeded belief-dependency graph generator (60 /
  150 / 300 beliefs, depth up to 5, topic clusters) with planted
  store imperfections - ~10% unrecorded dependency edges, explicit
  fact mentions concentrated at depth 1, session-only input
  contributions on ~15% of derived beliefs, and a refresh pass that
  spreads recent write times across depths.
- Five memory policies scored on the same update events:
  root-only, explicit-negation-only, recency window, dependency
  closure over recorded edges, and aggressive cluster flush - plus
  an oracle-closure control over the complete edge set that
  separates policy failure from provenance-recording failure.
- Scoring: invalidation completeness, silent staleness overall and
  per depth bucket (pooled counts, never per-run averages),
  collateral damage to unaffected beliefs, touched-but-wrong vs
  untouched stale split, and recomputation cost.
- Headline measurements: negation-only leaves 93.7% of affected
  beliefs silently stale (97.5% at depth >= 3) while repairing
  ~73% at depth 1; recorded-edge closure cuts deep staleness to
  26.4% with the oracle at 0.0%; the recency window spends 15.8
  recomputations per update for 95.9% deep staleness; the flush is
  the only policy with collateral damage (3.48%).
- Streamlit dashboard (3 tabs), CLI demo/evaluate commands, and a
  reproduction script with a headline-drift guard.
