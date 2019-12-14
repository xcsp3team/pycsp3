from pycsp3 import *

nNodes, edges, colorings = data.nNodes, data.edges, data.colorings  # multi-coloring not taken into account for the moment
colorings = [] if colorings is None else colorings

# c[i] is the color assigned to the ith node
c = VarArray(size=nNodes, dom=range(nNodes))

satisfy(
    [c[i] != c[j] if d == 1 else dist(c[i], c[j]) >= d for (i, j, d) in edges],

    # nodes with subsets of prefixed colors
    [c[coloring.node] in coloring.colors for coloring in colorings if len(coloring.colors) > 1],

    # nodes with preassigned colors
    [c[coloring.node] == coloring.colors[0] for coloring in colorings if len(coloring.colors) == 1]
)

if variant("sum"):
    minimize(
        # minimizing the sum of colors assigned to nodes
        Sum(c)
    )
else:
    minimize(
        Maximum(c)
    )
