# Evaluation summary

Seeded belief graphs (sizes 60, 150, 300, max depth 5), 18 graphs, 54 update events, 24.8 beliefs affected per update on average. Counts are pooled across all runs before rates are computed.

| Policy | Completeness | Staleness | Staleness depth>=3 | Collateral | Recomputes/update |
|---|---|---|---|---|---|
| Root only (no propagation) | 0.000 | 1.000 | 1.000 | 0.0000 | 0.0 |
| Explicit-negation only | 0.063 | 0.937 | 0.975 | 0.0000 | 3.3 |
| Recency window | 0.068 | 0.932 | 0.959 | 0.0000 | 15.8 |
| Dependency closure | 0.747 | 0.253 | 0.264 | 0.0007 | 29.2 |
| Aggressive cluster flush | 0.230 | 0.770 | 0.808 | 0.0348 | 29.2 |
| Oracle closure (control) | 1.000 | 0.000 | 0.000 | 0.0000 | 37.9 |

Reading: the negation-only baseline works at depth 1 (where explicit mentions live) and collapses below it; the recency window decays the same way, one window-membership coin flip per chain link. Recorded-edge closure removes most deep staleness, its own depth gradient is the signature of the 10% unlogged-edge rate, and the oracle control shows the remainder is a provenance-logging gap rather than a policy gap. The aggressive flush is the only policy that damages beliefs the update never touched.
