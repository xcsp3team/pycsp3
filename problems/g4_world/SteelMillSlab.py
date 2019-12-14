from pycsp3 import *

orders = data.orders
slabCapacities = sorted(set([0] + data.slabCapacities))
maxCapacity = slabCapacities[-1]
possibleLosses = [min([v for v in slabCapacities if v >= i]) - i for i in range(maxCapacity + 1)]

sizes = [order.size for order in orders]
allColors = sorted(set(order.color for order in orders))
nOrders, nSlabs, nColors = len(orders), len(orders), len(allColors)
colorGroups = [[i for i, order in enumerate(orders) if order.color == color] for color in allColors]

# sb[i] is the slab used to produce the ith order
sb = VarArray(size=nOrders, dom=range(nSlabs))

# ld[j] is the load of the jth slab
ld = VarArray(size=nSlabs, dom=range(maxCapacity + 1))

# ls[j] is the loss of the jth slab
ls = VarArray(size=nSlabs, dom=set(possibleLosses))

if not variant():
    satisfy(
        # computing (and checking) the load of each slab
        [[sb[i] == j for i in range(nOrders)] * sizes == ld[j] for j in range(nSlabs)],

        # computing the loss of each slab 
        [(ld[j], ls[j]) in [(i, loss) for i, loss in enumerate(possibleLosses)] for j in range(nSlabs)],

        # no more than two colors for each slab 
        [Sum(disjunction(sb[i] == j for i in g) for g in colorGroups) <= 2 for j in range(nSlabs)]
        # TODO si je fais disjunction()*2 pour tester le xml est mauvais
        # il doit manquer un str quelque part pour les args
    )

elif variant("01"):
    # y[j][i] is 1 iff the jth slab is used to produce the ith order
    y = VarArray(size=[nSlabs, nOrders], dom={0, 1})
    # z[j][c] is 1 iff the jth slab is used to produce an order of color c
    z = VarArray(size=[nSlabs, nColors], dom={0, 1})

    satisfy(
        # linking variables sb and y
        [iff(sb[i] == j, y[j][i]) for j in range(nSlabs) for i in range(nOrders)],

        # linking variables sb and z
        [imply(sb[i] == j, z[j][allColors.index(orders[i].color)]) for j in range(nSlabs) for i in range(nOrders)],

        # computing (and checking) the load of each slab
        [y[j] * sizes == ld[j] for j in range(nSlabs)],
        # the reverse side ? eq(z[s]{c] = 1 => or(...) // not really necessary but could help ?

        # computing the loss of each slab
        [(ld[j], ls[j]) in [(i, loss) for i, loss in enumerate(possibleLosses)] for j in range(nSlabs)],

        # no more than two colors for each slab
        [Sum(z[j]) <= 2 for j in range(nSlabs)]

    )

satisfy(
    # tag(redundant-constraints)
    Sum(ld) == sum(sizes),

    # tag(symmetry-breaking)
    [
        Decreasing(ld),

        [sb[i] <= sb[j] for i in range(nOrders) for j in range(i + 1, nOrders) if (orders[i].size, orders[i].color) == (orders[j].size, orders[j].color)]
    ]
)

minimize(
    # minimizing summed up loss
    Sum(ls)
)


#       [expr * sizes == ld[j] for j, expr in [(j, [sb[i] == j for i in range(nOrders)]) for j in range(nSlabs)]],
