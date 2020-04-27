from pycsp3 import *

x = VarArray(size=[10, 10], dom=range(150))
z = VarArray(size=[10, 10, 10], dom=range(150))
q = VarArray(size=[10, 10, 10], dom=range(150))
idx = Var(range(10))
res = Var(range(2, 152))

satisfy(
    x[x[0][0]][0] == 5,

    z[0][z[0][0][0]][q[0][1][2]] == 5,

    z[1][z[0][0][0]][q[0][1][2]] == 6,

    x[0][idx] == res - 2,

    res - 2 == x[1][idx],

    Sum(x[0]) > x[1] * range(10),

    Sum(x[0]) > cp_array(list(range(10))) * x[1]

)
