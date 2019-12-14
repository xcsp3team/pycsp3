from pycsp3 import *

nPlayers = data.nPlayers
leagueSize = data.leagueSize
rankings, countries = data.playerRankings, data.playerCountries

nLeagues = nPlayers // leagueSize + (1 if nPlayers % leagueSize != 0 else 0)
nCountries = len(set(countries))


def size(i):
    nFullLeagues = nLeagues if nPlayers % leagueSize == 0 else nLeagues - (leagueSize - nPlayers % leagueSize)
    return leagueSize + (0 if i < nFullLeagues else -1)


table1 = {(i, rank, countries[i]) for i, rank in enumerate(rankings)}
table2 = {(i, rank, *[1 if j - 2 + 1 == countries[i] else ANY for j in range(2, 2 + nCountries)]) for i, rank in enumerate(rankings)}

# p[i][j] is the jth player of the ith league
p = VarArray(size=[nLeagues, leagueSize], dom=lambda i, j: range(nPlayers) if j < size(i) else None)

# r[i][j] is the ranking of the jth player of the ith league
r = VarArray(size=[nLeagues, leagueSize], dom=lambda i, j: set(rankings) if j < size(i) else None)

# l[i] is the lowest ranking of a player of the ith league
l = VarArray(size=nLeagues, dom=set(rankings))

# h[i] is the highest ranking of a player of the ith league
h = VarArray(size=nLeagues, dom=set(rankings))

# d[i] is the difference between the highest and lowest rankings of players of the ith league
d = VarArray(size=nLeagues, dom={0} | set(rankings))

# nc[i] is the number of countries for players of the ith league
nc = VarArray(size=nLeagues, dom=lambda i: range(min(nCountries, size(i)) + 1))

satisfy(
    AllDifferent(p),

    [Minimum(r[i]) == l[i] for i in range(nLeagues)],

    [Maximum(r[i]) == h[i] for i in range(nLeagues)],

    [d[i] == h[i] - l[i] for i in range(nLeagues)]
)

if not variant():
    # c[i][j] is the country of the jth player of the ith league
    c = VarArray(size=[nLeagues, leagueSize], dom=lambda i, j: set(countries) if j < size(i) else None)

    satisfy(
        [(p[i][j], r[i][j], c[i][j]) in table1 for i in range(nLeagues) for j in range(size(i))],

        [NValues(c[i]) == nc[i] for i in range(nLeagues)]
    )

elif variant("01"):  # TODO not sure that this variant is correct
    # c[i][k] is 1 if at least one player of the ith league is from country k
    c = VarArray(size=[nLeagues, nCountries], dom={0, 1})

    satisfy(
        [(p[i][j], r[i][j], *c[i]) in table2 for i in range(nLeagues) for j in range(size(i))],

        [imply(c[i][k] == 0, p[i][j] != m) for (i, j, k, m) in product(range(nLeagues), range(leagueSize), range(nCountries), range(nPlayers))
         if j < size(i) and countries[m] == k + 1],

        [Sum(c[i]) == nc[i] for i in range(nLeagues)]
    )

minimize(
    Sum(d) * 100 - Sum(nc)
)

# Sum(x * 100 for x in diffrlp) + Sum(-x for x in nc)
# Sum(x * 100 for x in diffrlp) + Sum(x * -1 for x in nc)
# Sum((diffrlp + nc) * ([100] * nLeagues + [-1] * nLeagues))
# diffrlp * ([100] * nLeagues) + nc * ([-1] * nLeagues)
