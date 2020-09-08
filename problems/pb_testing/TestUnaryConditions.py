from pycsp3 import *

x = VarArray(size=10, dom=range(150))
y = Var(dom=range(150))

satisfy(
    [x[p] in range(100) for p in range(10)],
    [x[p] in {1, 2, 3} for p in range(10)],
    [x[p] not in range(100) for p in range(10)],
    [x[p] not in {1, 2, 3} for p in range(10)],
    [x[p] <= 5 for p in range(10)],
    [x[p] < 5 for p in range(10)],
    [x[p] >= 5 for p in range(10)],
    [x[p] > 5 for p in range(10)],
    [x[p] == 5 for p in range(10)],
    [x[p] != 5 for p in range(10)],

    y in range(50),
    y not in range(50),
    y in {1, 2, 3, 3},
    y not in {1, 2, 3},
    y <= 5,
    y < 5,
    y >= 5,
    y > 5,
    y == 5,
    y != 5
)
