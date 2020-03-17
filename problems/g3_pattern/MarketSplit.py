from pycsp3 import *

n = data.n

x = VarArray(size=n, dom={0, 1})

satisfy(
    x * t == k for (t, k) in data.ctrs
)
