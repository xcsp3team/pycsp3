from pycsp3 import *

"""
 See "Radio Link Frequency Assignment", by B. Cabon, S. de Givry, L. Lobjois, T. Schiex, J. Warners, Constraints An Int. J. 4(1): 79-89 (1999)
"""

domains, variables, constraints, interferenceCosts, mobilityCosts = data
domains = [domains[variable.domain] for variable in variables]  # we skip the indirection
d = dict((variable.number, i) for i, variable in enumerate(variables))  # dictionary to get variables (their indexes) from their numbers
n = len(variables)


def hard(x, y, eq, k):
    return abs(x - y) == k if eq else abs(x - y) > k


# f[i] is the frequency of the ith radio link
f = VarArray(size=n, dom=lambda i: set(domains[i]))

if variant("span") or variant("card"):  # all constraints are considered to be hard for these problems
    satisfy(
        #  managing pre-assigned frequencies
        [f[d[nb]] == v for (nb, _, v, _) in variables if v],

        # hard constraints on radio-links
        [abs(f[d[nb1]] - f[d[nb2]]) == k if eq else abs(f[d[nb1]] - f[d[nb2]]) > k for (nb1, nb2, eq, k, _) in constraints]
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

if variant("max"):
    satisfy(
        #  managing pre-assigned frequencies
        [f[d[nb]] == v for (nb, _, v, mobility) in variables if v and not mobility],

        # hard constraints on radio-links
        [hard(f[d[nb1]], f[d[nb2]], eq, k) for (nb1, nb2, eq, k, weight) in constraints if not weight]

    )

    minimize(
        # minimizing the sum of violation costs
        Sum(ift(f[d[nb]] == v, 0, mobilityCosts[mobility]) for (nb, _, v, mobility) in variables if v and mobility)
        + Sum(ift(hard(f[d[nb1]], f[d[nb2]], eq, k), 0, interferenceCosts[weight]) for (nb1, nb2, eq, k, weight) in constraints if weight)
    )



# [abs(f[d[nb1]] - f[d[nb2]]) == k if eq else abs(f[d[nb1]] - f[d[nb2]]) > k for (nb1, nb2, eq, k, weight) in constraints if not weight]
