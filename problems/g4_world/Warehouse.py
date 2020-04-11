"""
See Problem 034 on CSPLib

Examples of Execution:
  python3 Warehouse.py -data=Warehouse_example.json
  python3 Warehouse.py -data=Warehouse_example.txt -dataparser=Warehouse_Parser.py
"""

from pycsp3 import *

cost, capacities, costs = data  # cost is the fixed cost when opening a warehouse
nWarehouses, nStores = len(capacities), len(costs)

# w[i] is the warehouse supplying the ith store
w = VarArray(size=nStores, dom=range(nWarehouses))

# c[i] is the cost of supplying the ith store
c = VarArray(size=nStores, dom=lambda i: costs[i])

# o[j] is 1 if the jth warehouse is open
o = VarArray(size=nWarehouses, dom={0, 1})

satisfy(
    # capacities of warehouses must not be exceeded
    [Count(w, value=j) <= capacities[j] for j in range(nWarehouses)],

    # the warehouse supplier of the ith store must be open
    [o[w[i]] == 1 for i in range(nStores)],

    # computing the cost of supplying the ith store
    [costs[i][w[i]] == c[i] for i in range(nStores)]
)

minimize(
    # minimizing the overall cost
    Sum(c) + Sum(o) * cost
)
