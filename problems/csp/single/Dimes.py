"""
Dad wants one-cent, two-cent, three-cent, five-cent, and ten-cent stamps.
He said to get four each of two sorts and three each of the others, but I've
forgotten which. He gave me exactly enough to buy them; just these dimes."
How many stamps of each type does Dad want? A dime is worth ten cents.
-- J.A.H. Hunter

Execution:
  python3 Dimes.py
"""

from pycsp3 import *

# x is the number of dimes
x = Var(range(26))  # 26 is a safe upper bound

# s[i] is the number of stamps of value 1, 2, 3, 5 and 10 according to i
s = VarArray(size=5, dom={3, 4})

satisfy(
    s * [1, 2, 3, 5, 10] == x * 10
)

""" Comments
1) [1, 2, 3, 5, 10] * s cannot work (because the list of integers if not built from cp_array)
   one should write: cp_array(1, 2, 3, 5, 10) * s

2) there are two solutions
"""