from pycsp3 import *

n, m = data.nRows, data.nCols

# x[i][j] is the color at row i and column j
x = VarArray(size=[n, m], dom=range(n * m))

satisfy(
    [NValues(x[i1][j1], x[i1][j2], x[i2][j1], x[i2][j2]) > 1
     for i1 in range(n) for i2 in range(i1 + 1, n) for j1 in range(m) for j2 in range(j1 + 1, m)],

    # tag(symmetry-breaking)
    LexIncreasing(x, matrix=True)
)

minimize(
    Maximum(x)
)
