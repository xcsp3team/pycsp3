from pycsp3 import *

weights = data.coefficients
n = len(weights)

# x[i] is 1 iff the ith item is selected
x = VarArray(size=n, dom={0, 1})

satisfy(
    x * t <= k for (t, k) in data.constraints
)

maximize(
    x * weights
)
