"""
Problem 063 on CSPLib

Examples of Execution:
  python3 Auction.py
  python3 Auction.py -data=Auction_example.json
"""

from pycsp3 import *

bids = data or default_data("Auction_example.json")
items = sorted({item for bid in bids for item in bid.items})
vals = integer_scaling(bid.value for bid in bids)
nBids = len(bids)

# x[i] is 1 iff the ith bid is selected
x = VarArray(size=nBids, dom={0, 1})

satisfy(
    # avoiding intersection of bids
    Count(scp, value=1) <= 1 for scp in [[x[i] for i, bid in enumerate(bids) if item in bid.items] for item in items]
)

maximize(
    # maximizing summed values of selected bids
    x * vals
)

"""
1) we avoid using values instead of vals as name for the list of bid values 
   as it may enter in conflict with the function values() in a notebook 
"""
