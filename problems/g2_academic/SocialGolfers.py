from pycsp3 import *

# Problem 010 at CSPLib

nGroups, groupSize, nWeeks = data.nGroups, data.groupSize, data.nWeeks
allGroups = range(nGroups)
nPlayers = nGroups * groupSize

if not variant():
    #  x[w][p] is the group in which player p plays in week w
    x = VarArray(size=[nWeeks, nPlayers], dom=allGroups)

    satisfy(
        #  ensuring that two players don't meet more than one time
        [(x[w1][p1] != x[w1][p2]) | (x[w2][p1] != x[w2][p2]) for w1 in range(nWeeks)
         for w2 in range(w1 + 1, nWeeks) for p1 in range(nPlayers) for p2 in range(p1 + 1, nPlayers)],

        # respecting the size of the groups
        [Cardinality(x[w], occurrences={i: groupSize for i in range(nGroups)}) for w in range(nWeeks)],

        # tag(symmetry-breaking)
        [
            LexIncreasing(x, matrix=True),

            [x[0][p] == (p // groupSize) for p in range(nPlayers)],

            [x[w][k] == k for k in range(groupSize) for w in range(1, nWeeks)]

        ]
    )
elif variant("01"):
    # s[w][g][p] is 1 iff player p plays in group g at week w
    sch = VarArray(size=[nWeeks, nGroups, nPlayers], dom={0, 1})

    # tw[p1][p2][w] is 1 iff players p1 and p2 play together at week w
    tw = VarArray(size=[nPlayers, nPlayers, nWeeks], dom={0, 1}, when=lambda p1, p2, w: p1 < p2)

    # tgw[p1][p2][w][g] is 1 iff players p1 and p2 play together at week w in group g
    tgw = VarArray(size=[nPlayers, nPlayers, nWeeks, nGroups], dom={0, 1}, when=lambda p1, p2, w, g: p1 < p2)

    satisfy(
        #  each week, each player plays exactly once
        [Sum([sch[w][x][p] for x in range(nGroups)]) == 1 for w in range(nWeeks) for p in range(nPlayers)],

        #  each week, each group contains exactly #s players
        [Sum(sch[w][g]) == groupSize for w in range(nWeeks) for g in range(nGroups)],

        # constraints on scalar products for having no two players playing twice together
        [sch[w][g][p1] * sch[w][g][p2] == tgw[p1][p2][w][g] for w in range(nWeeks) for g in range(nGroups) for p1 in range(nPlayers) for p2 in range(p1 + 1, nPlayers)],

        [Sum(tgw[p1][p2][w]) == tw[p1][p2][w] for p1 in range(nPlayers) for p2 in range(p1 + 1, nPlayers) for w in range(nWeeks)],

        [Sum(tw[p1][p2]) <= 1 for p1 in range(nPlayers) for p2 in range(p1 + 1, nPlayers)],

        # tag(symmetry-breaking)
        [
            # lexicographic constraints ; each week, groups are strictly ordered
            [LexDecreasing(sch[w], strict=True) for w in range(nWeeks)],

            # lexicographic constraints ; weeks are strictly ordered (it suffices to consider the first group)
            LexDecreasing([sch[w][0] for w in range(nWeeks)], strict=True),

            # lexicographic constraints ; golfers are strictly ordered
            LexDecreasing([[sch[i][j][k] for i in range(nWeeks) for j in range(nGroups)] for k in range(nPlayers)], strict=True)
        ]

    )
