"""
For every odd positive integer n (and m = (n−1)/2), the 2cc Hadamard matrix Legendre pairs are defined from m quadratic constraints and 2 linear constraints.

See Problem 084 on CSPLib

## Data
  a unique integer, the order of the problem instance

## Model
  constraints: Sum

## Execution (example)
  - python Hadamard.py -data=35

## Links
  - https://www.csplib.org/Problems/prob084/
  - https://www.cril.univ-artois.fr/XCSP22/competitions/cop/cop

## Tags
  academic, csplib, xcsp22
"""

from pycsp3 import *

n = data or 35
assert n % 2 == 1
m = (n - 1) // 2

# x[i] is the ith value of the first sequence
x = VarArray(size=n, dom={-1, 1})

# y[i] is the ith value of the second sequence
y = VarArray(size=n, dom={-1, 1})

satisfy(
    Sum(x) == 1,

    Sum(y) == 1,

    # quadratic constraints
    [Sum(x[i] * x[i + k] for i in range(n)) + Sum(y[i] * y[i + k] for i in range(n)) == -2 for k in range(1, m + 1)]
)

"""
1) Note that, by auto-adjustment of array indexing:
  x[i + k]
is equivalent to:
  x[(i + k) % n] 
 You can avoid this behavior by using the option -dontadjustindexing
"""
