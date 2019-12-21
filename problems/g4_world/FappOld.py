from pyCSP3 import *

domains, routes = data.domains, data.routes
n = len(routes)
hards, softs = data.hards, data.softs
nHards, nSofts = len(hards) if hards else 0, len(softs)

cache = {}  # for tables


def frequency_domain(i):
    return set(domains[routes[i].domain])


def polarization_domain(i):
    return {0, 1} if routes[i].polarization == 0 else {1} if routes[i].polarization == 1 else {0}


def create_tuple():
    pass


def create_tuple_short_version():
    pass


def table_relaxable_link(c, short_version=False):
    OpOverrider.disable()
    dom1, dom2 = routes[c.route1].domain, routes[c.route2].domain
    pol1, pol2 = routes[c.route1].polarization, routes[c.route2].polarization
    key = str(dom1) + "*" + str(dom2) + "*" + str(pol1) + "*" + str(pol2) + "*" + ' '.join([str(e) for e in c.eqRelaxations]) + "*" + ' '.join(
        [str(e) for e in c.neRelaxations])
    if key in cache:
        return cache[key]
    set_short_version = set()
    table = []
    for f1 in domains[dom1]:
        for f2 in domains[dom2]:
            distance = abs(f1 - f2)
            if short_version and distance in set_short_version:
                continue
            for pol in range(4):
                p1 = 0 if pol < 2 else 1
                p2 = 1 if pol in {1, 3} else 0
                if (pol1, p1) in {(1, 0), (-1, 1)} or (pol2, p2) in {(1, 0), (-1, 1)}:
                    continue
                t = c.eqRelaxations if p1 == p2 else c.neRelaxations
                for k in range(12):
                    if k == 11 or distance >= t[k]:  # for k=11, we suppose t[k] = 0
                        size = len([l for l in range(0, k - 1) if distance < t[l]])
                        if short_version:
                            table.append((distance, p1, p2, k, 0 if k == 0 or distance >= t[k - 1] else 1, 0 if k <= 1 else size))
                        else:
                            table.append((f1, f2, p1, p2, k, 0 if k == 0 or distance >= t[k - 1] else 1, 0 if k <= 1 else size))
            set_short_version.add(distance)
    cache[key] = table
    OpOverrider.enable()
    return table


def distances(i, j):
    dom1, dom2 = domains[routes[i].domain], domains[routes[j].domain]
    return {abs(f1 - f2) for f1 in dom1 for f2 in dom2}


def soft_links():
    t = [[False] * n for _ in range(n)]
    for c in softs:
        i, j = c.route1, c.route2
        t[i][j] = True
        t[j][i] = True
    return t


def imperative(c):
    i, j = c.route1, c.route2
    if c.frequency:
        if c.gap == 0:
            return f[i] == f[j] if c.equality else f[i] != f[j]
        return dist(f[i], f[j]) == c.gap if c.equality else dist(f[i], f[j]) != c.gap
    return p[i] == p[j] if c.equality else p[i] != p[j]


softLinks = soft_links()  # used by model m2 (not currently implemented)

#  f[i] is the frequency of the ith radio-link
f = VarArray(size=[n], dom=frequency_domain)

#  p[i] is the polarization of the ith radio-link
p = VarArray(size=[n], dom=polarization_domain)

# k is the relaxation level to be optimized
k = Var(dom=range(12))

#  v1[q] is 1 iff the qth pair of radio-electric compatibility constraints is violated when relaxing another level
v1 = VarArray(size=[nSofts], dom={0, 1})

#  v2[q] is the number of times the qth pair of radio-electric compatibility constraints is violated when relaxing more than one level
v2 = VarArray(size=[nSofts], dom=range(11))

satisfy(
    # imperative constraints
    [imperative(h) for h in hards]
)

if not variant():
    satisfy(
        # relaxable radio-electric compatibility constraints
        (f[c.route1], f[c.route2], p[c.route1], p[c.route2], k, v1[i], v2[i]) in table_relaxable_link(c) for i, c in enumerate(softs)
    )

elif variant("short"):
    # d[i][j] is the distance between the ith and the jth frequencies (for i < j when a soft link exists)
    d = VarArray(size=[n, n], dom=lambda i, j: distances(i, j) if i < j and softLinks[i][j] else None)

    satisfy(

        # computing intermediary distances
        [d[i][j] == dist(f[i], f[j]) for i in range(n) for j in range(i + 1, n) if softLinks[i][j]],

        # relaxable radio-electric compatibility constraints
        [((d[c.route1][c.route2] if c.route1 < c.route2 else d[c.route2][c.route1]), p[c.route1], p[c.route2], k, v1[i], v2[i]) in table_relaxable_link(c, True)
         for i, c in enumerate(softs)]

    )

minimize(
    k * (10 * nSofts ** 2) + Sum(v1 * ([10 * nSofts] * nSofts)) + Sum(v2)
)
