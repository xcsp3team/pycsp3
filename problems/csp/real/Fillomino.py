"""
See https://en.wikipedia.org/wiki/Fillomino

Example of Execution:
  python3 Fillomino.py -data=Fillomino-08.json
"""

from pycsp3 import *

puzzle = data
n, m = len(puzzle), len(puzzle[0])

preassigned = dict()  # we collect pre-assigned starting squares for the first occurrences of specified values
for i in range(n):
    for j in range(m):
        if puzzle[i][j] != 0 and puzzle[i][j] not in preassigned:  # the second part is important
            preassigned[puzzle[i][j]] = (i + 1, j + 1)  # +1 because of the border

nRegions = len(preassigned) + (n * m - sum(preassigned.keys()))
nValues = max(*preassigned.keys(), n * m - sum(preassigned.keys())) + 1  # this is the maximal distance + 1


def tables():
    t = {(1, ANY, ANY, ANY, ANY, ANY, 0, ANY, ANY, ANY, ANY)}
    for k in range(nRegions):
        t.add((gt(1), k, k, ANY, ANY, ANY, 0, 1, ANY, ANY, ANY))
        t.add((gt(1), k, ANY, k, ANY, ANY, 0, ANY, 1, ANY, ANY))
        t.add((gt(1), k, ANY, ANY, k, ANY, 0, ANY, ANY, 1, ANY))
        t.add((gt(1), k, ANY, ANY, ANY, k, 0, ANY, ANY, ANY, 1))
        for v in range(1, nValues):
            t.add((gt(1), k, k, ANY, ANY, ANY, v, v - 1, ANY, ANY, ANY))
            t.add((gt(1), k, ANY, k, ANY, ANY, v, ANY, v - 1, ANY, ANY))
            t.add((gt(1), k, ANY, ANY, k, ANY, v, ANY, ANY, v - 1, ANY))
            t.add((gt(1), k, ANY, ANY, ANY, k, v, ANY, ANY, ANY, v - 1))
    return t, {(v, v, k, k) for v in range(nValues) for k in range(nRegions)} | {(v, ne(v), k, ne(k)) for v in range(nValues) for k in range(nRegions)}


table_connection, table_region = tables()

# x[i][j] is the region (number) where the square at row i and column j belongs (borders are inserted for simplicity)
x = VarArray(size=[n + 2, m + 2], dom=lambda i, j: {-1} if i in {0, n + 1} or j in {0, m + 1} else range(nRegions))

# y[i][j] is the value of the square at row i and column j
y = VarArray(size=[n + 2, m + 2],
             dom=lambda i, j: {-1} if i in {0, n + 1} or j in {0, m + 1} else {puzzle[i - 1][j - 1]} if puzzle[i - 1][j - 1] != 0 else range(nValues))

# d[i][j] is the distance of the square at row i and column j wrt the starting square of the (same) region
d = VarArray(size=[n + 2, m + 2], dom=lambda i, j: {-1} if i in {0, n + 1} or j in {0, m + 1} else range(nValues))

# s[k] is the size of the kth region
s = VarArray(size=nRegions, dom=range(nValues))

satisfy(
    # setting starting squares of pre-assigned regions
    [(x[i][j] == k, d[i][j] == 0, s[k] == sz) for k, (sz, (i, j)) in enumerate(preassigned.items())],

    # setting values according to the size of the regions
    [y[i][j] == s[x[i][j]] for i in range(1, n + 1) for j in range(1, m + 1) if puzzle[i - 1][j - 1] == 0 or (i, j) not in preassigned.values()],

    # controlling the size of each region
    [s[k] == Sum(x[i][j] == k for i in range(1, n + 1) for j in range(1, m + 1)) for k in range(nRegions)],

    # ensuring connection
    [(y[i][j], x.cross(i, j), d.cross(i, j)) in table_connection for i in range(1, n + 1) for j in range(1, m + 1)],

    # two regions of the same size cannot have neighbouring squares
    [
        [(y[i][j], y[i][j + 1], x[i][j], x[i][j + 1]) in table_region for i in range(1, n + 1) for j in range(1, m)],
        [(y[i][j], y[i + 1][j], x[i][j], x[i + 1][j]) in table_region for j in range(1, m + 1) for i in range(1, n)]
    ]
)

""" Comments
1) cross() is a predefined method on matrices of variables (of type ListVar).
   Hence, x.cross(i, j) is equivalent to :
   [t[i][j], t[i][j - 1], t[i][j + 1], t[i - 1][j], t[i + 1][j]] 
2) gt(1) when building a tuple allows to handle all tuples with a value > 1
   Later, it will be possible to generate smart tables instead of starred tables 
"""
