"""
Example: python3 pycsp3/problems/csp/complex/Blackhole.py  -dataparser=pycsp3/problems/data/parsers/Blackhole_Random.py 13 3 0
"""

import random

from pycsp3.compiler import Compilation
from pycsp3.problems.data.parsing import *

nCardsPerSuit = ask_number("Number of cards per suit (e.g., 13)")
nCardsPerPile = ask_number("Number of cards per pile (e.g., 3)")
seed = ask_number("Seed")

nCards = 4 * nCardsPerSuit
nPiles = (nCards - 1) // nCardsPerPile
assert (nCards - 1) % nCardsPerPile == 0

random.seed(seed)
active_piles = list(range(nPiles))
piles = [[] for _ in range(nPiles)]

for i in range(1, nCards):
    r = random.randrange(len(active_piles))
    k = active_piles[r]
    piles[k].insert(0, i)
    if len(piles[k]) == nCardsPerPile:
        del active_piles[r]

data["nCardsPerSuit"] = nCardsPerSuit
data["piles"] = piles
print(str(seed).format("{:03d}"))

Compilation.string_data = "-" + "-".join(str(v) for v in (nCardsPerSuit, nCardsPerPile, "{:02d}".format(seed)))
