"""
Problem 031 on CSPLib

Example of Execution:
  python3 Rack.py -data=Rack_r2.json
"""

from pycsp3 import *

nRacks, models, cardTypes = data
models.append([0, 0, 0])  # we add first a dummy model (0,0,0)
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
1) using zip is compacter than writing:
 powers, sizes, costs = [row[0] for row in models], [row[1] for row in models], [row[2] for row in models]
 cardPowers, cardDemands =[row[0] for row in cardTypes], [row[1] for row in cardTypes]

2) using a quaternary table constraint is simpler than using three binary table constraints, as below:
 # linking model and power of the ith rack
 [(m[i], p[i]) in enumerate(powers) for i in range(nRacks)],
 
 # linking model and size of the ith rack
 [(m[i], s[i]) in enumerate(sizes) for i in range(nRacks)],

 # linking model and cost of the ith rack
 [(m[i], c[i]) in enumerate(costs) for i in range(nRacks)],
"""
