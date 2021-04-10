"""
See problem as defined in "Boosting systematic search by weighting constraints" by Boussemart, Hemery, Lecoutre and Sais, ECAI 2004

Examples of Execution:
  python3 QueensKnights.py
  python3 QueensKnights.py -data=[15,5]
"""

from pycsp3 import *

n, nKnights = data or (8, 5)  # n is the order(board width), and so the number of queens

# q[i] is the column number of the board where is put the ith queen (in the ith row)
q = VarArray(size=n, dom=range(n))

# k[i] is the cell number of the board where is put the ith knight
k = VarArray(size=nKnights, dom=range(n * n))

satisfy(
    # all queens are put in different columns
    AllDifferent(q),

    # controlling no two queens on the same upward diagonal
    AllDifferent(q[i] + i for i in range(n)),

    # controlling no two queens on the same downward diagonal
    AllDifferent(q[i] - i for i in range(n)),

    # all knights are put in different cells
    AllDifferent(k),

    # all knights form a cycle
    [(abs(k[i] // n - k[(i + 1) % nKnights] // n), abs(k[i] % n - k[(i + 1) % nKnights] % n)) in {(1, 2), (2, 1)} for i in range(nKnights)]
)

""" Comments
1) adding  (q[i] != k[j] % n) | (i != k[j] // n) for i in range(n) for j in range(nKnights) does not seem to filter more values.

2) expressing a table constraint where the scope does not list simple variables entails automatically introducing auxiliary variables at compilation time
"""