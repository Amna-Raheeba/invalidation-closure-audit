"""Invalidation Closure Audit.

When one fact in an agent's memory changes, everything derived from
that fact should change with it. Real memory stores rarely manage
that: they fix the fact itself, maybe its explicit contradictions,
and leave derived beliefs quietly acting on the old value - silent
staleness, worst exactly at the depths nobody re-checks.

This audit models memory as a seeded dependency graph of beliefs
with known ground truth, fires one root-fact update at a time, and
scores five memory policies on invalidation completeness, silent
staleness per depth, collateral damage to beliefs the update never
touched, and recomputation cost. An oracle closure over the complete
edge set separates policy failure from provenance-recording failure.
"""

__version__ = "0.1.0"
__author__ = "Amna Raheeba"
