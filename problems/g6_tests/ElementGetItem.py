from pycsp3 import *

x = VarArray(size=[10, 10], dom=range(150))
z = VarArray(size=[10, 10, 10], dom=range(150))
q = VarArray(size=[10, 10, 10], dom=range(150))

satisfy(
    x[x[0][0]][0] == 5,

    z[0][z[0][0][0]][q[0][1][2]] == 5,

    z[1][z[0][0][0]][q[0][1][2]] == 6

)