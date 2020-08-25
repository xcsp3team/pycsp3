from pycsp3 import *

#  comment discarded
x, y, z = VarArray(size=3, dom={0, 1})

#  comment not discarded
xx = Var(dom={0, 1})

yy = Var(dom=[0, 1])
zz = Var(dom=(0, 1))

try:
    # comment discarded
    g1 = VarArray(size=[e for e in range(10)], dom=range(100))
except AssertionError as e:
    print("Wrong test 1:", e)

# comment not discarded
g1 = VarArray(size=[e for e in range(1, 5)], dom=range(100))
g2 = VarArray(size=[e for e in range(1, 5)], dom=[1, 2, 3])
g3 = VarArray(size=[e for e in range(1, 5)], dom={1, 2, 3})
g4 = VarArray(size=[e for e in range(1, 5)], dom=(1, 2, 3))

z1 = VarArray(size=[2] * 10, dom=range(100))

try:
    z1 = VarArray(size="tata", dom=range(100))
except TypeError as e:
    print("Wrong test 2:", e)

try:
    z1 = VarArray(size=1, dom="g")
except TypeError as e:
    print("Wrong test 3:", e)

try:
    z1 = VarArray(dom="g")
except TypeError as e:
    print("Wrong test 4:", e)

try:
    z1 = VarArray(size=1)
except TypeError as e:
    print("Wrong test 5:", e)

z1 = Var()

try:
    VarArray(size=[2], dom={0, 1})
except AssertionError as e:
    print("Wrong test 6:", e)

try:
    Var(dom={0, 1})
except AssertionError as e:
    print("Wrong test 7:", e)
