from pycsp3 import *

k, d = data.k, data.d

# x[i][j] is the value of the matrix at row i and column j
x = VarArray(size=[k, k], dom=set(range(-d, -1)) | {0} | set(range(2, d+1)))

det = Var(dom={-1, 1})

if k == 3:
    nodes = [
        x[0][0] * x[1][1] * x[2][2],
        x[0][0] * x[1][2] * x[2][1],
        x[0][1] * x[1][2] * x[2][0],
        x[0][1] * x[1][0] * x[2][2],
        x[0][2] * x[1][0] * x[2][1],
        x[0][2] * x[1][1] * x[2][0]
    ]
    satisfy(
        Sum(nodes * [1, -1, 1, -1, 1, -1]) == det
    )
    # TO BE continued


satisfy(
    # Increasingly ordering both rows and columns
    # tag(symmetryBreaking)
    LexIncreasing(x, matrix=True)
)

