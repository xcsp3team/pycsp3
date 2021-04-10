"""
See Problem 132 on CSPLib
See "Exploiting symmetries within constraint satisfaction search", by P. Meseguer and C. Torras,
    Artificial intelligence 129(1), 133–163, 2001 (Example of Section 3.3)

Execution:
  python3 Layout.py -data Layout_example.json
"""

from pycsp3 import *

grid, shapes = data
nRows, nCols, nShapes = len(grid), len(grid[0]), len(shapes)


def bases(shape):
    height, width = len(shape), len(shape[0])
    return [i * nCols + j for i in range(nRows - height + 1) for j in range(nCols - width + 1) if
            all(grid[i + gi][j + gj] == 1 or shape[gi][gj] == 0 for gi in range(height) for gj in range(width))]


def table(k):
    shape, height, width = shapes[k], len(shapes[k]), len(shapes[k][0])
    tbl = []
    for v in bases(shape):
        i, j = v // nCols, v % nCols
        t = [(i + gi) * nCols + (j + gj) for gi in range(height) for gj in range(width) if shape[gi][gj] == 1]
        tbl.append((v,) + tuple(k if w in t else ANY for w in range(nRows * nCols)))
    return tbl


# x[i][j] is the index of the shape occupying the cell at row i and column j (or -1 if the cell is free)
x = VarArray(size=[nRows, nCols], dom=lambda i, j: {-1} if grid[i][j] == 0 else range(nShapes))

# y[k] is the (index of the) base cell in the grid where we start putting the kth shape
y = VarArray(size=nShapes, dom=lambda k: bases(shapes[k]))

satisfy(
    # putting shapes in the grid
    (y[k], x) in table(k) for k in range(nShapes)
)

""" Comments
1) (y[k], x) is a possible shortcut for (y[k], *flatten(x))
"""