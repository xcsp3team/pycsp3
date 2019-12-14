from pycsp3 import *

n = 4

x = VarArray(size=n, dom={"r", "g", "b"})

satisfy(
    x[i] != x[j] for i in range(n) for j in range(i + 1, n)
)
