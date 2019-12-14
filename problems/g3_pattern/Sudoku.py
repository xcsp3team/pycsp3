from pycsp3 import *

import math

n = data.n  # order of the grid (typically, 9)
clues = data.clues  # if not 0, clues[i][j] is a value imposed at row i and col j
base = int(math.sqrt(n))

# x[i][j] is the value in cell at row i and col j.
x = VarArray(size=[n, n], dom=range(1, n + 1))

if not variant():
    satisfy(
        AllDifferent(x, matrix=True),

        # tag(blocks)
        [AllDifferent(x[i:i + base, j:j + base]) for i in range(0, n, base) for j in range(0, n, base)]
    )

elif variant("table"):
    table = list(permutations(range(1, n + 1)))
    satisfy(
        [
            [row in table for row in x],

            [col in table for col in columns(x)]
        ],

        # tag(blocks)
        [x[i:i + base, j:j + base] in table for i in range(0, n, base) for j in range(0, n, base)]
    )

if clues:
    satisfy(
        # tag(clues)
        x[i][j] == clues[i][j] for i in range(n) for j in range(n) if clues[i][j] > 0
    )
