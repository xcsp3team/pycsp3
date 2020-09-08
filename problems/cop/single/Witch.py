"""
A toy problem from my course about CP.

Execution:
  python3 Witch.py
"""

from pycsp3 import *

# x is the number of magic potions for love
x = Var(range(400))

# y is the number of magic potions for youth
y = Var(range(400))

satisfy(
    [x, y] * [3, 2] <= 800,
    [x, y] * [1, 3] <= 700,
    [x, y] * [1, 2] <= 400
)

maximize(
    4 * x + 5 * y
)
