from pycsp3 import *

x = VarArray(size=[10, 10], dom=range(150))
y = VarArray(size=[10, 10], dom=range(150))
z = VarArray(size=[10], dom=range(150))

satisfy(
    #  Equal to instantiation
    [x[i][j] == i * 10 + j for i in range(10) for j in range(10)]
)

satisfy(
    min(abs(x[0][0]), abs(y[0][0])),
    max(abs(x[0][0]), min(y[0], z[1]))
)

try:
    # TODO
    satisfy(x == z)
except TypeError as e:
    print("TODO:", e)

try:
    # TODO
    satisfy(x[0] == z)
except AssertionError as e:
    print("TODO:", e)

satisfy(x[0][0] == y[0][0])

try:
    # TODO
    satisfy(x[0] in {0, 1})
except AssertionError as e:
    print("TODO bousille forbidden fruit:", e)

print("HERE")

satisfy(
    #  right
    [x[0][0] == 0,
     x[0][0] > 0,
     x[0][0] < 0,
     x[0][0] != 0,
     x[0][0] >= 0,
     x[0][0] <= 0,
     x[0][0] in {0, 1},
     x[0][0] not in {0, 1}]
)
