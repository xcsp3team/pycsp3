"""
The Multi dimensional knapsack problem was originally proposed as an optimization problem by the OR community.
Here, it is the feasability version, as used, e.g., in (Refalo, CP 2004) and (Pesant et al., JAIR 2012.

Example of Execution:
  python3 MultiKnapsack.py -data=MultiKnapsack_example.json
"""

from pycsp3 import *

weights, constraints = data
n = len(weights)

# x[i] is 1 iff the ith item is selected
x = VarArray(size=n, dom={0, 1})

satisfy(
    x * coeffs <= k for (coeffs, k) in constraints
)

maximize(
    x * weights
)
