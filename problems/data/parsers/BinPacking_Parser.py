from pycsp3.problems.data.parsing import *

nItems = next_int()
data["binCapacity"] = next_int()
data["itemWeights"] = sorted(next_int() for _ in range(nItems))
