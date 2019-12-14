from pycsp3 import *

n, m, pieces = data.n, data.m, data.pieces
assert n * m == len(pieces), "badly formed data"
max_value = max(max(piece) for piece in pieces)  # max possible value on pieces

table = {(i, pieces[i][r % 4], pieces[i][(r + 1) % 4], pieces[i][(r + 2) % 4], pieces[i][(r + 3) % 4]) for i in range(n * m) for r in range(4)}

# id[i][j] is the id of the piece at row i and column j
id = VarArray(size=[n, m], dom=range(n * m))

# top[i][j] is the value at the top of the piece put at row i and column j
top = VarArray(size=[n, m], dom=range(max_value + 1))

# left[i][j] is the value at the left of the piece put at row i and column j
left = VarArray(size=[n, m], dom=range(max_value + 1))

# bot[j] is the value at the bottom of the piece put at the bottommost row and column j
bot = VarArray(size=m, dom=range(max_value + 1))

# right[i] is the value at the right of the piece put at the row i and the rightmost column
right = VarArray(size=n, dom=range(max_value + 1))


def scope(i, j):
    return id[i][j], top[i][j], left[i][j + 1] if j < m - 1 else right[j], top[i + 1][j] if i < n - 1 else bot[j], left[i][j]


satisfy(
    # all pieces must be placed (only once)
    AllDifferent(id),

    # all pieces must be valid (i.e., must correspond to those given initially, possibly after considering some rotation)
    [scope(i, j) in table for i in range(n) for j in range(m)],

    # put special value 0 on borders
    [x == 0 for x in left[:, 0] + right + top[0] + bot]
)
