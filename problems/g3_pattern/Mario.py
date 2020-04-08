"""
Problem proposed by A. Ollagnier and J.-G. Fages for the 2013 Minizinc Competition.

Examples of Execution:
  python3 Mario.py -data=Mario_easy-2.json
  python3 Mario.py -data=Mario_easy-2.json -variant=table
"""

from pycsp3 import *

marioHouse, luigiHouse, fuelLimit, houses = data
fuels = [house.fuelConsumption for house in houses]  # using cp_array is not necessary since intern arrays have the right type (for the constraint Element)
nHouses = len(houses)

# s[i] is the house succeeding to the ith house (itself if not part of the route)
s = VarArray(size=nHouses, dom=range(nHouses))

# f[i] is the fuel consumed at each step (from house i to its successor)
f = VarArray(size=nHouses, dom=lambda i: fuels[i])

if not variant():
    satisfy(
        # fuel consumption at each step
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

    # Mario must make a tour (not necessarily complete)
    Circuit(s),

    # Mario's house succeeds to Luigi's house
    s[luigiHouse] == marioHouse
)

maximize(
    # maximizing collected gold
    Sum((s[i] != i) * houses[i].gold for i in range(nHouses) if i not in {marioHouse, luigiHouse})
)


# [(s[i], f[i]) in [(j, houses[i].fuelConsumption[j]) for j in range(len(houses[i].fuelConsumption))] for i in range(nHouses)],

# [(s[i], f[i]) in [(j, fuel) for j, fuel in enumerate(houses[i].fuelConsumption)] for i in range(nHouses)],

# g[i] is the gold earned at house i
# g = VarArray(size=nHouses, dom=lambda i: {0, houses[i].gold})
# gold earned at each house
# maximize(
#    maximizing collected gold
#    Sum(g)
# )
