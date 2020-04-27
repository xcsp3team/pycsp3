from pycsp3 import *

#  comment discarded
x, y, z = VarArray(size=3, dom={0, 1})

#  comment not discarded
xx = Var(dom={0, 1})

yy = Var(dom=[0, 1])
try:
    zz = Var(dom=(0, 1))
except AssertionError as e:
    print("Test assert domain with tuple 1:", e)

try:
    # comment discarded
    g1 = VarArray(size=[e for e in range(10)], dom=range(100))
except AssertionError as e:
    print("Test assert dimensions != 0:", e)

# comment not discarded
g1 = VarArray(size=[e for e in range(1, 5)], dom=range(100))
g2 = VarArray(size=[e for e in range(1, 5)], dom=[1, 2, 3])
g3 = VarArray(size=[e for e in range(1, 5)], dom={1, 2, 3})

try:
    g3 = VarArray(size=[e for e in range(1, 5)], dom=(1, 2, 3))
except AssertionError as e:
    print("Test assert domain with tuple 2:", e)

z1 = VarArray(size=[2] * 10, dom=range(100))

try:
    z1 = VarArray(size="tata", dom=range(100))
except TypeError as e:
    print("Type error in size:", e)

try:
    z1 = VarArray(size=1, dom="g")
except TypeError as e:
    print("Type error in domain:", e)

try:
    z1 = VarArray(dom="g")
except TypeError as e:
    print("Missing a parameter:", e)

try:
    z1 = VarArray(size=1)
except TypeError as e:
    print("Missing a parameter:", e)

try:
    z1 = Var()
except TypeError as e:
    print("Missing a parameter:", e)

try:
    VarArray(size=[2], dom={0, 1})
except AssertionError as e:
    print("Not assigned VarArray:", e)

try:
    Var(dom={0, 1})
except AssertionError as e:
    print("Not assigned Var:", e)
