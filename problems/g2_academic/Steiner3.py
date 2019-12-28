from pycsp3 import *

# Problem 044 at CSPLib

n = data.n
nTriples = (n * (n - 1)) // 6


def condition(i1, i2, i3, j1, j2, j3):
    return different_values(i1, i2, i3) and different_values(j1, j2, j3) and len({i for i in {i1, i2, i3} if i in {j1, j2, j3}}) <= 1


table = {(i1, i2, i3, j1, j2, j3) for (i1, i2, i3, j1, j2, j3) in product(range(1, n + 1), repeat=6) if condition(i1, i2, i3, j1, j2, j3)}

# x[i] is the ith triplet of value
x = VarArray(size=[nTriples, 3], dom=range(1, n + 1))

satisfy(
    # ensuring that triples are formed of distinct elements, given in increasing order
    [Increasing(x[i], strict=True) for i in range(nTriples)],

    # ensuring that triples share at most one value
    [(x[i] + x[j]) in table for i in range(nTriples) for j in range(i + 1, nTriples)]
)


# return (1 if i1 in {j1, j2, j3} else 0) + (1 if i2 in {j1, j2, j3} else 0) + (1 if i3 in {j1, j2, j3} else 0)
