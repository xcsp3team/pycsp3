from pycsp3 import *

capacity, nItems = data.capacity, len(data.items)
weights = [item.weight for item in data.items]
values = [item.value for item in data.items]

# x[i] is 1 iff the ith item is selected
x = VarArray(size=nItems, dom={0, 1})

satisfy(
    x * weights <= capacity
)

maximize(
    # maximizing summed up value (benefit)
    x * values
)
