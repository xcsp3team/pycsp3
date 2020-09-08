"""
A problem for testing propagation speed of constraint solvers.

See MiniZinc challenges.

Execution:
  python3 PropStress.py
  python3 PropStress.py -data=20
"""

from pycsp3 import *

n = data or 10
k, m = n, n  # k : Number of times round the loop ; m : m^2 propagators per change of loop ; n : Number of iterations of change per loop

x = VarArray(size=m + 1, dom=range(k * n + 1))

y = VarArray(size=n + 1, dom=range(k * n + 1))

satisfy(
    [y[i - 1] - y[i] <= 0 for i in range(2, n + 1)],

    [y[0] - y[i] <= n - i + 1 for i in range(1, n + 1)],

    y[n] - x[0] <= 0,

    [x[i] - x[j] <= 0 for i in range(m + 1) for j in range(i + 1, m + 1)],

    x[m] - y[0] <= -2
)
