from pycsp3 import *

nIndustries, nPeriods = data.nIndustries, data.nPeriods
plantCapacity = data.plantCapacity
tankFlow, tankCapacity = data.tankFlow, data.tankCapacity
sd = data.sd  # schedule flow of discharge
spans = data.spans


def compatibility(i, j):
    scp = [d[i][j], b[i][j - 1]]
    if j in {nPeriods - 1, nPeriods} or (j - 1 == 0 and sd[i][0] == 0):
        return scp in [(0, 0)]
    flow, capacity = tankFlow[i], tankCapacity[i]
    table = [(0, ANY)] + [(flow, v) for v in range(flow, capacity + 1)] + [(v, v) for v in range(1, min(flow, capacity + 1))]
    if not variant():
        return scp in to_ordinary_table(table, [flow + 1, capacity + 1])
    elif variant("short"):
        return scp in table


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
    [[b[i][j], b[i][j - 1], d[i][j], c[i][j]] * ([1, -1, 1] + ([1] if c[i][j] else [])) == sd[i][j] for i in range(nIndustries) for j in
     range(1, nPeriods)],

    #  ensuring compatibility between stored and discharge flows
    [compatibility(i, j) for i in range(nIndustries) for j in range(1, nPeriods)],

    # spanning constraints
    [c[i][start:end] in {tuple([0] * (end - start)), tuple(sd[i][start:end])} for (i, start, end) in spans]
)
