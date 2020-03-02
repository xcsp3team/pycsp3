from pycsp3 import *

"""
 Problem 044 at CSPLib
"""

n = data.n
nTriples = (n * (n - 1)) // 6


def table():
    def condition(i1, i2, i3, j1, j2, j3):
        return different_values(i1, i2, i3) and different_values(j1, j2, j3) and len({i for i in {i1, i2, i3} if i in {j1, j2, j3}}) <= 1

    return {(i1, i2, i3, j1, j2, j3) for (i1, i2, i3, j1, j2, j3) in product(range(1, n + 1), repeat=6) if condition(i1, i2, i3, j1, j2, j3)}


table = table()

# x[i] is the ith triple of values
x = VarArray(size=[nTriples, 3], dom=range(1, n + 1))

satisfy(
    # each triple must be formed of strictly increasing integers
    [Increasing(x[i], strict=True) for i in range(nTriples)],

    # each pair of triples must share at most one value
    [(x[i] + x[j]) in table for i in range(nTriples) for j in range(i + 1, nTriples)]
)
