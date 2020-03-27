from pycsp3 import *

n, k = data.n, data.k
limit = (n * (n * n + 1)) // 2

x = VarArray(size=[n, n], dom=range(1, n * n + 1))

satisfy(
    AllDifferent(x),

    [Sum(row) == limit for row in x],

    [Sum(col) == limit for col in columns(x)],

    [Sum(dgn) == limit for dgn in [diagonal_down(x), diagonal_up(x)]],

    [
        [abs(x[i][j] - x[i][j + 1]) > k for i in range(n) for j in range(n - 1)],
        [abs(x[i][j] - x[i + 1][j]) > k for j in range(n) for i in range(n - 1)],
        [abs(dgn[i] - dgn[i + 1]) > k for dgn in diagonals_down(x) for i in range(len(dgn) - 1)],
        [abs(dgn[i] - dgn[i + 1]) > k for dgn in diagonals_up(x) for i in range(len(dgn) - 1)]
    ]
)
