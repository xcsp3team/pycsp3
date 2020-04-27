from pycsp3.problems.data.parsing import *

next_int()  # nItems
next_int()  # nBids
data["bids"] = [OrderedDict([("value", t[0]), ("items", [int(t[i]) for i in range(1, len(t))])]) for line in remaining_lines() for t in [line.split(" ")]]
