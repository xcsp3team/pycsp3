from pycsp3 import *

"""
 Problem 026 at CSPLib
"""

nTeams = data.nTeams
nWeeks, nPeriods, nMatches = nTeams - 1, nTeams // 2, (nTeams - 1) * nTeams // 2


def match_number(t1, t2):
    return nMatches - ((nTeams - t1) * (nTeams - t1 - 1)) // 2 + (t2 - t1 - 1)


table = {(t1, t2, match_number(t1, t2)) for t1 in range(nTeams) for t2 in range(t1 + 1, nTeams)}

# h[w][p] is the home team at week w and period p
h = VarArray(size=[nWeeks, nPeriods], dom=range(nTeams))

# a[w][p] is the away team at week w and period p
a = VarArray(size=[nWeeks, nPeriods], dom=range(nTeams))

# m[w][p] is the number of the match at week w and period p
m = VarArray(size=[nWeeks, nPeriods], dom=range(nMatches))

# hd[p] is the home team for the dummy match of period p  tag(dummy-week)
hd = VarArray(size=nPeriods, dom=range(nTeams))

# ad[p] is the away team for the dummy match of period p  tag(dummy-week)
ad = VarArray(size=nPeriods, dom=range(nTeams))

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
    ],

    # handling dummy week (variables and constraints)  tag(dummy-week)
    [
        # all teams are different in the dummy week
        AllDifferent(hd + ad),

        # each team plays two times in each period
        [Cardinality(h[:, p] + a[:, p] + [hd[p], ad[p]], occurrences={t: 2 for t in range(nTeams)}) for p in range(nPeriods)],

        [hd[p] < ad[p] for p in range(nPeriods)]
    ]
)



# group(extension([h[p][w], a[p][w], m[p][w]], table=table) for p in range(nPeriods) for w in range(nWeeks)).note(
#    "linking variables through ternary table constraints")

# allDifferent(m).note("all matches are different (no team can play twice against another team)")

# group(allDifferent([columnOf(h, w), columnOf(a, w)]) for w in range(nWeeks)).note("each week, all teams are different (each team plays each week)")
# group(cardinality([h[p], a[p]], values=allTeams, occurs=rangeClosed(1, 2)) for p in range(nPeriods)).note("each team plays at most two times in each period")

# b2 = block().note("handling dummy week (variables and constraints)").tag("dummyWeek")
# b2.add(allDifferent([hd, ad]).note("all teams are different in the dummy week"))
# b2.add(lessThan(hd[p], ad[p]) for p in range(nPeriods))
# b2.add(cardinality([h[p], hd[p], ad[p], a[p]], values=allTeams, occurs=2).note("each team plays two times in each period") for p in range(nPeriods))


# b = block().tag(SYMMETRY_BREAKING)
# b.add(
#    instantiation(columnOf(m, 0), values=[matchNumber(2 * p, 2 * p + 1) for p in range(nPeriods)]).note("the first week is set : 0 vs 1, 2 vs 3, 4 vs 5, etc."))
# b.add(exactlyOne(columnOf(m, w), assignedTo=matchNumber(0, w + 1)).note("the match '0 versus t' (with t strictly greater than 0) appears at week t-1") for w in
#      range(nWeeks))
