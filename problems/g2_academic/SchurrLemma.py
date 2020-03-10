from pycsp3 import *

"""
 Problem 015 at CSPLib

 Schurr's lemma problem.
 The variant 'mod' corresponds to the one proposed in [Bessiere Meseguer Freuder Larrosa, On forward checking for non-binary constraint satisfaction, 2002].
"""

n, d = data.nBalls, data.nBoxes

# x[i] is the box where the ith ball is put
x = VarArray(size=n, dom=range(d))

if not variant():
    satisfy(
        NValues(x[i], x[j], x[k]) > 1 for (i, j, k) in product(range(n), repeat=3) if i < j and i + 1 + j == k
    )
elif variant("mod"):
    satisfy(
        AllDifferent(x[i], x[j], x[k]) for (i, j, k) in product(range(n), repeat=3) if i < j and i + 1 + j == k
    )
