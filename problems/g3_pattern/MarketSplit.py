from pycsp3 import *

n = data.n

x = VarArray(size=n, dom={0, 1})

satisfy(
    x * c.coeffs == c.limit for c in data.ctrs
)
