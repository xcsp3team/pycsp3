from pycsp3 import *

n, nColors, edges = data.nNodes, data.nColors, data.edges
assert len(edges) != 0

# x[i] is the color assigned to the ith node of the graph
x = VarArray(size=n, dom=range(nColors))

satisfy(
    # two adjacent nodes must be colored differently
    [x[i] != x[j] for (i, j) in edges]
)

if not variant():
    minimize(
        # minimizing the maximum used color index (and, consequently, the number of colors)
        Maximum(x)
    )

elif variant("csp"):
    satisfy(
        # tag(symmetry-breaking)
        x[i] <= i for i in range(min(n, nColors))
    )
