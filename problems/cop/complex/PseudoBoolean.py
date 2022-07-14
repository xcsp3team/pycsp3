"""
See "The First Evaluation of Pseudo-Boolean Solvers (PB'05)" by Vasco M. Manquinho and Olivier Roussel. J. Satisf. Boolean Model. Comput. 2(1-4): 103-143 (2006)

Example of Execution:
  python3 PseudoBoolean.py -data=PseudoBoolean_example.opb -dataparser=PseudoBoolean_Parser.py
"""

from pycsp3 import *

n, e, constraints, objective = data  # n and e respectively denote the numbers of variables and constraints

x = VarArray(size=n, dom={0, 1})

satisfy(
    # respecting each linear constraint
    Sum(x[nums] * coeffs, condition=(op, limit)) for (coeffs, nums, op, limit) in constraints
)

if objective:
    minimize(
        # minimizing the linear objective
        [x[i] for i in objective.nums] * objective.coeffs
    )
