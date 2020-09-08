from pycsp3 import *

x = VarArray(size=[10, 4], dom=range(10))
y = VarArray(size=[4], dom=range(10))

satisfy(
    [Maximum(x[i]) == y[i] if i % 2 == 0 else Maximum(x[i]) > 4 for i in range(4)],
    [NValues(x[i]) == y[i] for i in range(4)],
    [Sum(x[:, i]) - y[i] < 3 for i in range(4)],  # TODO Sum(x[:, i]) < y[i] + 3  ... is not working
    [Maximum(x[i]) - Minimum(x[i]) < 6 for i in range(4)],
    [Maximum(x[i]) + Minimum(x[i]) < 6 for i in range(4)]
)
