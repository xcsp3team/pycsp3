"""
See https://en.wikipedia.org/wiki/Dudeney_number

In number theory, a Dudeney number in a given number base b is a natural number
equal to the perfect cube of another natural number such that the digit sum
of the first natural number is equal to the second.
The name derives from Henry Dudeney, who noted the existence of these numbers in one of his puzzles.

There are 5 non trivial numbers for base 10, and the highest such number is formed of 5 digits.
Below, the model is given for base 10.

Execution:
  python3 Dudeney.py
"""

from pycsp3 import *
from math import ceil

nDigits = 5  # for base 10

# n is a (non-trivial) Dudeney number
n = Var(range(2, 10 ** nDigits))

# s is the perfect cubic root of n
s = Var(range(ceil((10 ** nDigits) ** (1 / 3)) + 1))

# d[i] is the ith digit of the Dudeney number
d = VarArray(size=nDigits, dom=range(10))

satisfy(
    n == s * s * s,

    Sum(d) == s,

    d * [10 ** (nDigits - i - 1) for i in range(nDigits)] == n
)
