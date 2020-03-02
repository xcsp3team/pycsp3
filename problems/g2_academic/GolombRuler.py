from pycsp3 import *

"""
 Problem 006 at CSPLib
"""

n = data.n
ub = n * n + 1  # a trivial upper-bound of an optimal ruler length

# x[i] is the position of the ith tick
x = VarArray(size=n, dom=range(ub))

if not variant():
    satisfy(
        # all distances are different
        AllDifferent(abs(x[i] - x[j]) for i in range(n) for j in range(i + 1, n))
    )
elif variant("dec"):
    satisfy(
        # all distances are different
        [abs(x[i] - x[j]) != abs(x[k] - x[l]) for i in range(n) for j in range(i + 1, n) for k in range(i + 1, n) for l in range(k + 1, n)]
    )
elif variant("aux"):
    # y[i][j] is the distance between x[i] and x[j], for i strictly less than j
    y = VarArray(size=[n, n], dom=lambda i, j: range(1, ub) if i < j else None)

    satisfy(
        # all distances are different
        AllDifferent(y),

        # linking variables from both arrays
        [x[j] == x[i] + y[i][j] for i in range(n) for j in range(i + 1, n)]
    )
    annotate(decision=x)

satisfy(
    # tag(symmetry-breaking)
    [x[0] == 0, Increasing(x, strict=True)]
)

minimize(
    # minimizing the position of the rightmost tick
    Maximum(x)
)
