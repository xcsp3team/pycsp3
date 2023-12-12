"""
See https://www.researchgate.net/publication/220270875_The_Traveling_Tournament_Problem_Description_and_Benchmarks

Examples of Execution:
  python3 TravelingTournament.py -data=TravelingTournament_galaxy04.json -variant=a2
  python3 TravelingTournament.py -data=TravelingTournament_galaxy04.json -variant=a3
"""

from pycsp3 import *

distances = data
nTeams, nRounds = len(distances), len(distances) * 2 - 2
assert nTeams % 2 == 0, "An even number of teams is expected"
nConsecutiveGames = 2 if variant("a2") else 3  # used in one comment


def table(i):  # this is for the a game that is not the first or last one of the ith team
    return ({(1, 1, ANY, ANY, 0)} |
            {(0, 1, j, ANY, distances[i][j]) for j in range(nTeams) if j != i} |
            {(1, 0, ANY, j, distances[i][j]) for j in range(nTeams) if j != i} |
            {(0, 0, j1, j2, distances[j1][j2]) for j1 in range(nTeams) for j2 in range(nTeams) if different_values(i, j1, j2)})


def table_end(i):  # this is for the first or last game of the ith team
    return {(1, ANY, 0)} | {(0, j, distances[i][j]) for j in range(nTeams) if j != i}


def automaton():
    qi, q01, q02, q03, q11, q12, q13 = states = "q", "q01", "q02", "q03", "q11", "q12", "q13"
    tr2 = [(qi, 0, q01), (qi, 1, q11), (q01, 0, q02), (q01, 1, q11), (q11, 0, q01), (q11, 1, q12), (q02, 1, q11), (q12, 0, q01)]
    tr3 = [(q02, 0, q03), (q12, 1, q13), (q03, 1, q11), (q13, 0, q01)]
    return Automaton(start=qi, final=states[1:], transitions=tr2 if variant("a2") else tr2 + tr3)


# o[i][k] is the opponent (team) of the ith team  at the kth round
o = VarArray(size=[nTeams, nRounds], dom=range(nTeams))

# h[i][k] is 1 iff the ith team plays at home at the kth round
h = VarArray(size=[nTeams, nRounds], dom={0, 1})

# t[i][k] is the traveled distance by the ith team at the kth round. An additional round is considered for returning at home.
t = VarArray(size=[nTeams, nRounds + 1], dom=distances)

satisfy(
    # each team must play exactly two times against each other team
    [Cardinality(o[i], occurrences={j: 2 for j in range(nTeams) if j != i}) for i in range(nTeams)],

    # ensuring symmetry of games: if team i plays against j at round k, then team j plays against i at round k
    [o[o[i][k]][k] == i for i in range(nTeams) for k in range(nRounds)],

    # channeling the arrays o and h
    [h[o[i][k]][k] != h[i][k] for i in range(nTeams) for k in range(nRounds)],

    # playing against the same team must be done once at home and once away
    [
        If(
            o[i][k1] == o[i][k2],
            Then=h[i][k1] != h[i][k2]
        ) for i in range(nTeams) for k1, k2 in combinations(nRounds, 2)
    ],

    # at each round, opponents are all different  tag(redundant-constraints)
    [AllDifferent(o[:, k]) for k in range(nRounds)],

    # tag(symmetry-breaking)
    o[0][0] < o[0][-1],

    # at most 'nConsecutiveGames' consecutive games at home, or consecutive games away
    [h[i] in automaton() for i in range(nTeams)],

    # handling traveling for the first game
    [(h[i][0], o[i][0], t[i][0]) in table_end(i) for i in range(nTeams)],

    # handling traveling for the last game
    [(h[i][-1], o[i][-1], t[i][-1]) in table_end(i) for i in range(nTeams)],

    # handling traveling for two successive games
    [(h[i][k], h[i][k + 1], o[i][k], o[i][k + 1], t[i][k + 1]) in table(i) for i in range(nTeams) for k in range(nRounds - 1)]
)

minimize(
    # minimizing summed up traveled distance
    Sum(t)
)

""" Comments
1) with a cache, we could avoid building systematically similar automata (and tables)
2) note that when playing at home (whatever the opponent), the travel distance is 0
3) one can specify 'closed=True' as a parameter of Cardinality constraints, but this is
   not a requirement 
"""
