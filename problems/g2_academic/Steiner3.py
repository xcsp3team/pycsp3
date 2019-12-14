from pycsp3 import *

# Problem 044 at CSPLib

n = data.n
nTriples = (n * (n - 1)) // 6


def counting(i1, i2, i3, j1, j2, j3):
    return (1 if i1 in {j1, j2, j3} else 0) + (1 if i2 in {j1, j2, j3} else 0) + (1 if i3 in {j1, j2, j3} else 0)


def table():
    return {(i1, i2, i3, j1, j2, j3) for (i1, i2, i3, j1, j2, j3) in product(range(1, n + 1), repeat=6)
            if different_values(i1, i2, i3) and different_values(j1, j2, j3) and counting(i1, i2, i3, j1, j2, j3) <= 1}


# x[i] is the ith triplet of value
x = VarArray(size=[nTriples, 3], dom=range(1, n+1))

table = table()

satisfy(
    [Increasing(x[i], strict=True) for i in range(nTriples)],

    [(x[i] + x[j]) in table for i in range(nTriples) for j in range(i + 1, nTriples)]
)
