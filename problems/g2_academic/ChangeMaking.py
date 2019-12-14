from pycsp3 import *

# See https://en.wikipedia.org/wiki/Change-making_problem

k = data.amount

# c1 is the number of coins of 1 cent
c1 = Var(range(50))

# c5 is the number of coins of 5 cents
c5 = Var(range(50))

# c10 is the number of coins of 10 cents
c10 = Var(range(50))

# c20 is the number of coins of 20 cents
c20 = Var(range(50))

# c50 is the number of coins of 50 cents
c50 = Var(range(50))

# e1 is the number of coins of 1 euro
e1 = Var(range(50))

# e2 is the number of coins of 2 euros
e2 = Var(range(50))

satisfy(
    # the given change must be correct
    [c1, c5, c10, c20, c50, e1, e2] * [1, 5, 10, 20, 50, 100, 200] == k
)

minimize(
    # the given change must have the minimum number of coins
    c1 + c5 + c10 + c20 + c50 + e1 + e2
)
