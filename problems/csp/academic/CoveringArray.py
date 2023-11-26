"""
See Problem 045 on CSPLib.

## Data
  four integers: t, k, g and b

## Model
  constraints: AllDifferent, Channel, Table

## Execution
  - python CoveringArray.py -data=[number,number,number,number]

## Links
  - https://www.csplib.org/Problems/prob045/
  - https://www.cril.univ-artois.fr/XCSP23/competitions/csp/csp

## Tags
  academic, recreational, csplib, xcsp23
"""

from pycsp3 import *
from math import factorial

t, k, g, b = data or (3, 5, 2, 10)
n = factorial(k) // factorial(t) // factorial(k - t)
d = g ** t

T = {tuple(sum(pr[a] * g ** i for i, a in enumerate(reversed(co))) for co in combinations(range(k), t)) for pr in product(range(g), repeat=k)}

# p[i][j] is one of the position of the jth value of the ith 't'-combination
p = VarArray(size=[n, d], dom=range(b))

# v[i][j] is the jth value of the ith 't'-combination
v = VarArray(size=[n, b], dom=range(d))

satisfy(
    # all values must be present in each 't'-combination
    [AllDifferent(p[i]) for i in range(n)],

    [Channel(p[i], v[i]) for i in range(n)],

    # computing values
    [v[:, j] in T for j in range(b)]
)

""" Comments
1) for being compatible with the competition mini-track, we use:
   [v[i][p[i][j]] == j for i in range(n) for j in range(b)]
2) It is possible to get the covering array from v (the array of variables in the model below).
 For example, v[0][0] gives the t most significant bits of the first column (because the first t-combination is for the first t lines).
"""
