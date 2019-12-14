from pycsp3 import *

n, v = data.nDominos, data.nValues

# x[i] is the value of the ith domino
x = VarArray(size=n, dom=range(v))

if not variant():
    satisfy(
        AllEqual(x),

        disjunction(x[0] + 1 == x[- 1], (x[0] == x[- 1]) == v - 1)
    )

elif variant("table"):
    satisfy(
        [(x[i], x[i + 1]) in {(a, a) for a in range(v)} for i in range(n - 1)],

        (x[0], x[- 1]) in {(a + 1, a) for a in range(v - 1)} | {(v - 1, v - 1)}
    )