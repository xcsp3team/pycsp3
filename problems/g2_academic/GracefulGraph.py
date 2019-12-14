from pycsp3 import *

# Problem 053 at CSPLib

k = data.k  # size of each clique K (number of nodes)
p = data.p  # size of each path P (or equivalently, number of cliques)
nEdges = int(((k * (k - 1)) * p) / 2 + k * (p - 1))

# cn[i][j] is the color of the jth node of the ith clique
cn = VarArray(size=[p, k], dom=range(nEdges + 1))

# ce[i][j1][j2] is the color of the edge (j1,j2) of the ith clique, for j1 strictly less than j2
ce = VarArray(size=[p, k, k], dom=range(1, nEdges + 1), when=lambda i, j1, j2: j1 < j2)

# cp[i][j] is the color of the jth edge of the ith path
cp = VarArray(size=[p - 1, k], dom=range(1, nEdges + 1))

satisfy(
    # all nodes are colored differently
    AllDifferent(x for x in cn),

    # all edges are colored differently
    AllDifferent(x for x in ce + cp),

    # computing colors of edges from colors of nodes
    [
        [ce[i][j1][j2] == dist(cn[i][j1], cn[i][j2]) for i in range(p) for j1 in range(k) for j2 in range(j1 + 1, k)],

        [cp[i][j] == dist(cn[i][j], cn[i + 1][j]) for i in range(p - 1) for j in range(k)]
    ]
)
