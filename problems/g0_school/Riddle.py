from pycsp3 import *

x1 = Var(range(15))
x2 = Var(range(15))
x3 = Var(range(15))
x4 = Var(range(15))

satisfy(
    x1 + 1 == x2,
    x2 + 1 == x3,
    x3 + 1 == x4,
    x1 + x2 + x3 + x4 == 14
)
