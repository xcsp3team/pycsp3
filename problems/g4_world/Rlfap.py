from pycsp3 import *

"""
 See "Radio Link Frequency Assignment", by B. Cabon, S. de Givry, L. Lobjois, T. Schiex, J. Warners, Constraints An Int. J. 4(1): 79-89 (1999)
"""

domains, variables, constraints, interferenceCosts, mobilityCosts = data
domains = [domains[variable.domain] for variable in variables]  # we skip the indirection
d = dict((variable.number, i) for i, variable in enumerate(variables))  # dictionary to get variables (their indexes) from their original numbers
n = len(variables)


def hard(x, y, eq, k):
    return abs(x - y) == k if eq else abs(x - y) > k


# f[i] is the frequency of the ith radio link
f = VarArray(size=n, dom=lambda i: set(domains[i]))

satisfy(
    #  managing pre-assigned frequencies
    [f[d[num]] == val for (num, _, val, mob) in variables if val and not (variant("max") and mob)],

    # hard constraints on radio-links
    [hard(f[d[num1]], f[d[num2]], eq, k) for (num1, num2, eq, k, wgt) in constraints if not (variant("max") and wgt)]
)

if variant("span"):
    minimize(
        # minimizing the largest frequency
        Maximum(f)
    )
elif variant("card"):
    minimize(
        # minimizing the number of used frequencies
        NValues(f)
    )
elif variant("max"):
    minimize(
        # minimizing the sum of violation costs
        Sum(ift(f[d[num]] == val, 0, mobilityCosts[mob]) for (num, _, val, mob) in variables if val and mob)
        + Sum(ift(hard(f[d[num1]], f[d[num2]], eq, k), 0, interferenceCosts[wgt]) for (num1, num2, eq, k, wgt) in constraints if wgt)
    )
