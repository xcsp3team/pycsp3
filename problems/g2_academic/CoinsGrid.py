from pycsp3 import *

# See Constraint Solving and Planning with Picat (page 43)
# From Tony Hurlimann, A coin puzzle, SVOR-contest 2007
# some data: (8,4) (8,5) (9,4) (10,4) (31,14)
# TODO: variants in Hurlimann's paper

n, c = data.n, data.c

#  x[i][j] is 1 if a coin is placed at row i and column j
x = VarArray(size=[n, n], dom={0, 1})

satisfy(
    [Sum(row) == c for row in x],

    [Sum(col) == c for col in columns(x)]
)

minimize(
    Sum(x[i][j] * abs(i - j) ** 2 for i in range(n) for j in range(n))
)
