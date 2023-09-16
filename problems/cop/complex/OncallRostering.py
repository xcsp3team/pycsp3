"""
See Problem by Julien Fischer in MiniZinc -- https://github.com/MiniZinc/minizinc-benchmarks/tree/master/on-call-rostering

Examples of Execution:
  python3 OncallRostering.py -data=Oncall-4s-10d.json
  python3 OncallRostering.py -data=Oncall-4s-10d.dzn -dataparser=OncallRostering_ParserZ.py
"""

from pycsp3 import *

workloads, nDays, unavailable, fixed, offset, adjacency_cost, wednesday_cost = data
nWorkers = len(workloads)

assert nDays > 5 and nWorkers > 1
all_fixed = {v for t in fixed for v in t}
weekends = [i for i in range(nDays) if i % 5 == offset]
nWeekends = len(weekends)

# x[i] is the worker set for the ith day
x = VarArray(size=nDays, dom=range(nWorkers))

# do[j] is the number of times the jth worker is set for a regular day of the week
do = VarArray(size=nWorkers, dom=range(nDays - nWeekends + 1))

# wo[j] is the number of times the jth worker is set for a weekend
wo = VarArray(size=nWorkers, dom=range(nWeekends + 1))

# db is the balance violation wrt working days
db = Var(range(nDays + 1))

# db is the balance violation wrt working weekends
wb = Var(range(nDays + 1))

satisfy(
    # respecting fixed working days
    [x[i] == j for j in range(nWorkers) for i in fixed[j]],

    # respecting unavailability of workers
    [x[i] != j for j in range(nWorkers) for i in unavailable[j]],

    # counting working (regular) days by each worker
    Cardinality([x[i] for i in range(nDays) if i not in weekends], occurrences=do),

    # counting working weekends by each worker
    Cardinality([x[i] for i in weekends], occurrences=wo),

    # computing the balance violation wrt working days
    [abs(workloads[j2] * do[j1] - workloads[j1] * do[j2]) <= 100 * db for j1, j2 in combinations(range(nWorkers), 2)],

    # computing the balance violation wrt working weekends
    [abs(workloads[j2] * wo[j1] - workloads[j1] * wo[j2]) <= 100 * wb for j1, j2 in combinations(range(nWorkers), 2)],

    # no three successive days by the same worker (except if fixed days)
    [(x[i] != x[i + 1]) | (x[i] != x[i + 2]) for i in range(nDays - 2) if not {i, i + 1, i + 2}.issubset(all_fixed)],

    # no two successive weekends by the same worker (except if fixed days)
    [(x[i] != x[i + 5]) for i in weekends if i + 5 < nDays and not {i, i + 5}.issubset(all_fixed)],

    # a worker is not set for the day after the first one in case it is a weekend (except if fixed days)
    x[0] != x[1] if 0 in weekends and not {0, 1}.issubset(all_fixed) else None,

    # a worker is not set for the day before the last one in case it is a weekend (except if fixed days)
    x[nDays - 1] != x[nDays - 2] if nDays - 1 in weekends and not {nDays - 1, nDays - 2}.issubset(all_fixed) else None,

    # a worker is not set for the day before and after any day in case it is a weekend (except if fixed days)
    [(x[i] != x[i - 1]) & (x[i] != x[i + 1]) for i in weekends if 0 < i < nDays - 1 and not {i - 1, i, i + 1}.issubset(all_fixed)]
)

minimize(
    Sum((x[i] == x[i + 1]) * adjacency_cost for i in range(nDays - 1))
    + Sum((x[i] == x[i - 2]) * wednesday_cost for i in weekends if i >= 2)
    + db + wb
)

""" Comments
1) Compared to the mzn model (used for Competitions 2013 and 2018):
   - nDays-2 is used instead of nDays- 1 when considering adjacency cost (seems to be a typo in the mzn model?)
   - instead of explicitly introducing auxiliary variables to deal with some penalties (costs), 
     we post everything inside the objective function
2) Note how we can post a constraint according to a condition (by using ... if ... else None)
3) ACE is competitive: on a fast laptop, e.g., the bound 5 is found in 25 seconds for the instance 10s-150d 
"""
