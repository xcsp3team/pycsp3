from pycsp3 import *

"""
 Problem 007 on CSPLib

 For n=10:
 - 296 solutions if symmetry-breaking constraints are discarded
 - 148 and 104 solutions for the main and aux variants otherwise
"""

n = data.n

# x[i] is the ith note of the series
x = VarArray(size=n, dom=range(n))

if not variant():
    satisfy(
        # notes must occur once, and so form a permutation
        AllDifferent(x),

        # intervals between neighbouring notes must form a permutation
        AllDifferent(abs(x[i + 1] - x[i]) for i in range(n - 1)),

        # tag(symmetry-breaking)
        x[0] < x[n - 1]
    )

elif variant("aux"):
    # y[i] is the distance between x[i] and x[i+1]
    y = VarArray(size=n - 1, dom=range(1, n))

    satisfy(
        # notes must occur once, and so form a permutation
        AllDifferent(x),

        # intervals between neighbouring notes must form a permutation
        AllDifferent(y),

        # computing distances
        [y[i] == abs(x[i + 1] - x[i]) for i in range(n - 1)],

        # tag(symmetry-breaking)
        [x[0] < x[n - 1], y[0] < y[1]]
    )
