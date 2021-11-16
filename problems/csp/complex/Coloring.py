"""
See https://en.wikipedia.org/wiki/Graph_coloring

Examples of Execution:
  python3 Coloring.py -data=Coloring_rand1.json
  python3 Coloring.py -data=Coloring_rand1.json -variant=csp
"""

from pycsp3 import *

nNodes, nColors, edges = data

# x[i] is the color assigned to the ith node of the graph
x = VarArray(size=nNodes, dom=range(nColors))

satisfy(
    # two adjacent nodes must be colored differently
    x[i] != x[j] for (i, j) in edges
)

if not variant():
    minimize(
        # minimizing the greatest used color index (and, consequently, the number of colors)
        Maximum(x)
    )

elif variant("csp"):
    satisfy(
        # tag(symmetry-breaking)
        x[i] <= i for i in range(min(nNodes, nColors))
    )
