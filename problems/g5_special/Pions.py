from pycsp3 import *


n, p = data  # n is the board size -- p is the number of pions

x = VarArray(size=p, dom=range(n * n))

satisfy(
    (dist(x[i], x[j]) < p - 1) & (x[i] != x[j]) for i in range(p) for j in range(i + 1, p)
)
