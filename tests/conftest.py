import pytest

from invalidation_closure.graph import BeliefGraph
from invalidation_closure.models import Belief


def make_belief(
    belief_id,
    kind="derived",
    op=None,
    parents=(),
    value=0,
    depth=0,
    cluster=0,
    refs=(),
    offset=0,
    recorded=None,
    write_time=0,
):
    if recorded is None:
        recorded = tuple(True for _ in parents)
    return Belief(
        id=belief_id,
        kind=kind,
        op=op,
        parents=tuple(parents),
        value=value,
        depth=depth,
        cluster=cluster,
        explicit_refs=frozenset(refs),
        session_offset=offset,
        edge_recorded=tuple(recorded),
        write_time=write_time,
    )


@pytest.fixture()
def hand_graph():
    """A small graph with known ground truth.

    Roots: 0 (value 4, cluster 0), 1 (value 2, cluster 1).
    2 = dbl(0) = 8, depth 1, cluster 0, mentions root 0.
    3 = inc(2) = 11, depth 2, cluster 0.
    4 = add(0, 1) = 6, depth 1, cluster 1.
    5 = neg(3) = -11, depth 3, cluster 0, mentions root 0, and its
        edge from 3 is UNRECORDED.
    6 = inc(1) + session 4 = 9, depth 1, cluster 0 - not a dependent
        of root 0, but in root 0's cluster and unrecoverable.

    Updating root 0 from 4 to 7 changes the truth of 2 (14), 3 (17),
    4 (9), and 5 (-17); 6 stays 9.
    """
    beliefs = [
        make_belief(0, kind="root", value=4, depth=0, cluster=0),
        make_belief(1, kind="root", value=2, depth=0, cluster=1),
        make_belief(2, op="dbl", parents=(0,), value=8, depth=1,
                    cluster=0, refs=(0,)),
        make_belief(3, op="inc", parents=(2,), value=11, depth=2,
                    cluster=0),
        make_belief(4, op="add", parents=(0, 1), value=6, depth=1,
                    cluster=1),
        make_belief(5, op="neg", parents=(3,), value=-11, depth=3,
                    cluster=0, refs=(0,), recorded=(False,)),
        make_belief(6, op="inc", parents=(1,), value=9, depth=1,
                    cluster=0, offset=4),
    ]
    return BeliefGraph(beliefs)
