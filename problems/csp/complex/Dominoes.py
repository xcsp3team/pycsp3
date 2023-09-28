"""
See "Teaching Constraints through Logic Puzzles" by Peter Szeredi
See "Dominoes as a Constraint Problem" by Helmut Simonis

Example of Execution:
  python Dominoes.py -data=Dominoes_grid1.json
  python Dominoes.py -variant=table -data=Dominoes_grid1.json
"""

from pycsp3 import *

grid = data
nRows, nCols, nValues = len(grid), len(grid[0]), len(grid)
dominoes = [(i, j) for i in range(nValues) for j in range(i, nValues)]  # pairs of values to be considered
indexes = range(nRows * nCols)  # indexes of cells

P = [[i * nCols + j for i in range(nRows) for j in range(nCols) if grid[i][j] == value] for value in range(nValues)]  # possible positions

# x[i][j] is the index (position) in the grid of the value i of the domino i-j
x = VarArray(size=[nValues, nValues], dom=lambda i, j: indexes if i <= j else None)

# y[i][j] is the index (position) in the grid of the value j of the domino i-j
y = VarArray(size=[nValues, nValues], dom=lambda i, j: indexes if i <= j else None)

satisfy(
    # each part of each domino in a different cell
    AllDifferent(x + y),

    # unary constraints
    [(x[i][j] in P[i], y[i][j] in P[j]) for i, j in dominoes],
)

if not variant():
    satisfy(
        # adjacency constraints
        (abs(x[i][j] - y[i][j]) == nCols)  # adjacent values in the same column
        | (abs(x[i][j] - y[i][j]) == 1) & (x[i][j] // nCols == y[i][j] // nCols)  # or adjacent values in the same line
        for i, j in dominoes
    )

elif variant("table"):
    T = [(k1, k2) for k1 in indexes for k2 in indexes if abs(k1 - k2) == nCols or abs(k1 - k2) == 1 and k1 // nCols == k2 // nCols]

    satisfy(
        # adjacency constraints
        (x[i][j], y[i][j]) in T for i, j in dominoes
    )

""" Comments
1) one could use the If structure as follows:
   If(
      abs(x[i][j] - y[i][j]) != nCols,  # if not adjacent values in the same column
      Then=(abs(x[i][j] - y[i][j]) == 1) & (x[i][j] // nCols == y[i][j] // nCols)  # then adjacent values in the same line
   ) for i, j in dominoes

"""
