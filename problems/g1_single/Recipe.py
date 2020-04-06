"""
From the Minizinc tutorial

Execution:
  python3 Recipe.py
"""

from pycsp3 import *

# b is the number of banana cakes
b = Var(range(100))

# c is the number of chocolate cakes
c = Var(range(100))

satisfy(
    # using at most 4000 grams of flour
    250 * b + 200 * c <= 4000,

    # using at most 6 bananas
    2 * b <= 6,

    # using at most 2000 grams of sugar
    75 * b + 150 * c <= 2000,

    # using at most 500 grams of butter
    100 * b + 150 * c <= 500,

    # using at most 500 grams of cocoa
    75 * c <= 500
)

maximize(
    # maximizing the profit (400 and 450 cents for each banana and chocolate cake, respectively)
    b * 400 + c * 450
)
