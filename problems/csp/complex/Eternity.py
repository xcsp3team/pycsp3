"""
On a board of size n×m, you have to put square tiles (pieces) that are described by four colors (one for each direction : top, right, bottom and left).
All adjacent tiles on the board must have matching colors along their common edge. All edges must have color ’0’ on the border of the board.

## Data Example
  07x05.json

## Model
  constraints: AllDifferent, Table

## Execution
  - python Eternity.py -data=<datafile.json>

## Links
  - https://hal-lirmm.ccsd.cnrs.fr/lirmm-00364330/document
  - https://www.cril.univ-artois.fr/XCSP22/competitions/csp/csp

## Tags
  recreational, xcsp22
"""

from pycsp3 import *

n, m, pieces = data
assert n * m == len(pieces), "badly formed data"
max_value = max(max(piece) for piece in pieces)  # max possible value on pieces

T = {(i, piece[r % 4], piece[(r + 1) % 4], piece[(r + 2) % 4], piece[(r + 3) % 4]) for i, piece in enumerate(pieces) for r in range(4)}

# x[i][j] is the index of the piece at row i and column j
x = VarArray(size=[n, m], dom=range(n * m))

# top[i][j] is the value at the top of the piece at row i and column j
top = VarArray(size=[n + 1, m], dom=range(max_value + 1))

# lft[i][j] is the value at the left of the piece at row i and column j
lft = VarArray(size=[n, m + 1], dom=range(max_value + 1))

satisfy(
    # all pieces must be placed (only once)
    AllDifferent(x),

    # all pieces must be valid (i.e., must correspond to those given initially, possibly after applying some rotation)
    [(x[i][j], top[i][j], lft[i][j + 1], top[i + 1][j], lft[i][j]) in T for i in range(n) for j in range(m)],

    # putting special value 0 on borders
    [
        top[0] == 0,
        top[-1] == 0,
        lft[:, 0] == 0,
        lft[:, -1] == 0
    ]
)
