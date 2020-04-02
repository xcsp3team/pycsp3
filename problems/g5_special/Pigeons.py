from pycsp3 import *

n = data  # number of pigeons

# p[i] is the hole where is put the ith pigeon
p = VarArray(size=n, dom=range(n - 1))

if not variant():
    satisfy(
        AllDifferent(p)
    )

elif variant("dec"):
    satisfy(
        p[i] != p[j] for i in range(n) for j in range(i + 1, n)
    )
