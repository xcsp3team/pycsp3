"""
See https://en.wikipedia.org/wiki/Latin_square

Example of Execution:
  python3 LatinSquare2.py -data=LatinSquare2_7-2-0.json
"""

from pycsp3 import *

n, clues = data  # clues are given by tuples of the form (row, col, value)

# x[i][j] is the value at row i and col j of the Latin Square
x = VarArray(size=[n, n], dom=range(n))

satisfy(
    AllDifferent(x, matrix=True),

    # tag(clues)
    [x[i][j] == v for (i, j, v) in clues] if clues else None,

    # tag(diagonals)
    [AllDifferent(dgn) for dgn in diagonals_down(x, broken=True) + diagonals_up(x, broken=True)]
)
