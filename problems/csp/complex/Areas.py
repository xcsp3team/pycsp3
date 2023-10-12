"""
See "Teaching Constraints through Logic Puzzles" by Peter Szeredi

A rectangular board is given with some squares specified as positive integers.
Fill in all squares of the board with positive integers so that any maximal contiguous set of squares containing the same integer
has the area equal to this integer (two squares are contiguous if they share a side).

Important: we assume in the model below that each specified integer delimits its own region
(i.e., we cannot use two equal specified integers for the same region).

Example of Execution:
  python3 Areas.py -data=Areas-3-3-3.json
"""

from pycsp3 import *

puzzle = data
n, m = len(puzzle), len(puzzle[0])

Region = namedtuple("Region", "i j size")
regions = [Region(i + 1, j + 1, puzzle[i][j]) for i in range(n) for j in range(m) if puzzle[i][j] != 0]  # +1 because a border is inserted
nRegions = len(regions)

conflicting_regions = {(k1, k2) for k1 in range(nRegions) for k2 in range(nRegions) if k1 != k2 and regions[k1].size == regions[k2].size}


def table_start(k):  # to be used with the starting square (where clue is given) of (non-unit) region k
    return {(k, k, ANY, ANY, ANY, 0, 1, ANY, ANY, ANY),
            (k, ANY, k, ANY, ANY, 0, ANY, 1, ANY, ANY),
            (k, ANY, ANY, k, ANY, 0, ANY, ANY, 1, ANY),
            (k, ANY, ANY, ANY, k, 0, ANY, ANY, ANY, 1)}


def table_other():
    t = set()
    for k in range(nRegions):
        for v in range(1, regions[k].size):
            t.add((k, k, ANY, ANY, ANY, v, v - 1, ANY, ANY, ANY))
            t.add((k, ANY, k, ANY, ANY, v, ANY, v - 1, ANY, ANY))
            t.add((k, ANY, ANY, k, ANY, v, ANY, ANY, v - 1, ANY))
            t.add((k, ANY, ANY, ANY, k, v, ANY, ANY, ANY, v - 1))
    return t


# x[i][j] is the region (number) where the square at row i and column j belongs (borders are inserted for simplicity)
x = VarArray(size=[n + 2, m + 2], dom=lambda i, j: {-1} if i in {0, n + 1} or j in {0, m + 1} else range(nRegions))

# d[i][j] is the distance of the square at row i and column j wrt the starting square of the (same) region
d = VarArray(size=[n + 2, m + 2], dom=lambda i, j: {-1} if i in {0, n + 1} or j in {0, m + 1} else range(max(r.size for r in regions)))

satisfy(
    # setting starting squares of regions
    [(x[i][j] == k, d[i][j] == 0) for k, (i, j, _) in enumerate(regions)],

    # respecting the size of each region
    [Count(x, value=k) == s for k, (_, _, s) in enumerate(regions)],

    # two regions of the same size cannot have neighbouring squares
    [
        [(x[i][j], x[i][j + 1]) not in conflicting_regions for i in range(1, n + 1) for j in range(1, m)],
        [(x[i][j], x[i + 1][j]) not in conflicting_regions for j in range(1, m + 1) for i in range(1, n)]
    ],

    # each starting square of a (non-unit) region must have at least one neighbor at distance 1
    [(x.cross(i, j), d.cross(i, j)) in table_start(k) for k, (i, j, s) in enumerate(regions) if s > 1],

    # each square must be connected to a neighbour at distance 1
    [(x.cross(i, j), d.cross(i, j)) in table_other() for i in range(1, n + 1) for j in range(1, m + 1) if puzzle[i - 1][j - 1] == 0]
)

""" Comments 
1) (cross(x, i, j), cross(d, i, j)) is a tuple containing two sub-tuples of variables.
   This is automatically flattened (i.e., transformed into a single tuple). Of course, it is also possible to write:
   (*cross(x, i, j), *cross(d, i, j))
2) cross is a method that can be called on 2-dimensional arrays/lists of variables (ListVar).
   For an array t, and indexes i,j, it returns [t[i][j], t[i][j - 1], t[i][j + 1], t[i - 1][j], t[i + 1][j]]
"""
