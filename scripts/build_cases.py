"""Build the seeded demo graph summary stored in data/cases.json.

The stored file is the full belief list of the demo graph (seed 7,
80 beliefs) plus the ground truth of its largest update: which root
changes, and which derived beliefs are affected, by depth. Graphs
are always regenerated deterministically from the seed; the stored
file exists so readers can inspect one concrete case without
running anything.
"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from invalidation_closure.evaluate import _affected_by_depth
from invalidation_closure.generate import choose_updates, generate_graph


def main():
    graph = generate_graph(7, 80, 5)
    root_id, new_value = choose_updates(graph, count=1)[0]
    _, affected = graph.affected_after(root_id, new_value)
    payload = {
        "seed": 7,
        "n_beliefs": len(graph),
        "max_depth": 5,
        "update": {
            "root_id": root_id,
            "old_value": graph.by_id[root_id].value,
            "new_value": new_value,
            "affected_ids": sorted(affected),
            "affected_by_depth": dict(
                (str(k), v)
                for k, v in sorted(_affected_by_depth(graph, affected).items())
            ),
        },
        "beliefs": [belief.to_dict() for belief in graph.beliefs],
    }
    out = os.path.join(os.path.dirname(__file__), "..", "data", "cases.json")
    with open(out, "w") as fh:
        json.dump(payload, fh, indent=1, sort_keys=True)
    print(
        "Wrote %s (%d beliefs, %d affected)"
        % (out, len(graph), len(affected))
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
