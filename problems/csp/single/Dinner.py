"""
My son came to me the other day and said, "Dad, I need help with a math problem."
The problem went like this:
- We're going out to dinner taking 1-6 grandparents, 1-10 parents and/or 1-40 children
- Grandparents cost $3 for dinner, parents $2 and children $0.50
- There must be 20 total people at dinner and it must cost $20
How many grandparents, parents and children are going to dinner?

Execution:
  python3 Dinner.py
"""

from pycsp3 import *

# g is the number of grandparents
g = Var(range(1, 7))

# p is the number of parents
p = Var(range(1, 11))

# c is the number of children
c = Var(range(1, 41))

satisfy(
    g * 6 + p * 2 + c * 1 == 40,

    g + p + c == 20
)
