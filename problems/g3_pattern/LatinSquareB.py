from pycsp3 import *

n = data.n
clues = data.clues

# x[i][j] is the value at row i and col j of the Latin Square
x = VarArray(size=[n, n], dom=range(n))

satisfy(
    AllDifferent(x, matrix=True),

    # tag(clues)
    [x[i][j] == v for (i, j, v) in clues],

    # tag(diagonals)
    [AllDifferent(dgn) for dgn in diagonals_down(x, broken=True) + diagonals_up(x, broken=True)]
)
