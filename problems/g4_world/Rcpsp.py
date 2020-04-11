"""
Problem 061 on CSPLib

Example of Execution:
  python3 Rcpsp.py -data=Rcpsp_j30-01-01.json
"""

from pycsp3 import *

horizon, capacities, jobs = data
nJobs = len(jobs)


def cumulative_for(k):
    origins, lengths, heights = zip(*[(s[i], duration, quantities[k]) for i, (duration, _, quantities) in enumerate(jobs) if quantities[k] > 0])
    return Cumulative(origins=origins, lengths=lengths, heights=heights)


# s[i] is the starting time of the ith job
s = VarArray(size=nJobs, dom=lambda i: {0} if i == 0 else range(horizon))

satisfy(
    # precedence constraints
    [s[i] + duration <= s[j] for i, (duration, successors, _) in enumerate(jobs) for j in successors],

    # resource constraints
    [cumulative_for(k) <= capacity for k, capacity in enumerate(capacities)]
)

minimize(
    s[- 1]
)


# Note that:

# a) using zip is compacter than writing something like:
#   indexes = [i for i in range(nJobs) if jobs[i].requiredQuantities[k] > 0]
#   origins = [s[i] for i in indexes]
#   lengths = [jobs[i].duration for i in indexes]
#   heights = [jobs[i].requiredQuantities[k] for i in indexes]

# b) using namedtuple facility allows us to get directly fields of the tuples. Instead, we could write:
#   origins, lengths, heights = zip(*[(s[i], job.duration, job.requiredQuantities[k]) for i, job in enumerate(jobs) if job.requiredQuantities[k] > 0])
