""""
See https://en.wikipedia.org/wiki/Sudoku
See, e.g., "Sudoku as a Constraint Problem" by Helmut Simonis

Example of Execution:
  python3 Sudoku.py
  python3 Sudoku.py -data=null
  python3 Sudoku.py -data=None
  python3 Sudoku.py -data=Sudoku9-test.json
"""

from pycsp3 import *

clues = data  # if not 0, clues[i][j] is a value imposed at row i and col j




# x[i][j] is the value in cell at row i and col j.
x = VarArray(size=[9, 9], dom=range(1, 10))

satisfy(
    # imposing distinct values on each row and each column
    AllDifferent(x, matrix=True),

    # imposing distinct values on each block  tag(blocks)
    [AllDifferent(x[i:i + 3, j:j + 3]) for i in [0, 3, 6] for j in [0, 3, 6]],

    # imposing clues  tag(clues)
    [x[i][j] == clues[i][j] for i in range(9) for j in range(9) if clues and clues[i][j] > 0]
)
