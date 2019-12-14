from pycsp3 import *

m, n, r = data.m, data.n, data.r
connections = data.connections

# x[i][j] is 1 if the ith ring contains the jth node
x = VarArray(size=[m, n], dom={0, 1})

table = [tuple(1 if j // 2 == i else ANY for j in range(2 * m)) for i in range(m)]

satisfy(
    [[(x[i][j], x[i][k]) for i in range(m)] in table for (j, k) in connections],

    [Count(x[i], value=1) <= r for i in range(m)],

    LexIncreasing(x)
)

minimize(
    Sum(x)
)
