"""
Problem 022 on CSPLib

The model below is without the cost parameter, as in Minizinc.

Example of Execution:
  python3 BusScheduling.py -data=BusScheduling_r1.json
"""

from pycsp3 import *

nTasks, shifts = data
nShifts = len(shifts)

# x[i] is 1 iff the ith shift is selected
x = VarArray(size=nShifts, dom={0, 1})

satisfy(
    # each task is covered by exactly one shift
    Count(x[i] for i, shift in enumerate(shifts) if t in shift) == 1 for t in range(nTasks)
)

minimize(
    # minimizing the number of shifts
    Sum(x)
)

""" Comments
1) Note that the default value for Count is 1. We can equivalently write:
 Count([x[i] for i, shift in enumerate(shifts) if t in shift], value=1) == 1 for t in range(nTasks)
"""
