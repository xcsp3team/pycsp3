from pycsp3 import *

n = data.n

x = VarArray(size=[n, n], dom=range(n))

y = VarArray(size=[n, n], dom=range(n))

z = VarArray(size=[n * n], dom=range(n * n))

table = {(i, j, i * n + j) for i in range(n) for j in range(n)}

satisfy(
    AllDifferent(x, matrix=True),

    AllDifferent(y, matrix=True),

    AllDifferent(z),

    [(x[i][j], y[i][j], z[i * n + j]) in table for i in range(n) for j in range(n)],

    # tag(symmetryBreaking)
    [
        [x[0][j] == j for j in range(n)],
        [y[0][j] == j for j in range(n)]
    ]
)
