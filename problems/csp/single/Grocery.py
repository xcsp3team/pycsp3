"""
See "Constraint Programming in Oz. A Tutorial" by C. Schulte and G. Smolka, 2001

A kid goes into a grocery store and buys four items.
The cashier charges $7.11, the kid pays and is about to leave when the cashier calls the kid back, and says
``Hold on, I multiplied the four items instead of adding them;
  I'll try again;
  Hah, with adding them the price still comes to $7.11''.
What were the prices of the four items?

Execution:
  python3 Grocery.py
"""

from pycsp3 import *

# x[i] is the price (multiplied by 100) of the ith item
x = VarArray(size=4, dom=range(711))

satisfy(
    # adding the prices of items corresponds to 711 cents
    Sum(x) == 711,

    # multiplying the prices of items corresponds to 711 cents (times 1000000)
    x[0] * x[1] * x[2] * x[3] == 711 * 100 * 100 * 100,

    # tag(symmetry-breaking)
    Increasing(x)
)

""" Comments
1) in some models of the literature, sometimes, the product is decomposed as for example:
  y = VarArray(size=2, dom=range(71100))
  satisfy(
     x[0] * x[1] == y[0],
     x[2] * x[3] == y[1],
     y[0] * y[1] == 711 * 100 * 100 * 100
  )
"""