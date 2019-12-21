from pycsp3 import *

# Problem 017 at CSPLib

'''
  Ramsey problem.
  It is to colour the edges of a complete graph with n nodes using at most k colours.
  There must be no monochromatic triangle in the graph, i.e. in any triangle at most two edges have the same colour.
  With 3 colours, the problem has a solution if n < 17.
'''

n = data.n

x = VarArray(size=[n, n], dom=lambda i, j: range((n * (n - 1)) // 2) if i < j else None)

satisfy(
    NValues(x[i][j], x[i][k], x[j][k]) > 1 for (i, j, k) in combinations(range(n), 3)
)

minimize(
    Maximum(x)
)
