from pycsp3 import *

"""
 Problem 061 at CSPLib
"""

horizon = data.horizon
capacities = data.resourceCapacities
jobs, nJobs = data.jobs, len(data.jobs)


def cumulative_for(k):
    indexes = [i for i in range(nJobs) if jobs[i].requiredQuantities[k] > 0]
    origins = [s[i] for i in indexes]
    lengths = [jobs[i].duration for i in indexes]
    heights = [jobs[i].requiredQuantities[k] for i in indexes]
    return Cumulative(origins=origins, lengths=lengths, heights=heights)


# s[i] is the starting time of the ith job
s = VarArray(size=nJobs, dom=lambda i: {0} if i == 0 else range(horizon))

satisfy(
    # precedence constraints
    [s[i] + job.duration <= s[j] for i, job in enumerate(jobs) for j in job.successors],

    # resource constraints
    [cumulative_for(k) <= capacity for k, capacity in enumerate(capacities)]
)

minimize(
    s[- 1]
)
