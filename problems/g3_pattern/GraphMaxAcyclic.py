from pycsp3 import *

n, arcs = data.nNodes, data.arcs
valid_arcs = [(i, j) for i in range(n) for j in range(n) if i != j and arcs[i][j] != 0]


def n_valid(j):
    return len([(i, j) for i in range(n) if (i, j) in valid_arcs])


# x[i] is the number associated with the ith node
x = VarArray(size=n, dom=range(n))

# a[i][j] is 1 iff the arc from i to j is selected
a = VarArray(size=[n, n], dom=lambda i, j: {0, 1} if (i, j) in valid_arcs else None)

satisfy(
    AllDifferent(x)
)

if not variant():
    satisfy(
        iff(x[i] > x[j], a[i][j] == 1) for (i, j) in valid_arcs
    )

elif variant("cnt"):
    satisfy(
        [imply(x[i] <= x[j], a[i][j] == 0) for (i, j) in valid_arcs],

        [Count(a[:, j], value=1) <= 3 for j in range(n) if n_valid(j) > 3]
    )

maximize(
    Sum(a[i][j] * arcs[i][j] for (i, j) in valid_arcs)
)


# if modelVariant("smt"):
# c[i][j] is the cost of the link between i and j (whatever the direction)
#    c = varArray(size=[nNodes, nNodes], dom=lambda i, j: {arcs[i][j], arcs[j][i]}, when=lambda i, j: (arcs[i][j] != 0 or arcs[j][i] != 0) and i < j)
