from pycsp3 import *

"""
 See e.g. "AllDifferent-based filtering for subgraph isomorphism"  by Christine Solnon, Artificial Intelligence, 174(12-13): 850-864 (2010)
"""

n, m = data.nPatternNodes, data.nTargetNodes


def structures():
    p_edges, t_edges = data.patternEdges, data.targetEdges
    p_degrees = [len([edge for edge in p_edges if i in edge]) for i in range(n)]
    t_degrees = [len([edge for edge in t_edges if i in edge]) for i in range(m)]
    both_way_table = {(i, j) for (i, j) in t_edges} | {(j, i) for (i, j) in t_edges}
    degree_conflicts = [[j for j in range(m) if t_degrees[j] < p_degrees[i]] for i in range(n)]
    return [i for (i, j) in p_edges if i == j], [i for (i, j) in t_edges if i == j], both_way_table, degree_conflicts


p_loops, t_loops, table, degree_conflicts = structures()

# x[i] is the target node to which the ith pattern node is mapped
x = VarArray(size=n, dom=range(m))

satisfy(
    # ensuring injectivity
    AllDifferent(x),

    # preserving edges
    [(x[i], x[j]) in table for (i, j) in data.patternEdges],

    # being careful of self-loops
    [x[i] in t_loops for i in p_loops],

    # tag(redundant-constraints)
    [x[i] not in conflicts for i, conflicts in enumerate(degree_conflicts) if len(conflicts) > 0]
)
