from pycsp3 import *

n, constraints = data.n, data.ctrs

x = VarArray(size=n, dom={0, 1})

satisfy(
    x * c.coeffs == c.limit for c in constraints
)
