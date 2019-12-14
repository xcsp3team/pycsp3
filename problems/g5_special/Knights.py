from pycsp3 import *

n, k = data.n, data.nKnights  # n is the order(board width)

#  x[i] is the cell number of the board where is put the ith knight
x = VarArray(size=k, dom=range(n * n))

satisfy(
    [x[i] != x[j] for i in range(k) for j in range(i + 2, k) if i != 0 or j != k - 1],

    Slide(knight_attack(x[i], x[(i + 1) % k], n) for i in range(k))
)
