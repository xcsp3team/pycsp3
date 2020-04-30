from pycsp3 import *

n, k = data  # n is the order(board width)  -- k is the number of knights

#  x[i] is the cell number of the board where is put the ith knight
x = VarArray(size=k, dom=range(n * n))

satisfy(
    [x[i] != x[j] for i in range(k) for j in range(i + 2, k) if i != 0 or j != k - 1],

    [knight_attack(x[i], x[(i + 1) % k], n) for i in range(k)]
)
