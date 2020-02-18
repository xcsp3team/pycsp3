from pycsp3 import *

distances = data.distances
nCities = len(distances)

# c[i] is the ith city of the tour
c = VarArray(size=nCities, dom=range(nCities))

# d[i] is the distance between the cities i and i+1
d = VarArray(size=nCities, dom={d for row in distances for d in row})

satisfy(
    # Visiting each city only once
    AllDifferent(c)
)

if not variant():
    satisfy(
        # computing the distance between any two successive cities in the tour
        distances[c[i]][c[(i + 1) % nCities]] == d[i] for i in range(nCities)
    )

elif variant("table"):
    table = {(i, j, distances[i][j]) for i in range(nCities) for j in range(nCities) if i != j}

    satisfy(
        # computing the distance between any two successive cities in the tour
        [(c[i], c[(i + 1) % nCities], d[i]) in table for i in range(nCities)]
    )

minimize(
    Sum(d)
)
