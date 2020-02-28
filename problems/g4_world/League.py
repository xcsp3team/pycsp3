from pycsp3 import *

nPlayers = data.nPlayers
leagueSize = data.leagueSize
rankings, countries = data.playerRankings, data.playerCountries

nLeagues = nPlayers // leagueSize + (1 if nPlayers % leagueSize != 0 else 0)
nCountries = len(set(countries))


def size(i):
    nFullLeagues = nLeagues if nPlayers % leagueSize == 0 else nLeagues - (leagueSize - nPlayers % leagueSize)
    return leagueSize + (0 if i < nFullLeagues else -1)


table = {(i, rankings[i], countries[i]) for i in range(nPlayers)}

# p[i][j] is the jth player of the ith league
p = VarArray(size=[nLeagues, leagueSize], dom=lambda i, j: range(nPlayers) if j < size(i) else None)

# r[i][j] is the ranking of the jth player of the ith league
r = VarArray(size=[nLeagues, leagueSize], dom=lambda i, j: set(rankings) if j < size(i) else None)

# c[i][j] is the country of the jth player of the ith league
c = VarArray(size=[nLeagues, leagueSize], dom=lambda i, j: set(countries) if j < size(i) else None)

satisfy(
    # each player belongs to only one league
    AllDifferent(p),

    # linking players with their rankings and countries
    [(p[i][j], r[i][j], c[i][j]) in table for i in range(nLeagues) for j in range(size(i))]
)

minimize(
    # minimizing overall differences between highest and lowest rankings of players in leagues while paying attention to numbers of countries
    Sum(Maximum(r[i]) - Minimum(r[i]) for i in range(nLeagues)) * 100
    - Sum(NValues(c[i]) for i in range(nLeagues))
)
