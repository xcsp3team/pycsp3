from pycsp3 import *

from pycsp3.tools.curser import OpOverrider

domains = [data.domains[route.domain] for route in data.routes]  # we discard the indirection
polarizations = [route.polarization for route in data.routes]
n = len(data.routes)

for c in data.softs:  # To speed up calculations
    c['neRelaxations'] = tuple(c['neRelaxations'])
    c['eqRelaxations'] = tuple(c['eqRelaxations'])
hards, softs = data.hards, data.softs
nSofts = len(data.softs)


def expr_hard(scp, equality, gap):
    x, y = scp
    if gap == 0:
        return x == y if equality else x != y
    return dist(x, y) == gap if equality else dist(x, y) != c.gap


def table_soft(c, short_table=True):
    def calculate_size():
        size = 0
        for l in range(kl - 1):
            if distance < t[l]:
                size += 1
        return size

    OpOverrider.disable()
    i, j = c.route1, c.route2
    table, set_short_version = set(), set()
    for f1 in domains[i]:
        for f2 in domains[j]:
            distance = abs(f1 - f2)
            if distance in set_short_version:
                continue
            for pol in range(4):
                p1 = 0 if pol < 2 else 1
                p2 = 1 if pol in {1, 3} else 0
                if (polarizations[i], p1) in [(1, 0), (-1, 1)] or (polarizations[j], p2) in [(1, 0), (-1, 1)]:
                    continue
                t = c.eqRelaxations if p1 == p2 else c.neRelaxations
                for kl in range(12):
                    if kl == 11 or distance >= t[kl]:  # for kl=11, we suppose t[kl] = 0
                        suffix = (p1, p2, kl, 0 if kl == 0 or distance >= t[kl - 1] else 1, 0 if kl <= 1 else calculate_size())
                        table.add((distance, *suffix) if short_table else (f1, f2, *suffix))
                        # set_short_version.add(distance)  # not possible to use that because parallel computation?
    OpOverrider.enable()
    return table


# f[i] is the frequency of the ith radio-link
f = VarArray(size=n, dom=lambda i: domains[i])

# p[i] is the polarization of the ith radio-link
p = VarArray(size=n, dom=lambda i: {0, 1} if polarizations[i] == 0 else {1} if polarizations[i] == 1 else {0})

# k is the relaxation level to be optimized
k = Var(dom=range(12))

# v1[q] is 1 iff the qth pair of radio-electric compatibility constraints is violated when relaxing another level
v1 = VarArray(size=nSofts, dom={0, 1})

# v2[q] is the number of times the qth pair of radio-electric compatibility constraints is violated when relaxing more than one level
v2 = VarArray(size=nSofts, dom=range(11))

satisfy(
    # imperative constraints
    expr_hard((f[i], f[j]) if fq else (p[i], p[j]), eq, gap) for i, j, fq, eq, gap in ((h.route1, h.route2, h.frequency, h.equality, h.gap) for h in hards)
)

if not variant():
    satisfy(
        # soft radio-electric compatibility constraints
        (f[i], f[j], p[i], p[j], k, v1[l], v2[l]) in table_soft(s, False) for i, j, l, s in ((s.route1, s.route2, l, s) for l, s in enumerate(softs))

    )

elif variant("short"):
    soft_links = [[False] * n for _ in range(n)]
    for c in data.softs:
        soft_links[c.route1][c.route2] = soft_links[c.route2][c.route1] = True

    # d[i][j] is the distance between the ith and the jth frequencies (for i < j when a soft link exists)
    d = VarArray(size=[n, n], dom=lambda i, j: {abs(f1 - f2) for f1 in domains[i] for f2 in domains[j]} if i < j and soft_links[i][j] else None)

    satisfy(
        # computing intermediary distances
        [d[i][j] == dist(f[i], f[j]) for i in range(n) for j in range(i + 1, n) if d[i][j]],

        # soft radio-electric compatibility constraints
        [(d[min(i, j)][max(i, j)], p[i], p[j], k, v1[l], v2[l]) in table_soft(s) for i, j, l, s in ((s.route1, s.route2, l, s) for l, s in enumerate(softs))]
    )

minimize(
    k * (10 * nSofts ** 2) + Sum(v1) * (10 * nSofts) + Sum(v2)
)
