from pycsp3.problems.data.dataparser import *

next_int()  # nItems
next_int()  # nBids
data.bids = [DataDict({"value": t[0], "items": [int(t[i]) for i in range(1, len(t))]}) for line in remaining_lines() for t in [line.split(" ")]]
