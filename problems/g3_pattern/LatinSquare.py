from pycsp3 import *

n = data.n
clues = data.clues  # if not -1, clues[i][j] is a value imposed at row i and col j

# x[i][j] is the value at row i and col j of the Latin Square
x = VarArray(size=[n, n], dom=range(n))

satisfy(
    AllDifferent(x, matrix=True),

    # tag(clues)
    [x[i][j] == clues[i][j] for i in range(n) for j in range(n) if clues[i][j] != -1]
)
