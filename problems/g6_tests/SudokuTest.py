from pycsp3 import *

clues = data.clues  # if not 0, clues[i][j] is a value imposed at row i and col j

# x[i][j] is the value in cell at row i and col j.
x = VarArray(size=[9, 9], dom=range(1, 10))

satisfy(
    # imposing distinct values on each row and each column
    AllDifferent(x, matrix=True),

    # imposing distinct values on each block  tag(blocks)
    [AllDifferent(x[i:i + 3, j:j + 3]) for i in [0, 3, 6] for j in [0, 3, 6]]
)

if clues:
    satisfy(
        # imposing clues  tag(clues)
        x[i][j] == clues[i][j]
        for i in range(9) for j in range(9) if clues[i][j] > 0
    )
