from pycsp3 import *

"""
 See https://en.wikipedia.org/wiki/Futoshiki
"""

n, numHints, opHints = data.size, data.numHints, data.opHints

# x[i][j] is the number put at row i and column j
x = VarArray(size=[n, n], dom=range(1, n + 1))

satisfy(
    AllDifferent(x, matrix=True),

    # number hints
    [x[i][j] == k for (i, j, k) in numHints],

    # operator hints
    [y < z if lt else y > z for (y, z, lt) in [(x[i][j], x[i][j + 1] if hr else x[i + 1][j], lt) for (i, j, lt, hr) in opHints]]
)
