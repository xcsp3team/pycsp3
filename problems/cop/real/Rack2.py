"""
Problem 031 on CSPLib

Example of Execution:
  python3 Rack2.py -data=Rack_r2b.json
"""

from pycsp3 import *

nRacks, models, cardTypes = data
models.append(models[0].__class__(0, 0, 0))  # we add first a dummy model (0,0,0) ; we get the class of the used named tuples to build a new one
powers, sizes, costs = zip(*models)
cardPowers, cardDemands = zip(*cardTypes)
nModels, nTypes = len(models), len(cardTypes)

table = {(i, powers[i], sizes[i], costs[i]) for i in range(nModels)}

# m[i] is the model used for the ith rack
m = VarArray(size=nRacks, dom=range(nModels))

# p[i] is the power of the model used for the ith rack
p = VarArray(size=nRacks, dom=powers)

# s[i] is the size (number of connectors) of the model used for the ith rack
s = VarArray(size=nRacks, dom=sizes)

# c[i] is the cost (price) of the model used for the ith rack
c = VarArray(size=nRacks, dom=costs)

# nc[i][j] is the number of cards of type j put in the ith rack
nc = VarArray(size=[nRacks, nTypes], dom=lambda i, j: range(min(max(sizes), cardDemands[j]) + 1))

satisfy(
    # linking rack models with powers, sizes and costs
    [(m[i], p[i], s[i], c[i]) in table for i in range(nRacks)],

    # connector-capacity constraints
    [Sum(nc[i]) <= s[i] for i in range(nRacks)],

    # power-capacity constraints
    [nc[i] * cardPowers <= p[i] for i in range(nRacks)],

    # demand constraints
    [Sum(nc[:, j]) == cardDemands[j] for j in range(nTypes)],

    # tag(symmetry-breaking)
    [Decreasing(m), imply(m[0] == m[1], nc[0][0] >= nc[1][0])]
)

minimize(
    # minimizing the total cost being paid for all racks
    Sum(c)
)

""" Comments
1) the introduced dummy model is not saved when using the option -dataexport because here we don't modify data.rackModels

2) one could write (to be ckecked)
 models = [{'power': 0, 'nConnectors': 0, 'price': 0}] + models

3) using zip allows a more compact statement, compared to:
 powers, sizes, costs = [model.power for model in models], [model.nConnectors for model in models], [model.price for model in models]
 cardPowers, cardDemands = [cardType.power for cardType in cardTypes], [cardType.demand for cardType in cardTypes]
"""
