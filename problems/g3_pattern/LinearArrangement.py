from pycsp3 import *

n, a = data.n, data.adjacence

# x[i] denotes the 'node' at the i-th position of the stack to be built (primal variables)
x = VarArray(size=n, dom=range(n))

# y[i] denotes the position of the 'node' whose value is i (dual variables)
y = VarArray(size=n, dom=range(n))  # TODO This array is irrelevant/useless ?

# d[i][j] denotes the distance between the ith and jth nodes (if they are adjacent)
d = VarArray(size=[n, n], dom=lambda i, j: range(1, n) if i < j and a[i][j] == 1 else None)

satisfy(
    AllDifferent(x),

    AllDifferent(y),

    Channel(x, y),

    # linking primal and distance variables
    [d[i][j] == dist(x[i], x[j]) for i in range(n) for j in range(i + 1, n) if a[i][j] == 1],

    # triangle constraints: distance(i,j) <= distance(i,k) + distance(k,j)  tag(redundant-constraints)
    [d[i][j] <= d[min(i, k)][max(i, k)] + d[min(j, k)][max(j, k)] for i in range(n) for j in range(i + 1, n) if a[i][j] == 1 for k in range(n)
     if a[i][k] == a[j][k] == 1]
)

minimize(
    Sum(d)
)
