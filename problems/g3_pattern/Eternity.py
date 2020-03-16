from pycsp3 import *

n, m, pieces = data.n, data.m, data.pieces
assert n * m == len(pieces), "badly formed data"
max_value = max(max(piece) for piece in pieces)  # max possible value on pieces

table = {(i, pieces[i][r % 4], pieces[i][(r + 1) % 4], pieces[i][(r + 2) % 4], pieces[i][(r + 3) % 4]) for i in range(n * m) for r in range(4)}

# x[i][j] is the index of the piece at row i and column j
x = VarArray(size=[n, m], dom=range(n * m))

# t[i][j] is the value at the top of the piece at row i and column j
t = VarArray(size=[n + 1, m], dom=range(max_value + 1))

# l[i][j] is the value at the left of the piece at row i and column j
l = VarArray(size=[n, m + 1], dom=range(max_value + 1))

satisfy(
    # all pieces must be placed (only once)
    AllDifferent(x),

    # all pieces must be valid (i.e., must correspond to those given initially, possibly after applying some rotation)
    [(x[i][j], t[i][j], l[i][j + 1], t[i + 1][j], l[i][j]) in table for i in range(n) for j in range(m)],

    # putting special value 0 on borders
    [z == 0 for z in t[0] + l[:, -1] + t[-1] + l[:, 0]]
)
