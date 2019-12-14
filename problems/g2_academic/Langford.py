from pycsp3 import *

# Problem 024 at CSPLib

k = data.k  # number of occurrences for a value
n = data.n  # number of values

# x[i][j] is the position in the sequence of the ith occurrence of j
x = VarArray(size=[k, n], dom=range(k * n))

satisfy(
    AllDifferent(x),

    [x[i + 1][j] == x[i][j] + j + 2 for i in range(k - 1) for j in range(n)]
)
