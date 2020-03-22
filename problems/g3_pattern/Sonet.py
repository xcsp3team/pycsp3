from pycsp3 import *

# Problem 056 at CSPLib

m, n, r = data.m, data.n, data.r

# x[i][j] is 1 if the ith ring contains the jth node
x = VarArray(size=[m, n], dom={0, 1})

table = {tuple(1 if j // 2 == i else ANY for j in range(2 * m)) for i in range(m)}

satisfy(
    [(x[i][j1] if k == 0 else x[i][j2] for i in range(m) for k in range(2)) in table for (j1, j2) in data.connections],

    [Count(x[i], value=1) <= r for i in range(m)],

    LexIncreasing(x)
)

minimize(
    Sum(x)
)
