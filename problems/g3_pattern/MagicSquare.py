from pycsp3 import *

n, clues = data.n, data.clues
magic = n * (n * n + 1) // 2

# x[i][j] is the value at row i and column j of the magic square
x = VarArray(size=[n, n], dom=range(1, n * n + 1))

satisfy(
    AllDifferent(x),

    [Sum(row) == magic for row in x],

    [Sum(col) == magic for col in columns(x)],

    # tag(diagonals)
    [Sum(dgn) == magic for dgn in [diagonal_down(x), diagonal_up(x)]],

    # respecting specified clues (if any)  tag(clues)
    [x[i][j] == clues[i][j] for i in range(n) for j in range(n) if clues and clues[i][j] != 0]
)


