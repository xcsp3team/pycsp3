from pycsp3 import *

p, a, d = data

x = VarArray(size=[p, a], dom=range(d))

satisfy(
    AllDifferentList(x)
)
