from pycsp3 import *

shifts = data.shifts
nTasks, nShifts = data.nTasks, len(shifts)

# x[i] is 1 iff the ith shift is selected
x = VarArray(size=nShifts, dom={0, 1})

satisfy(
    # Each task is covered by exactly one shift
    Count(x[i] for i, shift in enumerate(shifts) if t in shift) == 1 for t in range(nTasks)
)

minimize(
    Sum(x)
)


# Count([x[i] for i, shift in enumerate(shifts) if t in shift], value=1) == 1 for t in range(nTasks)
