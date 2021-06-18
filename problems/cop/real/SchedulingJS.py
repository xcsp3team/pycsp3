"""
See https://en.wikipedia.org/wiki/Job_shop_scheduling

Example of Execution:
  python3 SchedulingJS.py -data=Sadeh-js-e0ddr1-0.json
"""
from pycsp3 import *

jobs = data
horizon = max(job.dueDate for job in jobs) if all(job.dueDate != -1 for job in jobs) else sum(sum(job.durations) for job in jobs)
durations = [job.durations for job in jobs]
indexes = [[job.resources.index(j) for j in range(len(job.durations))] for job in jobs]
n, m = len(jobs), len(jobs[0].durations)

# s[i][j] is the start time of the jth operation for the ith job
s = VarArray(size=[n, m], dom=range(horizon))

satisfy(
    # operations must be ordered on each job
    [Increasing(s[i], lengths=durations[i]) for i in range(n)],

    # respecting release dates
    [s[i][0] > jobs[i].releaseDate for i in range(n) if jobs[i].releaseDate > 0],

    # respecting due dates
    [s[i][-1] <= jobs[i].dueDate - durations[i][-1] for i in range(n) if 0 <= jobs[i].dueDate < horizon - 1],

    # no overlap on resources
    [NoOverlap(tasks=[(s[i][indexes[i][j]], durations[i][indexes[i][j]]) for i in range(n)]) for j in range(m)]
)

minimize(
    # minimizing the makespan
    Maximum(s[i][-1] + durations[i][-1] for i in range(n))
)

""" Comments
1) the group of overlap constraints could be equivalently written:
 [NoOverlap(origins=[s[i][indexes[i][j]] for i in range(n)], lengths=[durations[i][indexes[i][j]] for i in range(n)]) for j in range(m)]
"""