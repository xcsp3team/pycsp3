"""
See https://en.wikipedia.org/wiki/Latin_square

Examples of Execution:
  python3 LatinSquare.py -data=[8,]
  python3 LatinSquare.py -data=LatinSquare_qwh-o030-h320.json
"""

from pycsp3 import *

n, clues = data  # if not -1, clues[i][j] is a value imposed at row i and col j

# x[i][j] is the value at row i and col j of the Latin Square
x = VarArray(size=[n, n], dom=range(n))

satisfy(
    AllDifferent(x, matrix=True),

    # tag(clues)
    [x[i][j] == clues[i][j] for i in range(n) for j in range(n) if clues and clues[i][j] != -1]
)
