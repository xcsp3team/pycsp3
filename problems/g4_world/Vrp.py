from pycsp3 import *

n, capacity, demand, distances = data.n, data.capacity, data.demand, data.distances

# x[i][j] is 1 iff the arc (i,j) is part of a route
x = VarArray(size=[n, n], dom=lambda i, j: {0} if i == j else {0, 1})

# u[i] is the load of vehicle after visiting node i (used for subtour elimination)
u = VarArray(size=n, dom=lambda i: {0} if i == 0 else range(capacity + 1))

satisfy(
    # exactly one incoming arc for each node j other than depot (node 0)
    [Count(x[:, j], value=1) == 1 for j in range(1, n)],

    # exactly one outgoing arc for each node i other than depot (node 0)  
    [Count(x[i], value=1) == 1 for i in range(1, n)],

    # Miller-Tucker-Zemlin subtour elimination 
    [[u[i], u[j], x[i][j]] * [1, -1, capacity] <= capacity - demand[j] for i in range(1, n) for j in range(1, n) if i != j],

    [u[i] >= demand[i] for i in range(1, n)]
)

minimize(
    x * distances
)
