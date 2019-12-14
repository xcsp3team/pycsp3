from pycsp3 import *

# Problem 003 at CSPLib

n = data.n

#  x[i][j] is the value at row i and column j of the quasi-group
x = VarArray(size=[n, n], dom=range(n))

satisfy(
    # ensuring a Latin square
    AllDifferent(x, matrix=True),

    # ensuring idempotence (x[i][i] = i)
    # tag(idempotence)
    [x[i][i] == i for i in range(n)]
)

if variant("base"):
    if subvariant("v3"):
        satisfy(
            x[x[i][j], x[j][i]] == i for i in range(n) for j in range(n)
        )
    elif subvariant("v4"):
        satisfy(
            x[x[j, i], x[i, j]] == i for i in range(n) for j in range(n)
        )
    elif subvariant("v5"):
        satisfy(
            # TODO
            x[x[x[j, i], j], j] == i for i in range(n) for j in range(n)
        )
    elif subvariant("v6"):
        satisfy(
            # TODO
            x[x[i, j], j] == x[i, x[i, j]] for i in range(n) for j in range(n)
        )
    elif subvariant("v7"):
        satisfy(
            # TODO
            x[x[j, i], j] == x[i, x[j, i]] for i in range(n) for j in range(n)
        )
elif variant("aux"):
    if subvariant("v3"):
        y = VarArray(size=[n, n], dom=range(n * n))

        satisfy(
            [x[y[i][j]] == i for i in range(n) for j in range(n) if i != j],

            [y[i][j] == x[i][j] * n + x[j][i] for i in range(n) for j in range(n) if i != j]
        )
    elif subvariant("v4"):
        y = VarArray(size=[n, n], dom=range(n * n))

        satisfy(
            [x[y[i][j]] == i for i in range(n) for j in range(n) if i != j],

            [y[i][j] == x[j][i] * n + x[i][j] for i in range(n) for j in range(n) if i != j]
        )
    elif subvariant("v5"):
        y = VarArray(size=[n, n], dom=range(n))

        satisfy(
            [x[ANY, i][x[i][j]] == y[i][j] for i in range(n) for j in range(n) if i != j],

            [x[ANY, i][y[i][j]] == j for i in range(n) for j in range(n) if i != j]
        )
    elif subvariant("v7"):
        y = VarArray(size=[n, n], dom=range(n))

        satisfy(
            (col[x[j][i]] == y[i][j], x[i][x[j][i]] == y[i][j]) for i in range(n) for j, col in enumerate(columns(x)) if i != j
        )
