from pycsp3 import *

x = VarArray(size=4, dom=range(15))

satisfy(
    x[0] + 1 == x[1],
    x[1] + 1 == x[2],
    x[2] + 1 == x[3],
    x[0] + x[1] + x[2] + x[3] == 14
)
