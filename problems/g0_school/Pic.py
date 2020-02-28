from pycsp3 import *

a, b = "a", "b"  # two symbols

x = Var(a, b)
y = Var(a, b)
z = Var(a, b)

satisfy(
    (x, y) in {(a, a), (b, b)},
    (x, z) in {(a, a), (b, b)},
    (y, z) in {(a, b), (b, a)}
)

