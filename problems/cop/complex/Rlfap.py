"""
See "Radio Link Frequency Assignment", by B. Cabon, S. de Givry, L. Lobjois, T. Schiex, J. Warners, Constraints An Int. J. 4(1): 79-89 (1999)

Examples of Execution:
  python3 Rlfap.py -data=Rlfap_card-scen-04.json -variant=card
  python3 Rlfap.py -data=Rlfap_span-scen-05.json -variant=span
  python3 Rlfap.py -data=Rlfap_max-graph-05.json -variant=max
"""

from pycsp3 import *

domains, variables, constraints, interferenceCosts, mobilityCosts = data
n = len(variables)

# f[i] is the frequency of the ith radio link
f = VarArray(size=n, dom=lambda i: domains[variables[i].domain])

satisfy(
    # managing pre-assigned frequencies
    [f[i] == v for i, (_, v, mob) in enumerate(variables) if v and not (variant("max") and mob)],

    # hard constraints on radio-links
    [expr(op, abs(f[i] - f[j]), k) for (i, j, op, k, wgt) in constraints if not (variant("max") and wgt)]
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
        Sum(ift(f[i] == v, 0, mobilityCosts[mob]) for i, (_, v, mob) in enumerate(variables) if v and mob)
        + Sum(ift(expr(op, abs(f[i] - f[j]), k), 0, interferenceCosts[wgt]) for (i, j, op, k, wgt) in constraints if wgt)
    )

""" Comments
1) expr allows us to build an expression (constraint) with an operator given as first parameter (possibly, a string)
   otherwise, it could have been written: abs(f[i] - f[j]) == k if op == "=" else abs(f[i] - f[j]) > k
"""
