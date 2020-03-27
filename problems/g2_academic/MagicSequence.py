from pycsp3 import *

"""
 Problem 019 on CSPLib
"""

n = data.n

# x[i] is the ith value of the sequence
x = VarArray(size=n, dom=range(n))

satisfy(
    # each value i occurs exactly x[i] times in the sequence
    Cardinality(x, occurrences={i: x[i] for i in range(n)}),

    # tag(redundant-constraints)
    [Sum(x) == n, Sum((i - 1) * x[i] for i in range(n)) == 0]
)


# Sum((i - 1) * x[i] for i in range(n)) == 0, or equivalently, x * range(-1, n - 1) == 0
