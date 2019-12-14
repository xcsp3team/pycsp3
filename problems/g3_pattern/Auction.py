from decimal import Decimal

from pycsp3 import *

# Problem 063 at CSPLib

bids = data.bids
items = sorted({item for bid in bids for item in bid.items})
nBids = len(bids)


def values():
    scale = 0
    for v in [bid.value for bid in bids]:
        pos = v.find('.')
        if pos >= 0:
            i = len(v) - 1
            while v[i] == '0':
                i -= 1
            if i - pos > scale:
                scale = i - pos
    return [int(Decimal(v) * (10 ** scale)) for v in [Decimal(bid.value) for bid in bids]]


# b[i] is 1 iff the ith bid is selected
b = VarArray(size=nBids, dom={0, 1})

satisfy(
    # avoiding intersection of bids
    Count(scp, value=1) <= 1 for scp in [[b[i] for i, bid in enumerate(bids) if item in bid.items] for item in items]
)

maximize(
    # maximizing summed value of selected bids
    b * values()
)
