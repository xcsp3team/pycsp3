"""
See "Solving the Wastewater Treatment Plant Problem with SMT", by Miquel Bofill, Víctor Muñoz, Javier Murillo. CoRR abs/1609.05367 (2016)

Examples of Execution:
  python3 Wwtpp.py -data=Wwtpp_ex04400.json
  python3 Wwtpp.py -data=Wwtpp_ex04400.json -variant=short
"""

from pycsp3 import *

nIndustries, nPeriods, plantCapacity, tankFlow, tankCapacity, sd, spans = data  # sd for schedule flow of discharge


def table_compatibility(i, j):
    if j in {nPeriods - 1, nPeriods} or (j - 1 == 0 and sd[i][0] == 0):
        return {(0, 0)}
    tf, tc = tankFlow[i], tankCapacity[i]
    tbl = {(0, ANY)} | {(tf, v) for v in range(tf, tc + 1)} | {(v, v) for v in range(1, min(tf, tc + 1))}
    return tbl if variant("short") else to_ordinary_table(tbl, [tf + 1, tc + 1])


def table_spanning(i, start, stop):
    return {tuple([0] * (stop - start)), tuple(sd[i][start:stop])}


# b[i][j] is the flow stored in buffer i at the end of period j
b = VarArray(size=[nIndustries, nPeriods], dom=lambda i, j: {0} if (j == 0 and sd[i][0] == 0) or j == nPeriods - 1 else range(tankCapacity[i] + 1))

# d[i][j] is the flow discharged from buffer (or industry) i during time period j
d = VarArray(size=[nIndustries, nPeriods], dom=lambda i, j: {0} if j == 0 else range(tankFlow[i] + 1))

# c[i][j] is the actual capacity requirement of industry i during time period j
c = VarArray(size=[nIndustries, nPeriods], dom=lambda i, j: {0, sd[i][j]} if sd[i][j] != 0 else None)

satisfy(
    # not exceeding the Wastewater Treatment Plant
    [Sum(c[:, j] + d[:, j]) <= plantCapacity for j in range(nPeriods)],

    # managing scheduled discharge flows at period 0
    [Sum(b[i][0], c[i][0]) == sd[i][0] for i in range(nIndustries) if sd[i][0] != 0],

    # managing scheduled discharge flows at all periods except 0
    [[b[i][j], b[i][j - 1], d[i][j], c[i][j]] * [1, -1, 1, 1 if c[i][j] else None] == sd[i][j] for i in range(nIndustries) for j in range(1, nPeriods)],

    # ensuring compatibility between stored and discharge flows
    [(d[i][j], b[i][j - 1]) in table_compatibility(i, j) for i in range(nIndustries) for j in range(1, nPeriods)],

    # spanning constraints
    [c[i][start:stop] in table_spanning(i, start, stop) for (i, start, stop) in spans]
)

""" Comments
1) when managing scheduled discharge flows, we have a list with four cells for variables and integers.
 However, when there is the special value None (at the fourth position in both lists), the two lists will be automatically reduced to three cells.
"""