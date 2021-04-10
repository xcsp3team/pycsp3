"""
See https://en.wikipedia.org/wiki/LITS

Example of Execution:
  python3 Lits.py -data=Lits_example.json
"""

from collections import OrderedDict

from pycsp3 import *

puzzle = data
n, m = len(puzzle), len(puzzle[0])

shapes = [  # the offsets, wrt (0,0), for the three other points of the basic shapes of each tetramino
    [[(1, 0), (2, 0), (2, 1)], [(0, 1), (1, 0), (2, 0)], [(0, 1), (1, 1), (2, 1)], [(0, 1), (0, 2), (-1, 2)]],  # L
    [[(0, 1), (0, 2), (0, 3)]],  # I
    [[(0, 1), (0, 2), (1, 1)], [(1, -1), (1, 0), (1, 1)]],  # T
    [[(0, 1), (-1, 1), (-1, 2)], [(1, 0), (1, 1), (2, 1)]]  # S
]
shapes = [s + [[(j, i) for (i, j) in t] for t in s] for s in shapes]  # adding symmetric shapes (by the downward diagonal)

regions = OrderedDict()
for i in range(n):
    for j in range(m):
        regions.setdefault(puzzle[i][j], []).append((i + 1, j + 1))  # +1 because of the border
nRegions = len(regions)
nValues = nRegions * 4  # maximal distance


def table_connection():
    tbl = {(0, ANY, ANY, ANY, ANY, -1, ANY, ANY, ANY, ANY)}
    tbl.add((1, 1, ANY, ANY, ANY, 0, 1, ANY, ANY, ANY))
    tbl.add((1, ANY, 1, ANY, ANY, 0, ANY, 1, ANY, ANY))
    tbl.add((1, ANY, ANY, 1, ANY, 0, ANY, ANY, 1, ANY))
    tbl.add((1, ANY, ANY, ANY, 1, 0, ANY, ANY, ANY, 1))
    for v in range(1, nValues):
        tbl.add((1, 1, ANY, ANY, ANY, v, v - 1, ANY, ANY, ANY))
        tbl.add((1, ANY, 1, ANY, ANY, v, ANY, v - 1, ANY, ANY))
        tbl.add((1, ANY, ANY, 1, ANY, v, ANY, ANY, v - 1, ANY))
        tbl.add((1, ANY, ANY, ANY, 1, v, ANY, ANY, ANY, v - 1))
    return tbl


def table_region(squares):
    tbl = set()
    for p, (i, j) in enumerate(squares):
        for v in range(4):  # four shapes (L, I, T, S)
            for shape in shapes[v]:
                l = sorted([p] + [squares.index((i + voffset, j + hoffset)) for (voffset, hoffset) in shape if (i + voffset, j + hoffset) in squares])
                if len(l) == 4:  # if the shape can be put in the region from the square at (i,j)
                    tbl.add(tuple(1 if i in l else 0 for i in range(len(squares))) + tuple(v if i in l else -1 for i in range(len(squares))))
    return tbl


def cross(t, i, j):
    return t[i][j], t[i][j - 1], t[i][j + 1], t[i - 1][j], t[i + 1][j]


# x[i][j] is 1 iff the square at row i and column j is colored (borders are inserted for simplicity)
x = VarArray(size=[n + 2, m + 2], dom=lambda i, j: {-1} if i in {0, n + 1} or j in {0, m + 1} else {0, 1})

# s[i][j] is the shape of the tetromino involving the square at row i and column j, or -1 if the square is not colored
s = VarArray(size=[n + 2, m + 2], dom=lambda i, j: {-1} if i in {0, n + 1} or j in {0, m + 1} else range(-1, 4))

# d[i][j] is the distance of the square at row i and column j wrt the starting square of the puzzle, or -1 if the square is not colored
d = VarArray(size=[n + 2, m + 2], dom=lambda i, j: {-1} if i in {0, n + 1} or j in {0, m + 1} else range(-1, nValues))

satisfy(
    # setting a tetromino in each region
    [[x[i][j] for (i, j) in region] + [s[i][j] for (i, j) in region] in table_region(region) for region in regions.values()],

    # no two tetrominoes of the same shape can touch
    [
        [(s[i][j], s[i][j + 1]) not in {(v, v) for v in range(4)} for i in range(1, n + 1) for j in range(1, m) if puzzle[i - 1][j - 1] != puzzle[i - 1][j]],
        [(s[i][j], s[i + 1][j]) not in {(v, v) for v in range(4)} for j in range(1, m + 1) for i in range(1, n) if puzzle[i - 1][j - 1] != puzzle[i][j - 1]]
    ],

    # ensuring connection
    [(cross(x, i, j), cross(d, i, j)) in table_connection() for i in range(1, n + 1) for j in range(1, m + 1)],

    # no presence of 2x2 colored squares
    [Count(x[i:i + 2, j:j + 2], value=0) > 0 for i in range(1, n) for j in range(1, m)],

    # setting the starting square in the first region  tag(symmetry-breaking)
    [
        Count([d[i][j] for (i, j) in regions[0]], value=0) == 1,

        [d[i][j] != 0 for k in range(1, nRegions) for (i, j) in regions[k]]
    ]
)

""" Comments
1) x[i:i+2][j:j+2] is not correct

2) other possible array on which building the model:
 shapes = [
     [[(1, 0), (2, 0), (2, 1)], [(-1, 0), (-1, 1), (-1, 2)], [(0, 1), (1, 1), (2, 1)], [(0, 1), (0, 2), (-1, 2)], [(0, 1), (-1, 1), (-2, 1)],
      [(1, 0), (1, 1), (1, 2)], [(-1, 0), (-2, 0), (-2, 1)], [(0, 1), (0, 2), (1, 2)]],
     [[(0, 1), (0, 2), (0, 3)], [(1, 0), (2, 0), (3, 0)]],
     [[(-1, -1), (-1, 0), (-1, 1)], [(1, -1), (1, 0), (1, 1)], [(-1, 1), (0, 1), (1, 1)], [(-1, -1), (0, -1), (1, -1)]],
     [[(0, 1), (-1, 1), (-1, 2)], [(1, 0), (1, 1), (2, 1)], [(-1, 0), (-1, 1), (-2, 1)], [(0, 1), (1, 1), (1, 2)]]
 ]
"""