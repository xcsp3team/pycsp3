from pycsp3 import *

from multiprocessing import cpu_count, Pool
from pycsp3.tools.curser import OpOverrider

domains, routes = data.domains, data.routes
n = len(routes)
for c in data.softs:  # To speed up calculations
    c['neRelaxations'] = tuple(c['neRelaxations'])
    c['eqRelaxations'] = tuple(c['eqRelaxations'])
nSofts = len(data.softs)


def table_relaxable_link(c, short):
    def calculate_size():
        size = 0
        for l in range(kl - 1):
            if distance < t[l]:
                size += 1
        return size

    # print("Creation of table in parallel " + c)
    OpOverrider.disable()
    dom1, dom2 = routes[c.route1].domain, routes[c.route2].domain
    pol1, pol2 = routes[c.route1].polarization, routes[c.route2].polarization
    set_short_version = set()
    table = set()
    for f1 in domains[dom1]:
        for f2 in domains[dom2]:
            distance = abs(f1 - f2)
            if distance in set_short_version:
                continue
            for pol in range(4):
                p1 = 0 if pol < 2 else 1
                p2 = 1 if pol in {1, 3} else 0
                if (pol1, p1) in [(1, 0), (-1, 1)] or (pol2, p2) in [(1, 0), (-1, 1)]:
                    continue
                t = c.eqRelaxations if p1 == p2 else c.neRelaxations
                for kl in range(12):
                    if kl == 11 or distance >= t[kl]:  # for kl=11, we suppose t[kl] = 0
                        suffix = (p1, p2, kl, 0 if kl == 0 or distance >= t[kl - 1] else 1, 0 if kl <= 1 else calculate_size())
                        table.add((distance, *suffix) if short else (f1, f2, *suffix))
            # set_short_version.add(distance)  # not possible because parallel computation?
    OpOverrider.enable()
    return table


def soft_table(c, short=False):
    return pool.apply_async(table_relaxable_link, args=(c, short)).get()


print("Creating tables in parallel (started)...")
pool = Pool(processes=cpu_count())


def imperative(c):
    i, j = c.route1, c.route2
    if c.frequency:
        if c.gap == 0:
            return f[i] == f[j] if c.equality else f[i] != f[j]
        return dist(f[i], f[j]) == c.gap if c.equality else dist(f[i], f[j]) != c.gap
    return p[i] == p[j] if c.equality else p[i] != p[j]


def frequency_domain(i):
    return set(domains[routes[i].domain])


def polarization_domain(i):
    return {0, 1} if routes[i].polarization == 0 else {1} if routes[i].polarization == 1 else {0}


# f[i] is the frequency of the ith radio-link
f = VarArray(size=n, dom=frequency_domain)

# p[i] is the polarization of the ith radio-link
p = VarArray(size=n, dom=polarization_domain)

# k is the relaxation level to be optimized
k = Var(dom=range(12))

# v1[q] is 1 iff the qth pair of radio-electric compatibility constraints is violated when relaxing another level
v1 = VarArray(size=nSofts, dom={0, 1})

# v2[q] is the number of times the qth pair of radio-electric compatibility constraints is violated when relaxing more than one level
v2 = VarArray(size=nSofts, dom=range(11))

satisfy(
    # imperative constraints
    imperative(h) for h in data.hards
)

if not variant():
    satisfy(
        # relaxable radio-electric compatibility constraints
        (f[c.route1], f[c.route2], p[c.route1], p[c.route2], k, v1[i], v2[i]) in soft_table(c, False) for i, c in enumerate(data.softs)
    )

elif variant("short"):
    soft_links = [[False] * n for _ in range(n)]
    for c in data.softs:
        soft_links[c.route1][c.route2] = soft_links[c.route2][c.route1] = True


    def distance_domain(i, j):
        return {abs(f1 - f2) for f1 in domains[routes[i].domain] for f2 in domains[routes[j].domain]} if i < j and soft_links[i][j] else None


    # d[i][j] is the distance between the ith and the jth frequencies (for i < j when a soft link exists)
    d = VarArray(size=[n, n], dom=distance_domain)

    satisfy(
        # computing intermediary distances
        [d[i][j] == dist(f[i], f[j]) for i in range(n) for j in range(i + 1, n) if d[i][j]],

        # relaxable radio-electric compatibility constraints
        [(d[min(c.route1, c.route2)][max(c.route1, c.route2)], p[c.route1], p[c.route2], k, v1[i], v2[i]) in soft_table(c, True)
         for i, c in enumerate(data.softs)]
    )

minimize(
    k * (10 * nSofts ** 2) + Sum(v1) * (10 * nSofts) + Sum(v2)
)

# pool.close()
# pool.join()
print("Creating tables in parallel (finished)")
