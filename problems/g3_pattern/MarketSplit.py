from pycsp3 import *

n = data.n

x = VarArray(size=n, dom={0, 1})

satisfy(
    x * coeffs == k for (coeffs, k) in data.ctrs
)
