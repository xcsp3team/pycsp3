"""
Illustrative problem used in the PyCSP3 guide (See Chapter 1)

Once upon a time, there were three friends called Xavier, Yannick and Zachary, who wanted to travel
the world. However, in their times and countries, they were obliged to do their military service. So,
each friend had to decide if he travels after or before his due military service. Xavier and Yannick
wanted to travel together. Xavier and Zachary also wanted to travel together. However, because
Yannick and Zachary didn’t always get along very well, they preferred not traveling together. Can
the three friends be satisfied?

Example of Execution:
  python3 TravelingWorld.py
  python3 TravelingWorld.py -variant="integer"
"""

from pycsp3 import *

if not variant():
    a, b = "a", "b"  # two symbols

    x = Var(a, b)
    y = Var(a, b)
    z = Var(a, b)

    satisfy(
        (x, y) in {(a, a), (b, b)},
        (x, z) in {(a, a), (b, b)},
        (y, z) in {(a, b), (b, a)}
    )
elif variant("integer"):

    x = Var(0, 1)
    y = Var(0, 1)
    z = Var(0, 1)

    satisfy(
        (x, y) in {(0, 0), (1, 1)},
        (x, z) in {(0, 0), (1, 1)},
        (y, z) in {(0, 1), (1, 0)}
    )
