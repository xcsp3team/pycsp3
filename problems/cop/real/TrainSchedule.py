"""
The Brussels Central Problem (Fom course at UCL -- Louvain La Neuve))

The SNCB finally decided to rely on optimization technologies to schedule the departure
of its fleet at Brussels central. The problem to be solved is the following:
- Each train has a scheduled departure time.
- If a train departs earlier or later than expected, a penalty cost is inccured per time unit.
- After a train has left the station, no other train can depart for a given period
 (number of time units, or 'gap', which depends of the train that has left).
- The goal is to minimize the cost incurred by early and late departs.

Execution:
  python3 TrainSchedule.py -data=brussels.json
"""

from pycsp3 import *

trains = data or default_data("Brussels.json")
departures, gaps, costs = zip(*trains)
nTrains, horizon = len(trains), max(departures) + max(gaps) * 4 + 1  # arbitrary horizon

# x[i] is the time at which leaves the ith train
x = VarArray(size=nTrains, dom=range(horizon))

satisfy(
    # respecting security gaps between two trains leaving the station
    NoOverlap(origins=(x[i], x[j]), lengths=(gaps[i], gaps[j])) for i, j in combinations(range(nTrains), 2)
)

minimize(
    # minimizing penalty costs
    Sum(abs(x[i] - departures[i]) * costs[i] for i in range(nTrains))
)

""" Comments
1) we can also write:
 (s[i] + gaps[i] <= s[j]) | (s[j] + gaps[j] <= s[i]) for i, j in combinations(range(nTrains), 2)
  but the solver might not recognize the NoOverlap/disjunctive constraints
"""