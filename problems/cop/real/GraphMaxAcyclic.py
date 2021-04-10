"""
Given a edge-weighted directed graph with possibly many cycles, the task is to find an acyclic sub-graph of maximal weight.

Examples of Execution:
  python3 GraphMaxAcyclic.py -data=GraphMaxAcyclic_example.json
  python3 GraphMaxAcyclic.py -data=GraphMaxAcyclic_example.json -variant=cnt
  python3 GraphMaxAcyclic.py -data=GraphMaxAcyclic_example.txt -dataparser=GraphMaxAcyclic_Parser.py
"""

from pycsp3 import *

n, arcs = data

valid_arcs = [(i, j) for i in range(n) for j in range(n) if i != j and arcs[i][j] != 0]
valid_numbers = [len([(i, j) for i in range(n) if (i, j) in valid_arcs]) for j in range(n)]

# x[i] is the number associated with the ith node; arcs are only possible from greater to lower numbers (nodes)
x = VarArray(size=n, dom=range(n))

# a[i][j] is 1 iff the arc from i to j is selected
a = VarArray(size=[n, n], dom=lambda i, j: {0, 1} if (i, j) in valid_arcs else None)

satisfy(
    # different numbers must be associated to nodes
    AllDifferent(x)
)

if not variant():
    satisfy(
        # ensuring acyclicity
        iff(x[i] > x[j], a[i][j] == 1) for (i, j) in valid_arcs
    )

elif variant("cnt"):
    satisfy(
        # ensuring acyclicity
        [imply(x[i] <= x[j], a[i][j] == 0) for (i, j) in valid_arcs],

        [Count(a[:, j], value=1) <= 3 for j in range(n) if valid_numbers[j] > 3]
    )

maximize(
    # maximising the summed weight of selected arcs
    Sum(a[i][j] * arcs[i][j] for (i, j) in valid_arcs)
)

""" Comments
1) a possible variant "smart ?
   elif variant("smart"):
      # c[i][j] is the cost of the link between i and j (whatever the direction)
      c = varArray(size=[n, n], dom=lambda i, j: {arcs[i][j], arcs[j][i]}, when=lambda i, j: (arcs[i][j] != 0 or arcs[j][i] != 0) and i < j)
      ... TODO
"""