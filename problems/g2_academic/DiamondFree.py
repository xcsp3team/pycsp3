from pycsp3 import *

# Problem 050 at CSPLib

n = data.n

# x is the adjacency matrix
x = VarArray(size=[n, n], dom=lambda i, j: {0, 1} if i != j else {0})

# y[i] is the degree of the ith node
y = VarArray(size=n, dom={i for i in range(1, n) if i % 3 == 0})

# s is the sum of all degrees
s = Var(dom={i for i in range(n, n * (n - 1) + 1) if i % 12 == 0})

satisfy(
    [Sum(x[i][j], x[i][k], x[i][l], x[j][k], x[j][l], x[k][l]) <= 4 for (i, j, k, l) in combinations(range(n), 4)],

    [x[i][j] == x[j][i] for i in range(n) for j in range(n) if i != j],

    [Sum(x[i]) == y[i] for i in range(n)],

    Sum(y) == s,

    # tag(symmetry-breaking)
    [Decreasing(y), LexIncreasing(x)]
)





#  for i in range(n) for j in range(i + 1, n) for k in range(j + 1, n) for l in     range(k + 1, n)],

