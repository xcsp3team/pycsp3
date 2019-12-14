from pycsp3 import *

nDepots, nRestaurants = data.nDepots, len(data.restaurants)
positions = [r.position for r in data.restaurants]
distances = cp_array([abs(p - positions[i]) for p in positions] for i in range(nRestaurants))  # NOTE: cp_array is necessary for using the constraint Element

# x[j] is the index of the restaurant used as the jth depot
x = VarArray(size=nDepots, dom=range(nRestaurants))

# d[i][j] is the distance between the ith restaurant and the jth depot
d = VarArray(size=[nRestaurants, nDepots], dom=lambda i, j: distances[i])

# md[i] is the minimum distance between the ith restaurant and any depot
md = VarArray(size=nRestaurants, dom=lambda i: distances[i])

satisfy(
    # linking positions of depots with their distances to the restaurants
    [distances[i][x[j]] == d[i][j] for i in range(nRestaurants) for j in range(nDepots)],

    # computing minimum distances
    [Minimum(d[i]) == md[i] for i in range(nRestaurants)],

    # tag(symmetry-breaking)
    Increasing(x, strict=True)
)

minimize(
    Sum(md)
)


# alternative : a table constraint:
# [(x[j], d[i][j]) in [(k, distance) for (k, distance) in enumerate(distances[i])] for i in range(nRestaurants) for j in range(nDepots)],
