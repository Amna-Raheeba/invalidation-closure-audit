"""Core data model: beliefs, derivation ops, and shared constants.

A memory is a dependency graph of beliefs. Root beliefs are facts
with directly stored values. Derived beliefs are computed from their
parents by a deterministic derivation op, so the ground-truth value
of every belief is always known - before and after any update. That
is what makes the audit possible: when a root fact changes, we can
recompute the truth for the whole graph and check, belief by belief,
whether a memory policy's stored state matches it.
"""

from dataclasses import dataclass

VALUE_MIN = -500
VALUE_MAX = 500

# Derivation ops by parent count. Single-parent ops transform one
# input; multi-parent ops combine two or three.
SINGLE_PARENT_OPS = ("neg", "inc", "dbl")
MULTI_PARENT_OPS = ("add", "diff", "mul", "max", "min")
ALL_OPS = SINGLE_PARENT_OPS + MULTI_PARENT_OPS

# The five memory policies under audit, in increasing order of how
# much machinery they assume. "none" and "negation_only" are the
# baselines; "dependency_closure" is the strongest policy that still
# works by targeted recomputation; "aggressive_flush" trades the
# opposite failure direction (collateral damage) for freshness.
POLICIES = (
    "none",
    "negation_only",
    "recency_wins",
    "dependency_closure",
    "aggressive_flush",
)

POLICY_LABELS = {
    "none": "Root only (no propagation)",
    "negation_only": "Explicit-negation only",
    "recency_wins": "Recency window",
    "dependency_closure": "Dependency closure",
    "aggressive_flush": "Aggressive cluster flush",
}

DEPTH_BUCKETS = ("1", "2", "3+")


def clamp(value):
    if value < VALUE_MIN:
        return VALUE_MIN
    if value > VALUE_MAX:
        return VALUE_MAX
    return value


def derive(op, values):
    """Apply a derivation op to parent values (ground-truth semantics).

    The result is clamped to the value range. Ops are total: a
    multi-parent op given one value degrades gracefully so hand-built
    graphs in tests cannot crash the derivation.
    """
    if not values:
        raise ValueError("derive needs at least one parent value")
    if op == "neg":
        return clamp(-values[0])
    if op == "inc":
        return clamp(values[0] + 3)
    if op == "dbl":
        return clamp(values[0] * 2)
    if op == "add":
        return clamp(sum(values))
    if op == "diff":
        if len(values) == 1:
            return clamp(values[0])
        return clamp(values[0] - values[1])
    if op == "mul":
        out = 1
        for value in values:
            out *= value
        return clamp(out)
    if op == "max":
        return clamp(max(values))
    if op == "min":
        return clamp(min(values))
    raise ValueError("unknown op: %s" % op)


def depth_bucket(depth):
    if depth <= 1:
        return "1"
    if depth == 2:
        return "2"
    return "3+"


@dataclass
class Belief:
    """One belief in the memory graph.

    ``value`` is the ground-truth value (what the belief should hold
    given the current root facts). ``explicit_refs`` lists root facts
    the belief's stored statement explicitly mentions - the only
    channel the negation-only policy can see. ``session_offset`` is a
    private input contribution that lives only in the belief's own
    record: in-place recomputation preserves it, but a flush that
    deletes and rebuilds the record loses it. ``edge_recorded``
    aligns with ``parents`` and marks which dependency edges the
    store actually logged - the closure policy can only follow
    recorded edges.
    """

    id: int
    kind: str  # "root" or "derived"
    op: object  # op name for derived beliefs, None for roots
    parents: tuple
    value: int
    depth: int
    cluster: int
    explicit_refs: frozenset = frozenset()
    session_offset: int = 0
    edge_recorded: tuple = ()
    # When the belief was last written. Creation order by default,
    # but a living memory re-derives and re-stores beliefs over
    # time, so the generator's refresh pass moves some beliefs to
    # late write times. The recency policy can only see the most
    # recent writes.
    write_time: int = 0

    @property
    def unrecoverable(self):
        """True when part of this belief's value lives only in its
        own record (a session-only input), so deleting the record
        destroys information no recomputation can restore."""
        return self.session_offset != 0

    def recompute(self, parent_values, keep_session=True):
        """Value this belief takes when re-derived from parent values.

        In-place recomputation keeps the session contribution; a
        rebuild-from-scratch (flush) does not.
        """
        base = derive(self.op, parent_values)
        if keep_session:
            return clamp(base + self.session_offset)
        return base

    def to_dict(self):
        return {
            "id": self.id,
            "kind": self.kind,
            "op": self.op,
            "parents": list(self.parents),
            "value": self.value,
            "depth": self.depth,
            "cluster": self.cluster,
            "explicit_refs": sorted(self.explicit_refs),
            "session_offset": self.session_offset,
            "edge_recorded": list(self.edge_recorded),
            "write_time": self.write_time,
        }
