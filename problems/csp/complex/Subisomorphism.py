"""
See, e.g., "AllDifferent-based filtering for subgraph isomorphism"  by Christine Solnon, Artificial Intelligence, 174(12-13): 850-864 (2010)

Example of Execution:
  python3 Subisomorphism.py -data=Subisomorphism_A-01.json
"""

from pycsp3 import *

n, m, p_edges, t_edges = data


def structures():
    both_way_table = {(i, j) for (i, j) in t_edges} | {(j, i) for (i, j) in t_edges}
    p_degrees = [len([edge for edge in p_edges if i in edge]) for i in range(n)]
    t_degrees = [len([edge for edge in t_edges if i in edge]) for i in range(m)]
    degree_conflicts = [{j for j in range(m) if t_degrees[j] < p_degrees[i]} for i in range(n)]
    return [i for (i, j) in p_edges if i == j], [i for (i, j) in t_edges if i == j], both_way_table, degree_conflicts


p_loops, t_loops, T, conflicts = structures()

# x[i] is the target node to which the ith pattern node is mapped
x = VarArray(size=n, dom=range(m))

satisfy(
    # ensuring injectivity
    AllDifferent(x),

    # preserving edges
    [(x[i], x[j]) in T for (i, j) in p_edges],

    # being careful of self-loops
    [x[i] in t_loops for i in p_loops],

    # tag(redundant-constraints)
    [x[i] not in C for i, C in enumerate(conflicts)]
)
