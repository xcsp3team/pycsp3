"""
Problem 061 on CSPLib

## Data Example
  j030-01-01.json

## Model
  constraints: Cumulative

## Execution
  - python RCPSP.py -data=<datafile.json>
  - python RCPSP.py -data=<datafile.txt> -parser=RCPSP_Parser.py

## Links
  - https://www.csplib.org/Problems/prob061/
  - https://www.cril.univ-artois.fr/XCSP22/competitions/cop/cop

## Tags
  real, csplib, xcsp22
"""

from pycsp3 import *

horizon, capacities, jobs = data
# jobs, horizon, capacities = data
durations, successors, quantities = zip(*jobs)  # [job.duration for job in jobs]
nJobs = len(jobs)

# s[i] is the starting time of the ith job
s = VarArray(size=nJobs, dom=lambda i: {0} if i == 0 else range(horizon))

satisfy(
    # precedence constraints
    [s[i] + durations[i] <= s[j] for i in range(nJobs) for j in successors[i]],

    # resource constraints
    [
        Cumulative(
            Task(origin=s[i], length=durations[i], height=quantities[i][k]) for i in range(nJobs) if quantities[i][k] > 0
        ) <= capacity for k, capacity in enumerate(capacities)
    ]
)

minimize(
    s[-1]
)

""" Comments
1) for posting Cumulative constraints in an alternative way, it would be less compact to write:
 def cumulative_for(k):
    origins, lengths, heights = zip(*[(s[i], duration, quantities[k]) for i, (duration, _, quantities) in enumerate(jobs) if quantities[k] > 0])
    return Cumulative(origins=origins, lengths=lengths, heights=heights)
 ...
 [cumulative_for(k) <= capacity for k, capacity in enumerate(capacities)]

2) in case of 1), using zip is compacter than writing something like:
 indexes = [i for i in range(nJobs) if jobs[i].requiredQuantities[k] > 0]
 origins = [s[i] for i in indexes]
 lengths = [jobs[i].duration for i in indexes]
 heights = [jobs[i].requiredQuantities[k] for i in indexes]
"""
