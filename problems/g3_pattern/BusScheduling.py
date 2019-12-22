from pycsp3 import *

nTasks, nShifts = data.nTasks, len(data.shifts)

# x[i] is 1 iff the ith shift is selected
x = VarArray(size=nShifts, dom={0, 1})

satisfy(
    # Each task is covered by exactly one shift
    Count(x[i] for i, shift in enumerate(data.shifts) if t in shift) == 1 for t in range(nTasks)
)

minimize(
    Sum(x)
)


# Count([x[i] for i in range(nShifts) if t in shifts[i]], value=1) == 1 for t in range(nTasks)
