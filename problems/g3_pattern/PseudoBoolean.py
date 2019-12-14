from pycsp3 import *

n, e = data.n, data.e  # number of variables and constraints
constraints, objective = data.constraints, data.objective


x = VarArray(size=n, dom={0, 1})


satisfy(
    # respecting each linear constraint
    [Sum([x[i] for i in c.nums] * c.coeffs, condition=(c.op, c.limit)) for c in constraints]
)

if objective:
    minimize(
        # minimizing the linear objective
        [x[i] for i in objective.nums] * objective.coeffs
    )

