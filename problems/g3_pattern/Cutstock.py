from pycsp3 import *

nPieces, pieceLength = data.nPieces, data.pieceLength
lengths = [item.length for item in data.items]
demands = [item.demand for item in data.items]
nItems = len(data.items)

# p[i] is 1 iff the ith piece of the stock is used
p = VarArray(size=[nPieces], dom={0, 1})

# r[i][j] is the number of items of type j built using stock piece i
r = VarArray(size=[nPieces, nItems], dom=lambda i, j: range(demands[j] + 1))

satisfy(
    # each item demand must be exactly satisfied
    [Sum(r[:, i]) == demand for i, demand in enumerate(demands)],

    # each piece of the stock cannot provide more than its length
    [r[i] * lengths <= p[i] * pieceLength for i in range(nPieces)],

    # tag(symmetry-breaking)
    [Decreasing(p), LexDecreasing(r)]
)

minimize(
    Sum(p)
)
