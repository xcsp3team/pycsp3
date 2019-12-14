from pycsp3 import *

n = data.n

# x[i][j] is the color at row i and column j
x = VarArray(size=[n, n], dom=range(n))

satisfy(
    # different colors on rows and columns
    AllDifferent(x, matrix=True),

    # different colors on downward diagonals
    [AllDifferent(dgn) for dgn in diagonals_down(x)],

    # different colors on upward diagonals
    [AllDifferent(dgn) for dgn in diagonals_up(x)]
)
