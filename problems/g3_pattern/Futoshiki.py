from pycsp3 import *

n, numHints, opHints = data.size, data.numHints, data.opHints


def operator_ctr(i, j, lt, hr):
    y = x[i][j]
    z = x[i + (0 if hr else 1)][j + (1 if hr else 0)]
    return y < z if lt else y > z


# x[i][j] is the number put at row i and column j
x = VarArray(size=[n, n], dom=range(1, n + 1))

satisfy(
    AllDifferent(x, matrix=True),

    # number hints
    [x[i][j] == k for (i, j, k) in numHints],

    # operator hints
    [operator_ctr(i, j, lt, hr) for (i, j, lt, hr) in opHints]
)


# [x[i][j] == k for i, j, k in [(hint.row, hint.col, hint.number) for hint in data.numHints]],
