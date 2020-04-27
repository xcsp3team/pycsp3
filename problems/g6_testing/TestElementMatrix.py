from pycsp3 import *

t = cp_array([[1, 2, 3], [4, 5, 6]])
a = Var(0, 1)
b = Var(0, 1, 2)
r = Var(range(1, 7))

x = VarArray(size=[2, 2], dom=range(150))

y = Var(dom=range(5))
z = Var(dom=range(5))


satisfy(
    t[a][b] == r,
    a + b + 1 == r
    # ,x[y][z] == 1
)
