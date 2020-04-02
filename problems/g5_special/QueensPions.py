from pycsp3 import *

order, nQueens, nPions= data

q = VarArray(size=nQueens, dom=range(order))

p = VarArray(size=nPions, dom=range(order * order))

satisfy(
    [(q[i] != q[j]) & (dist(q[i], q[j]) != dist(i, j)) for i in range(nQueens) for j in range(i + 1, nQueens)],

    [(dist(p[i], p[j]) < nPions - 1) & (p[i] != p[j]) for i in range(nPions) for j in range(i + 1, nPions)]
)

if variant("mul"):
    satisfy(
        (q[i] != p[j] % order) | (i != p[j] // order) for i in range(nQueens) for j in range(nPions)
    )