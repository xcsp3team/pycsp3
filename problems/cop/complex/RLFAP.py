"""
Radio Link Frequency Assignment.

## Data Example
  scen01.json

## Model
  constraints: Maximum, NValues, Sum

## Execution
  - python RLFAP.py -data=<datafile.json> -variant=card
  - python RLFAP.py -data=<datafile.json> -variant=span
  - python RLFAP.py -data=<datafile.txt> -variant=max

## Links
  - https://link.springer.com/article/10.1023/A:1009812409930
  - https://www.cril.univ-artois.fr/XCSP22/competitions/cop/cop

## Tags
  real, xcsp22
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
