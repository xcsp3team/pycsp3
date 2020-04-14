from pycsp3 import *

n, m, points1, points2 = data
nPairs = len(points1)

# x[i][j] is the value at row i and column j (a boundary is put around the board).
x = VarArray(size=[n + 2, m + 2], dom=lambda i, j: {0} if i in {0, n + 1} or j in {0, m + 1} else range(nPairs + 1))

table = ({(0, ANY, ANY, ANY, ANY)}
         | {tuple(ne(v) if k in (i, j) else v for k in range(5)) for i, j in combinations(range(1, 5), 2) for v in range(1, nPairs + 1)})

satisfy(
    # putting two occurrences of each value on the board
    [x[i, j] == v + 1 for v in range(nPairs) for (i, j) in [points1[v], points2[v]]],

    # each cell with a fixed value has exactly one neighbour with the same value
    [Count([x[i - 1][j], x[i + 1][j], x[i][j - 1], x[i][j + 1]], value=v + 1) == 1 for v in range(nPairs) for (i, j) in [points1[v], points2[v]]],

    # each empty cell either contains 0 or has exactly two neighbours with the same value
    [(x[i][j], x[i - 1][j], x[i + 1][j], x[i][j - 1], x[i][j + 1]) in table for i in range(1, n + 1) for j in range(1, m + 1) if
     [i, j] not in points1 + points2]
)

minimize(
    Sum(x)
)


# Note that the table use (smart) conditions, which make code more compact than:

# table = ({(0, ANY, ANY, ANY, ANY)}
#          | {(v, v, v, ne(v), ne(v)) for v in range(1, nPairs + 1)}
#          | {(v, v, ne(v), v, ne(v)) for v in range(1, nPairs + 1)}
#          | {(v, v, ne(v), ne(v), v) for v in range(1, nPairs + 1)}
#          | {(v, ne(v), v, v, ne(v)) for v in range(1, nPairs + 1)}
#          | {(v, ne(v), v, ne(v), v) for v in range(1, nPairs + 1)}
#          | {(v, ne(v), ne(v), v, v) for v in range(1, nPairs + 1)})
