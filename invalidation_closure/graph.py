"""The belief graph: adjacency, reachability, and ground truth.

Beliefs are stored in topological order (a belief's id is always
greater than its parents' ids), so a single pass in id order
recomputes the whole graph. The graph precomputes two dependent
adjacencies: the full one (every dependency edge) and the recorded
one (only edges the store logged). The gap between them is the
provenance-recording gap the closure policy falls into.
"""

class BeliefGraph:
    def __init__(self, beliefs):
        self.beliefs = list(beliefs)
        self.by_id = dict((b.id, b) for b in self.beliefs)
        self.dependents = dict((b.id, []) for b in self.beliefs)
        self.recorded_dependents = dict((b.id, []) for b in self.beliefs)
        for belief in self.beliefs:
            for idx, parent in enumerate(belief.parents):
                self.dependents[parent].append(belief.id)
                if belief.edge_recorded and belief.edge_recorded[idx]:
                    self.recorded_dependents[parent].append(belief.id)
        self.roots = [b.id for b in self.beliefs if b.kind == "root"]

    def __len__(self):
        return len(self.beliefs)

    def root_ancestors(self, belief_id):
        """All root facts a belief (transitively) depends on."""
        seen = set()
        stack = list(self.by_id[belief_id].parents)
        roots = set()
        while stack:
            current = stack.pop()
            if current in seen:
                continue
            seen.add(current)
            belief = self.by_id[current]
            if belief.kind == "root":
                roots.add(current)
            else:
                stack.extend(belief.parents)
        return roots

    def reachable(self, root_id, recorded_only=False):
        """Beliefs reachable from a root following dependent edges.

        With ``recorded_only`` this is the set the dependency-closure
        policy can possibly reach; the difference from the full set
        is the closure gap created by unlogged provenance.
        """
        adjacency = (
            self.recorded_dependents if recorded_only else self.dependents
        )
        seen = set()
        stack = list(adjacency[root_id])
        while stack:
            current = stack.pop()
            if current in seen:
                continue
            seen.add(current)
            stack.extend(adjacency[current])
        return seen

    def true_values_after(self, root_id, new_value):
        """Ground-truth value of every belief after a root update.

        One pass in id order (topological). Derived beliefs keep
        their session contribution: the truth is what the belief
        *should* hold, and the session input still exists in truth -
        only a flush that deletes the record loses it.
        """
        values = [b.value for b in self.beliefs]
        values[root_id] = new_value
        for belief in self.beliefs:
            if belief.kind == "derived":
                parent_values = [values[p] for p in belief.parents]
                values[belief.id] = belief.recompute(parent_values)
        return values

    def affected_after(self, root_id, new_value):
        """Derived beliefs whose true value changes under an update,
        mapped to their new true value."""
        truth = self.true_values_after(root_id, new_value)
        affected = {}
        for belief in self.beliefs:
            if belief.kind == "derived" and truth[belief.id] != belief.value:
                affected[belief.id] = truth[belief.id]
        return truth, affected
