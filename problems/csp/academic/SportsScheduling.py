"""
Problem 026 on CSPLib

Examples of Execution:
  python3 SportsScheduling.py
  python3 SportsScheduling.py -data=10
  python3 SportsScheduling.py -data=10 -variant=dummy
"""

from pycsp3 import *

nTeams = data or 8
nWeeks, nPeriods, nMatches = nTeams - 1, nTeams // 2, (nTeams - 1) * nTeams // 2


def match_number(t1, t2):
    return nMatches - ((nTeams - t1) * (nTeams - t1 - 1)) // 2 + (t2 - t1 - 1)


table = {(t1, t2, match_number(t1, t2)) for t1, t2 in combinations(range(nTeams),2)}

# h[w][p] is the home team at week w and period p
h = VarArray(size=[nWeeks, nPeriods], dom=range(nTeams))

# a[w][p] is the away team at week w and period p
a = VarArray(size=[nWeeks, nPeriods], dom=range(nTeams))

# m[w][p] is the number of the match at week w and period p
m = VarArray(size=[nWeeks, nPeriods], dom=range(nMatches))

satisfy(
    # linking variables through ternary table constraints
    [(h[w][p], a[w][p], m[w][p]) in table for w in range(nWeeks) for p in range(nPeriods)],

    # all matches are different (no team can play twice against another team)
    AllDifferent(m),

    # each week, all teams are different (each team plays each week)
    [AllDifferent(h[w] + a[w]) for w in range(nWeeks)],

    # each team plays at most two times in each period
    [Cardinality(h[:, p] + a[:, p], occurrences={t: range(1, 3) for t in range(nTeams)}) for p in range(nPeriods)],

    # tag(symmetry-breaking)
    [
        # the match '0 versus t' (with t strictly greater than 0) appears at week t-1
        [Count(m[w], value=match_number(0, w + 1)) == 1 for w in range(nWeeks)],

        # the first week is set : 0 vs 1, 2 vs 3, 4 vs 5, etc.
        [m[0][p] == match_number(2 * p, 2 * p + 1) for p in range(nPeriods)]
    ]
)

if variant("dummy"):
    # hd[p] is the home team for the dummy match of period p  tag(dummy-week)
    hd = VarArray(size=nPeriods, dom=range(nTeams))

    # ad[p] is the away team for the dummy match of period p  tag(dummy-week)
    ad = VarArray(size=nPeriods, dom=range(nTeams))

    satisfy(
        # handling dummy week (variables and constraints)  tag(dummy-week)
        [
            # all teams are different in the dummy week
            AllDifferent(hd + ad),

            # each team plays two times in each period
            [Cardinality(h[:, p] + a[:, p] + [hd[p], ad[p]], occurrences={t: 2 for t in range(nTeams)}) for p in range(nPeriods)],

            # tag(symmetry-breaking)
            [hd[p] < ad[p] for p in range(nPeriods)]
        ]
    )
