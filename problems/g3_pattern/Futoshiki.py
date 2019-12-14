from pycsp3 import *

size, numHints, opHints = data.size, data.numHints, data.opHints;

# x[i][j] is the number put at row i and column j
x = VarArray(size=[size, size], dom=range(1, size + 1))


def operator_ctr(hint):
    y = x[hint.row][hint.col]
    z = x[hint.row + (0 if hint.horizontal else 1)][hint.col + (1 if hint.horizontal else 0)]
    return y < z if hint.lessThan else y > z


satisfy(
    AllDifferent(x, matrix=True),

    # number hints
    [x[hint.row][hint.col] == hint.number for hint in numHints],

    # operator hints
    [operator_ctr(hint) for hint in opHints]
)
