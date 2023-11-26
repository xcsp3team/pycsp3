"""
This problem consists in finding a partition of the set of numbers {1, 2, ..., n} into two sets A and B such that:
  - A and B have the same cardinality
  - the sum of numbers in A is equal to the sum of numbers in B
  - the sum of squares of numbers in A is equal to the sum of squares of numbers in B
See Problem 049 on CSPLib.

## Data
  an integer n

## Model
  constraints: AllDifferent, Sum

## Execution
  - python NumberPartitioning.py -data=[number]

## Links
  - https://www.csplib.org/Problems/prob049/
  - https://www.cril.univ-artois.fr/XCSP22/competitions/csp/csp

## Tags
  recreational, xcsp22
"""

from pycsp3 import *

n = data or 8
assert n % 2 == 0, "The value of n must be even"
K1, K2 = n * (n + 1) // 4, n * (n + 1) * (2 * n + 1) // 12

# x[i] is the ith value of the first set
x = VarArray(size=n // 2, dom=range(1, n + 1))

# y[i] is the ith value of the second set
y = VarArray(size=n // 2, dom=range(1, n + 1))

satisfy(
    AllDifferent(x + y),

    # tag(power1)
    [
        Sum(x) == K1,
        Sum(y) == K1
    ],

    # tag(power2)
    [
        Sum(x[i] * x[i] for i in range(n // 2)) == K2,
        Sum(y[i] * y[i] for i in range(n // 2)) == K2
    ],

    # tag(symmetry-breaking)
    [
        x[0] == 1,
        Increasing(x, strict=True),
        Increasing(y, strict=True)
    ]
)
