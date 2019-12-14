from pycsp3 import *

x = Var(0, 1)
y = Var(0, 1)
z = Var(0, 1)

satisfy(
    (x, y) in {(0, 0), (1, 1)},
    (x, z) in {(0, 0), (1, 1)},
    (y, z) in {(0, 1), (1, 0)}
)
