"""
See "Teaching Constraints through Logic Puzzles" by Peter Szeredi
See "Dominoes as a Constraint Problem" by Helmut Simonis

Example of Execution:
  python3 Dominoes.py -data=Dominoes_grid1.json
"""

from pycsp3 import *

grid = data
nRows, nCols, nValues = len(grid), len(grid[0]), len(grid)

positions = [[i * nCols + j for i in range(nRows) for j in range(nCols) if grid[i][j] == value] for value in range(nValues)]
pairs = [(i, j) for i in range(nValues) for j in range(i, nValues)]  # pairs of values to be considered

# x[i][j] concerns the domino (having values) i-j; this is the position of the value i in the grid for this domino
x = VarArray(size=[nValues, nValues], dom=lambda i, j: range(nRows * nCols) if i <= j else None)

# y[i][j] concerns the domino (having values) i-j; this is the position of the value j in the grid for this domino
y = VarArray(size=[nValues, nValues], dom=lambda i, j: range(nRows * nCols) if i <= j else None)

satisfy(
    # each part of each domino in a different cell
    AllDifferent(x + y),

    # unary constraints
    [(x[i][j] in positions[i], y[i][j] in positions[j]) for i, j in pairs],
)

if not variant():
    satisfy(
        # adjacency constraints
        (abs(x[i][j] - y[i][j]) == nCols) | (abs(x[i][j] - y[i][j]) == 1) & (x[i][j] // nCols == y[i][j] // nCols) for i, j in pairs
    )

elif variant("table"):
    T = [(v1, v2) for v1 in range(nRows * nCols) for v2 in range(nRows * nCols) if abs(v1 - v2) == nCols or abs(v1 - v2) == 1 and v1 // nCols == v2 // nCols]

    satisfy(
        # adjacency constraints
        (x[i][j], y[i][j]) in T for i, j in pairs
    )
