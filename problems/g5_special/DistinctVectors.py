from pycsp3 import *

p, a, d = data.p, data.a, data.d

x = VarArray(size=[p, a], dom=range(d))

satisfy(
    AllDifferentList(x)
)
