from pycsp3 import *

# similar model proposed by A. Ollagnier and J.-G. Fages for the 2013 Minizinc Competition

marioHouse, luigiHouse = data.marioHouse, data.luigiHouse
fuelLimit = data.fuelLimit
houses = data.houses
fuels = [house.fuelConsumption for house in houses]  # using cp_array is not necessary since intern arrays have the right type
nHouses = len(houses)

# s[i] is the house succeeding to the ith house (itself if not part of the route)
s = VarArray(size=nHouses, dom=range(nHouses))

# f[i] is the fuel consumed at each step (from house i to its successor)
f = VarArray(size=nHouses, dom=lambda i: set(fuels[i]))

# g[i] is the gold earned at house i
g = VarArray(size=nHouses, dom=lambda i: {0, houses[i].gold})

if not variant():
    satisfy(
        fuels[i][s[i]] == f[i] for i in range(nHouses)
    )

elif variant("table"):
    satisfy(
        # fuel consumption at each step
        (s[i], f[i]) in {(j, fuel) for (j, fuel) in enumerate(house.fuelConsumption)} for i, house in enumerate(houses)
    )

satisfy(
    # we cannot consume more than the available fuel
    Sum(f) <= fuelLimit,

    # gold earned at each house
    [iff(s[i] == i, g[i] == 0) for i in range(nHouses) if i not in {marioHouse, luigiHouse}],

    # Mario must make a tour (not necessarily complete)
    Circuit(s),

    # Mario's house succeedes to Luigi's house
    s[luigiHouse] == marioHouse
)

maximize(
    # maximizing collected gold
    Sum(g)
)


# [(s[i], f[i]) in [(j, houses[i].fuelConsumption[j]) for j in range(len(houses[i].fuelConsumption))] for i in range(nHouses)],

# [(s[i], f[i]) in [(j, fuel) for j, fuel in enumerate(houses[i].fuelConsumption)] for i in range(nHouses)],
