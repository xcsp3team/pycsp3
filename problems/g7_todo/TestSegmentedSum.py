from pycsp3 import *

# Problem 028 at CSPLib

r = data.r

# x[i][j] is the value of the matrix at row i and column j
x = VarArray(size=[r, r], dom={0, 1})

satisfy(
    # constraints on rows
    [Sum(row) in range(r // 2, r//2+1) for row in x],

    # constraints on columns
    [Sum(col) in range(r // 2, r//2 +1) for col in columns(x)],

    LexIncreasing(x, matrix=True)

)
