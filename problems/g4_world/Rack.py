from pycsp3 import *

nRacks, models, cardTypes = data.nRacks, data.models, data.cardTypes

# we add first a dummy model (0,0,0)
models = [(0, 0, 0)] + [tuple(model) for model in models]
nModels, nTypes = len(models), len(cardTypes)

powers, sizes, costs = [row[0] for row in models], [row[1] for row in models], [row[2] for row in models]
cardPowers, cardDemands = [row[0] for row in cardTypes], [row[1] for row in cardTypes]

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

# note that we use a quaternary table constraint instead of three binary table constraints, as below

# linking model and power of the ith rack
# [(m[i], p[i]) in enumerate(powers) for i in range(nRacks)],

# linking model and size of the ith rack
# [(m[i], s[i]) in enumerate(sizes) for i in range(nRacks)],

# linking model and cost of the ith rack
# [(m[i], c[i]) in enumerate(costs) for i in range(nRacks)],
