"""
Problem 013 on CSPLib

Example of Execution:
  python3 ProgressiveParty.py -data=ProgressiveParty_example.json
"""

from pycsp3 import *

nPeriods, boats = data
nBoats = len(boats)
capacities, crews = zip(*boats)

# h[b] indicates if the boat b is a host boat
h = VarArray(size=nBoats, dom={0, 1})

# s[b][p] is the scheduled (visited) boat by the crew of boat b at period p
s = VarArray(size=[nBoats, nPeriods], dom=range(nBoats))

# g[b1][p][b2] is 1 if s[b1][p] = b2
g = VarArray(size=[nBoats, nPeriods, nBoats], dom={0, 1})

satisfy(
    # identifying host boats (when receiving)
    [iff(s[b][p] == b, h[b]) for b in range(nBoats) for p in range(nPeriods)],

    # identifying host boats (when visiting)
    [imply(s[b1][p] == b2, h[b2]) for b1 in range(nBoats) for b2 in range(nBoats) if b1 != b2 for p in range(nPeriods)],

    # channeling variables from arrays s and g
    [Channel(g[b][p], s[b][p]) for b in range(nBoats) for p in range(nPeriods)],

    # boat capacities must be respected
    [g[:, p, b] * crews <= capacities[b] for b in range(nBoats) for p in range(nPeriods)],

    # a guest boat cannot revisit a host
    [AllDifferent(s[b], excepting=b) for b in range(nBoats)],

    # guest crews cannot meet more than once
    [Sum(s[b1][p] == s[b2][p] for p in range(nPeriods)) <= 2 for b1, b2 in combinations(range(nBoats), 2)]
)

minimize(
    # minimizing the number of host boats
    Sum(h)
)


# less compact way of posting : [[g[i][p][b] for i in range(nBoats)] * crews <= boats[b].capacity for b in range(nBoats) for p in range(nPeriods)],
