from pycsp3 import *

x = VarArray(size=4, dom=range(15))

satisfy(
    [x[i] + 1 == x[i + 1] for i in range(3)],

    Sum(x) == 14
)
