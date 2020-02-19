from pycsp3 import *

nRacks, models, cardTypes = data.nRacks, data.rackModels, data.cardTypes

# we add first a dummy model (0,0,0)
models = [{'power': 0, 'nConnectors': 0, 'price': 0}] + models
nModels, nTypes = len(models), len(cardTypes)

powers, sizes, costs = [model['power'] for model in models], [model['nConnectors'] for model in models], [model['price'] for model in models]
cardPowers, cardDemands = [cardType['power'] for cardType in cardTypes], [cardType['demand'] for cardType in cardTypes]

table = {(i, powers[i], sizes[i], costs[i]) for i in range(nModels)}

# m[i] is the model used for the ith rack
m = VarArray(size=nRacks, dom=range(nModels))

# nc[i][j] is the number of cards of type j put in the ith rack
nc = VarArray(size=[nRacks, nTypes], dom=lambda i, j: range(min(max(sizes), cardDemands[j]) + 1))

# p[i] is the power of the ith rack
p = VarArray(size=nRacks, dom=set(powers))

# s[i] is the size of the ith rack
s = VarArray(size=nRacks, dom=set(sizes))

# c[i] is the cost of the ith rack
c = VarArray(size=nRacks, dom=set(costs))

satisfy(
    # linking model with power, size and cost of the ith rack
    [(m[i], p[i], s[i], c[i]) in table for i in range(nRacks)],

    # connector-capacity constraints
    [Sum(nc[i]) <= s[i] for i in range(nRacks)],

    # power-capacity constraints
    [nc[i] * cardPowers <= p[i] for i in range(nRacks)],

    # demand constraints
    [Sum(nc[:, j]) == cardDemands[j] for j in range(nTypes)],

    # tag(symmetry-breaking)
    [
        Decreasing(m),
        (m[0] != m[1]) | (nc[0][0] >= nc[1][0])
    ]
)

minimize(
    # minimizing the total cost paid for all racks
    Sum(c)
)
