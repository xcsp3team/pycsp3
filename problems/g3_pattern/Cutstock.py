from pycsp3 import *

"""
 See "Mathematical methods of organizing and planning production" by L. V. Kantorovich, Management Science, 6(4):366–422, 1960
     "From High-Level Model to Branch-and-Price Solution in G12", by J. Puchinger, P. Stuckey, M. Wallace, and S. Brand, CPAIOR 2008: 218-232
"""

nPieces, pieceLength = data.nPieces, data.pieceLength
lengths, demands = [item.length for item in data.items], [item.demand for item in data.items]  # or zip(*data.items)
nItems = len(data.items)

# p[i] is 1 iff the ith piece of the stock is used
p = VarArray(size=nPieces, dom={0, 1})

# r[i][j] is the number of items of type j built using stock piece i
r = VarArray(size=[nPieces, nItems], dom=lambda i, j: range(demands[j] + 1))

satisfy(
    # each item demand must be exactly satisfied
    [Sum(r[:, j]) == demand for j, demand in enumerate(demands)],

    # each piece of the stock cannot provide more than its length
    [r[i] * lengths <= p[i] * pieceLength for i in range(nPieces)],

    # tag(symmetry-breaking)
    [Decreasing(p), LexDecreasing(r)]
)

minimize(
    # minimizing the number of used pieces
    Sum(p)
)
