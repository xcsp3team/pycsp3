"""
Problem 076 on CSPLib, and NumberJack example


Examples of Execution:
  python3 CostasArray.py
  python3 CostasArray.py -data=10
"""

from pycsp3 import *

n = data or 8

# x[i] is the row where is put the ith mark (on the ith column)
x = VarArray(size=n, dom=range(n))

satisfy(
    # all marks are on different rows (and columns)
    AllDifferent(x),

    # all displacement vectors between the marks must be different
    [AllDifferent(x[i] - x[i + d] for i in range(n - d)) for d in range(1, n - 1)]
)

""" Comments
1) how to break all symmetries?  x[0] <= math.ceil(n / 2), x[0] < x[-1], ... ? TODO
"""
