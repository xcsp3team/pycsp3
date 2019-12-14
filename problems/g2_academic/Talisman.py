from pycsp3 import *

n, k = data.n, data.k
limit = (n * (n * n + 1)) // 2

x = VarArray(size=[n, n], dom=range(1, n * n + 1))

satisfy(
    AllDifferent(x),

    [Sum(row) == limit for row in x],

    [Sum(col) == limit for col in columns(x)],

    Sum(diagonal_down(x)) == limit,

    Sum(diagonal_up(x)) == limit,

    [
        [dist(x[i][j], x[i][j + 1]) > k for i in range(n) for j in range(n - 1)],
        [dist(x[i][j], x[i + 1][j]) > k for j in range(n) for i in range(n - 1)],
        [dist(t[i], t[i + 1]) > k for t in diagonals_down(x) for i in range(len(t) - 1)],
        [dist(t[i], t[i + 1]) > k for t in diagonals_up(x) for i in range(len(t) - 1)]
    ]
)
