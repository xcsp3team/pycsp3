from pycsp3 import *

grid = data.grid
nRows, nCols, nValues = len(grid), len(grid[0]), len(grid)


def adjacency(d1, d2):
    va = (d1 == d2 + nCols) | (d2 == d1 + nCols)  # vertical adjacency
    ha = (d1 == d2 + 1) & (d1 % nCols != 0) | (d2 == d1 + 1) & (d2 % nCols != 0)  # horizontal adjacency
    return va | ha


def positions(value):
    return [i * nCols + j for i in range(nRows) for j in range(nCols) if grid[i][j] == value]


# x[i][j] concerns the domino (having values) i-j; this is the position of the value i in the grid for this domino
x = VarArray(size=[nValues, nValues], dom=lambda i, j: range(nRows * nCols) if i <= j else None)

# y[i][j] concerns the domino (having values) i-j; this is the position of the value j in the grid for this domino
y = VarArray(size=[nValues, nValues], dom=lambda i, j: range(nRows * nCols) if i <= j else None)

satisfy(
    # each part of each domino in a different cell
    AllDifferent(x + y),

    # unary constraints
    [(x[i][j] in positions(i), y[i][j] in positions(j)) for i in range(nValues) for j in range(i, nValues)],

    # adjacency constraints
    [adjacency(x[i][j], y[i][j]) for i in range(nValues) for j in range(i, nValues)]
)
