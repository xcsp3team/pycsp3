"""
See 'Constraint Solving and Planning with Picat' (page 43)
From Tony Hurlimann, A coin puzzle, SVOR-contest 2007

Some data: (8,4) (8,5) (9,4) (10,4) (31,14)

Examples of Execution:
  python3 CoinsGrid.py
  python3 CoinsGrid.py -data=[10,4]
"""

from pycsp3 import *

n, c = data or (8, 4)

# x[i][j] is 1 if a coin is placed at row i and column j
x = VarArray(size=[n, n], dom={0, 1})

satisfy(
    [Sum(x[i]) == c for i in range(n)],

    [Sum(x[:, j]) == c for j in range(n)]
)

minimize(
    Sum(x[i][j] * abs(i - j) ** 2 for i in range(n) for j in range(n))
)

""" Comments
1) there are other variants in Hurlimann's paper (TODO)
"""

