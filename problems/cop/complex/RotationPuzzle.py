"""
See http://www-groups.dcs.st-and.ac.uk/~gap/ForumArchive/Harris.1/Bob.1/Re__GAP_.59/1.html

This problem was called "rotation" at Nokia's web site.

The puzzle is a 4x4 grid of numbers. There are four operations, each of
which involves rotating the numbers in a 3x3 subgrid clockwise.
Given an arbitrary initial state, with all values from 0 to 15 put
in the grid, one must reach the following final state:
  0  1  2  3
  4  5  6  7
  8  9 10  11
  12 13 14 15
by applying a minimal sequence of rotations. We can observe that the effect
of rotations on the final state is given by the following cycles:
- (0, 1, 2, 6, 10, 9, 8, 4)
- (1, 2, 3, 7, 11, 10, 9, 5)
- (4, 5, 6, 10, 14, 13, 12, 8)
- (5, 6, 7, 11, 15, 14, 13, 9)

Examples of Execution:
  python3 RotationPuzzle.py -data=0
  python3 RotationPuzzle.py -data=inst.json
"""

from collections import OrderedDict
from pycsp3 import *

# preset data (series of 4 instances, followed by 4 artificial instances)
series = [([7, 11, 6, 14, 0, 13, 15, 12, 2, 9, 10, 8, 4, 1, 3, 5], 11), ([1, 6, 3, 7, 0, 2, 10, 11, 4, 5, 8, 9, 12, 13, 14, 15], 4),
          ([7, 11, 6, 14, 0, 3, 1, 9, 2, 5, 10, 13, 4, 8, 12, 15], 8), ([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 15, 14], 55),
          ([5, 3, 1, 4, 0, 13, 15, 12, 2, 9, 10, 8, 14, 6, 11, 7], 21), ([3, 6, 7, 1, 0, 2, 10, 11, 4, 5, 8, 9, 12, 13, 14, 15], 17),
          ([3, 11, 6, 14, 0, 7, 1, 9, 2, 5, 10, 13, 4, 8, 12, 15], 20), ([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 15, 11, 12, 13, 14, 10], 18),
          ]
rotations = [[0, 1, 2, 6, 10, 9, 8, 4], [1, 2, 3, 7, 11, 10, 9, 5], [4, 5, 6, 10, 14, 13, 12, 8], [5, 6, 7, 11, 15, 14, 13, 9]]
nCells, nRotations = 16, len(rotations)

grid, nPeriods = series[data] if isinstance(data, int) else data

mappings = [[v] + [v if v not in t else t[(len(t) + t.index(v) - 1) % len(t)] for t in rotations] for v in range(16)]
scopes = [list(OrderedDict.fromkeys(t)) for t in mappings]
tables = [{(op, v, *(v if pos == mappings[i][op] else ANY for pos in scopes[i])) for op in range(5) for v in range(16)} for i in
          range(nCells)]  # tables for transitions

# x[t][i] is the value in the ith cell at time t
x = VarArray(size=[nPeriods, nCells], dom=range(nCells))

# o[t] is the rotation performed at time t
o = VarArray(size=nPeriods, dom=range(nRotations + 1))  # +1 for 0 (no rotation)

# f is the time at which the final state is reached
f = Var(range(1, nPeriods))

satisfy(
    # setting the initial state (at time 0)
    x[0] == grid,

    # ensuring a correct transition between two successive times
    [(o[t], x[t][i], (x[t - 1][j] for j in scopes[i])) in tables[i] for i in range(nCells) for t in range(1, nPeriods)],

    # ensuring that the final state is reached at time given by f
    [x[f][i] == i for i in range(nCells)],

    # once the final state is reached, there is no more rotation
    [(f > t) | (o[t] == 0) for t in range(1, nPeriods)],

    # tag(redundant-constraints)
    [AllDifferent(x[t]) for t in range(1, nPeriods)]
)

minimize(
    f
)

""" Comments
1) Solutions are respectively: (4, 4, 4, 1, 2, 3, 2, 2, 3), (2, 1), (1, 2, 3, 2, 2, 3) for the three first instances
2) x[0] == grid is equivalent to [x[0][i] == grid[i] for i in range(nCells)]
3) (o[t], x[t][i], (x[t - 1][j] for j in scopes[i])) builds a scope. Note that the generator is automatically unpacked.
   one could write: (o[t], x[t][i], *(x[t - 1][j] for j in scopes[i]))
"""
