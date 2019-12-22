from pycsp3 import *

x = VarArray(size=[10, 10], dom=range(150))
y = VarArray(size=[10, 10], dom=range(150))
z = VarArray(size=10, dom=range(150))

satisfy(
    [Sum(x[p]) in range(100) for p in range(10)],
    [Sum(x[p]) in {1, 2, 3} for p in range(10)],
    [Sum(x[p]) not in range(100) for p in range(10)],
    [Sum(x[p]) not in {1, 2, 3} for p in range(10)],
    [Sum(x[p]) <= 5 for p in range(10)],
    [Sum(x[p]) < 5 for p in range(10)],
    [Sum(x[p]) >= 5 for p in range(10)],
    [Sum(x[p]) > 5 for p in range(10)],
    [Sum(x[p]) == 5 for p in range(10)],
    [Sum(x[p]) != 5 for p in range(10)],

    Sum(y) in range(50),
    Sum(y) not in range(50),
    Sum(y) in {1, 2, 3},
    Sum(y) not in {1, 2, 3},
    Sum(y) <= 5,
    Sum(y) < 5,
    Sum(y) >= 5,
    Sum(y) > 5,
    Sum(y) == 5,
    Sum(y) != 5
)
