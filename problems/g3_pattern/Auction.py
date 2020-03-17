from pycsp3 import *

"""
 Problem 063 on CSPLib
"""

items = sorted({item for bid in data.bids for item in bid.items})
values = integer_scaling(bid.value for bid in data.bids)
nBids = len(data.bids)

# x[i] is 1 iff the ith bid is selected
x = VarArray(size=nBids, dom={0, 1})

satisfy(
    # avoiding intersection of bids
    Count(scp, value=1) <= 1 for scp in [[x[i] for i, bid in enumerate(data.bids) if item in bid.items] for item in items]
)

maximize(
    # maximizing summed values of selected bids
    x * values
)
