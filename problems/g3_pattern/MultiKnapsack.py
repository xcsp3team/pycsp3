from pycsp3 import *

weights, constraints = data.coefficients, data.constraints
n = len(weights)

# x[i] is 1 iff the ith item is selected
x = VarArray(size=n, dom={0, 1})

satisfy(
    x * c.coeffs <= c.limit for c in constraints
)

maximize(
    x * weights
)
