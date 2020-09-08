"""
The classical "Pigeon-hole" problem (See https://en.wikipedia.org/wiki/Pigeonhole_principle)

It can be useful to test the efficiency of filtering/reasoning algorithms.

Execution:
  python3 Pigeons.py
  python3 Pigeons.py -data=10
"""

from pycsp3 import *

n = data or 8 # number of pigeons

# p[i] is the hole where is put the ith pigeon
p = VarArray(size=n, dom=range(n - 1))

if not variant():
    satisfy(
        AllDifferent(p)
    )

elif variant("dec"):
    satisfy(
        p[i] != p[j] for i in range(n) for j in range(i + 1, n)
    )
