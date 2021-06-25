"""
See Problem 132 on CSPLib
See "Exploiting symmetries within constraint satisfaction search", by P. Meseguer and C. Torras,
    Artificial intelligence 129(1), 133–163, 2001 (Example of Section 3.3)

Execution:
  python3 Layout.py -data Layout_example.json
"""

from pycsp3 import *

grid, shapes = data
n, m, nShapes = len(grid), len(grid[0]), len(shapes)


def domain_y(k):
    shape, height, width = shapes[k], len(shapes[k]), len(shapes[k][0])
    return [i * m + j for i in range(n - height + 1) for j in range(m - width + 1) if
            all(grid[i + gi][j + gj] == 1 or shape[gi][gj] == 0 for gi in range(height) for gj in range(width))]


def table(k):
    shape, height, width = shapes[k], len(shapes[k]), len(shapes[k][0])
    tbl = []
    for v in domain_y(k):
        i, j = v // m, v % m
        t = [(i + gi) * m + (j + gj) for gi in range(height) for gj in range(width) if shape[gi][gj] == 1]
        tbl.append((v,) + tuple(k if w in t else ANY for w in range(n * m)))
    return tbl


# x[i][j] is the index of the shape occupying the cell at row i and column j (or -1 if the cell is free)
x = VarArray(size=[n, m], dom=lambda i, j: {-1} if grid[i][j] == 0 else range(nShapes))

# y[k] is the (index of the) base cell in the grid where we start putting the kth shape
y = VarArray(size=nShapes, dom=domain_y)

satisfy(
    # putting shapes in the grid
    (y[k], x) in table(k) for k in range(nShapes)
)

""" Comments
1) (y[k], x) is a shortcut for (y[k], *flatten(x))
"""
