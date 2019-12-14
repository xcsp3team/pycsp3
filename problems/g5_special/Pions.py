from pycsp3 import *


n = data.n  # board size
p = data.p  # number of pions

x = VarArray(size=p, dom=range(n * n))

satisfy(
    (dist(x[i], x[j]) < p - 1) & (x[i] != x[j]) for i in range(p) for j in range(i + 1, p)
)
