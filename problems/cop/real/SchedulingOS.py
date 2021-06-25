"""
See https://en.wikipedia.org/wiki/Open-shop_scheduling

Example of Execution:
  python3 SchedulingOS.py -data=GP-os-01.json
"""

from pycsp3 import *

durations = data  # durations[i][j] is the duration of operation/machine j for job i
horizon = sum(sum(t) for t in durations) + 1
n, m = len(durations), len(durations[0])

# s[i][j] is the start time of the jth operation for the ith job
s = VarArray(size=[n, m], dom=range(horizon))

# d[i][j] is the duration of the jth operation of the ith job
d = VarArray(size=[n, m], dom=lambda i, j: durations[i])

# mc[i][j] is the machine used for the jth operation of the ith job
mc = VarArray(size=[n, m], dom=range(m))

# sd[i][k] is the start (dual) time of the kth machine when used for the ith job
sd = VarArray(size=[n, m], dom=range(horizon))

satisfy(
    # operations must be ordered on each job
    [Increasing(s[i], lengths=d[i]) for i in range(n)],

    # each machine must be used for each job
    [AllDifferent(mc[i]) for i in range(n)],

    [(mc[i][j], d[i][j]) in enumerate(durations[i]) for j in range(m) for i in range(n)],

    # tag(channeling)
    [sd[i][mc[i][j]] == s[i][j] for j in range(m) for i in range(n)],

    # no overlap on resources
    [NoOverlap(origins=sd[:, j], lengths=durations[:, j]) for j in range(m)],

    # tag(redundant-constraints)
    [s[i][-1] + d[i][-1] >= sum(durations[i]) for i in range(n)]
)

minimize(
    # minimizing the makespan
    Maximum(s[i][-1] + d[i][-1] for i in range(n))
)
