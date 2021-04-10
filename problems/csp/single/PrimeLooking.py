"""
See Model in OscaR

Martin Gardner Problem:
 * Call a number "prime-looking" if it is composite but not divisible by 2,3 or 5.
 * The three smallest prime-looking numbers are 49, 77 and 91.
 * There are 168 prime numbers less than 1000.
 * How many prime-looking numbers are there less than 1000?

Example of Execution:
  python3 PrimeLooking.py -solver=[ace,v,limit=no]
"""

from pycsp3 import *

# the number we look for
x = Var(range(1000))

# a first divider
d1 = Var(range(2, 1000))

# a second divider
d2 = Var(range(2, 1000))

satisfy(
    x == d1 * d2,
    x % 2 != 0,
    x % 3 != 0,
    x % 5 != 0,
    d1 <= d2
)
