from pycsp3 import *

capacity, items = data.capacity, data.items
weights = [item.weight for item in items]
values = [item.value for item in items]

# x[i] is 1 iff the ith item is selected
x = VarArray(size=len(items), dom={0, 1})

satisfy(
    x * weights <= capacity
)

maximize(
    # maximizing summed up value (benefit)
    x * values
)
