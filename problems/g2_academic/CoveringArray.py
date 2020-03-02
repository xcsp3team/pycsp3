from pycsp3 import *
from math import factorial

"""
 Problem 045 at CSPLib
"""

t, k, g, b = data.t, data.k, data.g, data.b
n = factorial(k) // factorial(t) // factorial(k - t)
d = g ** t


def table():
    def value(prod, comb):
        return sum(prod[a] * g ** i for i, a in enumerate(reversed(comb)))

    return {tuple(value(prod, comb) for comb in combinations(range(k), t)) for prod in product(range(g), repeat=k)}


p = VarArray(size=[n, d], dom=range(b))

v = VarArray(size=[n, b], dom=range(d))

satisfy(
    [AllDifferent(p[i]) for i in range(n)],

    [Channel(p[i], v[i]) for i in range(n)],

    [v[:, j] in table() for j in range(b)]
)
