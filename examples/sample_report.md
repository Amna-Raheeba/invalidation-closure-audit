# Sample report

Captured from `python -m invalidation_closure demo` and `python examples/run_audit.py` on the seeded demo graph (seed 7, 80 beliefs).

## Demo

Invalidation closure audit - single update
Graph: 80 beliefs (seed 7, max depth 5)
Update: root fact 3 changes 3 -> 5 (cluster 1); 46 derived beliefs change in truth
Affected by depth: depth 1: 1, depth 2: 2, depth 3: 4, depth 4: 10, depth 5: 29

Root only (no propagation)   complete 0.000 | stale 1.000 (depth>=3 1.000) | collateral 0.0000 | recomputes 0.0
Explicit-negation only       complete 0.022 | stale 0.978 (depth>=3 1.000) | collateral 0.0000 | recomputes 3.0
Recency window               complete 0.000 | stale 1.000 (depth>=3 1.000) | collateral 0.0000 | recomputes 24.0
Dependency closure           complete 0.457 | stale 0.543 (depth>=3 0.558) | collateral 0.0000 | recomputes 27.0
Aggressive cluster flush     complete 0.283 | stale 0.717 (depth>=3 0.767) | collateral 0.0000 | recomputes 18.0
Oracle closure (control)     complete 1.000 | stale 0.000 (depth>=3 0.000) | collateral 0.0000 | recomputes 55.0

Explicit-negation only leaves 45 beliefs silently stale (first ids: 17, 18, 19, 20, 22, 23, 26, 27)
Dependency closure leaves 25 beliefs silently stale (first ids: 17, 18, 19, 20, 26, 28, 30, 31)
## Example audit

Root fact 3: 3 -> 5; 46 beliefs affected in truth
Root only (no propagation)   stale 1.000 (deep 1.000) | collateral 0.0000 | recomputes 0
Explicit-negation only       stale 0.978 (deep 1.000) | collateral 0.0000 | recomputes 3
Recency window               stale 1.000 (deep 1.000) | collateral 0.0000 | recomputes 24
Dependency closure           stale 0.543 (deep 0.558) | collateral 0.0000 | recomputes 27
Aggressive cluster flush     stale 0.717 (deep 0.767) | collateral 0.0000 | recomputes 18
Oracle closure (control)     stale 0.000 (deep 0.000) | collateral 0.0000 | recomputes 55
