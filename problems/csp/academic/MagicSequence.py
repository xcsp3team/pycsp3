"""
Problem 019 on CSPLib

Examples of Execution:
  python3 MagicSequence.py
  python3 MagicSequence.py -data=10
"""

from pycsp3 import *

n = data or 8

# x[i] is the ith value of the sequence
x = VarArray(size=n, dom=range(n))

satisfy(
    # each value i occurs exactly x[i] times in the sequence
    Cardinality(x, occurrences={i: x[i] for i in range(n)}),

    # tag(redundant-constraints)
    [Sum(x) == n, Sum((i - 1) * x[i] for i in range(n)) == 0]
)

""" Comments
1) Sum((i - 1) * x[i] for i in range(n)) == 0
   could be equivalently written x * range(-1, n - 1) == 0
   but range(-1, n - 1) * x == 0 is currently not possible (requires 'cursing' * for range objects)
"""