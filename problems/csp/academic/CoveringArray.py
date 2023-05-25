"""
Problem 045 on CSPLib

It is possible to get the covering array from v (the array of variables in the model below).
For example, v[0][0] gives the t most significant bits of the first column (because the first t-combination is for the first t lines).

Examples of Execution:
  python3 CoveringArray.py
  python3 CoveringArray.py -data=[3,5,2,10]
"""

from pycsp3 import *
from math import factorial

t, k, g, b = data or (3, 5, 2, 10)
n = factorial(k) // factorial(t) // factorial(k - t)
d = g ** t

table = {tuple(sum(pr[a] * g ** i for i, a in enumerate(reversed(co))) for co in combinations(range(k), t)) for pr in product(range(g), repeat=k)}

# p[i][j] is one of the position of the jth value of the ith 't'-combination
p = VarArray(size=[n, d], dom=range(b))

# v[i][j] is the jth value of the ith 't'-combination
v = VarArray(size=[n, b], dom=range(d))

satisfy(
    # all values must be present in each 't'-combination
    [AllDifferent(p[i]) for i in range(n)],

    [Channel(p[i], v[i]) for i in range(n)],

    # computing values
    [v[:, j] in table for j in range(b)]
)

"""
1) for being compatible with the competition mini-track, we use:
   [v[i][p[i][j]] == j for i in range(n) for j in range(b)]
"""
