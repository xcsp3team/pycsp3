"""
For a given (undirected) graph G, the problem consists in arranging the nodes of the graph in a line
in such a way to minimize the sum of distances between adjacent nodes (in G).

Example of Execution:
  python3 LinearArrangement.py -data=MinLA01.json
"""

from pycsp3 import *

n, edges = data
edges = [(i, j) for i, j in edges]  # to be sure to have tuples

# x[i] denotes the position (in the line) of the ith node
x = VarArray(size=n, dom=range(n))

# d[i][j] denotes the distance in the line between the ith and jth nodes (if they are adjacent in the graph)
d = VarArray(size=[n, n], dom=lambda i, j: range(1, n) if (i, j) in edges else None)

satisfy(
    # putting nodes at different positions
    AllDifferent(x),

    # computing distances
    [d[i][j] == abs(x[i] - x[j]) for (i, j) in edges],

    # triangle constraints: distance(i,j) <= distance(i,k) + distance(k,j)  tag(redundant-constraints)
    [d[i][j] <= d[min(i, k)][max(i, k)] + d[min(j, k)][max(j, k)] for (i, j) in edges
     for k in range(n) if (min(i, k), max(i, k)) in edges and (min(j, k), max(j, k)) in edges]
)

minimize(
    # minimizing the sum of distances between adjacent nodes
    Sum(d)
)

""" Comments
1) Note that for large instances, one may think about using an adjacency matrix, as with:
 a = [[1 if (i, j) in e or (j, i) in e else 0 for j in range(n)] for i in range(n)]
"""
