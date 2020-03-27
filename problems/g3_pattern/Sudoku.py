import math

from pycsp3 import *

"""
 See e.g., "Sudoku as a Constraint Problem" by Helmut Simonis
"""

n, base = data.n, int(math.sqrt(data.n))  # n (order of the grid); typically 9
assert base * base == n
clues = data.clues  # if not 0, clues[i][j] is a value imposed at row i and col j

# x[i][j] is the value in cell at row i and col j.
x = VarArray(size=[n, n], dom=range(1, n + 1))

if not variant():
    satisfy(
        # imposing distinct values on each row and each column
        AllDifferent(x, matrix=True),

        # imposing distinct values on each block  tag(blocks)
        [AllDifferent(x[i:i + base, j:j + base]) for i in range(0, n, base) for j in range(0, n, base)]
    )

elif variant("table"):
    table = list(permutations(range(1, n + 1)))
    satisfy(
        # imposing distinct values on each row and each column
        [line in table for line in x + columns(x)],

        # imposing distinct values on each block  tag(blocks)
        [x[i:i + base, j:j + base] in table for i in range(0, n, base) for j in range(0, n, base)]
    )

satisfy(
    # imposing clues  tag(clues)
    x[i][j] == clues[i][j] for i in range(n) for j in range(n) if clues and clues[i][j] > 0
)
