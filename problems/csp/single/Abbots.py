"""
The Abbot's Puzzle (from "Amusements in Mathematics, Dudeney", number 110)

See also https://www.comp.nus.edu.sg/~henz/projects/puzzles/arith/index.html

We know that 100 bushels of corn were distributed among 100 people.
Each man received three bushels, each woman two, and each child half a bushel.
There are five times as many women as men.
How many men, women, and children were there?

Execution:
  python3 Abbots.py
"""

from pycsp3 import *

# m is the number of men
m = Var(range(100))

# w is the number of women
w = Var(range(100))

# m is the number of children
c = Var(range(100))

satisfy(
    m + w + c == 100,
    m * 6 + w * 4 + c == 200,
    m * 5 == w
)
