"""
Problem proposed by A. Ollagnier and J.-G. Fages for the 2013 Minizinc Competition.

Examples of Execution:
  python3 Mario.py -data=Mario_easy-2.json
  python3 Mario.py -data=Mario_easy-2.json -variant=table
"""

from pycsp3 import *

marioHouse, luigiHouse, fuelLimit, houses = data
fuels, golds = zip(*houses)  # using cp_array is not necessary since intern arrays have the right type (for the constraint Element)
nHouses = len(houses)

# s[i] is the house succeeding to the ith house (itself if not part of the route)
s = VarArray(size=nHouses, dom=range(nHouses))

if not variant():
    satisfy(
        # we cannot consume more than the available fuel
        Sum(fuels[i][s[i]] for i in range(nHouses)) <= fuelLimit,

        # Mario must make a tour (not necessarily complete)
        Circuit(s),

        # Mario's house succeeds to Luigi's house
        s[luigiHouse] == marioHouse
    )

else:
    # f[i] is the fuel consumed at each step (from house i to its successor)
    f = VarArray(size=nHouses, dom=lambda i: fuels[i])

    if variant("aux"):
        satisfy(
            # fuel consumption at each step
            fuels[i][s[i]] == f[i] for i in range(nHouses)
        )

    elif variant("table"):
        satisfy(
            # fuel consumption at each step
            (s[i], f[i]) in {(j, fuel) for (j, fuel) in enumerate(fuels[i])} for i, house in enumerate(houses)
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
    Sum((s[i] != i) * golds[i] for i in range(nHouses) if golds[i] != 0)
)

""" Comments
1) Note that the code below, when building the table is more compact than:
 [(s[i], f[i]) in [(j, houses[i].fuelConsumption[j]) for j in range(len(houses[i].fuelConsumption))] for i in range(nHouses)],
 or [(s[i], f[i]) in [(j, fuel) for j, fuel in enumerate(houses[i].fuelConsumption)] for i in range(nHouses)],

2) Note that introducing auxiliary variables for handling gold earned at each house could be as follows:
 # g[i] is the gold earned at house i
 g = VarArray(size=nHouses, dom=lambda i: {0, houses[i].gold})
 
  in that case, We need to introduce additional constraints, while the objective becomes:
 maximize(
   # maximizing collected gold
   Sum(g)
 )
"""
