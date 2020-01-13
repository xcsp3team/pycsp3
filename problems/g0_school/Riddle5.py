from pycsp3 import *

# x[i] is the ith value of the sequence
x = VarArray(size=4, dom=range(15))

satisfy(
    # four successive values are needed
    [x[i] + 1 == x[i + 1] for i in range(3)],

    # values must sum up to 14
    Sum(x) == 14
)
