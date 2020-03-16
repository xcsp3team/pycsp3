from pycsp3 import *

n, colorings = data.nNodes, dicts_values(data.colorings) if data.colorings else []  # multi-coloring not taken into account for the moment

# c[i] is the color assigned to the ith node
c = VarArray(size=n, dom=range(n))

satisfy(
    [c[i] != c[j] if d == 1 else dist(c[i], c[j]) >= d for (i, j, d) in data.edges],

    # nodes with preassigned colors
    [c[i] == colors[0] for (i, colors) in colorings if len(colors) == 1],

    # nodes with subsets of prefixed colors
    [c[i] in colors for (i, colors) in colorings if len(colors) > 1]
)

if not variant():
    minimize(
        # minimizing the number of used colors
        Maximum(c)
    )
elif variant("sum"):
    minimize(
        # minimizing the sum of colors assigned to nodes
        Sum(c)
    )

# if we have data.colorings instead of  dicts_values(data.colorings), we have to write:
# [c[coloring.node] == coloring.colors[0] for coloring in colorings if len(coloring.colors) == 1],
