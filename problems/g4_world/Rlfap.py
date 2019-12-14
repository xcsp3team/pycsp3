from pycsp3 import *

domains = data.domains
vars, ctrs = data.vars, data.ctrs
n = len(vars)
interferenceCosts = data.interferenceCosts
mobilityCosts = data.mobilityCosts


def imperative(c):
    x, y = map[c.x], map[c.y]
    return dist(x, y) == c.limit if c.equality else dist(x, y) > c.limit


# f[i] is the frequency of the ith radio link
f = VarArray(size=n, dom=lambda i: set(domains[vars[i].domain]))

map = dict((vars[i].number, f[i]) for i in range(n))

if variant("span") or variant("card"):  # all constraints are considered to be hard for these problems
    satisfy(
        #  managing pre-assigned frequencies
        [map[var.number] == var.value for var in vars if var.value],

        # hard constraints on radio-links
        [imperative(c) for c in ctrs]
    )

if variant("span"):
    minimize(
        # minimizing the largest frequency
        Maximum(f)
    )

if variant("card"):
    minimize(
        # minimizing the number of used frequencies
        NValues(f)
    )
