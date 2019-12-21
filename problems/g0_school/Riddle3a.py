from pycsp3 import *


def domain_x(i):
    return range(6) if i < 2 else range(9)


x = VarArray(size=4, dom=domain_x)

satisfy(
    x[0] + 1 == x[1],
    x[1] + 1 == x[2],
    x[2] + 1 == x[3],
    x[0] + x[1] + x[2] + x[3] == 14
)
